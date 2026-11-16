CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS raw.departments (
    department_id INT  PRIMARY KEY,
    department    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.aisles (
    aisle_id INT  PRIMARY KEY,
    aisle    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.products (
    product_id    INT  PRIMARY KEY,
    product_name  TEXT NOT NULL,
    aisle_id      INT  NOT NULL,
    department_id INT  NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.orders (
    order_id               INT      PRIMARY KEY,
    user_id                INT      NOT NULL,
    eval_set               TEXT     NOT NULL,
    order_number           INT      NOT NULL,
    order_dow              SMALLINT NOT NULL,
    order_hour_of_day      SMALLINT NOT NULL,
    days_since_prior_order REAL
);

CREATE TABLE IF NOT EXISTS raw.order_products_prior (
    order_id          INT      NOT NULL,
    product_id        INT      NOT NULL,
    add_to_cart_order INT      NOT NULL,
    reordered         SMALLINT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.order_products_train (
    order_id          INT      NOT NULL,
    product_id        INT      NOT NULL,
    add_to_cart_order INT      NOT NULL,
    reordered         SMALLINT NOT NULL
);

CREATE OR REPLACE VIEW raw.v_order_products AS
SELECT 'prior'::text AS eval_set, order_id, product_id, add_to_cart_order, reordered
FROM raw.order_products_prior
UNION ALL
SELECT 'train'::text AS eval_set, order_id, product_id, add_to_cart_order, reordered
FROM raw.order_products_train;

CREATE OR REPLACE VIEW raw.v_products AS
SELECT p.product_id, p.product_name, a.aisle, d.department
FROM raw.products p
JOIN raw.aisles a      USING (aisle_id)
JOIN raw.departments d USING (department_id);
