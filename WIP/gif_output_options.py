"""GIF 출력 한 건에만 적용되는 옵션을 정의한다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GifOutputOptions:
    """원본 Screenshot을 바꾸지 않는 GIF 및 외부 복사 옵션."""

    filename: str
    gif_export_root: Path | None = None
    export_images: bool = True
    images_with_gif: bool = True
    image_export_root: Path | None = None
    blur_enabled: bool = False
    blur_strength: int = 2
    crop_enabled: bool = False
    hide_top: bool = False
    hide_bottom: bool = False
    crop_top_px: int = 0
    crop_bottom_px: int = 0
    watermark_enabled: bool = False
    watermark_text: str = "ImageDiary"
    watermark_opacity_level: int = 2
    watermark_size: int = 2
    timecode_enabled: bool = False
    timecode_show_date: bool = True
    timecode_background_level: int = 2
    timecode_horizontal: str = "left"
    timecode_vertical: str = "upper_middle"
    playback_speed: int = 2

    def __post_init__(self) -> None:
        filename = Path(self.filename).name
        if not filename or filename in {".", ".."}:
            raise ValueError("GIF 파일 이름을 입력하세요.")
        if Path(filename).suffix.lower() != ".gif":
            filename = f"{filename}.gif"
        if self.crop_top_px < 0 or self.crop_bottom_px < 0:
            raise ValueError("크롭 값은 0 이상이어야 합니다.")
        if self.blur_strength not in {1, 2, 3}:
            raise ValueError("블러 강도는 약, 중, 강 중 하나여야 합니다.")
        if self.watermark_opacity_level not in {1, 2, 3}:
            raise ValueError("워터마크 투명도는 약, 중, 강 중 하나여야 합니다.")
        if self.watermark_size not in {1, 2, 3}:
            raise ValueError("워터마크 크기는 작게, 중간, 크게 중 하나여야 합니다.")
        if self.timecode_background_level not in {1, 2, 3}:
            raise ValueError("타임코드 배경 선명도는 약, 중, 강 중 하나여야 합니다.")
        if self.timecode_horizontal not in {"left", "center", "right"}:
            raise ValueError("타임코드 가로 위치가 올바르지 않습니다.")
        if self.timecode_vertical not in {"top", "upper_middle", "middle", "lower_middle", "bottom"}:
            raise ValueError("타임코드 세로 위치가 올바르지 않습니다.")
        if self.playback_speed not in {1, 2, 3}:
            raise ValueError("GIF 재생 속도는 빠르게, 기본, 느리게 중 하나여야 합니다.")
        object.__setattr__(self, "filename", filename)
