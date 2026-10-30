"""
Process Execution Engine for Scripts Hub
Manages parallel QProcess executions, output streaming, child tree termination,
and external dependency health checks.
"""

import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QObject, QProcess, Signal


class TaskInstance:
    def __init__(self, task_id: str, script_id: str, script_name: str, process: QProcess, args: List[str]):
        self.task_id = task_id
        self.script_id = script_id
        self.script_name = script_name
        self.process = process
        self.args = args
        self.start_time = datetime.now()
        self.status = "RUNNING"
        self.logs: List[str] = []
        self.exit_code: Optional[int] = None


class ProcessManager(QObject):
    task_started = Signal(str, str)             # task_id, script_id
    task_output = Signal(str, str, bool)        # task_id, text, is_error
    task_finished = Signal(str, int, str)       # task_id, exit_code, status
    active_count_changed = Signal(int)          # active_tasks_count

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.tasks: Dict[str, TaskInstance] = {}
        self._task_counter = 0

    def check_dependency(self, tool_name: str) -> bool:
        """Check if an external CLI or tool is available in PATH or known locations."""
        if shutil.which(tool_name) is not None:
            return True

        # Check Python 3.14 Scripts folder for whisper.exe
        if tool_name.lower() == "whisper":
            py314_whisper = Path(r"C:\Users\Sanjay D\AppData\Local\Programs\Python\Python314\Scripts\whisper.exe")
            if py314_whisper.exists():
                return True

        return False

    def get_active_tasks(self) -> List[TaskInstance]:
        return [t for t in self.tasks.values() if t.status == "RUNNING"]

    def is_script_running(self, script_id: str) -> bool:
        return any(t.script_id == script_id and t.status == "RUNNING" for t in self.tasks.values())

    def get_latest_task_for_script(self, script_id: str) -> Optional[TaskInstance]:
        matches = [t for t in self.tasks.values() if t.script_id == script_id]
        return matches[-1] if matches else None

    def launch_script(
        self,
        script_info: Dict,
        param_args: List[str],
        working_dir: Optional[Path] = None
    ) -> str:
        """Spawn a new independent script process."""
        self._task_counter += 1
        script_id = script_info.get("id", "unknown")
        script_name = script_info.get("name", script_id)
        task_id = f"{script_id}_{self._task_counter}"

        script_file = script_info.get("script_file")
        base_dir = working_dir or Path(__file__).resolve().parent.parent
        full_script_path = base_dir / script_file

        if not full_script_path.exists():
            raise FileNotFoundError(f"Script file not found: {full_script_path}")

        # Choose Python interpreter
        python_exe = sys.executable

        # Set up QProcess
        process = QProcess(self)
        process.setProgram(python_exe)
        # Use -u for unbuffered Python standard output
        process_args = ["-u", str(full_script_path)] + param_args
        process.setArguments(process_args)
        process.setWorkingDirectory(str(base_dir))

        task = TaskInstance(task_id, script_id, script_name, process, process_args)
        self.tasks[task_id] = task

        # Connect signals
        process.readyReadStandardOutput.connect(lambda: self._on_stdout(task_id))
        process.readyReadStandardError.connect(lambda: self._on_stderr(task_id))
        process.finished.connect(lambda code, status: self._on_finished(task_id, code, status))

        # Log launch banner
        timestamp = datetime.now().strftime("%H:%M:%S")
        cmd_str = f"{python_exe} {script_file} {' '.join(param_args)}".strip()
        banner = (
            f"[{timestamp}] === LAUNCHING {script_name.upper()} ===\n"
            f"[{timestamp}] Command: {cmd_str}\n"
            f"[{timestamp}] Working Dir: {base_dir}\n"
            f"[{timestamp}] --------------------------------------------------\n"
        )
        task.logs.append(banner)

        process.start()

        self.task_started.emit(task_id, script_id)
        self.task_output.emit(task_id, banner, False)
        self.active_count_changed.emit(len(self.get_active_tasks()))

        return task_id

    def send_input_to_task(self, task_id: str, text: str) -> bool:
        """Write user input line into the process stdin pipe."""
        task = self.tasks.get(task_id)
        if not task or task.status != "RUNNING":
            return False

        if not text.endswith("\n"):
            text += "\n"

        task.process.write(text.encode("utf-8"))
        echo = f"> {text}"
        task.logs.append(echo)
        self.task_output.emit(task_id, echo, False)
        return True

    def stop_task(self, task_id: str) -> bool:
        """Terminate a specific task and its child process tree."""
        task = self.tasks.get(task_id)
        if not task or task.status != "RUNNING":
            return False

        pid = task.process.processId()
        timestamp = datetime.now().strftime("%H:%M:%S")
        stop_msg = f"\n[{timestamp}] [USER] Stop requested for task PID {pid}...\n"
        task.logs.append(stop_msg)
        self.task_output.emit(task_id, stop_msg, True)

        # Force terminate process tree via taskkill on Windows
        if sys.platform == "win32" and pid > 0:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            except Exception:
                task.process.kill()
        else:
            task.process.kill()

        task.status = "STOPPED"
        self.task_finished.emit(task_id, -1, "STOPPED")
        self.active_count_changed.emit(len(self.get_active_tasks()))
        return True

    def stop_all_tasks(self) -> int:
        """Stop all running tasks."""
        running = self.get_active_tasks()
        count = 0
        for task in running:
            if self.stop_task(task.task_id):
                count += 1
        return count

    def _on_stdout(self, task_id: str):
        task = self.tasks.get(task_id)
        if not task:
            return
        data = task.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        task.logs.append(data)
        self.task_output.emit(task_id, data, False)

    def _on_stderr(self, task_id: str):
        task = self.tasks.get(task_id)
        if not task:
            return
        data = task.process.readAllStandardError().data().decode("utf-8", errors="replace")
        task.logs.append(data)
        self.task_output.emit(task_id, data, True)

    def _on_finished(self, task_id: str, exit_code: int, exit_status: QProcess.ExitStatus):
        task = self.tasks.get(task_id)
        if not task:
            return

        if task.status != "STOPPED":
            task.status = "SUCCESS" if exit_code == 0 else "ERROR"

        task.exit_code = exit_code
        timestamp = datetime.now().strftime("%H:%M:%S")
        duration = datetime.now() - task.start_time
        summary = (
            f"\n[{timestamp}] --------------------------------------------------\n"
            f"[{timestamp}] Process finished with exit code {exit_code} (Status: {task.status})\n"
            f"[{timestamp}] Elapsed Time: {str(duration).split('.')[0]}\n"
        )
        task.logs.append(summary)
        self.task_output.emit(task_id, summary, exit_code != 0)
        self.task_finished.emit(task_id, exit_code, task.status)
        self.active_count_changed.emit(len(self.get_active_tasks()))

