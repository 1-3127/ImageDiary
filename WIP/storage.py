"""세션 디렉터리 및 결과 파일 경로 생성을 담당한다."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class SessionStorage:
    def __init__(self, storage_root: Path) -> None:
        self._storage_root = storage_root

    def create_session_directory(self, started_at: datetime) -> Path:
        """YYMMDD 폴더를 만들고 같은 날짜의 추가 세션에는 순번을 붙인다."""

        base_name = started_at.strftime("%y%m%d")
        sequence = 1

        while True:
            folder_name = base_name if sequence == 1 else f"{base_name}-{sequence:02d}"
            candidate = self._storage_root / folder_name
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
        filename = f"Diary_{started_at:%H%M}-{finished_at:%H%M}.gif"
        return session_directory / filename
