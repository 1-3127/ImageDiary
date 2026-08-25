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
                export_root=Path("D:/WorkDiary"),
                capture_interval_seconds=30 * 60,
                capture_format="webp",
                image_quality=85,
                run_at_login=True,
                always_on_top=True,
                internal_retention_days=7,
                export_screenshots_on_finish=False,
            )

            repository.save(expected)

            self.assertEqual(repository.load(), expected)

    def test_migrates_removed_debug_interval_to_default(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            backend = QSettings(
                str(Path(temporary_directory) / "settings.ini"),
                QSettings.Format.IniFormat,
            )
            backend.setValue("capture/interval_seconds", 60)

            loaded = SettingsRepository(backend).load()

            self.assertEqual(loaded.capture_interval_seconds, 15 * 60)
