"""ImageDiary v0.1의 변경 가능한 기본값과 저장 경로를 정의한다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    """앱 전체 기본 설정. 향후 영구 사용자 설정으로 확장한다."""

    storage_root: Path
    capture_format: str = "png"
    gif_frame_duration_ms: int = 500
    gif_loop: int = 0
    open_output_on_finish: bool = True


def default_storage_root() -> Path:
    """Pictures/WorkDiary를 우선 사용하고, 없으면 홈 폴더를 사용한다."""

    pictures = Path.home() / "Pictures"
    base_directory = pictures if pictures.exists() else Path.home()
    return base_directory / "WorkDiary"


DEFAULT_SETTINGS = AppSettings(storage_root=default_storage_root())
