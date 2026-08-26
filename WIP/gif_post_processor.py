"""GIF 프레임에만 적용하는 공유용 후처리."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from gif_output_options import GifOutputOptions


class GifPostProcessor:
    def __init__(self, options: GifOutputOptions) -> None:
        self._options = options

    def process(self, frame: Image.Image, source_path: Path) -> Image.Image:
        processed = frame.convert("RGB")
        self._apply_blur(processed)
        processed = self._crop(processed)
        if self._options.watermark_enabled and self._options.watermark_text.strip():
            self._apply_watermark(processed)
        if self._options.timecode_enabled:
            self._apply_timecode(processed, source_path)
        return processed

    def _apply_blur(self, frame: Image.Image) -> None:
        for x, y, width, height in self._options.blur_regions:
            left = max(0, x)
            top = max(0, y)
            right = min(frame.width, x + width)
            bottom = min(frame.height, y + height)
            if right <= left or bottom <= top:
                continue
            box = (left, top, right, bottom)
            region = frame.crop(box).filter(ImageFilter.GaussianBlur(radius=12))
            frame.paste(region, box)
            region.close()

    def _crop(self, frame: Image.Image) -> Image.Image:
        top = self._options.crop_top_px
        bottom = self._options.crop_bottom_px
        if top + bottom >= frame.height:
            frame.close()
            raise ValueError("상단과 하단 크롭 합계가 이미지 높이보다 작아야 합니다.")
        if top == 0 and bottom == 0:
            return frame
        cropped = frame.crop((0, top, frame.width, frame.height - bottom))
        frame.close()
        return cropped

    def _apply_watermark(self, frame: Image.Image) -> None:
        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        text = self._options.watermark_text.strip()
        step_x = max(180, len(text) * 12)
        step_y = 100
        fill = (255, 255, 255, self._options.watermark_opacity)
        for y in range(-step_y, frame.height + step_y, step_y):
            for x in range(-step_x, frame.width + step_x, step_x):
                draw.text((x, y), text, fill=fill)
        frame.paste(overlay, (0, 0), overlay)
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
        x = max(padding, frame.width - (right - left) - padding)
        y = max(padding, frame.height - (bottom - top) - padding)
        draw.rectangle(
            (x - padding, y - padding, frame.width, frame.height),
            fill=(0, 0, 0, 150),
        )
        draw.text((x, y), text, fill=(255, 255, 255, 255))

