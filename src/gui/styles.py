from __future__ import annotations


APP_STYLESHEET = """
QMainWindow {
    background: #f5f7f9;
}

QWidget {
    color: #1b2430;
    font-size: 14px;
}

QFrame#Header {
    background: #1a2733;
    border: 1px solid #1a2733;
    border-radius: 10px;
}

QLabel#AppTitle {
    color: #ffffff;
    font-size: 24px;
    font-weight: 700;
}

QLabel#AppSubtitle {
    color: #c9d2da;
    font-size: 13px;
}

QLabel#StepLabel {
    color: #ffffff;
    background: #15766f;
    border-radius: 6px;
    padding: 6px 10px;
    font-weight: 700;
}

QLabel#PromptLabel {
    color: #17212b;
    font-size: 21px;
    font-weight: 700;
}

QLabel#CanvasHint {
    color: #687586;
    font-size: 13px;
}

QLabel#ProgressText {
    color: #d5dde3;
    font-weight: 600;
}

QLabel#GlyphIdentity {
    background: #e9f5f2;
    border: 1px solid #c0e2db;
    border-radius: 9px;
    color: #0d5d58;
    font-size: 28px;
    font-weight: 700;
    min-width: 52px;
    max-width: 52px;
    min-height: 52px;
    max-height: 52px;
}

QLabel#GlyphDetail {
    color: #748092;
    font-size: 12px;
}

QLabel#GlyphStatus {
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    padding: 5px 8px;
}

QLabel#GlyphStatus[state="saved"] {
    background: #e5f4eb;
    color: #176542;
}

QLabel#GlyphStatus[state="dirty"] {
    background: #fff2d8;
    color: #8a5b08;
}

QLabel#GlyphStatus[state="patch"] {
    background: #e4f3f0;
    color: #0f665f;
}

QLabel#GlyphStatus[state="base"] {
    background: #eaf0f7;
    color: #426383;
}

QLabel#NavigatorCount {
    color: #687586;
    font-size: 12px;
    font-weight: 700;
}

QGroupBox {
    background: transparent;
    border: 0;
    border-top: 1px solid #e4e9ee;
    margin-top: 16px;
    padding: 15px 0 0 0;
    font-weight: 700;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 0;
    padding: 0 6px 0 0;
    color: #354353;
    font-size: 12px;
}

QFrame#Panel {
    background: #ffffff;
    border: 1px solid #dce4ea;
    border-radius: 10px;
}

QLabel#PanelTitle {
    color: #263342;
    font-weight: 700;
    font-size: 15px;
}

QLabel#SectionLabel {
    color: #7a8795;
    font-size: 11px;
    font-weight: 700;
    padding-top: 4px;
}

QLabel#BaseFontName {
    color: #25384a;
    font-size: 13px;
    font-weight: 700;
}

QLabel#BaseFontDetail {
    color: #768496;
    font-size: 12px;
}

QListWidget {
    background: transparent;
    border: 0;
    outline: 0;
}

QListWidget::item {
    border-radius: 6px;
    padding: 7px 8px;
    margin: 1px 0;
}

QListWidget::item:selected {
    background: #e1f1ee;
    color: #0d5d58;
}

QListWidget::indicator {
    width: 14px;
    height: 14px;
}

QListWidget::indicator:unchecked {
    border: 1px solid #b8c6d2;
    border-radius: 3px;
    background: #ffffff;
}

QListWidget::indicator:checked {
    border: 1px solid #15766f;
    border-radius: 3px;
    background: #15766f;
}

QLineEdit {
    background: #ffffff;
    border: 1px solid #d5dde4;
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: #15766f;
}

QLineEdit:focus {
    border: 1px solid #15766f;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #d2dbe3;
    border-radius: 6px;
    min-height: 18px;
    padding: 7px 10px;
    font-size: 13px;
    font-weight: 600;
    color: #273444;
}

QPushButton:hover {
    background: #f0f7f6;
    border-color: #95b8b2;
}

QPushButton:pressed {
    background: #e7edef;
}

QPushButton:disabled {
    background: #f1f3f5;
    border-color: #e1e6ea;
    color: #a0a9b4;
}

QPushButton:checked {
    background: #15766f;
    border-color: #15766f;
    color: #ffffff;
}

QPushButton#PrimaryButton {
    background: #15766f;
    border-color: #15766f;
    color: #ffffff;
}

QPushButton#PrimaryButton:hover {
    background: #0f655f;
}

QPushButton#ExportButton {
    background: #263342;
    border-color: #263342;
    color: #ffffff;
    padding: 9px 12px;
}

QToolButton#ToolIconButton {
    background: #ffffff;
    border: 1px solid #d2dbe3;
    border-radius: 6px;
    padding: 5px;
}

QToolButton#ToolIconButton:hover {
    background: #eef7f5;
    border-color: #93bcb5;
}

QToolButton#ToolIconButton:pressed {
    background: #dcefeb;
}

QPushButton#ExportButton:hover {
    background: #18232e;
}

QTabWidget::pane {
    border: 0;
    border-top: 1px solid #e2e8ed;
    top: -1px;
}

QTabBar::tab {
    background: transparent;
    border: 0;
    color: #778291;
    min-width: 62px;
    padding: 9px 10px;
    font-weight: 700;
}

QTabBar::tab:selected {
    color: #0d5d58;
    border-bottom: 2px solid #15766f;
}

QSplitter::handle {
    background: #e4e9ee;
}

QSplitter::handle:hover {
    background: #b9ddd7;
}

QSlider::groove:horizontal {
    height: 5px;
    border-radius: 2px;
    background: #d8e0e5;
}

QSlider::sub-page:horizontal {
    background: #15766f;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #263342;
    width: 15px;
    margin: -5px 0;
    border-radius: 7px;
}

QProgressBar {
    background: #3a4855;
    border: 0;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: #e6a632;
    border-radius: 4px;
}

QStatusBar {
    background: #f3f5f7;
    color: #647183;
}
"""
