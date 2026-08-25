"""ImageDiary v0.1의 최소 PySide6 사용자 인터페이스."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from gif_progress_dialog import GifProgressDialog
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
        self._pin_button = QToolButton(root)
        self._pin_button.setText("고정")
        self._pin_button.setCheckable(True)
        self._pin_button.setToolTip("항상 위에 고정")
        self._settings_button = QToolButton(root)
        self._settings_button.setText("설정")
        self._settings_button.setToolTip("설정 열기")
        toolbar.addWidget(self._pin_button)
        toolbar.addWidget(self._settings_button)

        interval_group = QGroupBox("캡처 간격", root)
        interval_layout = QHBoxLayout(interval_group)
        self._interval_buttons = QButtonGroup(self)
        self._debug_interval = QRadioButton("60초 (디버그)", interval_group)
        self._fifteen_minutes = QRadioButton("15분", interval_group)
        self._thirty_minutes = QRadioButton("30분", interval_group)
        self._fifteen_minutes.setChecked(True)
        self._interval_buttons.addButton(self._debug_interval, 60)
        self._interval_buttons.addButton(self._fifteen_minutes, 15 * 60)
        self._interval_buttons.addButton(self._thirty_minutes, 30 * 60)
        interval_layout.addWidget(self._debug_interval)
        interval_layout.addWidget(self._fifteen_minutes)
        interval_layout.addWidget(self._thirty_minutes)

        self._session_status = SessionStatusWidget(root)

        buttons = QHBoxLayout()
        self._start_button = QPushButton("시작", root)
        self._finish_button = QPushButton("종료 및 GIF 생성", root)
        buttons.addWidget(self._start_button)
        buttons.addWidget(self._finish_button)

        layout.addLayout(toolbar)
        layout.addWidget(interval_group)
        layout.addWidget(self._session_status)
        layout.addLayout(buttons)
        self.setCentralWidget(root)

    def _connect_signals(self) -> None:
        self._start_button.clicked.connect(self._start)
        self._finish_button.clicked.connect(self._controller.finish)
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
        interval_seconds = self._interval_buttons.checkedId()
        self._controller.start(interval_seconds)

    def _apply_state(self, state: SessionState) -> None:
        is_idle = state is SessionState.IDLE
        self._start_button.setEnabled(is_idle)
        self._finish_button.setEnabled(state is SessionState.RECORDING)
        self._debug_interval.setEnabled(is_idle)
        self._fifteen_minutes.setEnabled(is_idle)
        self._thirty_minutes.setEnabled(is_idle)
        if is_idle:
            self._session_status.set_next_capture(None)
        if state is SessionState.ENCODING:
            self._gif_progress.begin()
        elif is_idle:
            self._gif_progress.complete()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._settings, self)
        dialog.settings_saved.connect(self._save_settings)
        dialog.exec()

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
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        if self.isVisible():
            self.show()

    def check_for_recovery(self) -> None:
        candidate = find_latest_incomplete_session(
            self._settings.internal_storage_root
        )
        if candidate is None:
            return

        action = ask_recovery_action(candidate, self)
        if action is RecoveryAction.RESUME:
            self._controller.resume(candidate, self._interval_buttons.checkedId())
        elif action is RecoveryAction.FINISH:
            self._controller.finish_recovered(candidate)

    @staticmethod
    def _open_output_directory(directory: Path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))
