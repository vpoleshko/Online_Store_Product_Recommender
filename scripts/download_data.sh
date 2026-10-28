#!/usr/bin/env bash
. "$(dirname "$0")/_common.sh"

"$PYTHON" scripts/download_dataset.py "$RAW_DIR"
