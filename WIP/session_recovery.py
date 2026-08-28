"""최신 내부 세션의 비정상 종료 여부와 복구 시작 시각을 판정한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import ctypes
import os

from image_order import sorted_image_paths
from retention import SESSION_DIRECTORY_PATTERN, session_last_modified_ns


UNFINISHED_MARKER_NAME = ".unfin"
_FILE_ATTRIBUTE_HIDDEN = 0x02


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
    return recovery_candidate_from_directory(latest)


def find_marked_incomplete_sessions(internal_root: Path) -> tuple[RecoveryCandidate, ...]:
    """.unfin 마커가 남아 있는 미완료 세션을 최신 수정 순으로 반환한다."""

    if not internal_root.is_dir():
        return ()
    candidates = []
    for path in internal_root.iterdir():
        if not path.is_dir() or path.is_symlink() or not SESSION_DIRECTORY_PATTERN.fullmatch(path.name):
            continue
        if not (path / UNFINISHED_MARKER_NAME).is_file():
            continue
        candidate = recovery_candidate_from_directory(path)
        if candidate is not None:
            candidates.append(candidate)
    return tuple(sorted(candidates, key=lambda item: (session_last_modified_ns(item.session_directory), item.session_directory.name), reverse=True))


def find_completed_sessions_with_images(internal_root: Path) -> tuple[RecoveryCandidate, ...]:
    """GIF를 이미 만든 세션 중 내부 Screenshot 원본이 남아 있는 항목을 반환한다."""

    if not internal_root.is_dir():
        return ()
    candidates = []
    for path in internal_root.iterdir():
        if not path.is_dir() or path.is_symlink() or not SESSION_DIRECTORY_PATTERN.fullmatch(path.name):
            continue
        if not any(path.glob("Diary_*.gif")):
            continue
        screenshots = path / "Screenshot"
        image_paths = tuple(sorted_image_paths(screenshots)) if screenshots.is_dir() else ()
        if image_paths:
            candidates.append(
                RecoveryCandidate(path, screenshots, image_paths, infer_session_start(path, image_paths))
            )
    return tuple(sorted(candidates, key=lambda item: (session_last_modified_ns(item.session_directory), item.session_directory.name), reverse=True))


def recovery_candidate_from_directory(session_directory: Path) -> RecoveryCandidate | None:
    """GIF가 아직 없는 세션 디렉터리를 복구 후보로 변환한다."""

    screenshots = session_directory / "Screenshot"
    if not screenshots.is_dir() or any(session_directory.glob("Diary_*.gif")):
        return None
    image_paths = tuple(sorted_image_paths(screenshots))
    if not image_paths:
        return None
    return RecoveryCandidate(
        session_directory,
        screenshots,
        image_paths,
        infer_session_start(session_directory, image_paths),
    )


def mark_session_unfinished(session_directory: Path) -> Path:
    """사용자가 나중에 GIF 생성을 다시 시도할 수 있도록 세션에 숨김 마커를 남긴다."""

    marker = session_directory / UNFINISHED_MARKER_NAME
    marker.touch(exist_ok=True)
    if os.name == "nt":
        ctypes.windll.kernel32.SetFileAttributesW(str(marker), _FILE_ATTRIBUTE_HIDDEN)
    return marker


def clear_unfinished_marker(session_directory: Path) -> None:
    marker = session_directory / UNFINISHED_MARKER_NAME
    if marker.exists():
        marker.unlink()


def infer_session_start(session_directory: Path, image_paths: tuple[Path, ...]) -> datetime:
    """첫 이미지 수정 시각을 우선하고 세션 폴더 시각을 대체값으로 사용한다."""

    if image_paths:
        return datetime.fromtimestamp(image_paths[0].stat().st_mtime)
    return datetime.fromtimestamp(session_directory.stat().st_mtime)
