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
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from settings import AppSettings, SUPPORTED_CAPTURE_FORMATS


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

        self._screenshot_path = QLineEdit(str(self._settings.screenshot_export_root), self)
        self._gif_path = QLineEdit(str(self._settings.gif_export_root), self)
        form.addRow("스크린샷 저장 경로:", self._path_row(self._screenshot_path, "스크린샷"))
        form.addRow("GIF 저장 경로:", self._path_row(self._gif_path, "GIF"))

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
        screenshot_path = self._screenshot_path.text().strip()
        gif_path = self._gif_path.text().strip()
        if not screenshot_path or not gif_path:
            return

        updated = replace(
            self._settings,
            screenshot_export_root=Path(screenshot_path),
            gif_export_root=Path(gif_path),
            capture_format=self._format.currentText(),
            image_quality=self._quality.value(),
            run_at_login=self._run_at_login.isChecked(),
        )
        self.settings_saved.emit(updated)
        self.accept()
