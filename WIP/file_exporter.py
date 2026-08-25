"""내부 원본을 사용자 지정 경로에 복사한다."""

from __future__ import annotations

import shutil
from pathlib import Path


class FileExportError(RuntimeError):
    """사용자 경로로 복사하지 못했음을 나타낸다."""


class FileExporter:
    @staticmethod
    def copy_screenshot(source: Path, export_root: Path, session_name: str) -> Path:
        target_directory = export_root / session_name / "Screenshot"
        return FileExporter._copy(source, target_directory / source.name)

    @staticmethod
    def copy_gif(source: Path, export_root: Path, session_name: str) -> Path:
        target_directory = export_root / session_name
        return FileExporter._copy(source, target_directory / source.name)

    @staticmethod
    def _copy(source: Path, target: Path) -> Path:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.resolve() == target.resolve():
                return source
            shutil.copy2(source, target)
        except OSError as error:
            raise FileExportError(f"파일 복사 실패: {target}: {error}") from error
        return target
