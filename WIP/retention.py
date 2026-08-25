"""내부 원본 저장소에서 보존기간이 지난 세션을 안전하게 정리한다."""

from __future__ import annotations

import re
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path


SESSION_DIRECTORY_PATTERN = re.compile(r"^(?P<date>\d{6})(?:-\d{2})?$")


def cleanup_expired_sessions(
    internal_root: Path,
    retention_days: int,
    today: date | None = None,
) -> list[Path]:
    """폴더명의 YYMMDD가 보존기간 이상 지난 내부 세션만 삭제한다."""

    if retention_days < 1 or not internal_root.is_dir():
        return []

    today = today or date.today()
    cutoff = today - timedelta(days=retention_days)
    root_resolved = internal_root.resolve()
    removed: list[Path] = []

    for candidate in internal_root.iterdir():
        match = SESSION_DIRECTORY_PATTERN.fullmatch(candidate.name)
        if not match or not candidate.is_dir() or candidate.is_symlink():
            continue
        if hasattr(candidate, "is_junction") and candidate.is_junction():
            continue

        try:
            session_date = datetime.strptime(match.group("date"), "%y%m%d").date()
        except ValueError:
            continue
        if session_date > cutoff:
            continue

        candidate_resolved = candidate.resolve()
        if candidate_resolved.parent != root_resolved:
            continue
        shutil.rmtree(candidate)
        removed.append(candidate)

    return removed
