from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from PySide6.QtCore import QSettings

from settings import AppSettings
from settings_repository import SettingsRepository


class SettingsRepositoryTests(TestCase):
    def test_round_trip(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            backend = QSettings(
                str(Path(temporary_directory) / "settings.ini"),
                QSettings.Format.IniFormat,
            )
            repository = SettingsRepository(backend)
            expected = AppSettings(
                screenshot_export_root=Path("D:/Captures"),
                gif_export_root=Path("D:/Diaries"),
                capture_format="webp",
                image_quality=85,
                run_at_login=True,
                always_on_top=True,
                internal_retention_days=7,
            )

            repository.save(expected)

            self.assertEqual(repository.load(), expected)
