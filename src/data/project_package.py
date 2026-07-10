from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import zipfile

from src.data.character_storage import CharacterStorage
from src.utils.characters import DEFAULT_CHARACTER_SEQUENCE


class ProjectPackage:
    def __init__(self, storage: CharacterStorage) -> None:
        self.storage = storage

    def export_zip(self, output_path: Path, font_family: str) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        manifest = {
            "name": "Personal Handwriting Font Creator Project",
            "fontFamily": font_family,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "characterCount": len(DEFAULT_CHARACTER_SEQUENCE),
            "savedCharacters": self.storage.saved_characters(),
        }

        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
            for character in DEFAULT_CHARACTER_SEQUENCE:
                source = self.storage.existing_path_for_character(character)
                if source is not None:
                    archive.write(source, f"characters/{self.storage.path_for_character(character).name}")

        return output_path

    def import_zip(self, package_path: Path) -> int:
        package_path = Path(package_path)
        restored = 0

        with zipfile.ZipFile(package_path, "r") as archive:
            for info in archive.infolist():
                path = Path(info.filename)
                if len(path.parts) != 2 or path.parts[0] != "characters":
                    continue
                if path.name.startswith(".") or path.suffix.lower() != ".json":
                    continue

                target = self.storage.characters_dir / path.name
                with archive.open(info) as source:
                    raw = source.read().decode("utf-8")
                data = json.loads(raw)
                if not isinstance(data, dict) or "character" not in data or "strokes" not in data:
                    continue
                target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                restored += 1

        return restored

    def write_missing_report(self, output_path: Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        missing = self.storage.missing_characters()
        saved = self.storage.saved_characters()

        lines = [
            "Personal Handwriting Font Creator - Missing Character Report",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            "",
            f"Saved: {len(saved)}/{len(DEFAULT_CHARACTER_SEQUENCE)}",
            f"Missing: {len(missing)}/{len(DEFAULT_CHARACTER_SEQUENCE)}",
            "",
            "Missing characters:",
            "".join(missing) if missing else "None",
            "",
            "Saved characters:",
            "".join(saved) if saved else "None",
            "",
        ]
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path
