"""세션 시작 이후 선택한 간격에 맞춰 캡처 신호를 발생시킨다."""

from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QTimer, Signal

from settings import SUPPORTED_CAPTURE_INTERVAL_SECONDS


def next_capture_time(now: datetime, interval_seconds: int) -> datetime:
    """현재 시각에서 선택 간격 뒤의 다음 캡처 시각을 반환한다."""

    if interval_seconds not in SUPPORTED_CAPTURE_INTERVAL_SECONDS:
        raise ValueError("Unsupported capture interval")
    return now + timedelta(seconds=interval_seconds)


class CaptureScheduler(QObject):
    """단발성 QTimer를 매 캡처 뒤 재설정해 시스템 시계 오차 누적을 피한다."""

    capture_due = Signal()
    next_time_changed = Signal(datetime)

    def __init__(self, interval_seconds: int, parent: QObject | None = None) -> None:
        super().__init__(parent)
        if interval_seconds not in SUPPORTED_CAPTURE_INTERVAL_SECONDS:
            raise ValueError("Unsupported capture interval")
        self._interval_seconds = interval_seconds
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)
        self._next_time: datetime | None = None

    @property
    def next_time(self) -> datetime | None:
        return self._next_time

    def start(self) -> None:
        self._schedule_next()

    def stop(self) -> None:
        self._timer.stop()
        self._next_time = None

    def _on_timeout(self) -> None:
        self.capture_due.emit()
        self._schedule_next()

    def _schedule_next(self) -> None:
        now = datetime.now()
        if self._next_time is None:
            self._next_time = next_capture_time(now, self._interval_seconds)
        else:
            interval = timedelta(seconds=self._interval_seconds)
            self._next_time += interval
            while self._next_time <= now:
                self._next_time += interval
        delay_ms = max(1, int((self._next_time - now).total_seconds() * 1000))
        self._timer.start(delay_ms)
        self.next_time_changed.emit(self._next_time)
