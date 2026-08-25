import os
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from retention import cleanup_expired_sessions


class RetentionTests(TestCase):
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
