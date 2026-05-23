#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo
echo "=== Pressor Run ==="
echo "Using saved workspace defaults."
echo "Input:  ${HOME}/Pressor/input"
echo "Output: ${HOME}/Pressor/output"
echo "Progress will be shown below."
echo

if [[ ! -f "scripts/run_linux.sh" ]]; then
  echo "ERROR: scripts/run_linux.sh was not found."
  exit 1
fi

bash "scripts/run_linux.sh"
