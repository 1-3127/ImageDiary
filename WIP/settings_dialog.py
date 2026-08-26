"""ImageDiary 사용자 설정을 편집하는 대화상자."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from settings import AppSettings, SUPPORTED_CAPTURE_FORMATS
from data_cleanup import find_cleanup_candidates, move_old_sessions_to_trash


class SettingsDialog(QDialog):
    settings_saved = Signal(object)
    reset_requested = Signal()

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("설정")
        self.setModal(True)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._export_path = QLineEdit(str(self._settings.export_root), self)
        form.addRow("저장 경로:", self._path_row(self._export_path, "작업 일기"))

        interval_widget = QWidget(self)
        interval_layout = QHBoxLayout(interval_widget)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        self._interval = QSlider(Qt.Orientation.Horizontal, interval_widget)
        self._interval.setRange(5, 30)
        self._interval.setSingleStep(5)
        self._interval.setPageStep(5)
        self._interval.setTickInterval(5)
        self._interval.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._interval.setValue(self._settings.capture_interval_seconds // 60)
        self._interval_value = QLabel(interval_widget)
        self._interval.valueChanged.connect(self._snap_interval)
        self._snap_interval(self._interval.value())
        interval_layout.addWidget(self._interval)
        interval_layout.addWidget(self._interval_value)
        form.addRow("캡처 간격:", interval_widget)

        self._capture_target = QComboBox(self)
        self._capture_target.addItem("메인 모니터만", "primary")
        self._capture_target.addItem("전체 화면", "all")
        self._capture_target.setCurrentIndex(
            max(0, self._capture_target.findData(self._settings.capture_target))
        )
        form.addRow("캡처 대상:", self._capture_target)

        self._format = QComboBox(self)
        self._format.addItems(list(SUPPORTED_CAPTURE_FORMATS))
        self._format.setCurrentText(self._settings.capture_format)
        form.addRow("이미지 포맷:", self._format)

        self._quality = QSpinBox(self)
        self._quality.setRange(1, 100)
        self._quality.setSuffix("%")
        self._quality.setValue(self._settings.image_quality)
        form.addRow("JPG/WebP 품질:", self._quality)

        self._run_at_login = QCheckBox("Windows 로그인 시 ImageDiary 시작", self)
        self._run_at_login.setChecked(self._settings.run_at_login)
        form.addRow("", self._run_at_login)

        note = QLabel("진행 중 변경한 설정은 다음 세션부터 적용됩니다.", self)
        note.setWordWrap(True)

        cleanup_button = QPushButton("데이터 정리", self)
        cleanup_button.setToolTip(
            "내부 원본 중 최신 2개 세션을 제외한 폴더를 휴지통으로 이동"
        )
        cleanup_button.clicked.connect(self._cleanup_data)
        reset_button = QPushButton("설정 초기화", self)
        reset_button.clicked.connect(self.reset_requested.emit)
        help_button = QPushButton("도움말", self)
        help_button.clicked.connect(self._show_help)
        about_button = QPushButton("앱 정보", self)
        about_button.clicked.connect(self._show_about)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("저장")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("취소")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(note)
        layout.addWidget(cleanup_button)
        layout.addWidget(reset_button)
        layout.addWidget(help_button)
        layout.addWidget(about_button)
        layout.addWidget(buttons)

    def _path_row(self, line_edit: QLineEdit, label: str) -> QWidget:
        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        browse = QPushButton("찾아보기", widget)
        browse.clicked.connect(lambda: self._browse(line_edit, label))
        layout.addWidget(line_edit)
        layout.addWidget(browse)
        return widget

    def _browse(self, line_edit: QLineEdit, label: str) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            f"{label} 저장 폴더 선택",
            line_edit.text(),
        )
        if selected:
            line_edit.setText(selected)

    def _save(self) -> None:
        export_path = self._export_path.text().strip()
        if not export_path:
            return

        updated = replace(
            self._settings,
            export_root=Path(export_path),
            capture_interval_seconds=self._interval.value() * 60,
            capture_target=str(self._capture_target.currentData()),
            capture_format=self._format.currentText(),
            image_quality=self._quality.value(),
            run_at_login=self._run_at_login.isChecked(),
        )
        self.settings_saved.emit(updated)
        self.accept()

    def _snap_interval(self, value: int) -> None:
        snapped = min(30, max(5, round(value / 5) * 5))
        if snapped != value:
            self._interval.setValue(snapped)
            return
        self._interval_value.setText(f"{snapped}분")

    def _show_help(self) -> None:
        QMessageBox.information(
            self,
            "도움말",
            "시작을 누르면 즉시 한 장을 캡처하고, 이후 선택한 시스템 시각 경계마다 캡처합니다.\n\n"
            "종료 및 GIF 생성을 누르면 공유용 GIF 출력 설정을 선택할 수 있습니다.\n\n"
            "내부 원본은 최근 수정 세션 2개를 보호하며, 나머지는 마지막 활동 후 7일이 지나면 자동 정리됩니다.",
        )

    def _show_about(self) -> None:
        QMessageBox.information(
            self,
            "ImageDiary 정보",
            "ImageDiary v0.3 개발 중\n"
            "빌드 날짜: 2026-08-26\n"
            "실행 경로: 프로그램 설치 위치\n\n"
            "Python, PySide6, mss, Pillow 기반",
        )

    def _cleanup_data(self) -> None:
        internal_root = self._settings.internal_storage_root
        candidates = find_cleanup_candidates(internal_root)
        if not candidates:
            QMessageBox.information(self, "데이터 정리", "정리할 세션 폴더가 없습니다.")
            return

        confirmation = QMessageBox(self)
        confirmation.setIcon(QMessageBox.Icon.Warning)
        confirmation.setWindowTitle("데이터 정리 확인")
        confirmation.setText("데이터를 정리하시겠습니까?")
        confirmation.setInformativeText(
            "내부 원본에서 가장 최근 세션 2개는 남기고, 그보다 오래된 "
            "세션 폴더를 휴지통으로 이동합니다.\n\n"
            "설정한 저장 경로의 파일은 변경하거나 삭제하지 않습니다. "
            "휴지통으로 이동한 내부 원본은 복구하거나 영구 삭제할 수 있습니다."
        )
        cleanup = confirmation.addButton(
            "데이터 정리", QMessageBox.ButtonRole.DestructiveRole
        )
        confirmation.addButton("취소", QMessageBox.ButtonRole.RejectRole)
        confirmation.setDefaultButton(cleanup)
        confirmation.exec()
        if confirmation.clickedButton() is not cleanup:
            return

        try:
            moved = move_old_sessions_to_trash(internal_root)
        except OSError as error:
            QMessageBox.critical(self, "데이터 정리 실패", str(error))
            return
        QMessageBox.information(
            self,
            "데이터 정리 완료",
            f"{len(moved)}개 세션 폴더를 휴지통으로 이동했습니다.",
        )
