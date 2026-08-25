from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock

from session_controller import SessionController, SessionState
from settings import AppSettings


class SessionControllerTests(TestCase):
    def test_storage_failure_keeps_session_idle(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            controller = SessionController(AppSettings(Path(temporary_directory)))
            controller._storage = Mock()
            controller._storage.create_session_directory.side_effect = OSError("disk unavailable")
            statuses: list[str] = []
            controller.status_changed.connect(statuses.append)

            controller.start(15)

            self.assertIs(controller.state, SessionState.IDLE)
            self.assertEqual(statuses, ["Session start failed: disk unavailable"])
