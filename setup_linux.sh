#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo
echo "=== Pressor Linux Setup ==="
echo "This will install Python dependencies, initialize ~/Pressor, and open the input folder when possible."
echo

if [[ ! -f "scripts/install_linux.sh" ]]; then
  echo "ERROR: scripts/install_linux.sh was not found."
  exit 1
fi

bash "scripts/install_linux.sh"
