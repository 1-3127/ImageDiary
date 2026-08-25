from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from mss.exception import ScreenShotError

from screenshot_capture import ScreenshotCapture, ScreenshotCaptureError


class ScreenshotCaptureTests(TestCase):
    def test_saves_hhmm_png_filename(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            with patch("screenshot_capture.mss.mss") as mocked_mss:
                raw_image = mocked_mss.return_value.__enter__.return_value.grab.return_value
                raw_image.size = (2, 1)
                raw_image.rgb = b"\xff\x00\x00\x00\x00\xff"

                output = ScreenshotCapture().capture(
                    Path(temporary_directory),
                    datetime(2026, 8, 25, 20, 29),
                )

                self.assertEqual(output.name, "2029.png")
                self.assertTrue(output.is_file())

    def test_normalizes_mss_capture_failure(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            with patch("screenshot_capture.mss.mss") as mocked_mss:
                mocked_mss.return_value.__enter__.return_value.grab.side_effect = ScreenShotError(
                    "BitBlt failed"
                )

                with self.assertRaisesRegex(ScreenshotCaptureError, "BitBlt failed"):
                    ScreenshotCapture().capture(Path(temporary_directory))

    def test_does_not_overwrite_capture_from_same_minute(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            existing = output_directory / "2029.png"
            existing.write_bytes(b"original")

            with self.assertRaisesRegex(ScreenshotCaptureError, "이미 존재"):
                ScreenshotCapture().capture(
                    output_directory,
                    datetime(2026, 8, 25, 20, 29, 59),
                )

            self.assertEqual(existing.read_bytes(), b"original")

    def test_saves_each_supported_format(self) -> None:
        for image_format in ("png", "webp", "jpg"):
            with self.subTest(image_format=image_format), TemporaryDirectory() as temporary_directory:
                with patch("screenshot_capture.mss.mss") as mocked_mss:
                    raw_image = mocked_mss.return_value.__enter__.return_value.grab.return_value
                    raw_image.size = (2, 1)
                    raw_image.rgb = b"\xff\x00\x00\x00\x00\xff"

                    output = ScreenshotCapture().capture(
                        Path(temporary_directory),
                        datetime(2026, 8, 25, 20, 29),
                        image_format=image_format,
                        image_quality=85,
                    )

                    self.assertEqual(output.suffix, f".{image_format}")
                    self.assertTrue(output.is_file())
