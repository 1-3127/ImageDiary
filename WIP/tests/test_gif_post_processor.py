from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from PIL import Image

from gif_output_options import GifOutputOptions
from gif_post_processor import GifPostProcessor


class GifPostProcessorTests(TestCase):
    def test_crop_creates_processed_frame_without_mutating_source(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "001.png"
            source = Image.new("RGB", (20, 20), "red")
            source.save(source_path)
            source.close()
            original = Image.open(source_path)
            processor = GifPostProcessor(
                GifOutputOptions(
                    filename="Diary_test.gif",
                    crop_top_px=3,
                    crop_bottom_px=4,
                )
            )

            processed = processor.process(original, source_path)

            self.assertEqual(processed.size, (20, 13))
            with Image.open(source_path) as unchanged:
                self.assertEqual(unchanged.size, (20, 20))
            processed.close()

    def test_rejects_crop_larger_than_frame(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "001.png"
            source = Image.new("RGB", (10, 10), "red")
            source.save(source_path)
            source.close()
            with Image.open(source_path) as original:
                processor = GifPostProcessor(
                    GifOutputOptions(
                        filename="Diary_test.gif",
                        crop_top_px=5,
                        crop_bottom_px=5,
                    )
                )
                with self.assertRaisesRegex(ValueError, "크롭"):
                    processor.process(original, source_path)
