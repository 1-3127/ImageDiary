import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from data_cleanup import move_old_sessions_to_trash


class DataCleanupTests(TestCase):
    def test_keeps_two_latest_and_trashes_older_sessions(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sessions = [root / "260822", root / "260823", root / "260824", root / "260825"]
            for index, session in enumerate(sessions, start=1):
                session.mkdir()
                os.utime(session, (index, index))
            unrelated = root / "notes"
            unrelated.mkdir()
            trashed: list[str] = []

            moved = move_old_sessions_to_trash(root, trash=trashed.append)

            self.assertEqual(moved, [root / "260823", root / "260822"])
            self.assertEqual(trashed, [str(root / "260823"), str(root / "260822")])
            self.assertTrue(unrelated.exists())
