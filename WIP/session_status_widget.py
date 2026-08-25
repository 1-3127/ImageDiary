"""현재 세션 정보를 표시하며 향후 경과시간 표시를 수용한다."""

from __future__ import annotations

from datetime import datetime
from math import ceil

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFormLayout, QLabel, QWidget


class SessionStatusWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        self.status_label = QLabel("상태: 대기")
        self._capture_count = 0
        self._next_capture_time: datetime | None = None
        self._capture_overview = QLabel("-", self)
        layout.addRow("캡처 현황:", self._capture_overview)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(1000)
        self._refresh_timer.timeout.connect(self._refresh_capture_overview)

    def set_status(self, status: str) -> None:
        self.status_label.setText(f"상태: {status}")

    def set_capture_count(self, count: int) -> None:
        self._capture_count = count
        self._refresh_capture_overview()

    def set_next_capture(self, capture_time: datetime | None) -> None:
        self._next_capture_time = capture_time
        if capture_time is None:
            self._refresh_timer.stop()
        elif not self._refresh_timer.isActive():
            self._refresh_timer.start()
        self._refresh_capture_overview()

    def _refresh_capture_overview(self, now: datetime | None = None) -> None:
        if self._next_capture_time is None:
            self._capture_overview.setText("-")
            return
        next_number = self._capture_count + 1
        remaining_seconds = max(
            0,
            (self._next_capture_time - (now or datetime.now())).total_seconds(),
        )
        remaining_minutes = ceil(remaining_seconds / 60)
        self._capture_overview.setText(
            f"{next_number}번째 캡처까지: {remaining_minutes}m"
        )
