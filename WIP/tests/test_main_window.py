import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from app import MainWindow
from settings import default_settings
from settings_dialog import SettingsDialog
from settings_repository import SettingsRepository


class MainWindowTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def test_pin_toggle_keeps_visible_window_open(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            repository = SettingsRepository(
                QSettings(
                    str(Path(temporary_directory) / "settings.ini"),
                    QSettings.Format.IniFormat,
                )
            )
            window = MainWindow(repository, Mock())
            window.show()
            self.application.processEvents()

            window._pin_button.click()
            self.application.processEvents()
            self.assertTrue(window.isVisible())

            window._pin_button.click()
            self.application.processEvents()
            self.assertTrue(window.isVisible())
            window.close()

    def test_capture_overview_shows_next_number(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            repository = SettingsRepository(
                QSettings(
                    str(Path(temporary_directory) / "settings.ini"),
                    QSettings.Format.IniFormat,
                )
            )
            window = MainWindow(repository, Mock())
            window._session_status.set_capture_count(2)
            window._session_status.set_next_capture(
                datetime(2026, 8, 25, 21, 30)
            )

            self.assertEqual(
                window._session_status._capture_overview.text(),
                "2026-08-25 21:30:00 (3)",
            )
            window.close()

    def test_settings_dialog_has_unified_path_and_interval(self) -> None:
        dialog = SettingsDialog(default_settings())

        self.assertEqual(dialog._export_path.text(), str(default_settings().export_root))
        self.assertEqual(dialog._interval.count(), 3)
        self.assertEqual(dialog._interval.currentData(), 15 * 60)
        dialog.close()
