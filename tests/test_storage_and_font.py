from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from fontTools.ttLib import TTFont

from src.data.character_storage import CharacterStorage
from src.data.project_package import ProjectPackage
from src.font.glyph_generator import GlyphGenerator
from src.font.sample_exporter import FontSampleExporter
from src.font.ttf_builder import TTFBuilder


class StorageAndFontTests(unittest.TestCase):
    def test_character_storage_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = CharacterStorage(Path(temp_dir) / "characters")
            storage.save_character("A", [[[10, 20, 1.0, 1.0], [30, 40, 1.1, 0.8]]])
            data = storage.load_character("A")
            self.assertEqual(data["character"], "A")
            self.assertEqual(data["unicode"], "0041")
            self.assertTrue(storage.has_character("A"))

    def test_glyph_generator_creates_closed_contours(self) -> None:
        generator = GlyphGenerator()
        outline = generator.build_outline(
            [
                [[160, 590, 1.0, 1.0], [300, 140, 1.1, 1.0], [460, 590, 1.2, 1.0]],
                [[230, 395, 1.3, 1.0], [390, 395, 1.4, 1.0]],
            ]
        )
        self.assertGreaterEqual(len(outline.contours), 2)
        self.assertGreater(outline.advance_width, 300)
        self.assertIsNotNone(outline.bounds)
        for contour in outline.contours:
            self.assertGreaterEqual(len(contour), 3)

    def test_ttf_builder_writes_installable_font(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            storage = CharacterStorage(root / "characters")
            storage.save_character(
                "A",
                [
                    [[160, 590, 1.0, 1.0], [300, 140, 1.1, 1.0], [460, 590, 1.2, 1.0]],
                    [[230, 395, 1.3, 1.0], [390, 395, 1.4, 1.0]],
                ],
            )
            storage.save_character(
                "!",
                [
                    [[320, 160, 1.0, 1.0], [320, 480, 1.1, 1.0]],
                    [[320, 570, 1.2, 1.0], [321, 571, 1.3, 1.0]],
                ],
            )

            output = TTFBuilder(storage, family_name="UnitTestHand").build(root / "UnitTestHand.ttf")
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 1000)

            font = TTFont(output)
            cmap = font.getBestCmap()
            self.assertEqual(cmap[ord("A")], "uni0041")
            self.assertEqual(cmap[ord("!")], "uni0021")
            self.assertIn("glyf", font)
            self.assertIn("hmtx", font)

    def test_project_package_exports_restores_and_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            storage = CharacterStorage(root / "characters")
            storage.save_character("A", [[[10, 20, 1.0, 1.0], [30, 40, 1.1, 1.0]]])

            package = ProjectPackage(storage)
            zip_path = package.export_zip(root / "backup.zip", "UnitTestHand")
            self.assertTrue(zip_path.exists())

            report_path = package.write_missing_report(root / "missing.txt")
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("Saved: 1/", report)
            self.assertIn("Missing characters:", report)

            restored_storage = CharacterStorage(root / "restored")
            restored = ProjectPackage(restored_storage).import_zip(zip_path)
            self.assertEqual(restored, 1)
            self.assertTrue(restored_storage.has_character("A"))

    def test_sample_exporter_writes_html_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            font_path = root / "UnitTestHand.ttf"
            font_path.write_bytes(b"fake-font-for-html-reference")
            sample = FontSampleExporter().export_html(
                output_path=root / "sample.html",
                font_path=font_path,
                family_name="UnitTestHand",
                sample_text="Hello World!",
                saved_count=12,
                total_count=90,
            )
            html = sample.read_text(encoding="utf-8")
            self.assertIn("@font-face", html)
            self.assertIn("UnitTestHand", html)
            self.assertIn("Hello World!", html)


if __name__ == "__main__":
    unittest.main()
