import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from app import MainWindow
from gif_output_dialog import GifOutputDialog
from settings import AppSettings, default_settings
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
            window._session_status._refresh_capture_overview(
                datetime(2026, 8, 25, 21, 20, 1)
            )

            self.assertEqual(
                window._session_status._capture_overview.text(),
                "3번째 캡처까지: 10m",
            )
            window.close()

    def test_settings_dialog_has_unified_path_and_interval(self) -> None:
        dialog = SettingsDialog(default_settings())

        self.assertEqual(dialog._interval.minimum(), 5)
        self.assertEqual(dialog._interval.maximum(), 30)
        self.assertEqual(dialog._interval.singleStep(), 5)
        self.assertEqual(dialog._interval.value(), 15)
        self.assertEqual(dialog._capture_target.currentData(), "all")
        self.assertFalse(dialog._retention_count_enabled.isChecked())
        self.assertFalse(dialog._retention_size_enabled.isChecked())
        self.assertTrue(dialog._retention_days_enabled.isChecked())
        dialog.close()

    def test_gif_output_dialog_defaults_to_exporting_images_with_gif(self) -> None:
        dialog = GifOutputDialog("Diary_0900-1800.gif", Path("D:/WorkDiary"))

        options = dialog.options()

        self.assertEqual(options.filename, "Diary_0900-1800.gif")
        self.assertFalse(options.export_images)
        self.assertTrue(options.images_with_gif)
        self.assertFalse(options.blur_enabled)
        self.assertEqual(options.gif_export_root, Path("D:/WorkDiary"))
        remembered = dialog._remembered_values()
        self.assertIn("filename", remembered)
        self.assertIn("gif_path", remembered)
        self.assertIn("image_path", remembered)
        dialog.close()

    def test_gif_output_preview_uses_selected_playback_speed(self) -> None:
        dialog = GifOutputDialog("Diary_0900-1800.gif", Path("D:/WorkDiary"))

        dialog._playback_group.button(1).setChecked(True)

        self.assertEqual(dialog._combined_preview.playback_speed, 1)
        self.assertFalse(hasattr(dialog._combined_preview, "_timer"))
        self.assertIn("0.25초", dialog._playback_preview_text.text())
        tabs = dialog._help_button.parent()
        self.assertIs(tabs.cornerWidget(Qt.Corner.TopRightCorner), dialog._help_button)
        dialog.close()

    def test_export_dialog_cancel_confirmation_accepts_yes(self) -> None:
        dialog = GifOutputDialog("Diary_0900-1800.gif", Path("D:/WorkDiary"))
        with patch(
            "gif_output_dialog.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            dialog.reject()
        self.assertEqual(dialog.result(), dialog.DialogCode.Rejected)
        dialog.close()

    def test_data_cleanup_targets_internal_storage_only(self) -> None:
        settings = AppSettings(
            export_root=Path("D:/UserExport"),
            internal_storage_root=Path("C:/temp/workdiary-test"),
        )
        dialog = SettingsDialog(settings)

        with (
            patch(
                "settings_dialog.find_cleanup_candidates",
                return_value=[],
            ) as find_candidates,
            patch("settings_dialog.QMessageBox.information"),
        ):
            dialog._cleanup_data()

        find_candidates.assert_called_once_with(settings.internal_storage_root)
        dialog.close()

    def test_status_is_available_for_toolbar(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            repository = SettingsRepository(
                QSettings(
                    str(Path(temporary_directory) / "settings.ini"),
                    QSettings.Format.IniFormat,
                )
            )
            window = MainWindow(repository, Mock())
            window._session_status.set_status("기록 중")
            self.assertEqual(window._session_status.status_label.text(), "상태: 기록 중")
            window.close()
