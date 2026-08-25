"""현재 세션 정보를 표시하며 향후 경과시간 표시를 수용한다."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QFormLayout, QLabel, QWidget


class SessionStatusWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        self._status = QLabel("대기", self)
        self._captures = QLabel("0", self)
        self._next_capture = QLabel("-", self)
        layout.addRow("상태:", self._status)
        layout.addRow("캡처 수:", self._captures)
        layout.addRow("다음 캡처:", self._next_capture)

    def set_status(self, status: str) -> None:
        self._status.setText(status)

    def set_capture_count(self, count: int) -> None:
        self._captures.setText(str(count))

    def set_next_capture(self, capture_time: datetime | None) -> None:
        text = "-" if capture_time is None else capture_time.strftime("%Y-%m-%d %H:%M:%S")
        self._next_capture.setText(text)
