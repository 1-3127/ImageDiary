from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from mss.exception import ScreenShotError

from screenshot_capture import ScreenshotCapture, ScreenshotCaptureError


class ScreenshotCaptureTests(TestCase):
    def test_normalizes_mss_capture_failure(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            with patch("screenshot_capture.mss.mss") as mocked_mss:
                mocked_mss.return_value.__enter__.return_value.grab.side_effect = ScreenShotError(
                    "BitBlt failed"
                )

                with self.assertRaisesRegex(ScreenshotCaptureError, "BitBlt failed"):
                    ScreenshotCapture().capture(Path(temporary_directory))
