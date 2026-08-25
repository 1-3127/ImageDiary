"""세션 디렉터리 및 결과 파일 경로 생성을 담당한다."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class SessionStorage:
    def __init__(self, storage_root: Path) -> None:
        self._storage_root = storage_root

    def create_session_directory(self, started_at: datetime) -> Path:
        """세션 폴더를 만들고 같은 분에 재시작하면 순번 접미사를 붙인다."""

        day_directory = self._storage_root / started_at.strftime("%Y-%m-%d")
        base_name = started_at.strftime("%H%M")
        sequence = 1

        while True:
            folder_name = base_name if sequence == 1 else f"{base_name}-{sequence:02d}"
            candidate = day_directory / folder_name
            try:
                candidate.mkdir(parents=True, exist_ok=False)
                return candidate
            except FileExistsError:
                sequence += 1

    @staticmethod
    def gif_output_path(
        session_directory: Path,
        started_at: datetime,
        finished_at: datetime,
    ) -> Path:
        filename = f"{started_at:%Y%m%d_%H%M}-{finished_at:%H%M}.gif"
        return session_directory / filename
