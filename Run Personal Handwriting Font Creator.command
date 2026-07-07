#!/bin/zsh
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

echo "Personal Handwriting Font Creator"
echo "Project: $APP_DIR"
echo

if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.11)"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "Python was not found."
  echo
  echo "Install Python 3.11, then double-click this launcher again."
  echo "Download: https://www.python.org/downloads/"
  echo
  read "?Press Enter to close..."
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 9):
    raise SystemExit("Python 3.9 or newer is required.")
print(f"Using Python {sys.version.split()[0]}")
PY

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  "$PYTHON_BIN" -m venv .venv
fi

source ".venv/bin/activate"

python -m pip install -r requirements.txt

python - <<'PY'
import importlib

for module_name in ["PyQt6", "fontTools", "numpy", "bezier"]:
    importlib.import_module(module_name)

print("Dependencies ready.")
PY

echo
echo "Launching app..."
python main.py
