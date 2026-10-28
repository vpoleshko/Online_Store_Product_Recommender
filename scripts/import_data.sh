#!/usr/bin/env bash
. "$(dirname "$0")/_common.sh"

for f in events.csv item_properties_part1.csv item_properties_part2.csv category_tree.csv; do
    if [ ! -f "$RAW_DIR/$f" ]; then
        echo "Missing $RAW_DIR/$f - run scripts/download_data.sh first"
        exit 1
    fi
done

compose up -d db
wait_for_db

echo "== Importing CSVs =="
db_psql -f /sql/import_raw.sql

echo "== Building indexes =="
db_psql -f /sql/post_import.sql
