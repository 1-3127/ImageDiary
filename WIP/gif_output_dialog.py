"""기록 종료 시 GIF 출력 옵션을 받는 대화상자."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from gif_output_options import BlurRegion, GifOutputOptions


class GifOutputDialog(QDialog):
    def __init__(
        self,
        default_filename: str,
        default_export_root: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("GIF 출력 설정")
        self._default_export_root = default_export_root
        self._build_ui(default_filename)
        self._update_enabled_controls()

    def _build_ui(self, default_filename: str) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._filename = QLineEdit(default_filename, self)
        self._filename.setPlaceholderText("Diary_0930-1800.gif")
        form.addRow("GIF 이름", self._filename)
        layout.addLayout(form)

        privacy_group = QGroupBox("공유용 GIF 처리", self)
        privacy_form = QFormLayout(privacy_group)
        self._blur_enabled = QCheckBox("지정 영역 블러", privacy_group)
        self._blur_regions = QLineEdit(privacy_group)
        self._blur_regions.setPlaceholderText("예: 0,0,1920,80; 0,1040,1920,40")
        self._blur_regions.setToolTip("원본 화면 기준 x, y, 너비, 높이. 여러 영역은 세미콜론으로 구분합니다.")
        privacy_form.addRow(self._blur_enabled)
        privacy_form.addRow("블러 영역", self._blur_regions)

        self._crop_top = QSpinBox(privacy_group)
        self._crop_top.setRange(0, 10000)
        self._crop_top.setSuffix(" px")
        self._crop_bottom = QSpinBox(privacy_group)
        self._crop_bottom.setRange(0, 10000)
        self._crop_bottom.setSuffix(" px")
        privacy_form.addRow("상단 크롭", self._crop_top)
        privacy_form.addRow("하단 크롭", self._crop_bottom)

        self._watermark_enabled = QCheckBox("반복 워터마크", privacy_group)
        self._watermark_text = QLineEdit("ImageDiary", privacy_group)
        self._watermark_opacity = QSpinBox(privacy_group)
        self._watermark_opacity.setRange(0, 255)
        self._watermark_opacity.setValue(96)
        privacy_form.addRow(self._watermark_enabled)
        privacy_form.addRow("워터마크 문구", self._watermark_text)
        privacy_form.addRow("워터마크 투명도", self._watermark_opacity)

        self._timecode_enabled = QCheckBox("타임코드 표시", privacy_group)
        self._timecode_show_date = QCheckBox("날짜(MM/DD) 함께 표시", privacy_group)
        self._timecode_show_date.setChecked(True)
        privacy_form.addRow(self._timecode_enabled)
        privacy_form.addRow(self._timecode_show_date)
        layout.addWidget(privacy_group)

        export_group = QGroupBox("이미지 내보내기", self)
        export_form = QFormLayout(export_group)
        self._export_images = QCheckBox("GIF와 함께 원본 이미지 저장", export_group)
        self._export_images.setChecked(True)
        self._images_with_gif = QCheckBox("GIF와 같은 세션 폴더에 저장", export_group)
        self._images_with_gif.setChecked(True)
        self._image_export_path = QLineEdit(
            str(self._default_export_root), export_group
        )
        browse_button = QPushButton("찾아보기", export_group)
        browse_button.clicked.connect(self._browse_image_export_path)
        image_path_layout = QHBoxLayout()
        image_path_layout.addWidget(self._image_export_path)
        image_path_layout.addWidget(browse_button)
        self._image_path_widget = QWidget(export_group)
        self._image_path_widget.setLayout(image_path_layout)
        export_form.addRow(self._export_images)
        export_form.addRow(self._images_with_gif)
        export_form.addRow("별도 이미지 저장 경로", self._image_path_widget)
        layout.addWidget(export_group)

        note = QLabel("후처리는 생성되는 GIF에만 적용되며 내부 원본 Screenshot은 변경하지 않습니다.", self)
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok,
            Qt.Orientation.Horizontal,
            self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("GIF 생성")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._blur_enabled.toggled.connect(self._update_enabled_controls)
        self._watermark_enabled.toggled.connect(self._update_enabled_controls)
        self._timecode_enabled.toggled.connect(self._update_enabled_controls)
        self._export_images.toggled.connect(self._update_enabled_controls)
        self._images_with_gif.toggled.connect(self._update_enabled_controls)

    def _update_enabled_controls(self) -> None:
        self._blur_regions.setEnabled(self._blur_enabled.isChecked())
        watermark_enabled = self._watermark_enabled.isChecked()
        self._watermark_text.setEnabled(watermark_enabled)
        self._watermark_opacity.setEnabled(watermark_enabled)
        self._timecode_show_date.setEnabled(self._timecode_enabled.isChecked())
        image_path_needed = (
            self._export_images.isChecked() and not self._images_with_gif.isChecked()
        )
        self._images_with_gif.setEnabled(self._export_images.isChecked())
        self._image_path_widget.setVisible(image_path_needed)

    def _browse_image_export_path(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "이미지 저장 경로 선택",
            self._image_export_path.text(),
        )
        if selected:
            self._image_export_path.setText(selected)

    def _accept(self) -> None:
        try:
            self.options()
        except ValueError as error:
            QMessageBox.warning(self, "GIF 출력 설정", str(error))
            return
        self.accept()

    def options(self) -> GifOutputOptions:
        image_export_root = None
        if self._export_images.isChecked() and not self._images_with_gif.isChecked():
            path_text = self._image_export_path.text().strip()
            if not path_text:
                raise ValueError("별도 이미지 저장 경로를 선택하세요.")
            image_export_root = Path(path_text)
        return GifOutputOptions(
            filename=self._filename.text().strip(),
            export_images=self._export_images.isChecked(),
            images_with_gif=self._images_with_gif.isChecked(),
            image_export_root=image_export_root,
            blur_regions=self._parse_blur_regions(),
            crop_top_px=self._crop_top.value(),
            crop_bottom_px=self._crop_bottom.value(),
            watermark_enabled=self._watermark_enabled.isChecked(),
            watermark_text=self._watermark_text.text(),
            watermark_opacity=self._watermark_opacity.value(),
            timecode_enabled=self._timecode_enabled.isChecked(),
            timecode_show_date=self._timecode_show_date.isChecked(),
        )

    def _parse_blur_regions(self) -> tuple[BlurRegion, ...]:
        if not self._blur_enabled.isChecked():
            return ()
        raw_regions = self._blur_regions.text().strip()
        if not raw_regions:
            raise ValueError("블러 영역을 입력하세요.")
        regions: list[BlurRegion] = []
        for item in raw_regions.split(";"):
            values = [value.strip() for value in item.split(",")]
            if len(values) != 4:
                raise ValueError("블러 영역은 x, y, 너비, 높이 형식입니다.")
            try:
                region = tuple(int(value) for value in values)
            except ValueError as error:
                raise ValueError("블러 영역에는 정수만 입력하세요.") from error
            regions.append(region)  # type: ignore[arg-type]
        return tuple(regions)
