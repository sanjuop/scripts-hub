"""
Modern Dark Theme Stylesheet for Scripts Hub
"""

DARK_THEME = """
/* Global Application Settings */
QWidget {
    background-color: #16161e;
    color: #c0caf5;
    font-family: 'Segoe UI', 'SF Pro Text', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #3d59a1;
    selection-color: #ffffff;
}

/* Scroll Bars */
QScrollBar:vertical {
    border: none;
    background: #1a1b26;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #2f354a;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #414868;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    border: none;
    background: #1a1b26;
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #2f354a;
    min-width: 20px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #414868;
}

/* Splitter */
QSplitter::handle {
    background-color: #24283b;
    border-radius: 2px;
}
QSplitter::handle:vertical {
    height: 6px;
    margin: 3px 0px;
}
QSplitter::handle:horizontal {
    width: 6px;
    margin: 0px 3px;
}
QSplitter::handle:hover {
    background-color: #7aa2f7;
}

/* Sidebar & Containers */
#sidebar {
    background-color: #1a1b26;
    border-right: 1px solid #24283b;
    padding: 8px;
}

#header {
    background-color: #1f2335;
    border-bottom: 1px solid #292e42;
    padding: 6px 14px;
}

#detailArea {
    background-color: #16161e;
}

/* Search & Inputs */
QLineEdit {
    background-color: #24283b;
    border: 1px solid #3b4261;
    border-radius: 6px;
    padding: 7px 12px;
    color: #c0caf5;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #7aa2f7;
    background-color: #282e46;
}

QComboBox {
    background-color: #24283b;
    border: 1px solid #3b4261;
    border-radius: 6px;
    padding: 6px 12px;
    color: #c0caf5;
}
QComboBox:focus {
    border: 1px solid #7aa2f7;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #1f2335;
    border: 1px solid #3b4261;
    selection-background-color: #3d59a1;
    color: #c0caf5;
    padding: 4px;
}

QSpinBox {
    background-color: #24283b;
    border: 1px solid #3b4261;
    border-radius: 6px;
    padding: 6px 10px;
    color: #c0caf5;
}
QSpinBox:focus {
    border: 1px solid #7aa2f7;
}

/* List Widgets (Sidebar Scripts) */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 6px;
    margin-bottom: 3px;
    color: #a9b1d6;
}
QListWidget::item:hover {
    background-color: #24283b;
    color: #c0caf5;
}
QListWidget::item:selected {
    background-color: #292e42;
    color: #7aa2f7;
    font-weight: bold;
    border-left: 3px solid #7aa2f7;
}

/* Buttons */
QPushButton {
    background-color: #24283b;
    border: 1px solid #3b4261;
    border-radius: 6px;
    padding: 7px 14px;
    color: #c0caf5;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #2f354a;
    border-color: #7aa2f7;
}
QPushButton:pressed {
    background-color: #1f2335;
}
QPushButton:disabled {
    background-color: #1a1b26;
    border-color: #24283b;
    color: #565f89;
}

/* Action Buttons */
#btnRun {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    font-weight: bold;
    padding: 9px 20px;
    font-size: 13px;
}
#btnRun:hover {
    background-color: #3b82f6;
}
#btnRun:pressed {
    background-color: #1d4ed8;
}

#btnStop {
    background-color: #dc2626;
    color: #ffffff;
    border: none;
    font-weight: bold;
    padding: 9px 18px;
    font-size: 13px;
}
#btnStop:hover {
    background-color: #ef4444;
}
#btnStop:pressed {
    background-color: #b91c1c;
}
#btnStop:disabled {
    background-color: #24283b;
    color: #565f89;
}

#btnStopAll {
    background-color: #991b1b;
    color: #ffffff;
    border: none;
    font-weight: bold;
    padding: 6px 12px;
    border-radius: 5px;
    font-size: 11px;
}
#btnStopAll:hover {
    background-color: #dc2626;
}

/* Badges */
.badge-ready {
    background-color: #24283b;
    color: #9aa5ce;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
}
.badge-running {
    background-color: #1e3a8a;
    color: #93c5fd;
    border-radius: 4px;
    padding: 2px 6px;
    font-weight: bold;
    font-size: 11px;
}
.badge-success {
    background-color: #064e3b;
    color: #6ee7b7;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
}
.badge-error {
    background-color: #7f1d1d;
    color: #fca5a5;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #292e42;
    background-color: #0f0f17;
    border-radius: 6px;
}
QTabBar::tab {
    background-color: #1a1b26;
    border: 1px solid #292e42;
    border-bottom: none;
    padding: 7px 14px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #a9b1d6;
}
QTabBar::tab:selected {
    background-color: #0f0f17;
    color: #7aa2f7;
    border-color: #3b4261;
}
QTabBar::tab:hover:!selected {
    background-color: #24283b;
}

/* Console Output */
QPlainTextEdit {
    background-color: #0f0f17;
    color: #9ece6a;
    border: none;
    font-family: 'Consolas', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 12px;
    padding: 10px;
    border-radius: 6px;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    color: #c0caf5;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3b4261;
    border-radius: 4px;
    background-color: #24283b;
}
QCheckBox::indicator:hover {
    border-color: #7aa2f7;
}
QCheckBox::indicator:checked {
    background-color: #3b82f6;
    border-color: #3b82f6;
    image: none;
}

/* Status Bar */
QStatusBar {
    background-color: #1a1b26;
    border-top: 1px solid #24283b;
    color: #787c99;
    padding: 4px 10px;
    font-size: 11px;
}
"""

