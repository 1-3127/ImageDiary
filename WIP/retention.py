"""내부 원본 저장소에서 보존기간이 지난 세션을 안전하게 정리한다."""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path


SESSION_DIRECTORY_PATTERN = re.compile(r"^(?P<date>\d{6})(?:-\d{2})?$")


def session_last_modified_ns(session_directory: Path) -> int:
    """세션 폴더와 내부 파일을 포함한 가장 최근 수정 시각을 반환한다."""

    latest = session_directory.stat().st_mtime_ns
    for path in session_directory.rglob("*"):
        if path.is_symlink():
            continue
        try:
            latest = max(latest, path.stat().st_mtime_ns)
        except FileNotFoundError:
            continue
    return latest


def cleanup_expired_sessions(
    internal_root: Path,
    retention_days: int,
    now: datetime | None = None,
    keep_count: int = 2,
) -> list[Path]:
    """최근 수정 세션을 보호하고 활동이 보존기간 이상 지난 세션만 삭제한다."""

    if retention_days < 1 or not internal_root.is_dir():
        return []

    now = now or datetime.now()
    cutoff_timestamp = (now - timedelta(days=retention_days)).timestamp()
    root_resolved = internal_root.resolve()
    removed: list[Path] = []
    sessions = [
        candidate
        for candidate in internal_root.iterdir()
        if SESSION_DIRECTORY_PATTERN.fullmatch(candidate.name)
        and candidate.is_dir()
        and not candidate.is_symlink()
        and not (
            hasattr(candidate, "is_junction") and candidate.is_junction()
        )
    ]
    sessions.sort(
        key=lambda path: (session_last_modified_ns(path), path.name),
        reverse=True,
    )

    for candidate in sessions[max(0, keep_count):]:
        if session_last_modified_ns(candidate) / 1_000_000_000 > cutoff_timestamp:
            continue

        candidate_resolved = candidate.resolve()
        if candidate_resolved.parent != root_resolved:
            continue
        shutil.rmtree(candidate)
        removed.append(candidate)

    return removed
