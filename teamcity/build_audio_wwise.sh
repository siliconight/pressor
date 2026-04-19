#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
INPUT_ROOT="${INPUT_ROOT:-./AudioRaw}"
PREPARED_ROOT="${PREPARED_ROOT:-./AudioPrepared}"
ARTIFACTS_ROOT="${ARTIFACTS_ROOT:-./artifacts}"
DEFAULT_PROFILE="${DEFAULT_PROFILE:-dialogue}"

mkdir -p "$PREPARED_ROOT" "$ARTIFACTS_ROOT"

"$PYTHON_BIN" ./pressor.py \
  --input "$INPUT_ROOT" \
  --output "$PREPARED_ROOT" \
  --profile "$DEFAULT_PROFILE" \
  --wwise-prep \
  --review-pack "$ARTIFACTS_ROOT/review_pack" \
  --wwise-import-json-out "$ARTIFACTS_ROOT/wwise_import_starter.json" \
  --wwise-import-tsv-out "$ARTIFACTS_ROOT/wwise_import_starter.tsv"

echo "Prepared audio in $PREPARED_ROOT"
echo "Starter Wwise mappings written to $ARTIFACTS_ROOT"
echo "Next step: import the prepared WAV files into Wwise and generate SoundBanks."
