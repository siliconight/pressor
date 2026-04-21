#!/usr/bin/env bash
set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_ROOT}/.." && pwd)"
cd "$REPO_ROOT"

echo
echo "=== Pressor Run ==="
echo "Running Pressor using the saved workspace defaults."
echo

if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "ERROR: Python was not found."
  exit 1
fi

"$PYTHON_CMD" pressor.py --auto-profile --skip-lossy-inputs --benchmark
