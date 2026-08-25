"""ImageDiary 사용자 설정을 편집하는 대화상자."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Signal
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
        form.addRow("스크린샷 저장 경로:", self._path_row(self._export_path, "작업 일기"))

        self._interval = QComboBox(self)
        self._interval.addItem("60초 (디버그)", 60)
        self._interval.addItem("15분", 15 * 60)
        self._interval.addItem("30분", 30 * 60)
        interval_index = self._interval.findData(self._settings.capture_interval_seconds)
        self._interval.setCurrentIndex(max(0, interval_index))
        form.addRow("캡처 간격:", self._interval)

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
            capture_interval_seconds=int(self._interval.currentData()),
            capture_format=self._format.currentText(),
            image_quality=self._quality.value(),
            run_at_login=self._run_at_login.isChecked(),
        )
        self.settings_saved.emit(updated)
        self.accept()

    def _cleanup_data(self) -> None:
        export_root = Path(self._export_path.text().strip())
        candidates = find_cleanup_candidates(export_root)
        if not candidates:
            QMessageBox.information(self, "데이터 정리", "정리할 세션 폴더가 없습니다.")
            return

        answer = QMessageBox.warning(
            self,
            "데이터 정리 주의",
            "가장 최근 세션과 바로 이전 세션을 제외한 모든 세션 폴더를 정리합니다.\n\n"
            "정리된 폴더는 휴지통으로 버려집니다.",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Ok:
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
