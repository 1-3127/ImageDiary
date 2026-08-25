"""세션 디렉터리 및 결과 파일 경로 생성을 담당한다."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class SessionStorage:
    def __init__(self, storage_root: Path) -> None:
        self._storage_root = storage_root

    def create_session_directory(
        self,
        started_at: datetime,
        reserved_roots: tuple[Path, ...] = (),
    ) -> Path:
        """내부 및 사용자 경로 모두에서 비어 있는 세션 폴더명을 선택한다."""

        base_name = started_at.strftime("%y%m%d")
        sequence = 1

        while True:
            folder_name = base_name if sequence == 1 else f"{base_name}-{sequence:02d}"
            candidate = self._storage_root / folder_name
            if candidate.exists() or any(
                (root / folder_name).exists() for root in reserved_roots
            ):
                sequence += 1
                continue
            try:
                candidate.mkdir(parents=True, exist_ok=False)
                return candidate
            except FileExistsError:
                sequence += 1

    @staticmethod
    def gif_output_path(
        session_directory: Path,
        first_image: Path,
        last_image: Path,
    ) -> Path:
        filename = f"Diary_{first_image.stem}-{last_image.stem}.gif"
        return session_directory / filename
