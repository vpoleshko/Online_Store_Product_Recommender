#!/usr/bin/env bash
. "$(dirname "$0")/_common.sh"

for f in departments.csv aisles.csv products.csv orders.csv order_products__prior.csv order_products__train.csv; do
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
