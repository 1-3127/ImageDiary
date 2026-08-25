"""ImageDiary v0.1의 최소 PySide6 사용자 인터페이스."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from session_controller import SessionController, SessionState
from settings import AppSettings


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.setWindowTitle("ImageDiary")
        self._controller = SessionController(settings, self)
        self._build_ui()
        self._connect_signals()
        self._apply_state(SessionState.IDLE)

    def _build_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)

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

        details = QFormLayout()
        self._status = QLabel("대기", root)
        self._captures = QLabel("0", root)
        self._next_capture = QLabel("-", root)
        details.addRow("상태:", self._status)
        details.addRow("캡처 수:", self._captures)
        details.addRow("다음 캡처:", self._next_capture)

        buttons = QHBoxLayout()
        self._start_button = QPushButton("시작", root)
        self._finish_button = QPushButton("종료 및 GIF 생성", root)
        buttons.addWidget(self._start_button)
        buttons.addWidget(self._finish_button)

        layout.addWidget(interval_group)
        layout.addLayout(details)
        layout.addLayout(buttons)
        self.setCentralWidget(root)

    def _connect_signals(self) -> None:
        self._start_button.clicked.connect(self._start)
        self._finish_button.clicked.connect(self._controller.finish)
        self._controller.state_changed.connect(self._apply_state)
        self._controller.status_changed.connect(self._status.setText)
        self._controller.capture_count_changed.connect(lambda count: self._captures.setText(str(count)))
        self._controller.next_capture_changed.connect(self._show_next_capture)
        self._controller.output_ready.connect(self._open_output_directory)

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
            self._next_capture.setText("-")

    def _show_next_capture(self, capture_time: datetime) -> None:
        self._next_capture.setText(capture_time.strftime("%Y-%m-%d %H:%M:%S"))

    @staticmethod
    def _open_output_directory(directory: Path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))
