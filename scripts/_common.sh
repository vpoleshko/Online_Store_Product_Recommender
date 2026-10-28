#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export MSYS_NO_PATHCONV=1

if [ ! -f .env ]; then
    echo ".env not found, creating from .env.example"
    cp .env.example .env
fi
set -a
. ./.env
set +a

PYTHON="${PYTHON:-python3}"
RAW_DIR="$ROOT_DIR/data/raw"

compose() {
    docker compose "$@"
}

db_psql() {
    compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"
}

wait_for_db() {
    echo -n "Waiting for postgres"
    until compose exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; do
        echo -n "."
        sleep 1
    done
    echo " ready"
}
