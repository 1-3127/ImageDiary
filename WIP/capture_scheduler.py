"""시스템 시계의 15분 또는 30분 경계에 맞춰 캡처 신호를 발생시킨다."""

from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QTimer, Signal


def next_capture_time(now: datetime, interval_minutes: int) -> datetime:
    """현재 시각보다 엄격히 뒤에 있는 다음 interval 경계를 반환한다."""

    if interval_minutes not in (15, 30):
        raise ValueError("interval_minutes must be 15 or 30")

    boundary_minute = ((now.minute // interval_minutes) + 1) * interval_minutes
    candidate = now.replace(second=0, microsecond=0)
    if boundary_minute >= 60:
        candidate = candidate.replace(minute=0) + timedelta(hours=1)
    else:
        candidate = candidate.replace(minute=boundary_minute)
    return candidate


class CaptureScheduler(QObject):
    """단발성 QTimer를 매 캡처 뒤 재설정해 시스템 시계 오차 누적을 피한다."""

    capture_due = Signal()
    next_time_changed = Signal(datetime)

    def __init__(self, interval_minutes: int, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._interval_minutes = interval_minutes
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
        self._next_time = next_capture_time(now, self._interval_minutes)
        delay_ms = max(1, int((self._next_time - now).total_seconds() * 1000))
        self._timer.start(delay_ms)
        self.next_time_changed.emit(self._next_time)
