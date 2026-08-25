"""ImageDiary 설정 모델과 기본 경로를 정의한다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


INTERNAL_STORAGE_ROOT = Path(r"C:\temp\workdiary")
SUPPORTED_CAPTURE_FORMATS = ("png", "webp", "jpg")


def default_export_root() -> Path:
    """Pictures/WorkDiary를 우선 사용하고, 없으면 홈 폴더를 사용한다."""

    pictures = Path.home() / "Pictures"
    base_directory = pictures if pictures.exists() else Path.home()
    return base_directory / "WorkDiary"


@dataclass(frozen=True)
class AppSettings:
    """세션 시작 시 복사하여 사용하는 영구 앱 설정."""

    screenshot_export_root: Path
    gif_export_root: Path
    capture_format: str = "png"
    image_quality: int = 85
    run_at_login: bool = False
    always_on_top: bool = False
    internal_retention_days: int = 7
    gif_frame_duration_ms: int = 500
    gif_loop: int = 0
    open_output_on_finish: bool = True
    internal_storage_root: Path = INTERNAL_STORAGE_ROOT

    def __post_init__(self) -> None:
        if self.capture_format not in SUPPORTED_CAPTURE_FORMATS:
            raise ValueError(f"Unsupported capture format: {self.capture_format}")
        if not 1 <= self.image_quality <= 100:
            raise ValueError("image_quality must be between 1 and 100")
        if self.internal_retention_days < 1:
            raise ValueError("internal_retention_days must be at least 1")

    @property
    def storage_root(self) -> Path:
        """내부 원본 저장소를 사용하는 기존 호출부 호환 속성."""

        return self.internal_storage_root


def default_settings() -> AppSettings:
    export_root = default_export_root()
    return AppSettings(
        screenshot_export_root=export_root,
        gif_export_root=export_root,
    )


DEFAULT_SETTINGS = default_settings()
