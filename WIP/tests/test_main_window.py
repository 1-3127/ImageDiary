import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from app import MainWindow
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
