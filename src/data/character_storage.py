from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.utils.characters import (
    DEFAULT_CHARACTER_SEQUENCE,
    safe_filename_for_character,
    unicode_hex,
)


class CharacterStorage:
    def __init__(self, characters_dir: Path) -> None:
        self.characters_dir = Path(characters_dir)
        self.characters_dir.mkdir(parents=True, exist_ok=True)

    def path_for_character(self, character: str) -> Path:
        return self.characters_dir / safe_filename_for_character(character)

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

