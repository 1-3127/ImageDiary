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


def session_created_timestamp(session_directory: Path) -> float:
    """세션 폴더명에 기록한 생성 날짜를 자동 정리 기준으로 사용한다."""
    match = SESSION_DIRECTORY_PATTERN.fullmatch(session_directory.name)
    if match is None:
        return session_directory.stat().st_ctime
    return datetime.strptime(match.group("date"), "%y%m%d").timestamp()


def cleanup_expired_sessions(
    internal_root: Path,
    retention_days: int,
    now: datetime | None = None,
    keep_count: int = 2,
    days_enabled: bool = True,
    count_enabled: bool = False,
    size_enabled: bool = False,
    max_size_mb: int = 1024,
) -> list[Path]:
    """복수 조건(개수·용량·날짜)의 OR 정책으로 내부 세션을 정리한다."""

    if not internal_root.is_dir():
        return []
    if days_enabled and retention_days < 1:
        return []
    if count_enabled and keep_count < 1:
        return []
    if size_enabled and max_size_mb < 1:
        return []

    now = now or datetime.now()
    cutoff_timestamp = (now - timedelta(days=retention_days)).timestamp() if days_enabled else None
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

    protected = set(sessions[:keep_count]) if not count_enabled and not size_enabled else set()
    total_size = sum(session_size_bytes(session) for session in sessions)
    size_candidates: set[Path] = set()
    if size_enabled:
        limit = max_size_mb * 1024 * 1024
        for candidate in reversed(sessions):
            if total_size <= limit:
                break
            size_candidates.add(candidate)
            total_size -= session_size_bytes(candidate)

    for index, candidate in enumerate(sessions):
        if candidate in protected:
            continue
        expired = cutoff_timestamp is not None and session_last_modified_ns(candidate) / 1_000_000_000 <= cutoff_timestamp
        over_count = count_enabled and index >= keep_count
        over_size = candidate in size_candidates
        if not (expired or over_count or over_size):
            continue

        candidate_resolved = candidate.resolve()
        if candidate_resolved.parent != root_resolved:
            continue
        shutil.rmtree(candidate)
        removed.append(candidate)

    return removed


def session_size_bytes(session_directory: Path) -> int:
    total = 0
    for path in session_directory.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            total += path.stat().st_size
        except FileNotFoundError:
            continue
    return total
