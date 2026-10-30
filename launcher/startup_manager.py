"""
Windows Startup Manager for Scripts Hub
Manages automatic startup via the user's Windows Startup shortcut folder.
Requires zero admin privileges.
"""

import os
import sys
import subprocess
from pathlib import Path


class StartupManager:
    APP_NAME = "ScriptsHub"

    @classmethod
    def get_startup_shortcut_path(cls) -> Path:
        """Returns the full path to the shortcut in Windows Startup directory."""
        appdata = os.environ.get("APPDATA")
        if not appdata:
            appdata = str(Path.home() / "AppData" / "Roaming")
        startup_dir = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        return startup_dir / f"{cls.APP_NAME}.lnk"

    @classmethod
    def is_startup_enabled(cls) -> bool:
        """Checks if the startup shortcut currently exists."""
        return cls.get_startup_shortcut_path().exists()

    @classmethod
    def set_startup(cls, enable: bool, start_minimized: bool = True) -> bool:
        """Enable or disable startup launch."""
        shortcut_path = cls.get_startup_shortcut_path()

        if not enable:
            if shortcut_path.exists():
                try:
                    shortcut_path.unlink()
                    return True
                except Exception as e:
                    print(f"[Error] Failed to remove startup shortcut: {e}")
                    return False
            return True

        # Target script: launcher_app.pyw using pythonw.exe (windowless)
        scripts_dir = Path(__file__).resolve().parent.parent
        launcher_script = scripts_dir / "launcher_app.pyw"

        # Determine pythonw executable
        python_exe = Path(sys.executable)
        pythonw_exe = python_exe.parent / "pythonw.exe"
        if not pythonw_exe.exists():
            pythonw_exe = python_exe

        args = f'"{launcher_script}"'
        if start_minimized:
            args += " --minimized"

        # Create shortcut via PowerShell WScript.Shell
        ps_cmd = (
            f"$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{shortcut_path}'); "
            f"$s.TargetPath = '{pythonw_exe}'; "
            f"$s.Arguments = '{args}'; "
            f"$s.WorkingDirectory = '{scripts_dir}'; "
            f"$s.Description = 'Scripts Hub Launcher'; "
            f"$s.Save()"
        )

        try:
            shortcut_path.parent.mkdir(parents=True, exist_ok=True)
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                check=True
            )
            return shortcut_path.exists()
        except Exception as e:
            print(f"[Error] Failed to create startup shortcut: {e}")
            return False

