from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock

from PIL import Image

from session_controller import SessionController, SessionState
from settings import AppSettings


class SessionControllerTests(TestCase):
    def test_storage_failure_keeps_session_idle(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            controller = SessionController(
                AppSettings(
                    root / "screenshot-export",
                    root / "gif-export",
                    internal_storage_root=root / "internal",
                )
            )
            controller._storage = Mock()
            controller._storage.create_session_directory.side_effect = OSError("disk unavailable")
            statuses: list[str] = []
            controller.status_changed.connect(statuses.append)

            controller.start(15)

            self.assertIs(controller.state, SessionState.IDLE)
            self.assertEqual(statuses, ["세션 시작 실패: disk unavailable"])

    def test_complete_session_builds_gif_and_returns_to_idle(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            controller = SessionController(
                AppSettings(
                    root / "screenshot-export",
                    root / "gif-export",
                    internal_storage_root=root / "internal",
                )
            )

            def create_test_capture(output_directory: Path, **_options: object) -> Path:
                output_directory.mkdir(parents=True, exist_ok=True)
                output_path = output_directory / "1915.png"
                Image.new("RGB", (8, 8), "green").save(output_path)
                return output_path

            controller._screenshot_capture.capture = create_test_capture
            outputs: list[Path] = []
            controller.output_ready.connect(outputs.append)

            controller.start(15 * 60)
            controller._capture_screenshot()
            controller.finish()

            self.assertIs(controller.state, SessionState.IDLE)
            self.assertEqual(len(outputs), 1)
            self.assertEqual(len(list(outputs[0].glob("*.gif"))), 1)
            exported_screenshots = (
                root / "screenshot-export" / outputs[0].name / "Screenshot"
            )
            self.assertEqual(len(list(exported_screenshots.glob("*.png"))), 1)
