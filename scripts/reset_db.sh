#!/usr/bin/env bash
. "$(dirname "$0")/_common.sh"

read -r -p "This deletes ALL database data. Continue? [y/N] " answer
case "$answer" in
    y|Y) ;;
    *) echo "Aborted"; exit 1 ;;
esac

compose down -v
compose up -d db
wait_for_db
echo "Database recreated. Run scripts/import_data.sh to load the dataset."
