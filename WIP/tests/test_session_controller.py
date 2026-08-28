import os
from datetime import datetime
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from PIL import Image

from gif_output_options import GifOutputOptions
from file_exporter import FileExportError
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

    def test_exports_screenshots_with_gif_on_finish(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            controller = SessionController(
                AppSettings(
                    root / "export",
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
            self.assertTrue((outputs[0] / "Screenshot").is_dir())

    def test_can_export_only_custom_named_gif(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            controller = SessionController(
                AppSettings(
                    root / "export",
                    internal_storage_root=root / "internal",
                )
            )

            def create_test_capture(output_directory: Path, **_options: object) -> Path:
                output_path = output_directory / "001.png"
                Image.new("RGB", (8, 8), "green").save(output_path)
                return output_path

            controller._screenshot_capture.capture = create_test_capture
            controller.start()
            controller.finish(
                GifOutputOptions(
                    filename="shared-work.gif",
                    export_images=False,
                )
            )

            exported_session = next((root / "export").iterdir())
            self.assertTrue((exported_session / "shared-work.gif").is_file())
            self.assertFalse((exported_session / "Screenshot").exists())

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

    def test_cancelled_recovered_finish_marks_session_and_returns_idle(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            session = root / "internal" / "260828"
            screenshots = session / "Screenshot"
            screenshots.mkdir(parents=True)
            image = screenshots / "001.png"
            Image.new("RGB", (8, 8), "green").save(image)
            controller = SessionController(AppSettings(root / "export", internal_storage_root=root / "internal"))
            controller.prepare_recovered_finish(
                RecoveryCandidate(session, screenshots, (image,), datetime(2026, 8, 28, 10, 0))
            )

            controller.cancel_finish()

            self.assertIs(controller.state, SessionState.IDLE)
            self.assertTrue((session / ".unfin").is_file())

    def test_finish_without_gif_marks_active_session_and_returns_idle(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            controller = SessionController(AppSettings(root / "export", internal_storage_root=root / "internal"))
            controller._screenshot_capture.capture = lambda output_directory, **_options: output_directory / "001.png"
            controller.start()

            controller.finish_without_gif()

            self.assertIs(controller.state, SessionState.IDLE)
            assert controller._session_directory is not None
            self.assertTrue((controller._session_directory / ".unfin").is_file())

    def test_images_only_completion_creates_internal_gif_marker(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            controller = SessionController(AppSettings(root / "export", internal_storage_root=root / "internal"))

            def capture(output_directory: Path, **_options: object) -> Path:
                path = output_directory / "001.png"
                Image.new("RGB", (8, 8), "green").save(path)
                return path

            controller._screenshot_capture.capture = capture
            controller.start()
            controller.complete_with_images_only()

            assert controller._session_directory is not None
            self.assertEqual(len(list(controller._session_directory.glob("Diary_*.gif"))), 1)
            self.assertIs(controller.state, SessionState.IDLE)

    def test_failed_images_only_export_keeps_session_unfinished(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            controller = SessionController(AppSettings(root / "export", internal_storage_root=root / "internal"))

            def capture(output_directory: Path, **_options: object) -> Path:
                path = output_directory / "001.png"
                Image.new("RGB", (8, 8), "green").save(path)
                return path

            controller._screenshot_capture.capture = capture
            controller.start()
            controller._file_exporter.copy_screenshot = lambda *_args: (_ for _ in ()).throw(FileExportError("disk unavailable"))
            controller.save_images_only(GifOutputOptions(filename="Diary_test.gif"))

            assert controller._session_directory is not None
            self.assertFalse(any(controller._session_directory.glob("Diary_*.gif")))
            self.assertTrue((controller._session_directory / ".unfin").is_file())
