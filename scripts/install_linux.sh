#!/usr/bin/env bash
set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_ROOT}/.." && pwd)"
cd "$REPO_ROOT"

echo
echo "=== Pressor Linux Setup ==="
echo

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return
  fi
  echo ""
}

confirm_yes_no() {
  local prompt="$1"
  local default_yes="${2:-yes}"
  local suffix="[Y/n]"
  if [[ "$default_yes" != "yes" ]]; then
    suffix="[y/N]"
  fi
  read -r -p "$prompt $suffix " reply || true
  reply="${reply:-}"
  case "${reply,,}" in
    y|yes) return 0 ;;
    n|no) return 1 ;;
    "")
      [[ "$default_yes" == "yes" ]]
      return
      ;;
    *)
      [[ "$default_yes" == "yes" ]]
      return
      ;;
  esac
}

ffmpeg_ready() {
  command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1
}

show_manual_ffmpeg_instructions() {
  echo
  echo "FFmpeg is still not available."
  echo "Install it with your distro package manager, then run setup again."
  echo
  echo "Examples:"
  echo "  Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y ffmpeg"
  echo "  Fedora       : sudo dnf install -y ffmpeg"
  echo "  Arch         : sudo pacman -S --noconfirm ffmpeg"
  echo "  openSUSE     : sudo zypper install -y ffmpeg"
  echo
}

install_ffmpeg_with_apt() {
  echo
  echo "Attempting FFmpeg install with apt-get..."
  sudo apt-get update && sudo apt-get install -y ffmpeg
}

install_ffmpeg_with_dnf() {
  echo
  echo "Attempting FFmpeg install with dnf..."
  sudo dnf install -y ffmpeg
}

install_ffmpeg_with_pacman() {
  echo
  echo "Attempting FFmpeg install with pacman..."
  sudo pacman -Sy --noconfirm ffmpeg
}

install_ffmpeg_with_zypper() {
  echo
  echo "Attempting FFmpeg install with zypper..."
  sudo zypper install -y ffmpeg
}

PYTHON_CMD="$(find_python)"
if [[ -z "$PYTHON_CMD" ]]; then
  echo "ERROR: Python was not found."
  echo "Install Python 3, then run setup again."
  exit 1
fi

echo "Python found: $PYTHON_CMD"
"$PYTHON_CMD" --version

REQ_FILE="$REPO_ROOT/requirements.txt"
if [[ ! -f "$REQ_FILE" ]]; then
  echo "ERROR: requirements.txt not found in $REPO_ROOT"
  exit 1
fi

echo
echo "Upgrading pip, setuptools, and wheel..."
"$PYTHON_CMD" -m pip install --upgrade pip setuptools wheel

echo
echo "Installing Pressor Python dependencies..."
"$PYTHON_CMD" -m pip install -r "$REQ_FILE"

echo
echo "Installing optional GUI drag-and-drop support..."
"$PYTHON_CMD" -m pip install tkinterdnd2 || true

echo
echo "Checking FFmpeg..."
if ! ffmpeg_ready; then
  echo "FFmpeg and/or FFprobe not found."

  if command -v apt-get >/dev/null 2>&1; then
    if confirm_yes_no "Install FFmpeg automatically using apt-get?"; then
      install_ffmpeg_with_apt || true
    fi
  elif command -v dnf >/dev/null 2>&1; then
    if confirm_yes_no "Install FFmpeg automatically using dnf?"; then
      install_ffmpeg_with_dnf || true
    fi
  elif command -v pacman >/dev/null 2>&1; then
    if confirm_yes_no "Install FFmpeg automatically using pacman?"; then
      install_ffmpeg_with_pacman || true
    fi
  elif command -v zypper >/dev/null 2>&1; then
    if confirm_yes_no "Install FFmpeg automatically using zypper?"; then
      install_ffmpeg_with_zypper || true
    fi
  else
    echo "No supported Linux package manager was detected automatically."
  fi

  if ! ffmpeg_ready; then
    show_manual_ffmpeg_instructions
    exit 1
  fi
fi

echo
echo "FFmpeg detected:"
ffmpeg -version | head -n 1
echo "FFprobe detected:"
ffprobe -version | head -n 1

DEFAULT_WORKSPACE="${HOME}/Pressor"
echo
echo "Initializing Pressor workspace at: ${DEFAULT_WORKSPACE}"
"$PYTHON_CMD" pressor.py --init --workspace-root "${DEFAULT_WORKSPACE}"

echo
echo "Running Pressor doctor check..."
"$PYTHON_CMD" pressor.py --doctor

INPUT_FOLDER="${DEFAULT_WORKSPACE}/input"
OUTPUT_FOLDER="${DEFAULT_WORKSPACE}/output"

echo
echo "=== Setup Complete ==="
echo
echo "Pressor workspace: ${DEFAULT_WORKSPACE}"
echo "Input folder      : ${INPUT_FOLDER}"
echo "Output root       : ${OUTPUT_FOLDER}"
echo
echo "The input folder will open now when possible. Put source-quality audio there, then run ./run_linux.sh"

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${INPUT_FOLDER}" >/dev/null 2>&1 || true
elif command -v gio >/dev/null 2>&1; then
  gio open "${INPUT_FOLDER}" >/dev/null 2>&1 || true
fi
