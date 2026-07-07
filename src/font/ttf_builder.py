from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from src.data.character_storage import CharacterStorage
from src.font.glyph_generator import GlyphGenerator
from src.utils.characters import DEFAULT_CHARACTER_SEQUENCE, glyph_name_for_character


class TTFBuilder:
    def __init__(
        self,
        storage: CharacterStorage,
        family_name: str = "MyHandwriting",
        units_per_em: int = 1000,
    ) -> None:
        self.storage = storage
        self.family_name = family_name.strip() or "MyHandwriting"
        self.units_per_em = units_per_em
        self.generator = GlyphGenerator(units_per_em=units_per_em)

    def build(self, output_path: Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        glyph_order = [".notdef", "space"]
        character_to_glyph: dict[int, str] = {0x20: "space"}

        for character in DEFAULT_CHARACTER_SEQUENCE:
            glyph_name = glyph_name_for_character(character)
            glyph_order.append(glyph_name)
            character_to_glyph[ord(character)] = glyph_name

        glyphs = {}
        metrics = {}

        glyphs[".notdef"] = self._notdef_glyph()
        metrics[".notdef"] = (600, 50)

        space_pen = TTGlyphPen(None)
        glyphs["space"] = space_pen.glyph()
        metrics["space"] = (360, 0)

        for character in DEFAULT_CHARACTER_SEQUENCE:
            glyph_name = glyph_name_for_character(character)
            strokes = self.storage.load_strokes(character)
            glyph, outline = self.generator.make_glyph(strokes)
            glyphs[glyph_name] = glyph
            metrics[glyph_name] = (outline.advance_width, outline.left_side_bearing)

        builder = FontBuilder(self.units_per_em, isTTF=True)
        builder.setupGlyphOrder(glyph_order)
        builder.setupCharacterMap(character_to_glyph)
        builder.setupGlyf(glyphs)
        builder.setupHorizontalMetrics(metrics)
        builder.setupHorizontalHeader(ascent=820, descent=-300)
        builder.setupHead(
            created=self._font_timestamp(),
            modified=self._font_timestamp(),
            macStyle=0,
            lowestRecPPEM=8,
        )
        builder.setupOS2(
            sTypoAscender=820,
            sTypoDescender=-300,
            sTypoLineGap=120,
            usWinAscent=920,
            usWinDescent=360,
            sxHeight=470,
            sCapHeight=700,
            achVendID="PHFC",
        )
        builder.setupNameTable(self._name_table())
        builder.setupPost(italicAngle=0, underlinePosition=-100, underlineThickness=50)
        builder.setupMaxp()

        builder.save(output_path)
        return output_path

    def _name_table(self) -> dict[str, str]:
        full_name = f"{self.family_name} Regular"
        postscript_name = self._postscript_name(full_name)
        now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return {
            "familyName": self.family_name,
            "styleName": "Regular",
            "uniqueFontIdentifier": f"{postscript_name}-{now}",
            "fullName": full_name,
            "psName": postscript_name,
            "version": "Version 1.000",
            "manufacturer": "Personal Handwriting Font Creator",
            "designer": "Personal Handwriting Font Creator User",
            "description": "A personal handwriting font generated from vector strokes.",
        }

    def _postscript_name(self, full_name: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9-]", "", full_name.replace(" ", ""))
        return cleaned or "MyHandwritingRegular"

    def _font_timestamp(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def _notdef_glyph(self):
        pen = TTGlyphPen(None)
        pen.moveTo((60, -220))
        pen.lineTo((520, -220))
        pen.lineTo((520, 760))
        pen.lineTo((60, 760))
        pen.closePath()
        pen.moveTo((120, -120))
        pen.lineTo((460, 660))
        pen.lineTo((460, -120))
        pen.lineTo((120, 660))
        pen.closePath()
        return pen.glyph()

