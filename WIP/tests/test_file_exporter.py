from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from file_exporter import FileExporter


class FileExporterTests(TestCase):
    def test_copies_session_files_to_export_roots(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_png = root / "internal" / "260825" / "Screenshot" / "2030.png"
            source_png.parent.mkdir(parents=True)
            source_png.write_bytes(b"png")
            source_gif = source_png.parents[1] / "Diary_2029-2031.gif"
            source_gif.write_bytes(b"gif")

            copied_png = FileExporter.copy_screenshot(
                source_png, root / "screenshots", "260825"
            )
            copied_gif = FileExporter.copy_gif(source_gif, root / "gifs", "260825")

            self.assertEqual(copied_png.read_bytes(), b"png")
            self.assertEqual(copied_gif.read_bytes(), b"gif")
            self.assertEqual(copied_png.parent.name, "Screenshot")
