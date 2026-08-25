"""사용자 저장 경로의 오래된 세션을 휴지통으로 이동한다."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from send2trash import send2trash

from retention import SESSION_DIRECTORY_PATTERN


def find_cleanup_candidates(export_root: Path, keep_count: int = 2) -> list[Path]:
    """최신 keep_count개를 제외한 사용자 세션 폴더를 반환한다."""

    if not export_root.is_dir():
        return []
    sessions = [
        path
        for path in export_root.iterdir()
        if path.is_dir()
        and not path.is_symlink()
        and not (hasattr(path, "is_junction") and path.is_junction())
        and SESSION_DIRECTORY_PATTERN.fullmatch(path.name)
    ]
    sessions.sort(key=lambda path: (path.stat().st_mtime_ns, path.name), reverse=True)
    return sessions[keep_count:]


def move_old_sessions_to_trash(
    export_root: Path,
    keep_count: int = 2,
    trash: Callable[[str], None] = send2trash,
) -> list[Path]:
    """정확히 export_root 바로 아래의 정리 대상만 휴지통으로 이동한다."""

    root_resolved = export_root.resolve()
    moved: list[Path] = []
    for candidate in find_cleanup_candidates(export_root, keep_count):
        if candidate.resolve().parent != root_resolved:
            continue
        trash(str(candidate))
        moved.append(candidate)
    return moved
