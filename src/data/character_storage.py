from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.utils.characters import (
    DEFAULT_CHARACTER_SEQUENCE,
    legacy_filename_for_character,
    safe_filename_for_character,
    unicode_hex,
)


class CharacterStorage:
    def __init__(self, characters_dir: Path) -> None:
        self.characters_dir = Path(characters_dir)
        self.characters_dir.mkdir(parents=True, exist_ok=True)

    def path_for_character(self, character: str) -> Path:
        return self.characters_dir / safe_filename_for_character(character)

    def legacy_path_for_character(self, character: str) -> Path | None:
        legacy_name = legacy_filename_for_character(character)
        if legacy_name is None:
            return None
        return self.characters_dir / legacy_name

    def existing_path_for_character(self, character: str) -> Path | None:
        path = self.path_for_character(character)
        if path.exists():
            return path
        legacy_path = self.legacy_path_for_character(character)
        if legacy_path is not None and legacy_path.exists():
            return legacy_path
        return None

    def save_character(self, character: str, strokes: list[list[list[float]]]) -> Path:
        payload = {
            "character": character,
            "unicode": unicode_hex(character),
            "strokes": strokes,
        }
        path = self.path_for_character(character)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def load_character(self, character: str) -> dict[str, Any]:
        path = self.path_for_character(character)
        existing_path = self.existing_path_for_character(character)
        if existing_path is not None:
            path = existing_path

        if not path.exists():
            return {
                "character": character,
                "unicode": unicode_hex(character),
                "strokes": [],
            }

        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("character") != character:
            data["character"] = character
        data.setdefault("unicode", unicode_hex(character))
        data.setdefault("strokes", [])
        return data

    def has_character(self, character: str) -> bool:
        data = self.load_character(character)
        return bool(data.get("strokes"))

    def load_strokes(self, character: str) -> list[list[list[float]]]:
        data = self.load_character(character)
        return data.get("strokes", [])

    def load_all(self, characters: list[str] | None = None) -> dict[str, dict[str, Any]]:
        selected = characters or DEFAULT_CHARACTER_SEQUENCE
        return {character: self.load_character(character) for character in selected}

    def saved_count(self, characters: list[str] | None = None) -> int:
        selected = characters or DEFAULT_CHARACTER_SEQUENCE
        return sum(1 for character in selected if self.has_character(character))

    def saved_characters(self, characters: list[str] | None = None) -> list[str]:
        selected = characters or DEFAULT_CHARACTER_SEQUENCE
        return [character for character in selected if self.has_character(character)]

    def missing_characters(self, characters: list[str] | None = None) -> list[str]:
        selected = characters or DEFAULT_CHARACTER_SEQUENCE
        return [character for character in selected if not self.has_character(character)]
