# Personal Handwriting Font Creator

A polished desktop app for drawing letters, numbers, and punctuation directly on a canvas, saving the handwriting as vector stroke JSON, previewing the handwritten result, and generating a real installable TrueType font.

## Features

- PyQt6 handwriting canvas with mouse and tablet-event support.
- Vector stroke storage in `characters/*.json`.
- Focused in-app editor with pen, eraser, move, undo, redo, center, scale, and nudge tools.
- Progress-first workflow for uppercase, lowercase, numbers, and symbols.
- Live preview rendered from saved vector strokes.
- Export controls for font name, output folder, opening the generated font, opening the output folder, and copying the font path.
- TrueType generation with `fontTools`.
- Stroke-to-outline pipeline: simplify points, fit Catmull-Rom/Bezier curves, flatten curves, expand strokes into filled glyph outlines, write glyf/cmap tables.

## Requirements

- Python 3.9 or newer. Python 3.11 is recommended.
- macOS, Windows, or Linux with a desktop session

## One-click Run on macOS

Double-click:

```text
Run Personal Handwriting Font Creator.command
```

The launcher creates `.venv`, installs dependencies, verifies imports, and starts the editor.

## Install

```bash
cd PersonalHandwritingFontCreator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run

```bash
cd PersonalHandwritingFontCreator
source .venv/bin/activate
python main.py
```

The first launch opens the Character Setup Wizard. Draw characters on the canvas, save each one, then press **Generate Font**. By default, the generated font is written to:

```text
output/<FontName>.ttf
```

Install that file in your operating system, then choose **MyHandwriting** in Microsoft Word and type text such as:

```text
Hello World!
```

## Stroke JSON Format

Each character is saved as JSON:

```json
{
  "character": "A",
  "unicode": "0041",
  "strokes": [
    [
      [104.0, 320.0, 1719991000.0, 1.0],
      [110.0, 301.0, 1719991000.1, 1.0]
    ]
  ]
}
```

Coordinates are canvas-space points. Pressure defaults to `1.0` for mouse input and uses tablet pressure when available.

## Tests

```bash
cd PersonalHandwritingFontCreator
python -m unittest discover -s tests
```
