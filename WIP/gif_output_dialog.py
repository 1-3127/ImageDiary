"""기록 종료 시 GIF 출력 옵션을 받는 대화상자."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget)

from gif_output_options import GifOutputOptions


class _Preview(QWidget):
    def __init__(self, watermark: bool, parent: QWidget) -> None:
        super().__init__(parent); self.watermark = watermark; self.text = "ImageDiary"; self.size = 2; self.opacity = 2; self.date = True; self.setFixedHeight(80)

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self); painter.fillRect(self.rect(), QColor("#4a4a4a"))
        if self.watermark:
            painter.setPen(QColor(255, 255, 255, {1: 64, 2: 112, 3: 168}[self.opacity]))
            font = QFont(); font.setPixelSize({1: 14, 2: 22, 3: 34}[self.size]); painter.setFont(font)
            painter.translate(self.width() // 2, self.height() // 2); painter.rotate(-45); painter.drawText(0, 0, self.text or "ImageDiary")
        else:
            text = "08/26 19:15" if self.date else "19:15"; font = QFont(); font.setPixelSize(16); painter.setFont(font)
            rect = painter.fontMetrics().boundingRect(text); x, y, padding = 10, self.height() // 4, 8
            painter.fillRect(x-padding, y-padding, rect.width()+padding*2, rect.height()+padding*2, QColor(0, 0, 0, 150)); painter.setPen(QColor("white")); painter.drawText(x, y+rect.height(), text)
        painter.end()


class GifOutputDialog(QDialog):
    def __init__(self, default_filename: str, default_export_root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setWindowTitle("GIF 출력 설정"); self._root = default_export_root; self._build(default_filename); self._update()

    def _build(self, filename: str) -> None:
        layout = QVBoxLayout(self)
        group = QGroupBox("저장 위치", self); form = QFormLayout(group)
        self._filename = QLineEdit(filename, group); self._gif_path, gif_widget = self._path_widget(group); self._image_path, image_widget = self._path_widget(group)
        self._same_path = QCheckBox("GIF와 같은 경로에 원본 이미지 저장", group); self._same_path.setChecked(True)
        form.addRow("GIF 이름", self._filename); form.addRow("GIF 저장 경로", gif_widget); form.addRow("이미지 저장 경로", image_widget); form.addRow(self._same_path); layout.addWidget(group)
        self._image_path_widget = image_widget

        group = QGroupBox("공유용 GIF 처리", self); form = QFormLayout(group)
        self._blur = QCheckBox("전체 화면 블러", group); self._blur_strength = self._slider(group, "약", "중", "강")
        self._top = QSpinBox(group); self._bottom = QSpinBox(group)
        for control in (self._top, self._bottom): control.setRange(0, 10000); control.setSuffix(" px")
        self._watermark = QCheckBox("반복 워터마크", group); self._watermark_text = QLineEdit("ImageDiary", group); self._watermark_opacity = self._slider(group, "약", "중", "강"); self._watermark_size = self._slider(group, "작게", "중간", "크게"); self._watermark_preview = _Preview(True, group)
        self._timecode = QCheckBox("타임코드 표시", group); self._date = QCheckBox("날짜(MM/DD) 함께 표시", group); self._date.setChecked(True); self._timecode_preview = _Preview(False, group)
        form.addRow(self._blur); form.addRow("블러 강도", self._blur_strength); form.addRow("상단 크롭", self._top); form.addRow("하단 크롭", self._bottom)
        form.addRow(self._watermark); form.addRow("워터마크 문구", self._watermark_text); form.addRow("워터마크 투명도", self._watermark_opacity); form.addRow("워터마크 크기", self._watermark_size); form.addRow("워터마크 미리보기", self._watermark_preview)
        form.addRow(self._timecode); form.addRow(self._date); form.addRow("타임코드 미리보기", self._timecode_preview); layout.addWidget(group)
        note = QLabel("후처리는 생성되는 GIF에만 적용되며 내부 원본 Screenshot은 변경하지 않습니다.", self); note.setWordWrap(True); layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok, Qt.Orientation.Horizontal, self); buttons.button(QDialogButtonBox.StandardButton.Ok).setText("GIF 생성"); buttons.accepted.connect(self._accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
        self._same_path.toggled.connect(self._update); self._blur.toggled.connect(self._update); self._watermark.toggled.connect(self._update); self._timecode.toggled.connect(self._update)
        self._watermark_text.textChanged.connect(self._refresh_previews); self._value(self._watermark_size).valueChanged.connect(self._refresh_previews); self._value(self._watermark_opacity).valueChanged.connect(self._refresh_previews); self._date.toggled.connect(self._refresh_previews); self._refresh_previews()

    def _path_widget(self, parent: QWidget) -> tuple[QLineEdit, QWidget]:
        line = QLineEdit(str(self._root), parent); button = QPushButton("찾아보기", parent); button.clicked.connect(lambda: self._browse(line)); row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0); row.addWidget(line); row.addWidget(button); box = QWidget(parent); box.setLayout(row); return line, box

    def _slider(self, parent: QWidget, left: str, middle: str, right: str) -> QWidget:
        slider = QSlider(Qt.Orientation.Horizontal, parent); slider.setRange(1, 3); slider.setValue(2); labels = QHBoxLayout(); labels.addWidget(QLabel(left)); labels.addStretch(); labels.addWidget(QLabel(middle)); labels.addStretch(); labels.addWidget(QLabel(right)); box = QWidget(parent); layout = QVBoxLayout(box); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(slider); layout.addLayout(labels); box.slider = slider  # type: ignore[attr-defined]
        return box

    @staticmethod
    def _value(widget: QWidget) -> QSlider: return widget.slider  # type: ignore[attr-defined]

    def _browse(self, line: QLineEdit) -> None:
        selected = QFileDialog.getExistingDirectory(self, "저장 경로 선택", line.text())
        if selected: line.setText(selected)

    def _update(self) -> None:
        self._image_path_widget.setEnabled(not self._same_path.isChecked()); self._blur_strength.setEnabled(self._blur.isChecked())
        enabled = self._watermark.isChecked()
        for widget in (self._watermark_text, self._watermark_opacity, self._watermark_size, self._watermark_preview): widget.setEnabled(enabled)
        self._date.setEnabled(self._timecode.isChecked()); self._timecode_preview.setEnabled(self._timecode.isChecked())

    def _refresh_previews(self) -> None:
        self._watermark_preview.text = self._watermark_text.text(); self._watermark_preview.size = self._value(self._watermark_size).value(); self._watermark_preview.opacity = self._value(self._watermark_opacity).value(); self._watermark_preview.update(); self._timecode_preview.date = self._date.isChecked(); self._timecode_preview.update()

    def _accept(self) -> None:
        try: self.options()
        except ValueError as error: QMessageBox.warning(self, "GIF 출력 설정", str(error)); return
        self.accept()

    def options(self) -> GifOutputOptions:
        if not self._gif_path.text().strip(): raise ValueError("GIF 저장 경로를 선택하세요.")
        image_text = self._image_path.text().strip()
        if not self._same_path.isChecked() and not image_text:
            raise ValueError("이미지 저장 경로를 선택하세요.")
        image_root = None if self._same_path.isChecked() else Path(image_text)
        return GifOutputOptions(filename=self._filename.text().strip(), gif_export_root=Path(self._gif_path.text().strip()), images_with_gif=self._same_path.isChecked(), image_export_root=image_root, blur_enabled=self._blur.isChecked(), blur_strength=self._value(self._blur_strength).value(), crop_top_px=self._top.value(), crop_bottom_px=self._bottom.value(), watermark_enabled=self._watermark.isChecked(), watermark_text=self._watermark_text.text(), watermark_opacity_level=self._value(self._watermark_opacity).value(), watermark_size=self._value(self._watermark_size).value(), timecode_enabled=self._timecode.isChecked(), timecode_show_date=self._date.isChecked())
