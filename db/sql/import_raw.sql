\set ON_ERROR_STOP on
\timing on

BEGIN;

TRUNCATE raw.departments, raw.aisles, raw.products, raw.orders,
         raw.order_products_prior, raw.order_products_train;

\echo 'departments.csv'
COPY raw.departments (department_id, department)
FROM '/data/raw/departments.csv' WITH (FORMAT csv, HEADER true);

\echo 'aisles.csv'
COPY raw.aisles (aisle_id, aisle)
FROM '/data/raw/aisles.csv' WITH (FORMAT csv, HEADER true);

\echo 'products.csv'
COPY raw.products (product_id, product_name, aisle_id, department_id)
FROM '/data/raw/products.csv' WITH (FORMAT csv, HEADER true);

\echo 'orders.csv'
COPY raw.orders (order_id, user_id, eval_set, order_number, order_dow, order_hour_of_day, days_since_prior_order)
FROM '/data/raw/orders.csv' WITH (FORMAT csv, HEADER true);

\echo 'order_products__prior.csv'
COPY raw.order_products_prior (order_id, product_id, add_to_cart_order, reordered)
FROM '/data/raw/order_products__prior.csv' WITH (FORMAT csv, HEADER true);

\echo 'order_products__train.csv'
COPY raw.order_products_train (order_id, product_id, add_to_cart_order, reordered)
FROM '/data/raw/order_products__train.csv' WITH (FORMAT csv, HEADER true);

COMMIT;
