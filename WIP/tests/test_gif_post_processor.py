from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from PIL import Image, ImageChops

from gif_output_options import GifOutputOptions
from gif_post_processor import GifPostProcessor


class GifPostProcessorTests(TestCase):
    def test_masking_preserves_frame_size_without_mutating_source(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "001.png"
            source = Image.new("RGB", (20, 120), "red")
            source.save(source_path)
            source.close()
            original = Image.open(source_path)
            processor = GifPostProcessor(
                GifOutputOptions(
                    filename="Diary_test.gif",
                    crop_enabled=True,
                    hide_top=True,
                    hide_bottom=True,
                    crop_top_px=3,
                    crop_bottom_px=4,
                )
            )

            processed = processor.process(original, source_path)

            self.assertEqual(processed.size, (20, 120))
            self.assertEqual(processed.getpixel((10, 1)), (0, 0, 0))
            with Image.open(source_path) as unchanged:
                self.assertEqual(unchanged.size, (20, 120))
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
                    crop_enabled=True,
                    hide_top=True,
                    hide_bottom=True,
                        crop_top_px=5,
                        crop_bottom_px=5,
                    )
                )
                with self.assertRaises(ValueError):
                    processor.process(original, source_path)

    def test_applies_full_frame_blur(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "001.png"
            source = Image.new("RGB", (30, 30), "black")
            source.putpixel((15, 15), (255, 255, 255))
            source.save(source_path)
            source.close()
            with Image.open(source_path) as original:
                processed = GifPostProcessor(
                    GifOutputOptions(
                        filename="Diary_test.gif",
                        blur_enabled=True,
                        blur_strength=3,
                    )
                ).process(original, source_path)
            self.assertNotEqual(processed.getpixel((15, 15)), (255, 255, 255))
            processed.close()

    def test_applies_watermark_and_timecode_without_changing_source(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "001.png"
            source = Image.new("RGB", (200, 100), "black")
            source.save(source_path)
            source.close()
            with Image.open(source_path) as original:
                processed = GifPostProcessor(
                    GifOutputOptions(
                        filename="Diary_test.gif",
                        watermark_enabled=True,
                        watermark_text="TEST",
                        watermark_size=2,
                        watermark_opacity_level=2,
                        timecode_enabled=True,
                    )
                ).process(original, source_path)
            with Image.open(source_path) as unchanged:
                self.assertIsNotNone(ImageChops.difference(processed, unchanged).getbbox())
            processed.close()
