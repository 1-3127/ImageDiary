"""ImageDiary v0.1의 최소 PySide6 사용자 인터페이스."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from gif_progress_dialog import GifProgressDialog
from gif_output_dialog import GifOutputDialog
from gif_output_options import GifOutputOptions
from error_reporting import issue_report_guidance, show_retry_message
from recovery_dialog import RecoveryAction, ask_recovery_action
from session_controller import SessionController, SessionState
from session_recovery import (
    find_completed_sessions_with_images,
    find_latest_incomplete_session,
    find_marked_incomplete_sessions,
    mark_session_unfinished,
)
from session_status_widget import SessionStatusWidget
from settings import AppSettings
from settings_repository import SettingsRepository
from settings_dialog import SettingsDialog
from startup_manager import StartupManager, StartupRegistrationError
from unfinished_sessions_dialog import UnfinishedSessionsDialog


class MainWindow(QMainWindow):
    def __init__(
        self,
        settings_repository: SettingsRepository,
        startup_manager: StartupManager,
    ) -> None:
        super().__init__()
        self.setWindowTitle("ImageDiary")
        self._settings_repository = settings_repository
        self._startup_manager = startup_manager
        self._settings = settings_repository.load()
        self._controller = SessionController(self._settings, self)
        self._gif_progress = GifProgressDialog(self)
        self._build_ui()
        self._connect_signals()
        self._pin_button.setChecked(self._settings.always_on_top)
        self._apply_always_on_top(self._settings.always_on_top)
        self._apply_state(SessionState.IDLE)

    def _build_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        self._session_status = SessionStatusWidget(root)
        toolbar.addWidget(self._session_status.status_label)
        self._pin_button = QToolButton(root)
        self._pin_button.setText("고정")
        self._pin_button.setCheckable(True)
        self._pin_button.setToolTip("항상 위에 고정")
        self._settings_button = QToolButton(root)
        self._settings_button.setText("설정")
        self._settings_button.setToolTip("설정 열기")
        self._help_button = QToolButton(root)
        self._help_button.setText("?")
        self._help_button.setToolTip("도움말")
        toolbar.addWidget(self._pin_button)
        toolbar.addWidget(self._settings_button)
        toolbar.addWidget(self._help_button)

        buttons = QHBoxLayout()
        self._start_button = QPushButton("시작", root)
        self._finish_button = QPushButton("종료 및 저장", root)
        buttons.addWidget(self._start_button)
        buttons.addWidget(self._finish_button)

        layout.addLayout(toolbar)
        layout.addWidget(self._session_status)
        layout.addLayout(buttons)
        self.setCentralWidget(root)

    def _connect_signals(self) -> None:
        self._start_button.clicked.connect(self._start)
        self._finish_button.clicked.connect(self._finish)
        self._pin_button.toggled.connect(self._pin_toggled)
        self._settings_button.clicked.connect(self._open_settings)
        self._help_button.clicked.connect(self._show_help)
        self._controller.state_changed.connect(self._apply_state)
        self._controller.status_changed.connect(self._session_status.set_status)
        self._controller.capture_count_changed.connect(
            self._session_status.set_capture_count
        )
        self._controller.next_capture_changed.connect(
            self._session_status.set_next_capture
        )
        self._controller.output_ready.connect(self._open_output_directory)
        self._controller.encoding_progress.connect(self._gif_progress.update_progress)
        self._controller.gif_build_failed.connect(self._handle_gif_failure)
        self._controller.image_export_failed.connect(self._handle_image_export_failure)
        self._controller.screenshot_capture_failed.connect(self._handle_capture_failure)
        self._controller.configuration_error.connect(self._handle_configuration_error)

    def _start(self) -> None:
        self._controller.start()

    def _finish(self) -> None:
        default_filename = self._controller.begin_finish()
        if default_filename is None:
            QMessageBox.warning(
                self,
                "내보내기 설정",
                "캡처 이미지가 없어 GIF를 생성할 수 없습니다.",
            )
            return
        dialog = GifOutputDialog(
            default_filename,
            self._settings.export_root,
            self,
        )
        dialog.image_only_requested.connect(self._controller.save_images_only)
        if dialog.exec():
            self._controller.finish(dialog.options())
        elif dialog.return_to_session_requested:
            self._controller.cancel_finish()
        else:
            self._controller.finish_without_gif()

    def _apply_state(self, state: SessionState) -> None:
        is_idle = state is SessionState.IDLE
        self._start_button.setEnabled(is_idle)
        self._finish_button.setEnabled(state is SessionState.RECORDING)
        if is_idle:
            self._session_status.set_next_capture(None)
        if state is SessionState.ENCODING:
            self._gif_progress.begin()
        elif is_idle:
            self._gif_progress.complete()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._settings, self)
        dialog.settings_saved.connect(self._save_settings)
        dialog.reset_requested.connect(lambda: self._reset_settings(dialog))
        dialog.unfinished_sessions_requested.connect(
            lambda: self._open_unfinished_session(dialog)
        )
        dialog.completed_sessions_requested.connect(
            lambda: self._open_completed_session(dialog)
        )
        dialog.exec()

    def _open_unfinished_session(self, settings_dialog: SettingsDialog) -> None:
        candidates = find_marked_incomplete_sessions(self._settings.internal_storage_root)
        if not candidates:
            QMessageBox.information(settings_dialog, "미완료 세션", "GIF 저장을 다시 시도할 미완료 세션이 없습니다.")
            return
        dialog = UnfinishedSessionsDialog(candidates, settings_dialog)
        if not dialog.exec():
            return
        settings_dialog.reject()
        self._controller.prepare_recovered_finish(dialog.selected_candidate())
        self._finish()

    def _open_completed_session(self, settings_dialog: SettingsDialog) -> None:
        candidates = find_completed_sessions_with_images(self._settings.internal_storage_root)
        if not candidates:
            QMessageBox.information(settings_dialog, "이전 세션 GIF 다시 만들기", "내부 이미지가 남아 있는 완료 세션이 없습니다.")
            return
        dialog = UnfinishedSessionsDialog(
            candidates,
            settings_dialog,
            title="이전 세션 GIF 다시 만들기",
            description="GIF를 다시 만들 세션 폴더를 선택하세요.",
            confirm_text="내보내기 설정",
        )
        if not dialog.exec():
            return
        settings_dialog.reject()
        self._controller.prepare_recovered_finish(dialog.selected_candidate())
        self._finish()

    def _handle_gif_failure(self, error: str, options: object) -> None:
        if not isinstance(options, GifOutputOptions):
            return
        retry = show_retry_message(self, "GIF 저장 실패", f"GIF를 저장하지 못했습니다.\n{error}")
        if retry:
            self._controller.retry_finish(options)
            return
        self._controller.mark_current_session_unfinished()
        QMessageBox.information(
            self,
            "미완료 세션 보관",
            "미완료 세션으로 보관했습니다. 설정의 ‘미완료 세션 GIF 저장’에서 다시 시도할 수 있습니다.",
        )

    def _handle_image_export_failure(self, error: str, options: object) -> None:
        if not isinstance(options, GifOutputOptions):
            return
        if show_retry_message(self, "이미지 저장 실패", f"원본 이미지를 저장하지 못했습니다.\n{error}"):
            self._controller.retry_image_export(options)

    def _handle_capture_failure(self, error: str) -> None:
        if show_retry_message(self, "화면 캡처 실패", f"화면을 캡처하지 못했습니다.\n{error}"):
            self._controller.retry_capture()

    def _handle_configuration_error(self, error: str) -> None:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("설정 또는 저장 경로 오류")
        dialog.setText(f"설정값 또는 저장 경로를 확인해 주세요.\n{error}")
        dialog.setInformativeText(issue_report_guidance())
        reconfigure = dialog.addButton("설정 열기", QMessageBox.ButtonRole.AcceptRole)
        reset = dialog.addButton("초기화", QMessageBox.ButtonRole.DestructiveRole)
        dialog.addButton("닫기", QMessageBox.ButtonRole.RejectRole)
        dialog.exec()
        if dialog.clickedButton() is reset:
            self._reset_settings_without_dialog()
        elif dialog.clickedButton() is reconfigure:
            self._open_settings()

    def _reset_settings_without_dialog(self) -> None:
        try:
            self._startup_manager.set_enabled(False)
        except StartupRegistrationError as error:
            QMessageBox.critical(self, "설정 초기화 실패", f"{error}\n\n{issue_report_guidance()}")
            return
        self._settings_repository.reset()
        self._settings = self._settings_repository.load()
        self._controller.update_settings(self._settings)
        QMessageBox.information(self, "설정 초기화", "설정을 기본값으로 복원했습니다.")

    def _show_help(self) -> None:
        dialog = QMessageBox(self); dialog.setWindowTitle("메인 화면 도움말"); dialog.setTextFormat(Qt.TextFormat.RichText); dialog.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        dialog.setText(
            "<b>시작</b>을 누르면 즉시 한 장을 캡처하고, 이후 시스템 시각 경계마다 자동 저장합니다.<br><br>"
            "<b>종료 및 저장</b>을 누르면 기록을 멈추고 내보내기 설정을 엽니다.<br>"
            "<b>고정</b>은 창을 항상 위에 표시합니다. <b>설정</b>에서는 다음 세션의 기본값과 세션 복구를 관리합니다.<br><br>"
            '<a href="https://github.com/1-3127/ImageDiary/blob/main/docs/quick_start.md">GitHub 간단 사용 설명서</a>'
        ); dialog.exec()

    def _reset_settings(self, dialog: SettingsDialog) -> None:
        confirmation = QMessageBox(self)
        confirmation.setIcon(QMessageBox.Icon.Warning)
        confirmation.setWindowTitle("설정 초기화")
        confirmation.setText("앱 설정을 기본값으로 복원하시겠습니까?")
        confirmation.setInformativeText(
            "Windows 로그인 시 시작도 해제됩니다.\n\n"
            "저장된 이미지와 GIF는 삭제되지 않습니다."
        )
        reset_button = confirmation.addButton(
            "초기화", QMessageBox.ButtonRole.DestructiveRole
        )
        confirmation.addButton("취소", QMessageBox.ButtonRole.RejectRole)
        confirmation.exec()
        if confirmation.clickedButton() is not reset_button:
            return
        try:
            self._startup_manager.set_enabled(False)
        except StartupRegistrationError as error:
            QMessageBox.critical(self, "설정 초기화 실패", str(error))
            return
        self._settings_repository.reset()
        self._settings = self._settings_repository.load()
        self._controller.update_settings(self._settings)
        dialog.reject()
        QMessageBox.information(
            self,
            "설정 초기화",
            "설정을 기본값으로 복원했습니다.",
        )

    def _save_settings(self, settings: object) -> None:
        if not isinstance(settings, AppSettings):
            return
        try:
            self._startup_manager.set_enabled(settings.run_at_login)
        except StartupRegistrationError as error:
            QMessageBox.critical(self, "설정 저장 실패", str(error))
            return

        self._settings = settings
        self._settings_repository.save(settings)
        self._controller.update_settings(settings)
        if self._controller.state is not SessionState.IDLE:
            QMessageBox.information(
                self,
                "설정 저장",
                "변경된 설정은 다음 세션부터 적용됩니다.",
            )

    def _pin_toggled(self, enabled: bool) -> None:
        self._apply_always_on_top(enabled)
        self._settings = replace(self._settings, always_on_top=enabled)
        self._settings_repository.save(self._settings)
        self._controller.update_settings(self._settings)

    def _apply_always_on_top(self, enabled: bool) -> None:
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        if was_visible:
            self.show()

    def check_for_recovery(self) -> None:
        candidate = find_latest_incomplete_session(
            self._settings.internal_storage_root
        )
        if candidate is None:
            return

        action = ask_recovery_action(candidate, self)
        if action is RecoveryAction.RESUME:
            self._controller.resume(candidate)
        elif action is RecoveryAction.FINISH:
            self._controller.prepare_recovered_finish(candidate)
            self._finish()
        else:
            mark_session_unfinished(candidate.session_directory)

    @staticmethod
    def _open_output_directory(directory: Path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))
