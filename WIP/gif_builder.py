"""저장된 스크린샷을 파일명순으로 하나의 Animated GIF로 만든다."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


class GifBuilder:
    def build(
        self,
        screenshots_directory: Path,
        output_path: Path,
        frame_duration_ms: int,
        loop: int,
    ) -> int:
        image_paths = sorted(screenshots_directory.glob("*.png"))
        if not image_paths:
            raise ValueError("No screenshots are available for GIF generation.")

        frames: list[Image.Image] = []
        try:
            for image_path in image_paths:
                with Image.open(image_path) as source:
                    frames.append(source.convert("RGB"))

            first_frame, remaining_frames = frames[0], frames[1:]
            first_frame.save(
                output_path,
                format="GIF",
                save_all=True,
                append_images=remaining_frames,
                duration=frame_duration_ms,
                loop=loop,
            )
        finally:
            for frame in frames:
                frame.close()

        if not output_path.is_file():
            raise OSError(f"GIF was not saved: {output_path}")
        return len(image_paths)
