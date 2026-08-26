"""GIF 출력 한 건에만 적용되는 옵션을 정의한다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


BlurRegion = tuple[int, int, int, int]


@dataclass(frozen=True)
class GifOutputOptions:
    """원본 Screenshot을 바꾸지 않는 GIF 및 외부 복사 옵션."""

    filename: str
    export_images: bool = True
    images_with_gif: bool = True
    image_export_root: Path | None = None
    blur_regions: tuple[BlurRegion, ...] = ()
    crop_top_px: int = 0
    crop_bottom_px: int = 0
    watermark_enabled: bool = False
    watermark_text: str = "ImageDiary"
    watermark_opacity: int = 96
    timecode_enabled: bool = False
    timecode_show_date: bool = True

    def __post_init__(self) -> None:
        filename = Path(self.filename).name
        if not filename or filename in {".", ".."}:
            raise ValueError("GIF 파일 이름을 입력하세요.")
        if Path(filename).suffix.lower() != ".gif":
            filename = f"{filename}.gif"
        if self.crop_top_px < 0 or self.crop_bottom_px < 0:
            raise ValueError("크롭 값은 0 이상이어야 합니다.")
        if not 0 <= self.watermark_opacity <= 255:
            raise ValueError("워터마크 투명도 범위가 올바르지 않습니다.")
        for region in self.blur_regions:
            if len(region) != 4 or region[2] <= 0 or region[3] <= 0:
                raise ValueError("블러 영역은 x, y, 너비, 높이 형식이어야 합니다.")
        object.__setattr__(self, "filename", filename)
