"""내부 캡처 이미지를 수정 시각 기준으로 정렬한다."""

from __future__ import annotations

from pathlib import Path


SUPPORTED_IMAGE_SUFFIXES = {".png", ".webp", ".jpg", ".jpeg"}


def sorted_image_paths(screenshots_directory: Path) -> list[Path]:
    """수정 시각을 우선하고 파일명을 보조 기준으로 사용한다."""

    image_paths = [
        path
        for path in screenshots_directory.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    ]
    return sorted(
        image_paths,
        key=lambda path: (path.stat().st_mtime_ns, path.name),
    )
