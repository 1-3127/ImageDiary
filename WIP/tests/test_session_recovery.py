import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from session_recovery import find_latest_incomplete_session


class SessionRecoveryTests(TestCase):
    def test_returns_only_latest_incomplete_session(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            older = root / "260824"
            latest = root / "260825"
            for session in (older, latest):
                screenshot_directory = session / "Screenshot"
                screenshot_directory.mkdir(parents=True)
                (screenshot_directory / "2030.webp").write_bytes(b"image")
            expected_start = datetime(2026, 8, 25, 20, 30)
            latest_image = latest / "Screenshot" / "2030.webp"
            os.utime(latest_image, (expected_start.timestamp(), expected_start.timestamp()))
            os.utime(older, (1, 1))
            os.utime(latest, (2, 2))

            candidate = find_latest_incomplete_session(root)

            self.assertIsNotNone(candidate)
            assert candidate is not None
            self.assertEqual(candidate.session_directory, latest)
            self.assertEqual(candidate.started_at, expected_start)

    def test_latest_completed_session_suppresses_older_candidate(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            older = root / "260824"
            latest = root / "260825"
            for session in (older, latest):
                screenshot_directory = session / "Screenshot"
                screenshot_directory.mkdir(parents=True)
                (screenshot_directory / "2030.png").write_bytes(b"image")
            (latest / "Diary_2030-2100.gif").write_bytes(b"gif")
            os.utime(older, (1, 1))
            os.utime(latest, (2, 2))

            self.assertIsNone(find_latest_incomplete_session(root))
