import os
from datetime import datetime
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from PIL import Image

from session_controller import SessionController, SessionState
from session_recovery import RecoveryCandidate
from settings import AppSettings


class SessionControllerTests(TestCase):
    def test_storage_failure_keeps_session_idle(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            controller = SessionController(
                AppSettings(
                    root / "export",
                    internal_storage_root=root / "internal",
                )
            )
            statuses: list[str] = []
            controller.status_changed.connect(statuses.append)

            with patch(
                "session_controller.SessionStorage.create_session_directory",
                side_effect=OSError("disk unavailable"),
            ):
                controller.start()

            self.assertIs(controller.state, SessionState.IDLE)
            self.assertEqual(statuses, ["세션 시작 실패: disk unavailable"])

    def test_complete_session_builds_gif_and_returns_to_idle(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            controller = SessionController(
                AppSettings(
                    root / "export",
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

            controller.start()
            controller.finish()

            self.assertIs(controller.state, SessionState.IDLE)
            self.assertEqual(len(outputs), 1)
            self.assertEqual(len(list(outputs[0].glob("*.gif"))), 1)
            exported_screenshots = (
                root / "export" / outputs[0].name / "Screenshot"
            )
            self.assertEqual(len(list(exported_screenshots.glob("*.png"))), 1)

    def test_finishes_recovered_session(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            internal_session = root / "internal" / "260825"
            screenshots = internal_session / "Screenshot"
            screenshots.mkdir(parents=True)
            image_path = screenshots / "2030.png"
            Image.new("RGB", (8, 8), "green").save(image_path)
            last_image_path = screenshots / "2045.png"
            Image.new("RGB", (8, 8), "blue").save(last_image_path)
            first_time = datetime(2026, 8, 25, 20, 30)
            last_time = datetime(2026, 8, 25, 20, 45)
            os.utime(image_path, (first_time.timestamp(), first_time.timestamp()))
            os.utime(
                last_image_path,
                (last_time.timestamp(), last_time.timestamp()),
            )
            settings = AppSettings(
                root / "export",
                internal_storage_root=root / "internal",
            )
            controller = SessionController(settings)
            candidate = RecoveryCandidate(
                internal_session,
                screenshots,
                (image_path, last_image_path),
                datetime(2026, 8, 25, 20, 30),
            )

            controller.finish_recovered(candidate)

            self.assertIs(controller.state, SessionState.IDLE)
            exported_session = root / "export" / "260825"
            self.assertTrue((exported_session / "Diary_2030-2045.gif").is_file())

    def test_can_export_only_gif_on_finish(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            controller = SessionController(
                AppSettings(
                    root / "export",
                    export_screenshots_on_finish=False,
                    internal_storage_root=root / "internal",
                )
            )

            def create_test_capture(output_directory: Path, **_options: object) -> Path:
                output_path = output_directory / "1915.png"
                Image.new("RGB", (8, 8), "green").save(output_path)
                return output_path

            controller._screenshot_capture.capture = create_test_capture
            outputs: list[Path] = []
            controller.output_ready.connect(outputs.append)

            controller.start()
            controller.finish()

            self.assertEqual(len(list(outputs[0].glob("Diary_*.gif"))), 1)
            self.assertFalse((outputs[0] / "Screenshot").exists())

    def test_settings_changed_during_session_apply_next_time(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            initial_settings = AppSettings(
                root / "export",
                capture_format="png",
                internal_storage_root=root / "internal",
            )
            controller = SessionController(initial_settings)
            received_formats: list[str] = []
            received_sequences: list[int] = []

            def create_test_capture(
                output_directory: Path,
                **options: object,
            ) -> Path:
                received_formats.append(str(options["image_format"]))
                received_sequences.append(int(options["sequence_number"]))
                output_path = output_directory / "2030.png"
                Image.new("RGB", (8, 8), "green").save(output_path)
                return output_path

            controller._screenshot_capture.capture = create_test_capture
            controller.start()
            controller.update_settings(
                replace(initial_settings, capture_format="jpg")
            )
            controller.finish()

            self.assertEqual(received_formats, ["png"])
            self.assertEqual(received_sequences, [1])
