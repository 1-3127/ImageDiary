"""GIF 프레임에만 적용하는 공유용 후처리."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from gif_output_options import GifOutputOptions


class GifPostProcessor:
    def __init__(self, options: GifOutputOptions) -> None:
        self._options = options

    def process(self, frame: Image.Image, source_path: Path) -> Image.Image:
        processed = frame.convert("RGB")
        if self._options.blur_enabled:
            processed = self._apply_blur(processed)
        if self._options.crop_enabled:
            self._apply_letterbox(processed)
        if self._options.watermark_enabled and self._options.watermark_text.strip():
            self._apply_watermark(processed)
        if self._options.timecode_enabled:
            self._apply_timecode(processed, source_path)
        return processed

    def _apply_blur(self, frame: Image.Image) -> Image.Image:
        radius = {1: 6, 2: 14, 3: 24}[self._options.blur_strength]
        blurred = frame.filter(ImageFilter.GaussianBlur(radius=radius))
        frame.close()
        return blurred

    def _apply_letterbox(self, frame: Image.Image) -> None:
        top = self._options.crop_top_px
        bottom = self._options.crop_bottom_px
        if top + bottom >= frame.height:
            raise ValueError("상단과 하단 마스킹 합계가 이미지 높이보다 작아야 합니다.")
        draw = ImageDraw.Draw(frame)
        if top:
            draw.rectangle((0, 0, frame.width, top), fill="black")
        if bottom:
            draw.rectangle((0, frame.height - bottom, frame.width, frame.height), fill="black")

    def _apply_watermark(self, frame: Image.Image) -> None:
        text = self._options.watermark_text.strip()
        font_size = {1: 16, 2: 26, 3: 40}[self._options.watermark_size]
        opacity = {1: 64, 2: 112, 3: 168}[self._options.watermark_opacity_level]
        font = ImageFont.load_default(size=font_size)
        bounds = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox(
            (0, 0), text, font=font
        )
        tile = Image.new(
            "RGBA",
            (bounds[2] - bounds[0] + 24, bounds[3] - bounds[1] + 24),
            (0, 0, 0, 0),
        )
        ImageDraw.Draw(tile).text((12, 12), text, font=font, fill=(255, 255, 255, opacity))
        rotated = tile.rotate(45, expand=True)
        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        step_x = max(180, rotated.width + 80)
        step_y = max(110, rotated.height + 50)
        for y in range(-step_y, frame.height + step_y, step_y):
            for x in range(-step_x, frame.width + step_x, step_x):
                overlay.alpha_composite(rotated, (x, y))
        frame.paste(overlay, (0, 0), overlay)
        rotated.close()
        tile.close()
        overlay.close()

    def _apply_timecode(self, frame: Image.Image, source_path: Path) -> None:
        timestamp = datetime.fromtimestamp(source_path.stat().st_mtime)
        text = (
            timestamp.strftime("%m/%d %H:%M")
            if self._options.timecode_show_date
            else timestamp.strftime("%H:%M")
        )
        draw = ImageDraw.Draw(frame, "RGBA")
        left, top, right, bottom = draw.textbbox((0, 0), text)
        padding = 8
        x = 10
        y = max(padding, frame.height // 4)
        draw.rectangle(
            (x - padding, y - padding, x + (right - left) + padding, y + (bottom - top) + padding),
            fill=(0, 0, 0, 150),
        )
        draw.text((x, y), text, fill=(255, 255, 255, 255))
