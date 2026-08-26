"""세션 상태와 UI에 독립적인 캡처·GIF 처리 흐름을 관리한다."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from capture_scheduler import CaptureScheduler
from file_exporter import FileExportError, FileExporter
from gif_builder import GifBuilder
from gif_output_options import GifOutputOptions
from gif_post_processor import GifPostProcessor
from image_order import sorted_image_paths
from screenshot_capture import ScreenshotCapture, ScreenshotCaptureError
from settings import AppSettings
from session_recovery import RecoveryCandidate
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
    encoding_progress = Signal(int, int)

    def __init__(self, settings: AppSettings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._next_settings = settings
        self._session_settings: AppSettings | None = None
        self._state = SessionState.IDLE
        self._capture_count = 0
        self._session_start: datetime | None = None
        self._session_directory: Path | None = None
        self._screenshots_directory: Path | None = None
        self._scheduler: CaptureScheduler | None = None
        self._screenshot_capture = ScreenshotCapture()
        self._gif_builder = GifBuilder()
        self._file_exporter = FileExporter()
        self._storage = SessionStorage(settings.storage_root)

    @property
    def state(self) -> SessionState:
        return self._state

    def start(self) -> None:
        if self._state is not SessionState.IDLE:
            return

        self._session_settings = self._next_settings
        self._storage = SessionStorage(self._session_settings.internal_storage_root)
        self._session_start = datetime.now()
        try:
            self._session_directory = self._storage.create_session_directory(
                self._session_start,
                (self._session_settings.export_root,),
            )
            self._screenshots_directory = self._session_directory / "Screenshot"
            self._screenshots_directory.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            self.status_changed.emit(f"세션 시작 실패: {error}")
            return
        self._capture_count = 0
        self.capture_count_changed.emit(self._capture_count)
        self._set_state(SessionState.RECORDING)
        self.status_changed.emit("기록 중")

        self._scheduler = CaptureScheduler(
            self._session_settings.capture_interval_seconds,
            self,
        )
        self._scheduler.capture_due.connect(self._capture_screenshot)
        self._scheduler.next_time_changed.connect(self.next_capture_changed)
        self._scheduler.start()
        self._capture_screenshot()

    def update_settings(self, settings: AppSettings) -> None:
        """새 설정을 다음 세션에 사용한다. 진행 중인 세션 스냅샷은 유지한다."""

        self._next_settings = settings

    def resume(self, candidate: RecoveryCandidate) -> None:
        if self._state is not SessionState.IDLE:
            return

        self._session_settings = self._next_settings
        self._storage = SessionStorage(self._session_settings.internal_storage_root)
        self._session_start = candidate.started_at
        self._session_directory = candidate.session_directory
        self._screenshots_directory = candidate.screenshots_directory
        self._capture_count = len(candidate.image_paths)
        self.capture_count_changed.emit(self._capture_count)
        self._set_state(SessionState.RECORDING)
        self.status_changed.emit("복구된 세션 기록 중")

        self._scheduler = CaptureScheduler(
            self._session_settings.capture_interval_seconds,
            self,
        )
        self._scheduler.capture_due.connect(self._capture_screenshot)
        self._scheduler.next_time_changed.connect(self.next_capture_changed)
        self._scheduler.start()

    def finish_recovered(self, candidate: RecoveryCandidate) -> None:
        if self._state is not SessionState.IDLE:
            return

        self._session_settings = self._next_settings
        self._storage = SessionStorage(self._session_settings.internal_storage_root)
        self._session_start = candidate.started_at
        self._session_directory = candidate.session_directory
        self._screenshots_directory = candidate.screenshots_directory
        self._capture_count = len(candidate.image_paths)
        self.capture_count_changed.emit(self._capture_count)
        self._scheduler = None
        self._set_state(SessionState.RECORDING)
        self.finish()

    def default_gif_filename(self) -> str | None:
        if self._screenshots_directory is None or self._session_directory is None:
            return None
        image_paths = sorted_image_paths(self._screenshots_directory)
        if not image_paths:
            return None
        return self._storage.gif_output_path(
            self._session_directory,
            image_paths[0],
            image_paths[-1],
        ).name

    def begin_finish(self) -> str | None:
        """출력 옵션을 고르는 동안 추가 캡처를 멈춘다."""
        if self._state is not SessionState.RECORDING:
            return None
        if self._scheduler is not None:
            self._scheduler.stop()
        return self.default_gif_filename()

    def cancel_finish(self) -> None:
        """출력 설정 취소 시 현재 기록 세션의 캡처를 다시 시작한다."""
        if self._state is SessionState.RECORDING and self._scheduler is not None:
            self._scheduler.start()

    def finish(self, output_options: GifOutputOptions | None = None) -> None:
        if self._state is not SessionState.RECORDING:
            return
        if self._scheduler is not None:
            self._scheduler.stop()
        self._set_state(SessionState.ENCODING)
        self.status_changed.emit("GIF 생성 중")

        assert self._session_start is not None
        assert self._session_directory is not None
        assert self._screenshots_directory is not None
        assert self._session_settings is not None
        try:
            image_paths = sorted_image_paths(self._screenshots_directory)
            if not image_paths:
                raise ValueError("No screenshots are available for GIF generation.")
            if output_options is None:
                output_options = GifOutputOptions(
                    filename=self._storage.gif_output_path(
                        self._session_directory,
                        image_paths[0],
                        image_paths[-1],
                    ).name
                )
            gif_path = self._storage.gif_output_path(
                self._session_directory,
                image_paths[0],
                image_paths[-1],
                output_options.filename,
            )
            frame_processor = GifPostProcessor(output_options).process
            frame_count = self._gif_builder.build(
                self._screenshots_directory,
                gif_path,
                self._session_settings.gif_frame_duration_ms,
                self._session_settings.gif_loop,
                self.encoding_progress.emit,
                frame_processor,
            )
            exported_gif = self._file_exporter.copy_gif(
                gif_path,
                output_options.gif_export_root or self._session_settings.export_root,
                self._session_directory.name,
            )
            if output_options.export_images:
                image_root = (
                    output_options.gif_export_root or self._session_settings.export_root
                    if output_options.images_with_gif
                    else output_options.image_export_root
                )
                assert image_root is not None
                for screenshot in self._screenshots_directory.iterdir():
                    if screenshot.is_file():
                        self._file_exporter.copy_screenshot(
                            screenshot,
                            image_root,
                            self._session_directory.name,
                        )
            self.status_changed.emit(f"완료: {frame_count}프레임")
        except ValueError:
            self.status_changed.emit("캡처 이미지가 없어 GIF를 생성하지 않았습니다")
        except (OSError, RuntimeError, FileExportError) as error:
            self.status_changed.emit(f"GIF 생성 실패: {error}")
        finally:
            self._set_state(SessionState.IDLE)
            if self._session_settings.open_output_on_finish:
                output_directory = (
                    exported_gif.parent if "exported_gif" in locals() else self._session_directory
                )
                self.output_ready.emit(output_directory)

    def _capture_screenshot(self) -> None:
        if self._state is not SessionState.RECORDING:
            return
        assert self._screenshots_directory is not None
        assert self._session_directory is not None
        assert self._session_settings is not None
        try:
            self._screenshot_capture.capture(
                self._screenshots_directory,
                sequence_number=self._capture_count + 1,
                image_format=self._session_settings.capture_format,
                image_quality=self._session_settings.image_quality,
                capture_target=self._session_settings.capture_target,
            )
            self._capture_count += 1
            self.capture_count_changed.emit(self._capture_count)
            self.status_changed.emit("기록 중")
        except ScreenshotCaptureError as error:
            self.status_changed.emit(f"화면 캡처 실패: {error}")

    def _set_state(self, state: SessionState) -> None:
        self._state = state
        self.state_changed.emit(state)
