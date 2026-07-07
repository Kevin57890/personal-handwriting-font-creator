from __future__ import annotations


APP_STYLESHEET = """
QMainWindow {
    background: #edf2f7;
}

QWidget {
    color: #16202e;
    font-size: 14px;
}

QFrame#Header {
    background: #101827;
    border-radius: 0;
}

QLabel#AppTitle {
    color: #ffffff;
    font-size: 24px;
    font-weight: 700;
}

QLabel#AppSubtitle {
    color: #c8d3e2;
    font-size: 13px;
}

QLabel#StepLabel {
    color: #ffffff;
    background: #1d9a8a;
    border-radius: 4px;
    padding: 5px 9px;
    font-weight: 700;
}

QLabel#PromptLabel {
    color: #101827;
    font-size: 26px;
    font-weight: 700;
}

QLabel#CanvasHint {
    color: #697386;
    font-size: 13px;
}

QLabel#ProgressText {
    color: #c8d3e2;
    font-weight: 600;
}

QGroupBox {
    background: #ffffff;
    border: 1px solid #d7dee8;
    border-radius: 8px;
    margin-top: 18px;
    padding: 14px 10px 10px 10px;
    font-weight: 700;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: #1f2a3a;
}

QFrame#Panel {
    background: #ffffff;
    border: 1px solid #d7dee8;
    border-radius: 8px;
}

QLabel#PanelTitle {
    color: #1f2a3a;
    font-weight: 700;
}

QListWidget {
    background: transparent;
    border: 0;
    outline: 0;
}

QListWidget::item {
    color: #263448;
    border-radius: 5px;
    padding: 5px 7px;
    margin: 1px 0;
}

QListWidget::item:selected {
    background: #dcefeb;
    color: #0c554f;
}

QLineEdit {
    background: #ffffff;
    border: 1px solid #cfd8e3;
    border-radius: 6px;
    padding: 7px 9px;
    selection-background-color: #1d9a8a;
}

QLineEdit:focus {
    border: 1px solid #1d9a8a;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #cdd6e3;
    border-radius: 6px;
    padding: 7px 10px;
    font-weight: 600;
    color: #1d2736;
}

QPushButton:hover {
    background: #f5f8fb;
    border-color: #9fb0c4;
}

QPushButton:pressed {
    background: #e7edf5;
}

QPushButton:checked {
    background: #1d9a8a;
    border-color: #1d9a8a;
    color: #ffffff;
}

QPushButton#PrimaryButton {
    background: #1d9a8a;
    border-color: #1d9a8a;
    color: #ffffff;
}

QPushButton#PrimaryButton:hover {
    background: #18877a;
}

QPushButton#ExportButton {
    background: #253149;
    border-color: #253149;
    color: #ffffff;
    padding: 9px 12px;
}

QPushButton#ExportButton:hover {
    background: #1b2435;
}

QSlider::groove:horizontal {
    height: 5px;
    border-radius: 2px;
    background: #d9e1ea;
}

QSlider::sub-page:horizontal {
    background: #1d9a8a;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #253149;
    width: 15px;
    margin: -5px 0;
    border-radius: 7px;
}

QProgressBar {
    background: #27344a;
    border: 0;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: #f2b84b;
    border-radius: 4px;
}

QStatusBar {
    background: #edf2f7;
    color: #465568;
}
"""

