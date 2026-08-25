"""최신 내부 세션의 비정상 종료 여부와 복구 시작 시각을 판정한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from gif_builder import SUPPORTED_IMAGE_SUFFIXES
from retention import SESSION_DIRECTORY_PATTERN


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

    latest = max(sessions, key=lambda path: (path.stat().st_mtime_ns, path.name))
    screenshots = latest / "Screenshot"
    if not screenshots.is_dir() or any(latest.glob("Diary_*.gif")):
        return None

    image_paths = tuple(
        sorted(
            path
            for path in screenshots.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
        )
    )
    if not image_paths:
        return None

    started_at = infer_session_start(latest, image_paths)
    return RecoveryCandidate(latest, screenshots, image_paths, started_at)


def infer_session_start(session_directory: Path, image_paths: tuple[Path, ...]) -> datetime:
    """YYMMDD 세션명과 최초 HHMM 이미지명으로 복구 시작 시각을 추론한다."""

    date_text = session_directory.name[:6]
    time_text = image_paths[0].stem[:4]
    try:
        return datetime.strptime(date_text + time_text, "%y%m%d%H%M")
    except ValueError:
        return datetime.fromtimestamp(session_directory.stat().st_mtime)
