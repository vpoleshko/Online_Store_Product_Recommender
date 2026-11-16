#!/usr/bin/env bash
. "$(dirname "$0")/_common.sh"

compose up -d db
wait_for_db

echo "Open http://127.0.0.1:${API_PORT:-8765}"
"$PYTHON" -m uvicorn src.api.main:app --port "${API_PORT:-8765}"
