"""
Main UI Window for Scripts Hub (PySide6)
Implements parallel task execution, real-time terminal consoles, dynamic parameters,
tray integration, and startup configuration.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QAction, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QPlainTextEdit, QCheckBox, QComboBox, QSpinBox, QFileDialog,
    QScrollArea, QFrame, QSplitter, QStatusBar, QSystemTrayIcon,
    QMenu, QMessageBox, QDialog, QDialogButtonBox, QFormLayout
)

from .manifest import ScriptManifest
from .process_manager import ProcessManager
from .startup_manager import StartupManager
from .styles import DARK_THEME


class AddScriptDialog(QDialog):
    """Dialog to register a new Python script into the manifest."""
    def __init__(self, parent=None, default_dir: Optional[Path] = None):
        super().__init__(parent)
        self.setWindowTitle("Register New Script")
        self.setMinimumWidth(450)
        self.default_dir = default_dir or Path(__file__).resolve().parent.parent

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("e.g. Audio Extractor")
        form.addRow("Display Name:", self.edit_name)

        self.edit_desc = QLineEdit()
        self.edit_desc.setPlaceholderText("Short description of what the script does")
        form.addRow("Description:", self.edit_desc)

        self.combo_cat = QComboBox()
        self.combo_cat.setEditable(True)
        self.combo_cat.addItems(["Media & Video", "Disk & Backup", "Automation & Keep-Awake", "General"])
        form.addRow("Category:", self.combo_cat)

        file_row = QHBoxLayout()
        self.edit_file = QLineEdit()
        self.edit_file.setPlaceholderText("script_name.py")
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_file)
        file_row.addWidget(self.edit_file)
        file_row.addWidget(btn_browse)
        form.addRow("Script File:", file_row)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Python Script", str(self.default_dir), "Python Files (*.py)"
        )
        if file_path:
            p = Path(file_path)
            try:
                rel = p.relative_to(self.default_dir)
                self.edit_file.setText(str(rel))
            except ValueError:
                self.edit_file.setText(str(p))

            if not self.edit_name.text():
                # Derive friendly name
                name = p.stem.replace("_", " ").title()
                self.edit_name.setText(name)

    def get_data(self) -> Dict:
        name = self.edit_name.text().strip()
        script_id = name.lower().replace(" ", "_").replace("-", "_")
        return {
            "id": script_id,
            "name": name,
            "category": self.combo_cat.currentText().strip() or "General",
            "description": self.edit_desc.text().strip(),
            "script_file": self.edit_file.text().strip(),
            "interpreter": "auto",
            "dependencies": [],
            "parameters": []
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scripts Hub")
        self.resize(1150, 780)
        self.setStyleSheet(DARK_THEME)

        self.manifest = ScriptManifest()
        self.process_manager = ProcessManager(self)
        self.scripts_dir = Path(__file__).resolve().parent.parent

        # State
        self.param_widgets: Dict[str, QWidget] = {}
        self.console_tabs: Dict[str, QPlainTextEdit] = {}  # task_id -> text edit
        self.current_script_id: Optional[str] = None
        self.minimize_to_tray = True

        self._init_ui()
        self._init_tray()
        self._connect_signals()

        # Load first script
        scripts = self.manifest.get_scripts()
        if scripts:
            self.list_scripts.setCurrentRow(0)

    def _init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Bar
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        lbl_logo = QLabel("⚡ <b>SCRIPTS HUB</b>")
        lbl_logo.setStyleSheet("font-size: 15px; color: #7aa2f7; font-weight: bold;")
        header_layout.addWidget(lbl_logo)

        header_layout.addSpacing(20)

        self.lbl_task_counter = QLabel("0 Active Tasks")
        self.lbl_task_counter.setStyleSheet("color: #9aa5ce; font-size: 12px; background: #24283b; padding: 3px 8px; border-radius: 4px;")
        header_layout.addWidget(self.lbl_task_counter)

        header_layout.addStretch()

        self.btn_stop_all = QPushButton("⏹ Stop All Tasks")
        self.btn_stop_all.setObjectName("btnStopAll")
        self.btn_stop_all.clicked.connect(self._stop_all_tasks)
        header_layout.addWidget(self.btn_stop_all)

        main_layout.addWidget(header)

        # 2. Main Content Splitter (Sidebar + Script Area)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(260)
        sidebar.setMaximumWidth(340)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 10, 8, 8)
        sidebar_layout.setSpacing(8)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search scripts...")
        self.search_bar.textChanged.connect(self._filter_scripts)
        sidebar_layout.addWidget(self.search_bar)

        self.combo_category = QComboBox()
        self.combo_category.addItems(self.manifest.get_categories())
        self.combo_category.currentIndexChanged.connect(self._filter_scripts)
        sidebar_layout.addWidget(self.combo_category)

        self.list_scripts = QListWidget()
        self.list_scripts.currentRowChanged.connect(self._on_script_selected)
        sidebar_layout.addWidget(self.list_scripts)

        # Sidebar Bottom Buttons
        sidebar_btn_row = QHBoxLayout()
        self.btn_add_script = QPushButton("+ Add Script")
        self.btn_add_script.clicked.connect(self._show_add_script_dialog)
        self.btn_open_folder = QPushButton("📁 Folder")
        self.btn_open_folder.clicked.connect(self._open_scripts_folder)
        sidebar_btn_row.addWidget(self.btn_add_script)
        sidebar_btn_row.addWidget(self.btn_open_folder)
        sidebar_layout.addLayout(sidebar_btn_row)

        splitter.addWidget(sidebar)

        # --- Main Right Area ---
        content_area = QFrame()
        content_area.setObjectName("detailArea")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(16, 12, 16, 10)
        content_layout.setSpacing(10)

        # Script Details Header Card
        card_header = QFrame()
        card_header.setStyleSheet("background: #1f2335; border-radius: 8px; padding: 12px;")
        card_layout = QVBoxLayout(card_header)
        card_layout.setSpacing(6)

        title_row = QHBoxLayout()
        self.lbl_script_title = QLabel("Select a Script")
        self.lbl_script_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        title_row.addWidget(self.lbl_script_title)
        title_row.addStretch()

        self.lbl_script_status = QLabel("Ready")
        self.lbl_script_status.setStyleSheet("background: #24283b; color: #9aa5ce; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 11px;")
        title_row.addWidget(self.lbl_script_status)
        card_layout.addLayout(title_row)

        self.lbl_script_desc = QLabel("Description goes here...")
        self.lbl_script_desc.setWordWrap(True)
        self.lbl_script_desc.setStyleSheet("color: #a9b1d6; font-size: 12px;")
        card_layout.addWidget(self.lbl_script_desc)

        # Badges row (Python & Dependencies)
        self.badges_layout = QHBoxLayout()
        card_layout.addLayout(self.badges_layout)

        content_layout.addWidget(card_header)

        # Action Buttons
        action_row = QHBoxLayout()
        self.btn_run = QPushButton("▶ Run Script")
        self.btn_run.setObjectName("btnRun")
        self.btn_run.clicked.connect(self._run_current_script)
        action_row.addWidget(self.btn_run)

        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_current_script)
        action_row.addWidget(self.btn_stop)

        self.btn_edit_script = QPushButton("📝 Edit Script")
        self.btn_edit_script.clicked.connect(self._edit_current_script)
        action_row.addWidget(self.btn_edit_script)

        action_row.addStretch()
        content_layout.addLayout(action_row)

        # Parameters Scroll Area
        self.scroll_params = QScrollArea()
        self.scroll_params.setWidgetResizable(True)
        self.scroll_params.setMaximumHeight(200)
        self.scroll_params.setStyleSheet("background: #1a1b26; border: 1px solid #24283b; border-radius: 6px;")
        self.params_container = QWidget()
        self.params_layout = QFormLayout(self.params_container)
        self.params_layout.setContentsMargins(12, 10, 12, 10)
        self.scroll_params.setWidget(self.params_container)
        content_layout.addWidget(self.scroll_params)

        # Tabbed Output Console
        console_box = QVBoxLayout()
        console_header = QHBoxLayout()
        lbl_console_title = QLabel("Terminal Output")
        lbl_console_title.setStyleSheet("font-weight: bold; color: #7aa2f7; font-size: 12px;")
        console_header.addWidget(lbl_console_title)
        console_header.addStretch()

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self._clear_active_console)
        btn_copy = QPushButton("Copy Logs")
        btn_copy.clicked.connect(self._copy_active_logs)
        console_header.addWidget(btn_clear)
        console_header.addWidget(btn_copy)
        console_box.addLayout(console_header)

        self.tabs_console = QTabWidget()
        console_box.addWidget(self.tabs_console)

        # Stdin Input Row
        stdin_row = QHBoxLayout()
        self.edit_stdin = QLineEdit()
        self.edit_stdin.setPlaceholderText("Send input to running script (press Enter to send)...")
        self.edit_stdin.returnPressed.connect(self._send_stdin)
        self.btn_send_stdin = QPushButton("Send")
        self.btn_send_stdin.clicked.connect(self._send_stdin)
        stdin_row.addWidget(self.edit_stdin)
        stdin_row.addWidget(self.btn_send_stdin)
        console_box.addLayout(stdin_row)

        content_layout.addLayout(console_box)

        splitter.addWidget(content_area)
        splitter.setStretchFactor(1, 4)
        main_layout.addWidget(splitter)

        # 3. Bottom Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.chk_startup = QCheckBox("Launch on Windows Startup")
        self.chk_startup.setChecked(StartupManager.is_startup_enabled())
        self.chk_startup.toggled.connect(self._on_startup_toggled)
        self.status_bar.addPermanentWidget(self.chk_startup)

        self.chk_tray = QCheckBox("Minimize to Tray")
        self.chk_tray.setChecked(True)
        self.chk_tray.toggled.connect(lambda v: setattr(self, "minimize_to_tray", v))
        self.status_bar.addPermanentWidget(self.chk_tray)

        self.lbl_global_status = QLabel("System: Ready")
        self.status_bar.addWidget(self.lbl_global_status)

        self._populate_scripts_list()

    def _init_tray(self):
        """Initialize Windows system tray icon and menu."""
        self.tray_icon = QSystemTrayIcon(self)
        # Use standard system icon fallback
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)

        tray_menu = QMenu()
        act_show = QAction("Open Scripts Hub", self)
        act_show.triggered.connect(self.show_and_activate)
        tray_menu.addAction(act_show)

        act_stop_all = QAction("Stop All Running Scripts", self)
        act_stop_all.triggered.connect(self._stop_all_tasks)
        tray_menu.addAction(act_stop_all)

        tray_menu.addSeparator()
        act_exit = QAction("Exit", self)
        act_exit.triggered.connect(self._clean_exit)
        tray_menu.addAction(act_exit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _connect_signals(self):
        self.process_manager.task_started.connect(self._on_task_started)
        self.process_manager.task_output.connect(self._on_task_output)
        self.process_manager.task_finished.connect(self._on_task_finished)
        self.process_manager.active_count_changed.connect(self._on_active_count_changed)

    def _populate_scripts_list(self):
        """Populate the sidebar script list based on filters."""
        self.list_scripts.clear()
        query = self.search_bar.text().strip().lower()
        selected_cat = self.combo_category.currentText()

        for s in self.manifest.get_scripts():
            name = s.get("name", "")
            cat = s.get("category", "")
            script_id = s.get("id", "")

            # Filter check
            if selected_cat != "All Scripts" and cat != selected_cat:
                continue
            if query and (query not in name.lower() and query not in s.get("description", "").lower()):
                continue

            item = QListWidgetItem()
            item.setData(Qt.UserRole, script_id)
            self._update_item_display(item, s)
            self.list_scripts.addItem(item)

    def _update_item_display(self, item: QListWidgetItem, script_info: Dict):
        script_id = script_info.get("id")
        name = script_info.get("name", script_id)
        is_running = self.process_manager.is_script_running(script_id)
        dot = "🟢 " if is_running else "⚪ "
        item.setText(f"{dot} {name}")

    def _filter_scripts(self):
        self._populate_scripts_list()
        if self.list_scripts.count() > 0:
            self.list_scripts.setCurrentRow(0)

    def _on_script_selected(self, row: int):
        if row < 0:
            return
        item = self.list_scripts.item(row)
        if not item:
            return
        script_id = item.data(Qt.UserRole)
        self.current_script_id = script_id
        script_info = self.manifest.get_script_by_id(script_id)
        if not script_info:
            return

        # Render Header Card
        self.lbl_script_title.setText(script_info.get("name", script_id))
        self.lbl_script_desc.setText(script_info.get("description", ""))

        is_running = self.process_manager.is_script_running(script_id)
        self.btn_run.setEnabled(not is_running)
        self.btn_stop.setEnabled(is_running)
        self._update_status_badge(is_running)

        # Clear and rebuild badges
        while self.badges_layout.count():
            w = self.badges_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        lbl_py = QLabel("🐍 Python 3.12")
        lbl_py.setStyleSheet("background: #24283b; color: #7aa2f7; padding: 2px 8px; border-radius: 4px; font-size: 11px;")
        self.badges_layout.addWidget(lbl_py)

        # Check dependencies
        for dep in script_info.get("dependencies", []):
            found = self.process_manager.check_dependency(dep)
            lbl_dep = QLabel(f"{'✓' if found else '✗'} {dep}")
            color = "#10b981" if found else "#ef4444"
            bg = "#064e3b" if found else "#7f1d1d"
            lbl_dep.setStyleSheet(f"background: {bg}; color: {color}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;")
            self.badges_layout.addWidget(lbl_dep)

        self.badges_layout.addStretch()

        # Build Dynamic Parameter Form
        self._build_parameters_form(script_info)

        # Activate or create console tab for this script
        self._ensure_console_tab(script_info)

    def _update_status_badge(self, is_running: bool):
        if is_running:
            self.lbl_script_status.setText("● RUNNING")
            self.lbl_script_status.setStyleSheet("background: #1e3a8a; color: #93c5fd; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 11px;")
        else:
            self.lbl_script_status.setText("READY")
            self.lbl_script_status.setStyleSheet("background: #24283b; color: #9aa5ce; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 11px;")

    def _build_parameters_form(self, script_info: Dict):
        """Construct the dynamic input form based on script parameters in manifest."""
        # Clear existing widgets
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.param_widgets.clear()

        params = script_info.get("parameters", [])
        if not params:
            lbl_none = QLabel("No configuration parameters required for this script.")
            lbl_none.setStyleSheet("color: #565f89; font-style: italic;")
            self.params_layout.addRow(lbl_none)
            return

        for p in params:
            name = p.get("name")
            p_type = p.get("type", "text")
            label = p.get("label", name)
            default = p.get("default")

            if p_type == "directory":
                row = QHBoxLayout()
                edit = QLineEdit(str(default or ""))
                btn = QPushButton("Browse...")
                btn.clicked.connect(lambda _, e=edit: self._browse_dir(e))
                row.addWidget(edit)
                row.addWidget(btn)
                self.params_layout.addRow(f"{label}:", row)
                self.param_widgets[name] = edit

            elif p_type == "file":
                row = QHBoxLayout()
                edit = QLineEdit(str(default or ""))
                btn = QPushButton("Browse...")
                btn.clicked.connect(lambda _, e=edit: self._browse_file(e))
                row.addWidget(edit)
                row.addWidget(btn)
                self.params_layout.addRow(f"{label}:", row)
                self.param_widgets[name] = edit

            elif p_type == "choice":
                combo = QComboBox()
                combo.addItems(p.get("options", []))
                if default in p.get("options", []):
                    combo.setCurrentText(str(default))
                self.params_layout.addRow(f"{label}:", combo)
                self.param_widgets[name] = combo

            elif p_type == "multi_choice":
                # Checkboxes for formats (JSON, SRT, TXT, etc.)
                box = QWidget()
                h = QHBoxLayout(box)
                h.setContentsMargins(0, 0, 0, 0)
                checkboxes = []
                default_list = default if isinstance(default, list) else [str(default)]
                for opt in p.get("options", []):
                    chk = QCheckBox(opt.upper())
                    chk.setChecked(opt in default_list)
                    h.addWidget(chk)
                    checkboxes.append((opt, chk))
                h.addStretch()
                self.params_layout.addRow(f"{label}:", box)
                self.param_widgets[name] = checkboxes

            elif p_type == "bool":
                chk = QCheckBox()
                chk.setChecked(bool(default))
                self.params_layout.addRow(f"{label}:", chk)
                self.param_widgets[name] = chk

            elif p_type == "int":
                spin = QSpinBox()
                spin.setRange(p.get("min", 0), p.get("max", 999999))
                spin.setValue(int(default or 0))
                self.params_layout.addRow(f"{label}:", spin)
                self.param_widgets[name] = spin

            else:  # Text input
                edit = QLineEdit(str(default or ""))
                if p.get("placeholder"):
                    edit.setPlaceholderText(p.get("placeholder"))
                self.params_layout.addRow(f"{label}:", edit)
                self.param_widgets[name] = edit

    def _browse_dir(self, line_edit: QLineEdit):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text() or str(self.scripts_dir))
        if folder:
            line_edit.setText(folder)

    def _browse_file(self, line_edit: QLineEdit):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", line_edit.text() or str(self.scripts_dir))
        if file_path:
            line_edit.setText(file_path)

    def _build_args_from_params(self, script_info: Dict) -> List[str]:
        """Construct command line arguments from current form inputs."""
        args = []
        for p in script_info.get("parameters", []):
            name = p.get("name")
            flag = p.get("flag")
            p_type = p.get("type", "text")
            widget = self.param_widgets.get(name)

            if not widget or not flag:
                continue

            if p_type in ("directory", "file", "text"):
                val = widget.text().strip()
                if val:
                    args.extend([flag, val])

            elif p_type == "choice":
                val = widget.currentText().strip()
                if val:
                    args.extend([flag, val])

            elif p_type == "multi_choice":
                # List of (opt, chk)
                selected = [opt for opt, chk in widget if chk.isChecked()]
                if selected:
                    args.append(flag)
                    args.extend(selected)

            elif p_type == "bool":
                if widget.isChecked():
                    args.append(flag)

            elif p_type == "int":
                val = widget.value()
                args.extend([flag, str(val)])

        return args

    def _ensure_console_tab(self, script_info: Dict):
        script_id = script_info.get("id")
        tab_name = script_info.get("name", script_id)

        # Check if tab exists
        for idx in range(self.tabs_console.count()):
            if self.tabs_console.tabText(idx).startswith(tab_name):
                self.tabs_console.setCurrentIndex(idx)
                return

        # Create new console tab
        editor = QPlainTextEdit()
        editor.setReadOnly(True)
        editor.appendPlainText(f"[Ready] Selected '{tab_name}'. Click 'Run Script' to begin.")
        self.tabs_console.addTab(editor, tab_name)
        self.tabs_console.setCurrentWidget(editor)
        self.console_tabs[script_id] = editor

    def _run_current_script(self):
        if not self.current_script_id:
            return
        script_info = self.manifest.get_script_by_id(self.current_script_id)
        if not script_info:
            return

        # Check dependencies
        missing = [d for d in script_info.get("dependencies", []) if not self.process_manager.check_dependency(d)]
        if missing:
            res = QMessageBox.warning(
                self,
                "Missing Dependencies",
                f"The following required tool(s) were not found in PATH:\n\n• " + "\n• ".join(missing) +
                "\n\nDo you still want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if res != QMessageBox.Yes:
                return

        args = self._build_args_from_params(script_info)

        try:
            task_id = self.process_manager.launch_script(script_info, args, self.scripts_dir)
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to start script:\n{e}")
            return

        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._update_status_badge(True)
        self._refresh_sidebar_icons()

    def _stop_current_script(self):
        if not self.current_script_id:
            return
        task = self.process_manager.get_latest_task_for_script(self.current_script_id)
        if task and task.status == "RUNNING":
            self.process_manager.stop_task(task.task_id)

    def _stop_all_tasks(self):
        count = self.process_manager.stop_all_tasks()
        if count > 0:
            self.statusBar().showMessage(f"Stopped {count} running tasks.", 3000)

    def _edit_current_script(self):
        if not self.current_script_id:
            return
        script_info = self.manifest.get_script_by_id(self.current_script_id)
        if not script_info:
            return
        full_path = self.scripts_dir / script_info.get("script_file")
        if sys.platform == "win32":
            os.startfile(str(full_path))
        else:
            subprocess.run(["xdg-open", str(full_path)])

    def _open_scripts_folder(self):
        if sys.platform == "win32":
            os.startfile(str(self.scripts_dir))
        else:
            subprocess.run(["xdg-open", str(self.scripts_dir)])

    def _show_add_script_dialog(self):
        dlg = AddScriptDialog(self, self.scripts_dir)
        if dlg.exec():
            data = dlg.get_data()
            if not data.get("name") or not data.get("script_file"):
                QMessageBox.warning(self, "Incomplete", "Script Name and File are required.")
                return
            self.manifest.add_script(data)
            self.combo_category.clear()
            self.combo_category.addItems(self.manifest.get_categories())
            self._populate_scripts_list()
            QMessageBox.information(self, "Script Added", f"Registered '{data['name']}' successfully.")

    def _send_stdin(self):
        text = self.edit_stdin.text()
        if not text:
            return
        # Find active task for current script
        if not self.current_script_id:
            return
        task = self.process_manager.get_latest_task_for_script(self.current_script_id)
        if task and task.status == "RUNNING":
            self.process_manager.send_input_to_task(task.task_id, text)
            self.edit_stdin.clear()

    def _clear_active_console(self):
        current_widget = self.tabs_console.currentWidget()
        if isinstance(current_widget, QPlainTextEdit):
            current_widget.clear()

    def _copy_active_logs(self):
        current_widget = self.tabs_console.currentWidget()
        if isinstance(current_widget, QPlainTextEdit):
            from PySide6.QtGui import QGuiApplication
            QGuiApplication.clipboard().setText(current_widget.toPlainText())
            self.statusBar().showMessage("Logs copied to clipboard.", 2000)

    def _on_task_started(self, task_id: str, script_id: str):
        script_info = self.manifest.get_script_by_id(script_id)
        name = script_info.get("name", script_id) if script_info else script_id

        # Create or focus tab
        tab_label = f"▶ {name}"
        editor = QPlainTextEdit()
        editor.setReadOnly(True)
        idx = self.tabs_console.addTab(editor, tab_label)
        self.tabs_console.setCurrentIndex(idx)
        self.console_tabs[task_id] = editor

        if self.current_script_id == script_id:
            self.btn_run.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self._update_status_badge(True)

        self._refresh_sidebar_icons()

    def _on_task_output(self, task_id: str, text: str, is_error: bool):
        editor = self.console_tabs.get(task_id)
        if editor:
            editor.moveCursor(editor.textCursor().MoveOperation.End)
            editor.insertPlainText(text)
            editor.moveCursor(editor.textCursor().MoveOperation.End)

    def _on_task_finished(self, task_id: str, exit_code: int, status: str):
        task = self.process_manager.tasks.get(task_id)
        if task:
            # Update tab label
            for idx in range(self.tabs_console.count()):
                if self.tabs_console.widget(idx) == self.console_tabs.get(task_id):
                    icon = "✓" if status == "SUCCESS" else ("⏹" if status == "STOPPED" else "✗")
                    self.tabs_console.setTabText(idx, f"{icon} {task.script_name}")
                    break

            if self.current_script_id == task.script_id:
                self.btn_run.setEnabled(True)
                self.btn_stop.setEnabled(False)
                self._update_status_badge(False)

        self._refresh_sidebar_icons()

    def _on_active_count_changed(self, count: int):
        self.lbl_task_counter.setText(f"{count} Active Task{'s' if count != 1 else ''}")
        color = "#93c5fd" if count > 0 else "#9aa5ce"
        bg = "#1e3a8a" if count > 0 else "#24283b"
        self.lbl_task_counter.setStyleSheet(f"color: {color}; background: {bg}; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;")
        self.lbl_global_status.setText(f"System: {count} Task{'s' if count != 1 else ''} Running" if count > 0 else "System: Ready")

    def _refresh_sidebar_icons(self):
        for idx in range(self.list_scripts.count()):
            item = self.list_scripts.item(idx)
            s_id = item.data(Qt.UserRole)
            s_info = self.manifest.get_script_by_id(s_id)
            if s_info:
                self._update_item_display(item, s_info)

    def _on_startup_toggled(self, checked: bool):
        success = StartupManager.set_startup(checked, start_minimized=True)
        if success:
            msg = "Enabled startup launch on Windows boot." if checked else "Disabled startup launch."
            self.statusBar().showMessage(msg, 3000)
        else:
            QMessageBox.warning(self, "Startup Config", "Failed to update Windows Startup configuration.")
            self.chk_startup.setChecked(not checked)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_and_activate()

    def show_and_activate(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()

    def closeEvent(self, event):
        """Minimize to tray on window close if enabled."""
        if self.minimize_to_tray and self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "Scripts Hub",
                "Scripts Hub is still running in the system tray. Double-click to restore.",
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()
        else:
            self._clean_exit()

    def _clean_exit(self):
        running = self.process_manager.get_active_tasks()
        if running:
            res = QMessageBox.question(
                self,
                "Active Tasks Running",
                f"There are {len(running)} active background task(s). Stopping the application will terminate them.\n\nDo you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if res != QMessageBox.Yes:
                return

        self.process_manager.stop_all_tasks()
        self.tray_icon.hide()
        QApplication.quit()
