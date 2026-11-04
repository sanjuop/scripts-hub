#!/usr/bin/env python3
"""
Scripts Hub - Main Launcher Application
Qt/PySide6 desktop management interface for D:\Scripts
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
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from launcher.main_window import MainWindow

SINGLE_INSTANCE_KEY = "ScriptsHub_SingleInstance_IPC"


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

    # 1. Single Instance Check: Connect to existing instance if running
    test_socket = QLocalSocket()
    test_socket.connectToServer(SINGLE_INSTANCE_KEY)
    if test_socket.waitForConnected(400):
        # Already running: signal the primary instance to restore and activate
        test_socket.write(b"ACTIVATE")
        test_socket.waitForBytesWritten(1000)
        test_socket.disconnectFromServer()
        sys.exit(0)

    # 2. Primary Instance Setup: Clean up any stale pipe from previous crash and start IPC server
    QLocalServer.removeServer(SINGLE_INSTANCE_KEY)
    ipc_server = QLocalServer(app)

    # Set application icon
    icon_path = SCRIPTS_ROOT / "launcher" / "resources" / "app_icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window._ipc_server = ipc_server

    def handle_ipc_connection():
        client = ipc_server.nextPendingConnection()
        if client:
            client.waitForReadyRead(500)
            data = client.readAll().data().decode("utf-8", errors="ignore")
            if "ACTIVATE" in data:
                window.show_and_activate()
            client.disconnectFromServer()

    ipc_server.newConnection.connect(handle_ipc_connection)
    if not ipc_server.listen(SINGLE_INSTANCE_KEY):
        print(f"[Warning] Failed to start single instance IPC server: {ipc_server.errorString()}")

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
