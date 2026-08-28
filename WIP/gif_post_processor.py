"""GIF 이미지에만 적용하는 공유용 후처리."""

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
        if self._options.watermark_enabled and self._options.watermark_text.strip():
            self._apply_watermark(processed)
        if self._options.crop_enabled:
            self._apply_letterbox(processed)
        if self._options.timecode_enabled:
            self._apply_timecode(processed, source_path)
        return processed

    def _apply_blur(self, frame: Image.Image) -> Image.Image:
        radius = {1: 2, 2: 16, 3: 40}[self._options.blur_strength]
        blurred = frame.filter(ImageFilter.GaussianBlur(radius=radius))
        frame.close()
        return blurred

    def _apply_letterbox(self, frame: Image.Image) -> None:
        top = 50 if self._options.hide_top else 0
        bottom = 50 if self._options.hide_bottom else 0
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
        opacity = {1: 35, 2: 125, 3: 230}[self._options.watermark_opacity_level]
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
        center_x = (frame.width - rotated.width) // 2
        center_y = (frame.height - rotated.height) // 2
        for y in range(center_y, frame.height + step_y, step_y):
            for x in range(center_x, frame.width + step_x, step_x):
                overlay.alpha_composite(rotated, (x, y))
            for x in range(center_x - step_x, -step_x, -step_x):
                overlay.alpha_composite(rotated, (x, y))
        for y in range(center_y - step_y, -step_y, -step_y):
            for x in range(center_x, frame.width + step_x, step_x):
                overlay.alpha_composite(rotated, (x, y))
            for x in range(center_x - step_x, -step_x, -step_x):
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
        font = ImageFont.load_default(size=56)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        padding = 8
        text_width = right - left
        x = (
            10
            if self._options.timecode_horizontal == "left"
            else (frame.width - text_width) // 2
            if self._options.timecode_horizontal == "center"
            else frame.width - text_width - 10
        )
        vertical_ratios = {"top": 0, "upper_middle": 0.25, "middle": 0.5, "lower_middle": 0.75, "bottom": 1}
        y = int((frame.height - (bottom - top)) * vertical_ratios[self._options.timecode_vertical])
        background_alpha = {1: 35, 2: 145, 3: 245}[self._options.timecode_background_level]
        draw.rectangle(
            (x - padding, y - padding, x + (right - left) + padding, y + (bottom - top) + padding),
            fill=(0, 0, 0, background_alpha),
        )
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
