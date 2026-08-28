"""세션 상태와 캡처·GIF 처리를 관리한다."""

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
from session_recovery import RecoveryCandidate, clear_unfinished_marker, mark_session_unfinished
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
    encoding_progress = Signal(int, int)
    gif_build_failed = Signal(str, object)
    image_export_failed = Signal(str, object)
    screenshot_capture_failed = Signal(str)
    configuration_error = Signal(str)

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
                self._session_start, (self._session_settings.export_root,)
            )
            self._screenshots_directory = self._session_directory / "Screenshot"
            self._screenshots_directory.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            self.status_changed.emit(f"세션 시작 실패: {error}")
            self.configuration_error.emit(str(error))
            return
        self._capture_count = 0
        self.capture_count_changed.emit(0)
        self._set_state(SessionState.RECORDING)
        self.status_changed.emit("기록 중")
        self._scheduler = CaptureScheduler(self._session_settings.capture_interval_seconds, self)
        self._scheduler.capture_due.connect(self._capture_screenshot)
        self._scheduler.next_time_changed.connect(self.next_capture_changed)
        self._scheduler.start()
        self._capture_screenshot()

    def update_settings(self, settings: AppSettings) -> None:
        self._next_settings = settings

    def shutdown(self) -> None:
        """앱 종료 전에 활성 타이머와 보류 중인 내보내기 상태를 정리한다."""
        if self._scheduler is not None:
            self._scheduler.stop()
            self._scheduler = None
        self._pending_images_only_options = None

    def resume(self, candidate: RecoveryCandidate) -> None:
        if self._state is not SessionState.IDLE:
            return
        self._load_recovery_candidate(candidate)
        self._set_state(SessionState.RECORDING)
        self.status_changed.emit("복구한 세션 기록 중")
        assert self._session_settings is not None
        self._scheduler = CaptureScheduler(self._session_settings.capture_interval_seconds, self)
        self._scheduler.capture_due.connect(self._capture_screenshot)
        self._scheduler.next_time_changed.connect(self.next_capture_changed)
        self._scheduler.start()

    def finish_recovered(self, candidate: RecoveryCandidate) -> None:
        self.prepare_recovered_finish(candidate)
        self.finish()

    def prepare_recovered_finish(self, candidate: RecoveryCandidate) -> None:
        if self._state is not SessionState.IDLE:
            return
        self._load_recovery_candidate(candidate)
        self._scheduler = None
        self._set_state(SessionState.RECORDING)

    def _load_recovery_candidate(self, candidate: RecoveryCandidate) -> None:
        self._session_settings = self._next_settings
        self._storage = SessionStorage(self._session_settings.internal_storage_root)
        self._session_start = candidate.started_at
        self._session_directory = candidate.session_directory
        self._screenshots_directory = candidate.screenshots_directory
        self._capture_count = len(candidate.image_paths)
        self.capture_count_changed.emit(self._capture_count)

    def default_gif_filename(self) -> str | None:
        if self._screenshots_directory is None or self._session_directory is None:
            return None
        image_paths = sorted_image_paths(self._screenshots_directory)
        if not image_paths:
            return None
        return self._storage.gif_output_path(self._session_directory, image_paths[0], image_paths[-1]).name

    def begin_finish(self) -> str | None:
        if self._state is not SessionState.RECORDING:
            return None
        if self._scheduler is not None:
            self._scheduler.stop()
        return self.default_gif_filename()

    def cancel_finish(self) -> None:
        if self._state is not SessionState.RECORDING:
            return
        if self._scheduler is not None:
            self._scheduler.start()
            return
        self.mark_current_session_unfinished()
        self.status_changed.emit("대기")
        self._set_state(SessionState.IDLE)

    def mark_current_session_unfinished(self) -> None:
        if self._session_directory is not None:
            mark_session_unfinished(self._session_directory)

    def finish_without_gif(self) -> None:
        """GIF 없이 현재 캡처를 미완료 세션으로 보관하고 종료한다."""
        if self._state is not SessionState.RECORDING:
            return
        if self._scheduler is not None:
            self._scheduler.stop()
        self.mark_current_session_unfinished()
        self.status_changed.emit("완료")
        self._set_state(SessionState.IDLE)

    def complete_with_images_only(self) -> None:
        """이미지만 내보낸 세션을 내부 더미 GIF로 완료 상태로 확정한다."""
        assert self._session_directory is not None
        assert self._screenshots_directory is not None
        image_paths = sorted_image_paths(self._screenshots_directory)
        if image_paths:
            self._storage.gif_output_path(
                self._session_directory, image_paths[0], image_paths[-1]
            ).touch(exist_ok=True)
        clear_unfinished_marker(self._session_directory)
        self.status_changed.emit("완료")
        self._set_state(SessionState.IDLE)

    def retry_finish(self, output_options: GifOutputOptions) -> None:
        if self._state is not SessionState.IDLE or self._session_directory is None:
            return
        self._set_state(SessionState.RECORDING)
        self.finish(output_options)

    def finish(self, output_options: GifOutputOptions | None = None) -> None:
        if self._state is not SessionState.RECORDING:
            return
        if self._scheduler is not None:
            self._scheduler.stop()
        self._set_state(SessionState.ENCODING)
        self.status_changed.emit("GIF 생성 중")
        assert self._session_directory is not None
        assert self._screenshots_directory is not None
        assert self._session_settings is not None
        try:
            image_paths = sorted_image_paths(self._screenshots_directory)
            if not image_paths:
                raise ValueError("캡처 이미지가 없습니다.")
            if output_options is None:
                output_options = GifOutputOptions(filename=self._storage.gif_output_path(
                    self._session_directory, image_paths[0], image_paths[-1]
                ).name)
            gif_path = self._storage.gif_output_path(
                self._session_directory, image_paths[0], image_paths[-1], output_options.filename
            )
            frame_count = self._gif_builder.build(
                self._screenshots_directory, gif_path,
                int(self._session_settings.gif_frame_duration_ms * {1: 0.5, 2: 1.0, 3: 1.5}[output_options.playback_speed]),
                self._session_settings.gif_loop,
                self.encoding_progress.emit,
                GifPostProcessor(output_options).process,
            )
            exported_gif = self._file_exporter.copy_gif(
                gif_path,
                output_options.gif_export_root or self._session_settings.export_root,
                self._session_directory.name,
            )
            clear_unfinished_marker(self._session_directory)
        except ValueError:
            self.status_changed.emit("캡처 이미지가 없어 GIF를 생성하지 않았습니다.")
            self._set_state(SessionState.IDLE)
            return
        except (OSError, RuntimeError, FileExportError) as error:
            self.status_changed.emit(f"GIF 생성 실패: {error}")
            self._set_state(SessionState.IDLE)
            assert output_options is not None
            self.gif_build_failed.emit(str(error), output_options)
            return

        self.status_changed.emit(f"완료: 이미지 {frame_count}장")
        if self._session_settings.open_output_on_finish:
            self.output_ready.emit(exported_gif.parent)
        self._set_state(SessionState.IDLE)
        if output_options.export_images:
            self._export_images(output_options)

    def _export_images(self, output_options: GifOutputOptions) -> None:
        assert self._screenshots_directory is not None
        assert self._session_directory is not None
        assert self._session_settings is not None
        image_root = (
            output_options.gif_export_root or self._session_settings.export_root
            if output_options.images_with_gif else output_options.image_export_root
        )
        if image_root is None:
            return
        try:
            for screenshot in self._screenshots_directory.iterdir():
                if screenshot.is_file():
                    self._file_exporter.copy_screenshot(screenshot, image_root, self._session_directory.name)
        except (OSError, FileExportError) as error:
            self.status_changed.emit(f"이미지 저장 실패: {error}")
            self.image_export_failed.emit(str(error), output_options)

    def retry_image_export(self, output_options: GifOutputOptions) -> None:
        if self._screenshots_directory is not None:
            self._export_images(output_options)

    def save_images_only(self, output_options: GifOutputOptions) -> None:
        if self._state is not SessionState.RECORDING:
            return
        self._export_images(output_options)
        self.complete_with_images_only()

    def _capture_screenshot(self) -> None:
        if self._state is not SessionState.RECORDING:
            return
        assert self._screenshots_directory is not None
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
            self.screenshot_capture_failed.emit(str(error))

    def retry_capture(self) -> None:
        self._capture_screenshot()

    def _set_state(self, state: SessionState) -> None:
        self._state = state
        self.state_changed.emit(state)
