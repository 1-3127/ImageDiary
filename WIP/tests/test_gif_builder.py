from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from PIL import Image

from gif_builder import GifBuilder


class GifBuilderTests(TestCase):
    def test_builds_frames_in_filename_order(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            screenshots = root / "screenshots"
            screenshots.mkdir()
            Image.new("RGB", (8, 8), "blue").save(screenshots / "1930.png")
            Image.new("RGB", (8, 8), "red").save(screenshots / "1915.png")
            output = root / "diary.gif"

            frame_count = GifBuilder().build(screenshots, output, 500, 0)

            self.assertEqual(frame_count, 2)
            with Image.open(output) as gif:
                self.assertEqual(gif.n_frames, 2)
                gif.seek(0)
                self.assertEqual(gif.convert("RGB").getpixel((0, 0)), (255, 0, 0))
                gif.seek(1)
                self.assertEqual(gif.convert("RGB").getpixel((0, 0)), (0, 0, 255))

    def test_rejects_empty_screenshot_directory(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            screenshots = root / "screenshots"
            screenshots.mkdir()

            with self.assertRaises(ValueError):
                GifBuilder().build(screenshots, root / "diary.gif", 500, 0)

    def test_reports_encoding_progress(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            screenshots = root / "Screenshot"
            screenshots.mkdir()
            Image.new("RGB", (8, 8), "red").save(screenshots / "1915.png")
            progress: list[tuple[int, int]] = []

            GifBuilder().build(
                screenshots,
                root / "Diary_1915-1930.gif",
                500,
                0,
                lambda current, total: progress.append((current, total)),
            )

            self.assertEqual(progress[0], (0, 2))
            self.assertEqual(progress[-1], (2, 2))
