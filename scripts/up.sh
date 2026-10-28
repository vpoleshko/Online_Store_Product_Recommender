#!/usr/bin/env bash
. "$(dirname "$0")/_common.sh"

compose up -d db
wait_for_db
echo "Postgres: postgresql://$POSTGRES_USER:***@localhost:$POSTGRES_PORT/$POSTGRES_DB"
