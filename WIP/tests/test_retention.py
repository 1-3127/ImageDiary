import os
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from retention import cleanup_expired_sessions


class RetentionTests(TestCase):
    def test_count_rule_removes_sessions_over_limit(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sessions = [root / "260825", root / "260826", root / "260827"]
            for session in sessions:
                session.mkdir()

            removed = cleanup_expired_sessions(
                root, 7, datetime(2026, 8, 28), days_enabled=False,
                count_enabled=True, keep_count=2,
            )

            self.assertEqual(removed, [sessions[0]])

    def test_size_rule_removes_oldest_sessions_until_under_limit(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            older = root / "260825"; newer = root / "260826"
            for session in (older, newer):
                session.mkdir(); (session / "image.bin").write_bytes(b"x" * 700_000)

            removed = cleanup_expired_sessions(
                root, 7, datetime(2026, 8, 28), days_enabled=False,
                size_enabled=True, max_size_mb=1,
            )

            self.assertEqual(removed, [older])

    def test_removes_only_expired_internal_session_directories(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sessions = [
                root / "260815",
                root / "260816",
                root / "260817",
                root / "260818",
            ]
            unrelated = root / "notes"
            now = datetime(2026, 8, 25, 12)
            for index, session in enumerate(sessions):
                session.mkdir()
                modified_at = (now - timedelta(days=10, hours=index)).timestamp()
                os.utime(session, (modified_at, modified_at))
            unrelated.mkdir()

            removed = cleanup_expired_sessions(root, 7, now)

            self.assertEqual(removed, [sessions[2], sessions[3]])
            self.assertTrue(sessions[0].exists())
            self.assertTrue(sessions[1].exists())
            self.assertFalse(sessions[2].exists())
            self.assertFalse(sessions[3].exists())
            self.assertTrue(unrelated.exists())
