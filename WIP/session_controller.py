"""세션 상태와 UI에 독립적인 캡처·GIF 처리 흐름을 관리한다."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from capture_scheduler import CaptureScheduler
from gif_builder import GifBuilder
from screenshot_capture import ScreenshotCapture, ScreenshotCaptureError
from settings import AppSettings
from storage import SessionStorage


class SessionState(str, Enum):
    IDLE = "IDLE"
    RECORDING = "RECORDING"
    ENCODING = "ENCODING"


class SessionController(QObject):
    state_changed = Signal(SessionState)
    capture_count_changed = Signal(int)
    next_capture_changed = Signal(datetime)
    status_changed = Signal(str)
    output_ready = Signal(Path)

    def __init__(self, settings: AppSettings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._state = SessionState.IDLE
        self._capture_count = 0
        self._session_start: datetime | None = None
        self._session_directory: Path | None = None
        self._screenshots_directory: Path | None = None
        self._scheduler: CaptureScheduler | None = None
        self._screenshot_capture = ScreenshotCapture()
        self._gif_builder = GifBuilder()
        self._storage = SessionStorage(settings.storage_root)

    @property
    def state(self) -> SessionState:
        return self._state

    def start(self, interval_minutes: int) -> None:
        if self._state is not SessionState.IDLE:
            return

        self._session_start = datetime.now()
        try:
            self._session_directory = self._storage.create_session_directory(self._session_start)
            self._screenshots_directory = self._session_directory / "screenshots"
            self._screenshots_directory.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            self.status_changed.emit(f"Session start failed: {error}")
            return
        self._capture_count = 0
        self.capture_count_changed.emit(self._capture_count)
        self._set_state(SessionState.RECORDING)
        self.status_changed.emit("Recording")

        self._scheduler = CaptureScheduler(interval_minutes, self)
        self._scheduler.capture_due.connect(self._capture_screenshot)
        self._scheduler.next_time_changed.connect(self.next_capture_changed)
        self._scheduler.start()

    def finish(self) -> None:
        if self._state is not SessionState.RECORDING:
            return
        assert self._scheduler is not None
        self._scheduler.stop()
        self._set_state(SessionState.ENCODING)
        self.status_changed.emit("Encoding GIF")

        assert self._session_start is not None
        assert self._session_directory is not None
        assert self._screenshots_directory is not None
        finished_at = datetime.now()
        gif_path = self._storage.gif_output_path(
            self._session_directory,
            self._session_start,
            finished_at,
        )
        try:
            frame_count = self._gif_builder.build(
                self._screenshots_directory,
                gif_path,
                self._settings.gif_frame_duration_ms,
                self._settings.gif_loop,
            )
            self.status_changed.emit(f"Completed: {frame_count} frames")
        except ValueError:
            self.status_changed.emit("No screenshots captured; GIF was not created")
        except (OSError, RuntimeError) as error:
            self.status_changed.emit(f"GIF generation failed: {error}")
        finally:
            self._set_state(SessionState.IDLE)
            if self._settings.open_output_on_finish:
                self.output_ready.emit(self._session_directory)

    def _capture_screenshot(self) -> None:
        if self._state is not SessionState.RECORDING:
            return
        assert self._screenshots_directory is not None
        try:
            self._screenshot_capture.capture(self._screenshots_directory)
            self._capture_count += 1
            self.capture_count_changed.emit(self._capture_count)
            self.status_changed.emit("Recording")
        except ScreenshotCaptureError as error:
            self.status_changed.emit(f"Capture failed: {error}")

    def _set_state(self, state: SessionState) -> None:
        self._state = state
        self.state_changed.emit(state)
