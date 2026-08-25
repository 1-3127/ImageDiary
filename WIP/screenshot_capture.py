"""전체 가상 화면을 캡처하여 timestamp 파일명으로 즉시 저장한다."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import mss
from mss.exception import ScreenShotError
from PIL import Image

class ScreenshotCaptureError(RuntimeError):
    """화면 캡처 또는 이미지 저장 실패를 호출자에게 일관되게 전달한다."""


class ScreenshotCapture:
    def capture(
        self,
        output_directory: Path,
        captured_at: datetime | None = None,
        image_format: str = "png",
        image_quality: int = 85,
    ) -> Path:
        """선택한 포맷으로 한 장을 저장하고 실제 절대 경로를 반환한다."""

        captured_at = captured_at or datetime.now()
        output_directory.mkdir(parents=True, exist_ok=True)
        normalized_format = image_format.lower()
        if normalized_format not in {"png", "webp", "jpg"}:
            raise ScreenshotCaptureError(f"지원하지 않는 이미지 포맷: {image_format}")
        output_path = output_directory / captured_at.strftime(f"%H%M.{normalized_format}")
        if output_path.exists():
            raise ScreenshotCaptureError(
                f"같은 분의 스크린샷이 이미 존재합니다: {output_path.name}"
            )

        try:
            with mss.mss() as screen_capture:
                virtual_screen = screen_capture.monitors[0]
                raw_image = screen_capture.grab(virtual_screen)
                image = Image.frombytes("RGB", raw_image.size, raw_image.rgb)
                save_options: dict[str, object] = {}
                pillow_format = normalized_format.upper()
                if normalized_format == "jpg":
                    pillow_format = "JPEG"
                    save_options = {"quality": image_quality, "optimize": True}
                elif normalized_format == "webp":
                    save_options = {"quality": image_quality}
                image.save(output_path, format=pillow_format, **save_options)
        except (OSError, ScreenShotError) as error:
            raise ScreenshotCaptureError(f"화면 캡처 실패: {error}") from error

        if not output_path.is_file():
            raise ScreenshotCaptureError(f"스크린샷이 저장되지 않았습니다: {output_path}")
        return output_path
