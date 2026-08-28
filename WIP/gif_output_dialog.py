"""기록 종료 시 GIF 출력 옵션을 받는 대화상자."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSlider, QSpinBox, QTabWidget, QToolButton, QVBoxLayout, QWidget)

from gif_output_options import GifOutputOptions


class _Preview(QWidget):
    def __init__(self, watermark: bool, parent: QWidget) -> None:
        super().__init__(parent); self.watermark = watermark; self.text = "ImageDiary"; self.size = 2; self.opacity = 2; self.date = True; self.background = 2; self.horizontal = "left"; self.vertical = "upper_middle"; self.setFixedHeight(100 if watermark else 120)

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self); painter.fillRect(self.rect(), QColor("#4a4a4a"))
        if self.watermark:
            painter.setPen(QColor(255, 255, 255, {1: 35, 2: 125, 3: 230}[self.opacity]))
            font = QFont(); font.setPixelSize({1: 14, 2: 22, 3: 34}[self.size]); painter.setFont(font)
            text = self.text or "ImageDiary"; rect = painter.fontMetrics().boundingRect(text)
            step_x, step_y = max(110, rect.width() + 56), max(38, rect.height() + 24)
            for y in range(self.height() // 2, self.height() * 2, step_y):
                for x in range(self.width() // 2, self.width() * 2, step_x):
                    painter.save(); painter.translate(x, y); painter.rotate(-45); painter.drawText(-rect.width() // 2, rect.height() // 2, text); painter.restore()
                for x in range(self.width() // 2 - step_x, -self.width(), -step_x):
                    painter.save(); painter.translate(x, y); painter.rotate(-45); painter.drawText(-rect.width() // 2, rect.height() // 2, text); painter.restore()
        else:
            text = "08/26 19:15" if self.date else "19:15"; font = QFont(); font.setPixelSize(22); painter.setFont(font)
            rect = painter.fontMetrics().boundingRect(text); x = 10 if self.horizontal == "left" else self.width() // 2 - rect.width() // 2 if self.horizontal == "center" else self.width() - rect.width() - 10; ratios = {"top": 0, "upper_middle": .25, "middle": .5, "lower_middle": .75, "bottom": 1}; y, padding = int((self.height() - rect.height()) * ratios[self.vertical]), 8
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
        painter = QPainter(self); painter.fillRect(self.rect(), QColor("#272b33")); painter.fillRect(5, 5, self.width()-10, self.height()-10, QColor("#6686a4")); painter.fillRect(5, 5, self.width()-10, 12, QColor("#d7dde6")); painter.fillRect(5, self.height()-17, self.width()-10, 12, QColor("#1976d2"))
        if self.top: painter.fillRect(5, 5, self.width()-10, 18, QColor("black"))
        if self.bottom: painter.fillRect(5, self.height()-23, self.width()-10, 18, QColor("black"))
        painter.end()


class _CombinedPreview(QWidget):
    """선택한 GIF 후처리를 한 화면에 겹쳐 보여 주는 간단한 미리보기."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.blur = False; self.blur_strength = 2; self.hide_top = False; self.hide_bottom = False
        self.watermark = False; self.watermark_text = "ImageDiary"; self.watermark_opacity = 2; self.watermark_size = 2
        self.timecode = False; self.date = True; self.timecode_background = 2; self.horizontal = "left"; self.vertical = "upper_middle"
        self.playback_speed = 2
        self.setFixedHeight(150)

    def set_playback_speed(self, speed: int) -> None:
        self.playback_speed = speed

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self); painter.fillRect(self.rect(), QColor("#272b33")); area = self.rect().adjusted(8, 8, -8, -8)
        painter.fillRect(area, QColor("#6686a4")); painter.fillRect(area.x(), area.y(), area.width(), 18, QColor("#d7dde6")); painter.fillRect(area.x(), area.bottom() - 16, area.width(), 17, QColor("#1976d2"))
        font = QFont(); font.setPixelSize(24); painter.setFont(font); title = "ImageDiary"
        if self.blur:
            radius = {1: 1, 2: 3, 3: 7}[self.blur_strength]; painter.setPen(QColor(255, 255, 255, 45))
            for x in range(-radius, radius + 1):
                for y in range(-radius, radius + 1): painter.drawText(area.x() + 20 + x, area.y() + 70 + y, title)
        painter.setPen(QColor("white")); painter.drawText(area.x() + 20, area.y() + 70, title)
        if self.watermark:
            font.setPixelSize({1: 16, 2: 24, 3: 34}[self.watermark_size]); painter.setFont(font); painter.setPen(QColor(255, 255, 255, {1: 35, 2: 125, 3: 230}[self.watermark_opacity])); text = self.watermark_text or "ImageDiary"; rect = painter.fontMetrics().boundingRect(text)
            step_x, step_y = max(120, rect.width() + 58), max(40, rect.height() + 26)
            for y in range(area.center().y(), area.bottom() + area.height(), step_y):
                for x in range(area.center().x(), area.right() + area.width(), step_x):
                    painter.save(); painter.translate(x, y); painter.rotate(-45); painter.drawText(-rect.width() // 2, rect.height() // 2, text); painter.restore()
                for x in range(area.center().x() - step_x, area.left() - area.width(), -step_x):
                    painter.save(); painter.translate(x, y); painter.rotate(-45); painter.drawText(-rect.width() // 2, rect.height() // 2, text); painter.restore()
        mask_height = 18
        if self.hide_top: painter.fillRect(area.x(), area.y(), area.width(), mask_height, QColor("black"))
        if self.hide_bottom: painter.fillRect(area.x(), area.bottom() - mask_height + 1, area.width(), mask_height, QColor("black"))
        if self.timecode:
            text = "08/28 19:15" if self.date else "19:15"; font.setPixelSize(18); painter.setFont(font); rect = painter.fontMetrics().boundingRect(text); x = area.x() + 10 if self.horizontal == "left" else area.center().x() - rect.width() // 2 if self.horizontal == "center" else area.right() - rect.width() - 10; ratios = {"top": 0, "upper_middle": .25, "middle": .5, "lower_middle": .75, "bottom": 1}; y = area.y() + int((area.height() - rect.height()) * ratios[self.vertical]); painter.fillRect(x - 6, y - 5, rect.width() + 12, rect.height() + 10, QColor(0, 0, 0, {1: 35, 2: 145, 3: 245}[self.timecode_background])); painter.setPen(QColor("white")); painter.drawText(x, y + rect.height(), text)
        painter.end()


class GifOutputDialog(QDialog):
    image_only_requested = Signal(object)
    def __init__(self, default_filename: str, default_export_root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setWindowTitle("내보내기 설정"); self._root = default_export_root; self._preferences = QSettings("ImageDiary", "ImageDiary"); self._return_to_session = False; self._build(default_filename); self._load_preferences(); self._update()

    @property
    def return_to_session_requested(self) -> bool:
        return self._return_to_session

    def _build(self, filename: str) -> None:
        layout = QVBoxLayout(self); tabs = QTabWidget(self); self._help_button = QToolButton(tabs); self._help_button.setText("?"); self._help_button.setToolTip("내보내기 설정 도움말"); self._help_button.clicked.connect(self._show_export_help); tabs.setCornerWidget(self._help_button, Qt.Corner.TopRightCorner); layout.addWidget(tabs)
        storage_page = QWidget(tabs); storage_layout = QVBoxLayout(storage_page)
        group = QGroupBox("내보내기", self); form = QFormLayout(group)
        self._filename = QLineEdit(filename, group); self._gif_path, gif_widget = self._path_widget(group); self._image_path, image_widget = self._path_widget(group)
        self._export_images = QCheckBox("원본 이미지 저장", group); self._export_images.setChecked(False)
        self._same_path = QCheckBox("GIF와 같은 경로에 원본 이미지 저장", group); self._same_path.setChecked(True)
        self._playback_group = QButtonGroup(group); self._playback_group.setExclusive(True); playback_widget = QWidget(group); playback_layout = QHBoxLayout(playback_widget); playback_layout.setContentsMargins(0, 0, 0, 0)
        for identifier, label in ((1, "0.25초"), (2, "0.50초"), (3, "0.75초")):
            button = QCheckBox(label, playback_widget); self._playback_group.addButton(button, identifier); playback_layout.addWidget(button)
        self._playback_group.button(2).setChecked(True)
        form.addRow("GIF 이름", self._filename); form.addRow("GIF 내보내기 경로", gif_widget); form.addRow("1장당 할당 시간", playback_widget); form.addRow(self._export_images); form.addRow("이미지 내보내기 경로", image_widget); form.addRow(self._same_path); storage_layout.addWidget(group); storage_layout.addWidget(QLabel("GIF와 원본 이미지의 외부 내보내기 위치를 정합니다.", storage_page)); storage_layout.addStretch(); tabs.addTab(storage_page, "내보내기")
        self._image_path_widget = image_widget

        mask_page = QWidget(tabs); mask_layout = QVBoxLayout(mask_page); group = QGroupBox("블러 및 마스킹", mask_page); form = QFormLayout(group)
        self._blur = QCheckBox("전체 화면 블러", group); self._blur_strength = self._slider(group, "약", "중", "강")
        self._blur_preview = _BlurPreview(group)
        self._hide_top = QCheckBox("상단 마스킹 (50px)", group); self._hide_bottom = QCheckBox("하단 마스킹 (50px)", group); self._mask_preview = _MaskPreview(group)
        form.addRow(self._blur); form.addRow("블러 강도", self._blur_strength); form.addRow("블러 미리보기", self._blur_preview); form.addRow(self._hide_top); form.addRow(self._hide_bottom); form.addRow("마스킹 미리보기", self._mask_preview)
        mask_layout.addWidget(group); mask_layout.addWidget(QLabel("전체 블러와 상·하단 50px 마스킹을 적용합니다.", mask_page)); mask_layout.addStretch(); tabs.addTab(mask_page, "블러/마스킹")
        watermark_page = QWidget(tabs); watermark_layout = QVBoxLayout(watermark_page); group = QGroupBox("워터마크", watermark_page); form = QFormLayout(group)
        self._watermark = QCheckBox("반복 워터마크", group); self._watermark_text = QLineEdit("ImageDiary", group); self._watermark_opacity = self._slider(group, "약", "중", "강"); self._watermark_size = self._slider(group, "작게", "중간", "크게"); self._watermark_preview = _Preview(True, group)
        form.addRow(self._watermark); form.addRow("워터마크 문구", self._watermark_text); form.addRow("워터마크 선명도", self._watermark_opacity); form.addRow("워터마크 크기", self._watermark_size); form.addRow("워터마크 미리보기", self._watermark_preview); watermark_layout.addWidget(group); watermark_layout.addWidget(QLabel("반시계 45° 반복 워터마크를 설정합니다.", watermark_page)); watermark_layout.addStretch(); tabs.addTab(watermark_page, "워터마크")
        timecode_page = QWidget(tabs); timecode_layout = QVBoxLayout(timecode_page); group = QGroupBox("타임코드", timecode_page); form = QFormLayout(group)
        self._timecode = QCheckBox("타임코드 표시", group); self._date = QCheckBox("날짜(MM/DD) 함께 표시", group); self._date.setChecked(True); self._timecode_background = self._slider(group, "약", "중", "강"); self._timecode_horizontal = QComboBox(group); self._timecode_horizontal.addItem("좌측", "left"); self._timecode_horizontal.addItem("중앙", "center"); self._timecode_horizontal.addItem("우측", "right"); self._timecode_vertical = QComboBox(group)
        for label, value in (("상단", "top"), ("상중", "upper_middle"), ("중단", "middle"), ("중하", "lower_middle"), ("하단", "bottom")): self._timecode_vertical.addItem(label, value)
        self._timecode_vertical.setCurrentIndex(1); self._timecode_preview = _Preview(False, group)
        form.addRow(self._timecode); form.addRow(self._date); form.addRow("타임코드 배경 선명도", self._timecode_background); form.addRow("타임코드 가로 위치", self._timecode_horizontal); form.addRow("타임코드 세로 위치", self._timecode_vertical); form.addRow("타임코드 미리보기", self._timecode_preview); timecode_layout.addWidget(group); timecode_layout.addWidget(QLabel("각 이미지의 캡처 시각 표시 위치와 배경을 설정합니다.", timecode_page)); timecode_layout.addStretch(); tabs.addTab(timecode_page, "타임코드")
        tabs.clear(); tabs.addTab(timecode_page, "타임코드"); tabs.addTab(mask_page, "블러/마스킹"); tabs.addTab(watermark_page, "워터마크"); tabs.addTab(storage_page, "내보내기")
        self._image_only = QPushButton("GIF 없이 이미지만 내보내기", storage_page); self._image_only.setEnabled(False); self._image_only.clicked.connect(self._save_images_only); storage_layout.addWidget(self._image_only)
        storage_layout.addWidget(QLabel("통합 미리보기", storage_page)); self._combined_preview = _CombinedPreview(storage_page); storage_layout.addWidget(self._combined_preview); self._playback_preview_text = QLabel(storage_page); storage_layout.addWidget(self._playback_preview_text)
        note = QLabel("후처리는 GIF에만 적용됩니다.", self); note.setWordWrap(True); layout.addWidget(note)
        self._remember = QCheckBox("설정 기억하기", self); layout.addWidget(self._remember)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok, Qt.Orientation.Horizontal, self); buttons.button(QDialogButtonBox.StandardButton.Ok).setText("GIF 생성"); buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("취소"); buttons.accepted.connect(self._accept); buttons.rejected.connect(self.reject); self._return_button = QPushButton("세션으로 돌아가기", self); self._return_button.clicked.connect(self._return_to_recording); button_row = QHBoxLayout(); button_row.addWidget(self._return_button); button_row.addStretch(); button_row.addWidget(buttons); layout.addLayout(button_row)
        self._export_images.toggled.connect(self._update); self._same_path.toggled.connect(self._update); self._blur.toggled.connect(self._update); self._hide_top.toggled.connect(self._refresh_previews); self._hide_bottom.toggled.connect(self._refresh_previews); self._watermark.toggled.connect(self._update); self._timecode.toggled.connect(self._update); self._playback_group.idToggled.connect(lambda _identifier, checked: self._refresh_previews() if checked else None)
        self._watermark_text.textChanged.connect(self._refresh_previews); self._value(self._watermark_size).valueChanged.connect(self._refresh_previews); self._value(self._watermark_opacity).valueChanged.connect(self._refresh_previews); self._value(self._blur_strength).valueChanged.connect(self._refresh_previews); self._value(self._timecode_background).valueChanged.connect(self._refresh_previews); self._date.toggled.connect(self._refresh_previews); self._timecode_horizontal.currentIndexChanged.connect(self._refresh_previews); self._timecode_vertical.currentIndexChanged.connect(self._refresh_previews); self._refresh_previews()

    def _path_widget(self, parent: QWidget) -> tuple[QLineEdit, QWidget]:
        line = QLineEdit(str(self._root), parent); button = QPushButton("찾아보기", parent); button.clicked.connect(lambda: self._browse(line)); row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0); row.addWidget(line); row.addWidget(button); box = QWidget(parent); box.setLayout(row); return line, box

    def _slider(self, parent: QWidget, left: str, middle: str, right: str) -> QWidget:
        slider = QSlider(Qt.Orientation.Horizontal, parent); slider.setRange(1, 3); slider.setSingleStep(1); slider.setPageStep(1); slider.setValue(2); labels = QHBoxLayout(); labels.addWidget(QLabel(left)); labels.addStretch(); labels.addWidget(QLabel(middle)); labels.addStretch(); labels.addWidget(QLabel(right)); box = QWidget(parent); layout = QVBoxLayout(box); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(slider); layout.addLayout(labels); box.slider = slider  # type: ignore[attr-defined]
        return box

    @staticmethod
    def _value(widget: QWidget) -> QSlider: return widget.slider  # type: ignore[attr-defined]

    def _browse(self, line: QLineEdit) -> None:
        selected = QFileDialog.getExistingDirectory(self, "저장 경로 선택", line.text())
        if selected: line.setText(selected)

    def _update(self) -> None:
        save_images = self._export_images.isChecked(); self._image_only.setEnabled(save_images); self._same_path.setEnabled(save_images); self._image_path_widget.setEnabled(save_images and not self._same_path.isChecked()); self._blur_strength.setEnabled(self._blur.isChecked()); self._blur_preview.setEnabled(self._blur.isChecked())
        enabled = self._watermark.isChecked()
        for widget in (self._watermark_text, self._watermark_opacity, self._watermark_size, self._watermark_preview): widget.setEnabled(enabled)
        timecode_enabled = self._timecode.isChecked(); self._date.setEnabled(timecode_enabled); self._timecode_background.setEnabled(timecode_enabled); self._timecode_horizontal.setEnabled(timecode_enabled); self._timecode_vertical.setEnabled(timecode_enabled); self._timecode_preview.setEnabled(timecode_enabled); self._refresh_previews()

    def _refresh_previews(self) -> None:
        self._watermark_preview.text = self._watermark_text.text(); self._watermark_preview.size = self._value(self._watermark_size).value(); self._watermark_preview.opacity = self._value(self._watermark_opacity).value(); self._watermark_preview.update(); self._blur_preview.strength = self._value(self._blur_strength).value(); self._blur_preview.update(); self._mask_preview.top = self._hide_top.isChecked(); self._mask_preview.bottom = self._hide_bottom.isChecked(); self._mask_preview.update(); self._timecode_preview.date = self._date.isChecked(); self._timecode_preview.background = self._value(self._timecode_background).value(); self._timecode_preview.horizontal = str(self._timecode_horizontal.currentData()); self._timecode_preview.vertical = str(self._timecode_vertical.currentData()); self._timecode_preview.update(); self._combined_preview.blur = self._blur.isChecked(); self._combined_preview.blur_strength = self._value(self._blur_strength).value(); self._combined_preview.hide_top = self._hide_top.isChecked(); self._combined_preview.hide_bottom = self._hide_bottom.isChecked(); self._combined_preview.watermark = self._watermark.isChecked(); self._combined_preview.watermark_text = self._watermark_text.text(); self._combined_preview.watermark_opacity = self._value(self._watermark_opacity).value(); self._combined_preview.watermark_size = self._value(self._watermark_size).value(); self._combined_preview.timecode = self._timecode.isChecked(); self._combined_preview.date = self._date.isChecked(); self._combined_preview.timecode_background = self._value(self._timecode_background).value(); self._combined_preview.horizontal = str(self._timecode_horizontal.currentData()); self._combined_preview.vertical = str(self._timecode_vertical.currentData()); speed = self._playback_group.checkedId(); self._combined_preview.set_playback_speed(speed); self._playback_preview_text.setText({1: "1장당 할당 시간: 0.25초", 2: "1장당 할당 시간: 0.50초", 3: "1장당 할당 시간: 0.75초"}[speed]); self._combined_preview.update()

    def _accept(self) -> None:
        try: options = self.options()
        except ValueError as error: QMessageBox.warning(self, "내보내기 설정", str(error)); return
        if self._remember.isChecked():
            for key, value in self._remembered_values().items(): self._preferences.setValue(f"gif_output/{key}", value)
            self._preferences.sync()
        else:
            self._preferences.setValue("gif_output/remember", False)
            self._preferences.sync()
        self.accept()

    def _show_export_help(self) -> None:
        dialog = QMessageBox(self); dialog.setWindowTitle("내보내기 설정 도움말"); dialog.setTextFormat(Qt.TextFormat.RichText); dialog.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        dialog.setText(
            "<b>타임코드</b>: 캡처 시각의 표시 여부·위치·배경을 정합니다.<br>"
            "<b>블러/마스킹</b>: 전체 블러와 상·하단 50px 마스킹을 GIF에 적용합니다.<br>"
            "<b>워터마크</b>: 반복 워터마크 문구·선명도·크기를 정합니다.<br>"
            "<b>내보내기</b>: GIF와 원본 이미지의 내보내기 위치를 정합니다.<br><br>"
            "후처리는 GIF에만 적용되며 내부 원본은 바뀌지 않습니다.<br>"
            '<a href="https://github.com/1-3127/ImageDiary/blob/main/docs/quick_start.md">GitHub 간단 사용 설명서</a>'
        ); dialog.exec()

    def _return_to_recording(self) -> None:
        answer = QMessageBox.question(
            self,
            "기록 계속",
            "GIF 생성을 취소하고 기록을 계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._return_to_session = True
        super().reject()

    def reject(self) -> None:
        answer = QMessageBox.question(
            self,
            "내보내기 설정 취소",
            "GIF를 만들지 않고 끝내시겠습니까?\n\n추후 설정 창에서 이어갈 수 있습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            super().reject()

    def _save_images_only(self) -> None:
        answer = QMessageBox.question(self, "이미지 저장", "정말 GIF없이 이미지만 저장하시겠습니까?")
        if answer is QMessageBox.StandardButton.Yes:
            self.image_only_requested.emit(self.options())
            self.accept()

    def _load_preferences(self) -> None:
        if not bool(self._preferences.value("gif_output/remember", False)):
            return
        self._remember.setChecked(True)
        self._filename.setText(str(self._preferences.value("gif_output/filename", self._filename.text())))
        self._gif_path.setText(str(self._preferences.value("gif_output/gif_path", self._gif_path.text())))
        self._image_path.setText(str(self._preferences.value("gif_output/image_path", self._image_path.text())))
        speed = int(self._preferences.value("gif_output/playback_speed", 2))
        if self._playback_group.button(speed) is not None: self._playback_group.button(speed).setChecked(True)
        self._blur.setChecked(bool(self._preferences.value("gif_output/blur", False)))
        self._value(self._blur_strength).setValue(int(self._preferences.value("gif_output/blur_strength", 2)))
        self._watermark.setChecked(bool(self._preferences.value("gif_output/watermark", False)))
        self._watermark_text.setText(str(self._preferences.value("gif_output/watermark_text", "ImageDiary")))
        self._value(self._watermark_opacity).setValue(int(self._preferences.value("gif_output/watermark_opacity", 2)))
        self._value(self._watermark_size).setValue(int(self._preferences.value("gif_output/watermark_size", 2)))
        self._timecode.setChecked(bool(self._preferences.value("gif_output/timecode", False)))
        self._date.setChecked(bool(self._preferences.value("gif_output/date", True)))
        self._value(self._timecode_background).setValue(int(self._preferences.value("gif_output/timecode_background", 2)))
        self._export_images.setChecked(bool(self._preferences.value("gif_output/export_images", False)))
        self._same_path.setChecked(bool(self._preferences.value("gif_output/same_path", True)))
        self._hide_top.setChecked(bool(self._preferences.value("gif_output/hide_top", False)))
        self._hide_bottom.setChecked(bool(self._preferences.value("gif_output/hide_bottom", False)))
        self._timecode_horizontal.setCurrentIndex(max(0, self._timecode_horizontal.findData(self._preferences.value("gif_output/timecode_horizontal", "left"))))
        self._timecode_vertical.setCurrentIndex(max(0, self._timecode_vertical.findData(self._preferences.value("gif_output/timecode_vertical", "upper_middle"))))

    def _remembered_values(self) -> dict[str, object]:
        return {"remember": True, "filename": self._filename.text(), "gif_path": self._gif_path.text(), "image_path": self._image_path.text(), "playback_speed": self._playback_group.checkedId(), "blur": self._blur.isChecked(), "blur_strength": self._value(self._blur_strength).value(), "export_images": self._export_images.isChecked(), "same_path": self._same_path.isChecked(), "hide_top": self._hide_top.isChecked(), "hide_bottom": self._hide_bottom.isChecked(), "watermark": self._watermark.isChecked(), "watermark_text": self._watermark_text.text(), "watermark_opacity": self._value(self._watermark_opacity).value(), "watermark_size": self._value(self._watermark_size).value(), "timecode": self._timecode.isChecked(), "date": self._date.isChecked(), "timecode_background": self._value(self._timecode_background).value(), "timecode_horizontal": self._timecode_horizontal.currentData(), "timecode_vertical": self._timecode_vertical.currentData()}

    def options(self) -> GifOutputOptions:
        if not self._gif_path.text().strip(): raise ValueError("GIF 내보내기 경로를 선택하세요.")
        image_text = self._image_path.text().strip()
        if self._export_images.isChecked() and not self._same_path.isChecked() and not image_text:
            raise ValueError("이미지 내보내기 경로를 선택하세요.")
        image_root = None if self._same_path.isChecked() or not self._export_images.isChecked() else Path(image_text)
        return GifOutputOptions(filename=self._filename.text().strip(), gif_export_root=Path(self._gif_path.text().strip(),), export_images=self._export_images.isChecked(), images_with_gif=self._same_path.isChecked(), image_export_root=image_root, playback_speed=self._playback_group.checkedId(), crop_enabled=self._hide_top.isChecked() or self._hide_bottom.isChecked(), hide_top=self._hide_top.isChecked(), hide_bottom=self._hide_bottom.isChecked(), blur_enabled=self._blur.isChecked(), blur_strength=self._value(self._blur_strength).value(), watermark_enabled=self._watermark.isChecked(), watermark_text=self._watermark_text.text(), watermark_opacity_level=self._value(self._watermark_opacity).value(), watermark_size=self._value(self._watermark_size).value(), timecode_enabled=self._timecode.isChecked(), timecode_show_date=self._date.isChecked(), timecode_background_level=self._value(self._timecode_background).value(), timecode_horizontal=str(self._timecode_horizontal.currentData()), timecode_vertical=str(self._timecode_vertical.currentData()))
