from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Personal Handwriting Font Creator")
    app.setOrganizationName("PersonalFontTools")

    project_root = Path(__file__).resolve().parent
    window = MainWindow(project_root=project_root)
    window.resize(1280, 820)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

