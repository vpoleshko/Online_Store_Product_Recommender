\set ON_ERROR_STOP on
\timing on

CREATE INDEX IF NOT EXISTS events_visitor_idx ON raw.events (visitor_id);
CREATE INDEX IF NOT EXISTS events_item_idx    ON raw.events (item_id);
CREATE INDEX IF NOT EXISTS events_event_idx   ON raw.events (event);

CREATE INDEX IF NOT EXISTS item_properties_item_prop_idx
    ON raw.item_properties (item_id, property);

ANALYZE raw.events;
ANALYZE raw.item_properties;
ANALYZE raw.category_tree;

SELECT 'events' AS table_name, count(*) AS rows FROM raw.events
UNION ALL SELECT 'item_properties', count(*) FROM raw.item_properties
UNION ALL SELECT 'category_tree',   count(*) FROM raw.category_tree;
