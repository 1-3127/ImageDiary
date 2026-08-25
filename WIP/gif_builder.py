"""저장된 스크린샷을 파일명순으로 하나의 Animated GIF로 만든다."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PIL import Image


SUPPORTED_IMAGE_SUFFIXES = {".png", ".webp", ".jpg", ".jpeg"}


class GifBuilder:
    def build(
        self,
        screenshots_directory: Path,
        output_path: Path,
        frame_duration_ms: int,
        loop: int,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> int:
        image_paths = sorted(
            path
            for path in screenshots_directory.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
        )
        if not image_paths:
            raise ValueError("No screenshots are available for GIF generation.")

        frames: list[Image.Image] = []
        progress_total = len(image_paths) + 1
        if progress_callback is not None:
            progress_callback(0, progress_total)
        try:
            for index, image_path in enumerate(image_paths, start=1):
                with Image.open(image_path) as source:
                    frames.append(source.convert("RGB"))
                if progress_callback is not None:
                    progress_callback(index, progress_total)

            first_frame, remaining_frames = frames[0], frames[1:]
            first_frame.save(
                output_path,
                format="GIF",
                save_all=True,
                append_images=remaining_frames,
                duration=frame_duration_ms,
                loop=loop,
            )
            if progress_callback is not None:
                progress_callback(progress_total, progress_total)
        finally:
            for frame in frames:
                frame.close()

        if not output_path.is_file():
            raise OSError(f"GIF was not saved: {output_path}")
        return len(image_paths)
