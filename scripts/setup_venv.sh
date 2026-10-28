#!/usr/bin/env bash
. "$(dirname "$0")/_common.sh"

"$PYTHON" -m venv .venv
if [ -f .venv/Scripts/activate ]; then
    . .venv/Scripts/activate
else
    . .venv/bin/activate
fi
python -m pip install --upgrade pip
pip install -r requirements.txt
echo "Done. Activate with: source .venv/bin/activate (or .venv/Scripts/activate on Windows)"
