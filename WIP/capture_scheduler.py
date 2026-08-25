"""시스템 시계의 선택 간격 경계에 맞춰 캡처 신호를 발생시킨다."""

from __future__ import annotations

from datetime import datetime, timedelta
from math import ceil

from PySide6.QtCore import QObject, Qt, QTimer, Signal

from settings import SUPPORTED_CAPTURE_INTERVAL_SECONDS


def next_capture_time(now: datetime, interval_seconds: int) -> datetime:
    """현재 시각보다 엄격히 뒤에 있는 다음 interval 경계를 반환한다."""

    if interval_seconds not in SUPPORTED_CAPTURE_INTERVAL_SECONDS:
        raise ValueError("Unsupported capture interval")
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed_seconds = (now - day_start).total_seconds()
    next_boundary = (int(elapsed_seconds) // interval_seconds + 1) * interval_seconds
    return day_start + timedelta(seconds=next_boundary)


def timer_delay_milliseconds(now: datetime, capture_time: datetime) -> int:
    """경계보다 일찍 실행되지 않도록 남은 시간을 올림한 밀리초로 반환한다."""

    return max(1, ceil((capture_time - now).total_seconds() * 1000))


def is_capture_due(now: datetime, capture_time: datetime) -> bool:
    return now >= capture_time


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
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
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
        now = datetime.now()
        if self._next_time is not None and not is_capture_due(now, self._next_time):
            self._arm_timer(now)
            return
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
        self._arm_timer(now)
        self.next_time_changed.emit(self._next_time)

    def _arm_timer(self, now: datetime) -> None:
        assert self._next_time is not None
        self._timer.start(timer_delay_milliseconds(now, self._next_time))
