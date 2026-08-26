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
from recovery_dialog import RecoveryAction, ask_recovery_action
from session_controller import SessionController, SessionState
from session_recovery import find_latest_incomplete_session
from session_status_widget import SessionStatusWidget
from settings import AppSettings
from settings_repository import SettingsRepository
from settings_dialog import SettingsDialog
from startup_manager import StartupManager, StartupRegistrationError


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
        toolbar.addWidget(self._pin_button)
        toolbar.addWidget(self._settings_button)

        buttons = QHBoxLayout()
        self._start_button = QPushButton("시작", root)
        self._finish_button = QPushButton("종료 및 GIF 생성", root)
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

    def _start(self) -> None:
        self._controller.start()

    def _finish(self) -> None:
        default_filename = self._controller.begin_finish()
        if default_filename is None:
            QMessageBox.warning(
                self,
                "GIF 생성",
                "캡처 이미지가 없어 GIF를 생성할 수 없습니다.",
            )
            return
        dialog = GifOutputDialog(
            default_filename,
            self._settings.export_root,
            self,
        )
        if dialog.exec():
            self._controller.finish(dialog.options())
        else:
            self._controller.cancel_finish()

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
        dialog.exec()

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
            self._controller.finish_recovered(candidate)

    @staticmethod
    def _open_output_directory(directory: Path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))
