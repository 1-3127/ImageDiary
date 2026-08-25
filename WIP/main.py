"""ImageDiary v0.1 실행 진입점."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app import MainWindow
from settings import DEFAULT_SETTINGS


def main() -> int:
    application = QApplication(sys.argv)
    window = MainWindow(DEFAULT_SETTINGS)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
