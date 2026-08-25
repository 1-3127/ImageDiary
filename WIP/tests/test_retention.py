from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from retention import cleanup_expired_sessions


class RetentionTests(TestCase):
    def test_removes_only_expired_internal_session_directories(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            expired = root / "260818"
            recent = root / "260819-02"
            unrelated = root / "notes"
            expired.mkdir()
            recent.mkdir()
            unrelated.mkdir()

            removed = cleanup_expired_sessions(root, 7, date(2026, 8, 25))

            self.assertEqual(removed, [expired])
            self.assertFalse(expired.exists())
            self.assertTrue(recent.exists())
            self.assertTrue(unrelated.exists())
