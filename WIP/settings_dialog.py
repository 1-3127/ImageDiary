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
        self._interval.setRange(10, 30)
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

        self._export_screenshots = QCheckBox("종료 시 이미지 전체 저장하기", self)
        self._export_screenshots.setChecked(
            self._settings.export_screenshots_on_finish
        )
        self._export_screenshots.setToolTip(
            "끄면 사용자 저장 경로에는 GIF만 저장됩니다. 내부 원본은 유지됩니다."
        )
        form.addRow("", self._export_screenshots)

        note = QLabel("진행 중 변경한 설정은 다음 세션부터 적용됩니다.", self)
        note.setWordWrap(True)

        cleanup_button = QPushButton("데이터 정리", self)
        cleanup_button.setToolTip("최신 2개 세션을 제외한 폴더를 휴지통으로 이동")
        cleanup_button.clicked.connect(self._cleanup_data)

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
            capture_format=self._format.currentText(),
            image_quality=self._quality.value(),
            run_at_login=self._run_at_login.isChecked(),
            export_screenshots_on_finish=self._export_screenshots.isChecked(),
        )
        self.settings_saved.emit(updated)
        self.accept()

    def _snap_interval(self, value: int) -> None:
        snapped = min(30, max(10, round(value / 5) * 5))
        if snapped != value:
            self._interval.setValue(snapped)
            return
        self._interval_value.setText(f"{snapped}분")

    def _cleanup_data(self) -> None:
        export_root = Path(self._export_path.text().strip())
        candidates = find_cleanup_candidates(export_root)
        if not candidates:
            QMessageBox.information(self, "데이터 정리", "정리할 세션 폴더가 없습니다.")
            return

        confirmation = QMessageBox(self)
        confirmation.setIcon(QMessageBox.Icon.Warning)
        confirmation.setWindowTitle("데이터 정리 확인")
        confirmation.setText("데이터를 정리하시겠습니까?")
        confirmation.setInformativeText(
            "가장 최근 세션 2개는 남기고, 그보다 오래된 모든 세션 폴더를 "
            "휴지통으로 이동합니다.\n\n휴지통에서 복구하거나 영구 삭제할 수 있습니다."
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
            moved = move_old_sessions_to_trash(export_root)
        except OSError as error:
            QMessageBox.critical(self, "데이터 정리 실패", str(error))
            return
        QMessageBox.information(
            self,
            "데이터 정리 완료",
            f"{len(moved)}개 세션 폴더를 휴지통으로 이동했습니다.",
        )
