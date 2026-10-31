#!/usr/bin/env python3
"""
Scripts Hub - Main Launcher Application
Qt/PySide6 desktop management interface for D:\\Scripts
"""

import sys
import os
from pathlib import Path

# Ensure D:\Scripts is in Python path
SCRIPTS_ROOT = Path(__file__).resolve().parent
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from launcher.main_window import MainWindow


def main():
    # Set Windows AppUserModelID so Taskbar uses our custom icon instead of Python's logo
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ScriptsHub.Launcher.1.0")
        except Exception:
            pass

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Scripts Hub")
    app.setOrganizationName("ScriptsHub")

    # Set application icon
    icon_path = SCRIPTS_ROOT / "launcher" / "resources" / "app_icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()

    # Check for --minimized argument (e.g. from Windows boot startup)
    if "--minimized" in sys.argv:
        window.hide()
        if hasattr(window, "tray_icon") and window.tray_icon.isVisible():
            window.tray_icon.showMessage(
                "Scripts Hub",
                "Scripts Hub started in the background.",
                window.tray_icon.MessageIcon.Information,
                2000
            )
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

