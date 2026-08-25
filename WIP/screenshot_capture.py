"""전체 가상 화면을 캡처하여 timestamp 파일명으로 즉시 저장한다."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import mss
from PIL import Image


class ScreenshotCapture:
    def capture(self, output_directory: Path, captured_at: datetime | None = None) -> Path:
        """PNG 하나를 저장하고, 실제 생성된 절대 경로를 반환한다."""

        captured_at = captured_at or datetime.now()
        output_directory.mkdir(parents=True, exist_ok=True)
        filename = captured_at.strftime("%Y%m%d_%H%M%S.png")
        output_path = output_directory / filename

        with mss.mss() as screen_capture:
            virtual_screen = screen_capture.monitors[0]
            raw_image = screen_capture.grab(virtual_screen)
            image = Image.frombytes("RGB", raw_image.size, raw_image.rgb)
            image.save(output_path, format="PNG")

        if not output_path.is_file():
            raise OSError(f"Screenshot was not saved: {output_path}")
        return output_path
