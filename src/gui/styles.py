from __future__ import annotations


APP_STYLESHEET = """
QMainWindow {
    background: #f3f5f7;
}

QWidget {
    color: #1b2430;
    font-size: 14px;
}

QFrame#Header {
    background: #17212b;
    border: 1px solid #17212b;
    border-radius: 8px;
}

QLabel#AppTitle {
    color: #ffffff;
    font-size: 23px;
    font-weight: 700;
}

QLabel#AppSubtitle {
    color: #c9d2da;
    font-size: 13px;
}

QLabel#StepLabel {
    color: #ffffff;
    background: #15766f;
    border-radius: 5px;
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
    background: #e3f2ef;
    border: 1px solid #b9ddd7;
    border-radius: 8px;
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
    border-radius: 5px;
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

QLabel#NavigatorCount {
    color: #687586;
    font-size: 12px;
    font-weight: 700;
}

QGroupBox {
    background: transparent;
    border: 0;
    border-top: 1px solid #e4e9ee;
    margin-top: 14px;
    padding: 14px 0 0 0;
    font-weight: 700;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 0;
    padding: 0 6px 0 0;
    color: #354353;
}

QFrame#Panel {
    background: #ffffff;
    border: 1px solid #dbe2e8;
    border-radius: 8px;
}

QLabel#PanelTitle {
    color: #263342;
    font-weight: 700;
}

QListWidget {
    background: transparent;
    border: 0;
    outline: 0;
}

QListWidget::item {
    border-radius: 5px;
    padding: 6px 8px;
    margin: 1px 0;
}

QListWidget::item:selected {
    background: #e1f1ee;
    color: #0d5d58;
}

QLineEdit {
    background: #ffffff;
    border: 1px solid #cfd7df;
    border-radius: 6px;
    padding: 7px 9px;
    selection-background-color: #15766f;
}

QLineEdit:focus {
    border: 1px solid #15766f;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #ccd6df;
    border-radius: 6px;
    padding: 7px 10px;
    font-weight: 600;
    color: #273444;
}

QPushButton:hover {
    background: #f3f7f8;
    border-color: #9eb0bc;
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
    padding: 8px 9px;
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
