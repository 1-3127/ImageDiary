"""최신 내부 세션의 비정상 종료 여부와 복구 시작 시각을 판정한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from image_order import sorted_image_paths
from retention import SESSION_DIRECTORY_PATTERN, session_last_modified_ns


@dataclass(frozen=True)
class RecoveryCandidate:
    session_directory: Path
    screenshots_directory: Path
    image_paths: tuple[Path, ...]
    started_at: datetime


def find_latest_incomplete_session(internal_root: Path) -> RecoveryCandidate | None:
    """가장 최신 내부 폴더 하나만 검사해 미완료 세션이면 반환한다."""

    if not internal_root.is_dir():
        return None

    sessions = [
        path
        for path in internal_root.iterdir()
        if path.is_dir()
        and not path.is_symlink()
        and SESSION_DIRECTORY_PATTERN.fullmatch(path.name)
    ]
    if not sessions:
        return None

    latest = max(sessions, key=lambda path: (session_last_modified_ns(path), path.name))
    screenshots = latest / "Screenshot"
    if not screenshots.is_dir() or any(latest.glob("Diary_*.gif")):
        return None

    image_paths = tuple(sorted_image_paths(screenshots))
    if not image_paths:
        return None

    started_at = infer_session_start(latest, image_paths)
    return RecoveryCandidate(latest, screenshots, image_paths, started_at)


def infer_session_start(session_directory: Path, image_paths: tuple[Path, ...]) -> datetime:
    """첫 이미지 수정 시각을 우선하고 세션 폴더 시각을 대체값으로 사용한다."""

    if image_paths:
        return datetime.fromtimestamp(image_paths[0].stat().st_mtime)
    return datetime.fromtimestamp(session_directory.stat().st_mtime)
