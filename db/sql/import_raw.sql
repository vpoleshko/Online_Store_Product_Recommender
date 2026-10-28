\set ON_ERROR_STOP on
\timing on

BEGIN;

TRUNCATE raw.events, raw.item_properties, raw.category_tree;

\echo 'events.csv'
COPY raw.events (ts, visitor_id, event, item_id, transaction_id)
FROM '/data/raw/events.csv' WITH (FORMAT csv, HEADER true);

\echo 'item_properties_part1.csv'
COPY raw.item_properties (ts, item_id, property, value)
FROM '/data/raw/item_properties_part1.csv' WITH (FORMAT csv, HEADER true);

\echo 'item_properties_part2.csv'
COPY raw.item_properties (ts, item_id, property, value)
FROM '/data/raw/item_properties_part2.csv' WITH (FORMAT csv, HEADER true);

\echo 'category_tree.csv'
COPY raw.category_tree (category_id, parent_id)
FROM '/data/raw/category_tree.csv' WITH (FORMAT csv, HEADER true);

COMMIT;
