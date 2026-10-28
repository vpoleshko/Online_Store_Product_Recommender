#!/usr/bin/env bash
. "$(dirname "$0")/_common.sh"

compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"
