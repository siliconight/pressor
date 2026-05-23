#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found on PATH." >&2
  exit 1
fi

VENV_PATH="$PROJECT_ROOT/.venv-build"
if [[ ! -d "$VENV_PATH" ]]; then
  python3 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"
python -m pip install --upgrade pip
python -m pip install pyinstaller
if [[ -f support/requirements.txt ]]; then
  python -m pip install -r support/requirements.txt
fi

python -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name pressor \
  --add-data "config/pressor.profiles.json:config" \
  --add-data "config/pressor.routing.json:config" \
  --add-data "config/pressor.wwise.json:config" \
  --add-data "assets:assets" \
  pressor.py

echo
echo "Build complete."
echo "Binary: $PROJECT_ROOT/dist/pressor"
echo "Reminder: FFmpeg and FFprobe must still be installed and available on PATH."
