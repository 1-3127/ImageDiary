import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from data_cleanup import move_old_sessions_to_trash


class DataCleanupTests(TestCase):
    def test_keeps_two_latest_and_trashes_older_sessions(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            internal_root = root / "internal"
            export_root = root / "export"
            internal_root.mkdir()
            export_root.mkdir()
            exported_session = export_root / "260821"
            exported_session.mkdir()
            sessions = [
                internal_root / "260822",
                internal_root / "260823",
                internal_root / "260824",
                internal_root / "260825",
            ]
            for index, session in enumerate(sessions, start=1):
                session.mkdir()
                os.utime(session, (index, index))
            unrelated = internal_root / "notes"
            unrelated.mkdir()
            trashed: list[str] = []

            moved = move_old_sessions_to_trash(
                internal_root,
                trash=trashed.append,
            )

            self.assertEqual(moved, sessions[1::-1])
            self.assertEqual(trashed, [str(sessions[1]), str(sessions[0])])
            self.assertTrue(unrelated.exists())
            self.assertTrue(exported_session.exists())
