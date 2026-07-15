from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Iterable

from fontTools.ttLib import TTFont, TTLibError

from src.data.character_storage import CharacterStorage
from src.font.glyph_generator import GlyphGenerator
from src.utils.characters import DEFAULT_CHARACTER_SEQUENCE


class FontPatchError(ValueError):
    """Raised when a base font cannot safely be used for glyph replacement."""


@dataclass(frozen=True)
class BaseFontInfo:
    path: Path
    family_name: str
    units_per_em: int
    glyph_count: int
    supported_characters: frozenset[str]


@dataclass(frozen=True)
class FontPatchResult:
    output_path: Path
    replaced_characters: tuple[str, ...]


class FontPatcher:
    def __init__(
        self,
        storage: CharacterStorage,
        family_name: str,
        stroke_width: float = 76.0,
        tracking: int = 0,
    ) -> None:
        self.storage = storage
        self.family_name = family_name.strip() or "MyHandwriting"
        self.stroke_width = max(24.0, min(float(stroke_width), 180.0))
        self.tracking = int(max(-160, min(int(tracking), 280)))

    @classmethod
    def inspect(cls, source_path: Path) -> BaseFontInfo:
        source_path = Path(source_path)
        try:
            font = TTFont(source_path, lazy=False)
        except (OSError, TTLibError) as error:
            raise FontPatchError(f"Could not open the selected font: {error}") from error

        try:
            cls._validate_font(font)
            cmap = font.getBestCmap() or {}
            glyph_order = set(font.getGlyphOrder())
            supported = frozenset(
                character
                for character in DEFAULT_CHARACTER_SEQUENCE
                if cmap.get(ord(character)) in glyph_order
            )
            family_name = font["name"].getDebugName(1) or source_path.stem
            return BaseFontInfo(
                path=source_path,
                family_name=family_name,
                units_per_em=int(font["head"].unitsPerEm),
                glyph_count=len(glyph_order),
                supported_characters=supported,
            )
        finally:
            font.close()

    def build(
        self,
        source_path: Path,
        output_path: Path,
        characters: Iterable[str],
    ) -> FontPatchResult:
        source_path = Path(source_path)
        output_path = Path(output_path)
        selected = tuple(dict.fromkeys(characters))
        if not selected:
            raise FontPatchError("Select at least one saved glyph to replace.")

        try:
            font = TTFont(source_path, lazy=False)
        except (OSError, TTLibError) as error:
            raise FontPatchError(f"Could not open the selected font: {error}") from error

        try:
            self._validate_font(font)
            cmap = font.getBestCmap() or {}
            unavailable = [character for character in selected if ord(character) not in cmap]
            if unavailable:
                display = ", ".join(unavailable)
                raise FontPatchError(f"The base font does not contain: {display}")

            missing_strokes = [character for character in selected if not self.storage.has_character(character)]
            if missing_strokes:
                display = ", ".join(missing_strokes)
                raise FontPatchError(f"No saved strokes are available for: {display}")

            units_per_em = int(font["head"].unitsPerEm)
            generator = self._generator_for_units(units_per_em, self.stroke_width)
            tracking = int(round(self.tracking * units_per_em / 1000.0))
            replaced: list[str] = []
            for character in selected:
                glyph_name = (font.getBestCmap() or {}).get(ord(character))
                if glyph_name is None:
                    raise FontPatchError(f"The base font no longer maps {character!r}.")

                glyph, outline = generator.make_glyph(self.storage.load_strokes(character))
                target_name = self._target_glyph_name(font, glyph_name, ord(character))
                font["glyf"][target_name] = glyph
                font["hmtx"].metrics[target_name] = (
                    max(1, outline.advance_width + tracking),
                    outline.left_side_bearing,
                )
                replaced.append(character)

            font["maxp"].numGlyphs = len(font.getGlyphOrder())
            font.recalcBBoxes = True
            font.recalcTimestamp = True
            font.flavor = None
            self._update_names(font)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            font.save(output_path)
            return FontPatchResult(output_path=output_path, replaced_characters=tuple(replaced))
        finally:
            font.close()

    @staticmethod
    def _validate_font(font: TTFont) -> None:
        required_tables = {"glyf", "hmtx", "head", "maxp", "name", "cmap"}
        missing = required_tables.difference(font.keys())
        if missing:
            table_names = ", ".join(sorted(missing))
            raise FontPatchError(
                f"This font is not a static TrueType font with editable outlines (missing {table_names})."
            )
        if "fvar" in font:
            raise FontPatchError("Variable fonts are not supported as a base. Export a static TTF first.")

    @staticmethod
    def _generator_for_units(units_per_em: int, stroke_width: float) -> GlyphGenerator:
        scale = units_per_em / 1000.0
        return GlyphGenerator(
            units_per_em=units_per_em,
            x_margin=70.0 * scale,
            horizontal_scale=860.0 * scale,
            vertical_scale=950.0 * scale,
            stroke_width=stroke_width * scale,
        )

    def _target_glyph_name(self, font: TTFont, source_name: str, codepoint: int) -> str:
        if not self._glyph_is_shared(font, source_name, codepoint):
            return source_name

        new_name = self._unique_glyph_name(font, f"{source_name}.hand")
        glyph_order = list(font.getGlyphOrder())
        glyph_order.append(new_name)
        font.setGlyphOrder(glyph_order)
        self._replace_cmap_for_codepoint(font, codepoint, new_name)
        return new_name

    @staticmethod
    def _glyph_is_shared(font: TTFont, glyph_name: str, codepoint: int) -> bool:
        for table in font["cmap"].tables:
            if not table.isUnicode():
                continue
            for mapped_codepoint, mapped_name in table.cmap.items():
                if mapped_name == glyph_name and mapped_codepoint != codepoint:
                    return True
        return False

    @staticmethod
    def _replace_cmap_for_codepoint(font: TTFont, codepoint: int, glyph_name: str) -> None:
        for table in font["cmap"].tables:
            if table.isUnicode() and codepoint in table.cmap:
                table.cmap[codepoint] = glyph_name

    @staticmethod
    def _unique_glyph_name(font: TTFont, stem: str) -> str:
        glyph_names = set(font.getGlyphOrder())
        candidate = stem
        index = 2
        while candidate in glyph_names:
            candidate = f"{stem}{index}"
            index += 1
        return candidate

    def _update_names(self, font: TTFont) -> None:
        style_name = font["name"].getDebugName(2) or "Regular"
        full_name = f"{self.family_name} {style_name}".strip()
        postscript_name = self._postscript_name(full_name)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        values = {
            1: self.family_name,
            2: style_name,
            3: f"{postscript_name}-{timestamp}",
            4: full_name,
            5: "Version 1.001",
            6: postscript_name,
            16: self.family_name,
            17: style_name,
        }
        name_table = font["name"]
        for record in list(name_table.names):
            value = values.get(record.nameID)
            if value is not None:
                name_table.setName(value, record.nameID, record.platformID, record.platEncID, record.langID)

        for platform_id, encoding_id, language_id in ((3, 1, 0x0409), (1, 0, 0)):
            for name_id, value in values.items():
                name_table.setName(value, name_id, platform_id, encoding_id, language_id)

    @staticmethod
    def _postscript_name(full_name: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9-]", "", full_name.replace(" ", ""))
        return (cleaned or "MyHandwritingRegular")[:63]
