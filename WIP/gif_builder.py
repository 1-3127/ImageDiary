"""저장된 스크린샷을 파일명순으로 하나의 Animated GIF로 만든다."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PIL import Image

from image_order import sorted_image_paths

FrameProcessor = Callable[[Image.Image, Path], Image.Image]


class GifBuilder:
    def build(
        self,
        screenshots_directory: Path,
        output_path: Path,
        frame_duration_ms: int,
        loop: int,
        progress_callback: Callable[[int, int], None] | None = None,
        frame_processor: FrameProcessor | None = None,
    ) -> int:
        image_paths = sorted_image_paths(screenshots_directory)
        if not image_paths:
            raise ValueError("No screenshots are available for GIF generation.")

        frames: list[Image.Image] = []
        progress_total = len(image_paths) + 1
        if progress_callback is not None:
            progress_callback(0, progress_total)
        try:
            for index, image_path in enumerate(image_paths, start=1):
                with Image.open(image_path) as source:
                    frame = source.convert("RGB")
                if frame_processor is not None:
                    try:
                        frame = frame_processor(frame, image_path)
                    except Exception:
                        frame.close()
                        raise
                frames.append(frame)
                if progress_callback is not None:
                    progress_callback(index, progress_total)

            first_frame, remaining_frames = frames[0], frames[1:]
            endpoint_bonus = frame_duration_ms // 2
            durations = [frame_duration_ms] * len(frames)
            durations[0] += endpoint_bonus
            durations[-1] += endpoint_bonus
            first_frame.save(
                output_path,
                format="GIF",
                save_all=True,
                append_images=remaining_frames,
                duration=durations,
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
