#!/usr/bin/env bash
. "$(dirname "$0")/_common.sh"

step() {
    echo
    echo "== $*"
}

count() {
    db_psql -tA -c "SELECT count(*) FROM $1" 2>/dev/null | tr -d '[:space:]' || echo 0
}

missing_csv() {
    for f in departments.csv aisles.csv products.csv orders.csv order_products__prior.csv order_products__train.csv; do
        [ -f "$RAW_DIR/$f" ] || return 0
    done
    return 1
}

step "1/8 Instacart data"
if missing_csv; then
    "$PYTHON" scripts/download_dataset.py "$RAW_DIR"
else
    echo "already in data/raw, skipping"
fi

step "2/8 Food.com recipes"
if [ -f "$RAW_DIR/foodcom/RAW_recipes.csv" ] && [ -f "$RAW_DIR/foodcom/RAW_interactions.csv" ]; then
    echo "already in data/raw/foodcom, skipping"
else
    "$PYTHON" scripts/download_foodcom.py "$RAW_DIR/foodcom"
fi

step "3/8 Database and schemas"
compose up -d db
wait_for_db
for f in db/init/*.sql; do
    db_psql -q < "$f" >/dev/null
done

step "4/8 Import into Postgres"
if [ "$(count raw.orders)" -gt 0 ] 2>/dev/null; then
    echo "raw tables already filled, skipping"
else
    db_psql -f /sql/import_raw.sql
    db_psql -f /sql/post_import.sql
fi

step "5/8 Product categories"
db_psql -f /sql/classify_products.sql >/dev/null
echo "done"

step "6/8 Evaluation tables (data/processed)"
if [ -f data/processed/train.csv ]; then
    echo "already built, skipping"
else
    "$PYTHON" scripts/prepare_evaluation_data.py
fi

step "7/8 Product embeddings"
"$PYTHON" scripts/build_embeddings.py

step "8/8 Recipes"
if [ "$(count app.recipes)" -gt 0 ] 2>/dev/null; then
    echo "recipes already in the database, skipping"
else
    "$PYTHON" scripts/build_recipes.py
fi

if [ ! -f models/ranker.txt ]; then
    step "Ranker (models/ranker.txt is missing)"
    "$PYTHON" scripts/train_ranker.py
fi

echo
echo "Ready. Start the shop with: scripts/run_api.sh"
