"""현재 세션 정보를 표시하며 향후 경과시간 표시를 수용한다."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QFormLayout, QLabel, QWidget


class SessionStatusWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        self._status = QLabel("대기", self)
        self._capture_count = 0
        self._next_capture_time: datetime | None = None
        self._capture_overview = QLabel("-", self)
        layout.addRow("상태:", self._status)
        layout.addRow("캡처 현황:", self._capture_overview)

    def set_status(self, status: str) -> None:
        self._status.setText(status)

    def set_capture_count(self, count: int) -> None:
        self._capture_count = count
        self._refresh_capture_overview()

    def set_next_capture(self, capture_time: datetime | None) -> None:
        self._next_capture_time = capture_time
        self._refresh_capture_overview()

    def _refresh_capture_overview(self) -> None:
        if self._next_capture_time is None:
            self._capture_overview.setText("-")
            return
        next_number = self._capture_count + 1
        self._capture_overview.setText(
            f"{self._next_capture_time:%Y-%m-%d %H:%M:%S} ({next_number})"
        )
