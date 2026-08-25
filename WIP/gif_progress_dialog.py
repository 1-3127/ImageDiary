"""GIF 생성 진행률을 별도 팝업으로 표시한다."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QProgressDialog, QWidget


class GifProgressDialog(QProgressDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("GIF 생성 준비 중...", "", 0, 100, parent)
        self.setWindowTitle("GIF 생성")
        self.setCancelButton(None)
        self.setAutoClose(False)
        self.setMinimumDuration(0)

    def begin(self) -> None:
        self.setValue(0)
        self.show()
        QApplication.processEvents()

    def update_progress(self, current: int, total: int) -> None:
        percent = 0 if total <= 0 else int(current / total * 100)
        self.setLabelText(f"GIF 생성 중... {current}/{total}")
        self.setValue(percent)
        QApplication.processEvents()

    def complete(self) -> None:
        self.setValue(100)
        self.close()
