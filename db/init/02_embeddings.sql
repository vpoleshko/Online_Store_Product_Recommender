CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.product_embeddings (
    product_id INT          PRIMARY KEY,
    model      TEXT         NOT NULL,
    embedding  vector(384)  NOT NULL
);
