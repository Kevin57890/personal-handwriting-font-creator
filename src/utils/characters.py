from __future__ import annotations

import string
import unicodedata


UPPERCASE = list(string.ascii_uppercase)
LOWERCASE = list(string.ascii_lowercase)
DIGITS = list(string.digits)
SYMBOLS = list(".,!?;:'\"()[]{}-_/\\@#&$%+*=<>")
SPACE_CHARACTER = " "

CHARACTER_GROUPS: list[tuple[str, list[str]]] = [
    ("Uppercase", UPPERCASE),
    ("Lowercase", LOWERCASE),
    ("Numbers", DIGITS),
    ("Symbols", SYMBOLS),
]

DEFAULT_CHARACTER_SEQUENCE = [
    character for _, group in CHARACTER_GROUPS for character in group
]


def unicode_hex(character: str) -> str:
    return f"{ord(character):04X}"


def glyph_name_for_character(character: str) -> str:
    if character == SPACE_CHARACTER:
        return "space"
    return f"uni{ord(character):04X}"


def safe_filename_for_character(character: str) -> str:
    if character.isalnum() and character.isascii():
        return f"{character}.json"

    name = unicodedata.name(character, "SYMBOL")
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_")
    return f"U+{unicode_hex(character)}_{safe_name}.json"


def group_name_for_character(character: str) -> str:
    for group_name, group in CHARACTER_GROUPS:
        if character in group:
            return group_name
    return "Custom"

