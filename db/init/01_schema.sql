CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS raw.events (
    ts             BIGINT  NOT NULL,
    visitor_id     BIGINT  NOT NULL,
    event          TEXT    NOT NULL,
    item_id        BIGINT  NOT NULL,
    transaction_id BIGINT
);

CREATE TABLE IF NOT EXISTS raw.item_properties (
    ts       BIGINT NOT NULL,
    item_id  BIGINT NOT NULL,
    property TEXT   NOT NULL,
    value    TEXT
);

CREATE TABLE IF NOT EXISTS raw.category_tree (
    category_id BIGINT PRIMARY KEY,
    parent_id   BIGINT
);

CREATE OR REPLACE VIEW raw.v_events AS
SELECT to_timestamp(ts / 1000.0) AS event_time,
       visitor_id, event, item_id, transaction_id
FROM raw.events;
