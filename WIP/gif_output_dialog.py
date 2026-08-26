"""기록 종료 시 GIF 출력 옵션을 받는 대화상자."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget)

from gif_output_options import GifOutputOptions


class _Preview(QWidget):
    def __init__(self, watermark: bool, parent: QWidget) -> None:
        super().__init__(parent); self.watermark = watermark; self.text = "ImageDiary"; self.size = 2; self.opacity = 2; self.date = True; self.background = 2; self.horizontal = "left"; self.vertical = "upper_middle"; self.setFixedHeight(100 if watermark else 160)

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self); painter.fillRect(self.rect(), QColor("#4a4a4a"))
        if self.watermark:
            painter.setPen(QColor(255, 255, 255, {1: 35, 2: 125, 3: 230}[self.opacity]))
            font = QFont(); font.setPixelSize({1: 14, 2: 22, 3: 34}[self.size]); painter.setFont(font)
            painter.translate(self.width() // 2, self.height() // 2); painter.rotate(-45)
            rect = painter.fontMetrics().boundingRect(self.text or "ImageDiary")
            painter.drawText(-rect.width() // 2, rect.height() // 2, self.text or "ImageDiary")
        else:
            text = "08/26 19:15" if self.date else "19:15"; font = QFont(); font.setPixelSize(28); painter.setFont(font)
            rect = painter.fontMetrics().boundingRect(text); x = 10 if self.horizontal == "left" else self.width() - rect.width() - 10; ratios = {"top": 0, "upper_middle": .25, "middle": .5, "lower_middle": .75, "bottom": 1}; y, padding = int((self.height() - rect.height()) * ratios[self.vertical]), 8
            painter.fillRect(x-padding, y-padding, rect.width()+padding*2, rect.height()+padding*2, QColor(0, 0, 0, {1: 35, 2: 145, 3: 245}[self.background])); painter.setPen(QColor("white")); painter.drawText(x, y+rect.height(), text)
        painter.end()


class _BlurPreview(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent); self.strength = 2; self.setFixedHeight(80)

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self); painter.fillRect(self.rect(), QColor("#4a4a4a"))
        font = QFont(); font.setPixelSize(26); painter.setFont(font)
        opacity, radius = {1: (90, 0), 2: (40, 4), 3: (18, 10)}[self.strength]
        painter.setPen(QColor(255, 255, 255, opacity))
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1): painter.drawText(18 + x, 48 + y, "ImageDiary")
        painter.setPen(QColor("white")); painter.drawText(18, 48, "ImageDiary"); painter.end()


class _MaskPreview(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent); self.top = False; self.bottom = False; self.setFixedHeight(90)
    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self); painter.fillRect(self.rect(), QColor("#6686a4")); painter.setPen(QColor("white")); painter.drawText(12, 48, "프로그램 화면 / 작업 표시줄")
        if self.top: painter.fillRect(0, 0, self.width(), 18, QColor("black"))
        if self.bottom: painter.fillRect(0, self.height()-18, self.width(), 18, QColor("black"))
        painter.end()


class GifOutputDialog(QDialog):
    def __init__(self, default_filename: str, default_export_root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setWindowTitle("GIF 출력 설정"); self._root = default_export_root; self._preferences = QSettings("ImageDiary", "ImageDiary"); self._build(default_filename); self._load_preferences(); self._update()

    def _build(self, filename: str) -> None:
        layout = QVBoxLayout(self)
        group = QGroupBox("저장 위치", self); form = QFormLayout(group)
        self._filename = QLineEdit(filename, group); self._gif_path, gif_widget = self._path_widget(group); self._image_path, image_widget = self._path_widget(group)
        self._export_images = QCheckBox("원본 이미지 저장", group); self._export_images.setChecked(False)
        self._same_path = QCheckBox("GIF와 같은 경로에 원본 이미지 저장", group); self._same_path.setChecked(True)
        form.addRow("GIF 이름", self._filename); form.addRow("GIF 저장 경로", gif_widget); form.addRow(self._export_images); form.addRow("이미지 저장 경로", image_widget); form.addRow(self._same_path); layout.addWidget(group)
        self._image_path_widget = image_widget

        group = QGroupBox("GIF 후처리", self); form = QFormLayout(group)
        self._blur = QCheckBox("전체 화면 블러", group); self._blur_strength = self._slider(group, "약", "중", "강")
        self._blur_preview = _BlurPreview(group)
        self._hide_top = QCheckBox("상단 가리기 (50px)", group); self._hide_bottom = QCheckBox("하단 가리기 (50px)", group); self._mask_preview = _MaskPreview(group)
        self._watermark = QCheckBox("반복 워터마크", group); self._watermark_text = QLineEdit("ImageDiary", group); self._watermark_opacity = self._slider(group, "약", "중", "강"); self._watermark_size = self._slider(group, "작게", "중간", "크게"); self._watermark_preview = _Preview(True, group)
        self._timecode = QCheckBox("타임코드 표시", group); self._date = QCheckBox("날짜(MM/DD) 함께 표시", group); self._date.setChecked(True); self._timecode_background = self._slider(group, "약", "중", "강"); self._timecode_horizontal = QComboBox(group); self._timecode_horizontal.addItem("좌측", "left"); self._timecode_horizontal.addItem("우측", "right"); self._timecode_vertical = QComboBox(group)
        for label, value in (("상단", "top"), ("상중", "upper_middle"), ("중", "middle"), ("중하", "lower_middle"), ("하단", "bottom")): self._timecode_vertical.addItem(label, value)
        self._timecode_vertical.setCurrentIndex(1); self._timecode_preview = _Preview(False, group)
        form.addRow(self._blur); form.addRow("블러 강도", self._blur_strength); form.addRow("블러 미리보기", self._blur_preview); form.addRow(self._hide_top); form.addRow(self._hide_bottom); form.addRow("가리기 미리보기", self._mask_preview)
        form.addRow(self._watermark); form.addRow("워터마크 문구", self._watermark_text); form.addRow("워터마크 선명도", self._watermark_opacity); form.addRow("워터마크 크기", self._watermark_size); form.addRow("워터마크 미리보기", self._watermark_preview)
        form.addRow(self._timecode); form.addRow(self._date); form.addRow("타임코드 배경 선명도", self._timecode_background); form.addRow("타임코드 가로 위치", self._timecode_horizontal); form.addRow("타임코드 세로 위치", self._timecode_vertical); form.addRow("타임코드 미리보기", self._timecode_preview); layout.addWidget(group)
        self._remember = QCheckBox("설정 기억하기", self); layout.addWidget(self._remember)
        note = QLabel("후처리는 GIF에만 적용됩니다.", self); note.setWordWrap(True); layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok, Qt.Orientation.Horizontal, self); buttons.button(QDialogButtonBox.StandardButton.Ok).setText("GIF 생성"); buttons.accepted.connect(self._accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
        self._export_images.toggled.connect(self._update); self._same_path.toggled.connect(self._update); self._blur.toggled.connect(self._update); self._hide_top.toggled.connect(self._refresh_previews); self._hide_bottom.toggled.connect(self._refresh_previews); self._watermark.toggled.connect(self._update); self._timecode.toggled.connect(self._update)
        self._watermark_text.textChanged.connect(self._refresh_previews); self._value(self._watermark_size).valueChanged.connect(self._refresh_previews); self._value(self._watermark_opacity).valueChanged.connect(self._refresh_previews); self._value(self._blur_strength).valueChanged.connect(self._refresh_previews); self._value(self._timecode_background).valueChanged.connect(self._refresh_previews); self._date.toggled.connect(self._refresh_previews); self._timecode_horizontal.currentIndexChanged.connect(self._refresh_previews); self._timecode_vertical.currentIndexChanged.connect(self._refresh_previews); self._refresh_previews()

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
        save_images = self._export_images.isChecked(); self._same_path.setEnabled(save_images); self._image_path_widget.setEnabled(save_images and not self._same_path.isChecked()); self._blur_strength.setEnabled(self._blur.isChecked()); self._blur_preview.setEnabled(self._blur.isChecked())
        enabled = self._watermark.isChecked()
        for widget in (self._watermark_text, self._watermark_opacity, self._watermark_size, self._watermark_preview): widget.setEnabled(enabled)
        timecode_enabled = self._timecode.isChecked(); self._date.setEnabled(timecode_enabled); self._timecode_background.setEnabled(timecode_enabled); self._timecode_horizontal.setEnabled(timecode_enabled); self._timecode_vertical.setEnabled(timecode_enabled); self._timecode_preview.setEnabled(timecode_enabled)

    def _refresh_previews(self) -> None:
        self._watermark_preview.text = self._watermark_text.text(); self._watermark_preview.size = self._value(self._watermark_size).value(); self._watermark_preview.opacity = self._value(self._watermark_opacity).value(); self._watermark_preview.update(); self._blur_preview.strength = self._value(self._blur_strength).value(); self._blur_preview.update(); self._mask_preview.top = self._hide_top.isChecked(); self._mask_preview.bottom = self._hide_bottom.isChecked(); self._mask_preview.update(); self._timecode_preview.date = self._date.isChecked(); self._timecode_preview.background = self._value(self._timecode_background).value(); self._timecode_preview.horizontal = str(self._timecode_horizontal.currentData()); self._timecode_preview.vertical = str(self._timecode_vertical.currentData()); self._timecode_preview.update()

    def _accept(self) -> None:
        try: options = self.options()
        except ValueError as error: QMessageBox.warning(self, "GIF 출력 설정", str(error)); return
        if self._remember.isChecked():
            for key, value in self._remembered_values().items(): self._preferences.setValue(f"gif_output/{key}", value)
            self._preferences.sync()
        else:
            self._preferences.setValue("gif_output/remember", False)
            self._preferences.sync()
        self.accept()

    def _load_preferences(self) -> None:
        if not bool(self._preferences.value("gif_output/remember", False)):
            return
        self._remember.setChecked(True)
        self._blur.setChecked(bool(self._preferences.value("gif_output/blur", False)))
        self._value(self._blur_strength).setValue(int(self._preferences.value("gif_output/blur_strength", 2)))
        self._watermark.setChecked(bool(self._preferences.value("gif_output/watermark", False)))
        self._watermark_text.setText(str(self._preferences.value("gif_output/watermark_text", "ImageDiary")))
        self._value(self._watermark_opacity).setValue(int(self._preferences.value("gif_output/watermark_opacity", 2)))
        self._value(self._watermark_size).setValue(int(self._preferences.value("gif_output/watermark_size", 2)))
        self._timecode.setChecked(bool(self._preferences.value("gif_output/timecode", False)))
        self._date.setChecked(bool(self._preferences.value("gif_output/date", True)))
        self._value(self._timecode_background).setValue(int(self._preferences.value("gif_output/timecode_background", 2)))

    def _remembered_values(self) -> dict[str, object]:
        return {"remember": True, "blur": self._blur.isChecked(), "blur_strength": self._value(self._blur_strength).value(), "watermark": self._watermark.isChecked(), "watermark_text": self._watermark_text.text(), "watermark_opacity": self._value(self._watermark_opacity).value(), "watermark_size": self._value(self._watermark_size).value(), "timecode": self._timecode.isChecked(), "date": self._date.isChecked(), "timecode_background": self._value(self._timecode_background).value()}

    def options(self) -> GifOutputOptions:
        if not self._gif_path.text().strip(): raise ValueError("GIF 저장 경로를 선택하세요.")
        image_text = self._image_path.text().strip()
        if self._export_images.isChecked() and not self._same_path.isChecked() and not image_text:
            raise ValueError("이미지 저장 경로를 선택하세요.")
        image_root = None if self._same_path.isChecked() or not self._export_images.isChecked() else Path(image_text)
        return GifOutputOptions(filename=self._filename.text().strip(), gif_export_root=Path(self._gif_path.text().strip()), export_images=self._export_images.isChecked(), images_with_gif=self._same_path.isChecked(), image_export_root=image_root, crop_enabled=self._hide_top.isChecked() or self._hide_bottom.isChecked(), hide_top=self._hide_top.isChecked(), hide_bottom=self._hide_bottom.isChecked(), blur_enabled=self._blur.isChecked(), blur_strength=self._value(self._blur_strength).value(), watermark_enabled=self._watermark.isChecked(), watermark_text=self._watermark_text.text(), watermark_opacity_level=self._value(self._watermark_opacity).value(), watermark_size=self._value(self._watermark_size).value(), timecode_enabled=self._timecode.isChecked(), timecode_show_date=self._date.isChecked(), timecode_background_level=self._value(self._timecode_background).value(), timecode_horizontal=str(self._timecode_horizontal.currentData()), timecode_vertical=str(self._timecode_vertical.currentData()))
