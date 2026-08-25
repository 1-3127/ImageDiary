from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from storage import SessionStorage


class SessionStorageTests(TestCase):
    def test_same_minute_sessions_receive_unique_directories(self) -> None:
        started_at = datetime(2026, 8, 25, 19, 7)
        with TemporaryDirectory() as temporary_directory:
            storage = SessionStorage(Path(temporary_directory))
            first = storage.create_session_directory(started_at)
            second = storage.create_session_directory(started_at)

            self.assertEqual(first.name, "260825")
            self.assertEqual(second.name, "260825-02")
            self.assertTrue(first.is_dir())
            self.assertTrue(second.is_dir())

    def test_existing_export_folder_reserves_session_name(self) -> None:
        started_at = datetime(2026, 8, 25, 19, 7)
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            internal_root = root / "internal"
            export_root = root / "export"
            (export_root / "260825").mkdir(parents=True)

            session = SessionStorage(internal_root).create_session_directory(
                started_at,
                (export_root,),
            )

            self.assertEqual(session.name, "260825-02")

    def test_gif_output_name_contains_session_times(self) -> None:
        started_at = datetime(2026, 8, 25, 19, 7)
        finished_at = datetime(2026, 8, 25, 22, 15)
        output = SessionStorage.gif_output_path(Path("session"), started_at, finished_at)
        self.assertEqual(output.name, "Diary_1907-2215.gif")
