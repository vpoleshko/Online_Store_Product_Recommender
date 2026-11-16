\set ON_ERROR_STOP on
\timing on

CREATE INDEX IF NOT EXISTS orders_user_idx ON raw.orders (user_id);
CREATE INDEX IF NOT EXISTS orders_eval_idx ON raw.orders (eval_set);

CREATE INDEX IF NOT EXISTS op_prior_order_idx   ON raw.order_products_prior (order_id);
CREATE INDEX IF NOT EXISTS op_prior_product_idx ON raw.order_products_prior (product_id);
CREATE INDEX IF NOT EXISTS op_train_order_idx   ON raw.order_products_train (order_id);
CREATE INDEX IF NOT EXISTS op_train_product_idx ON raw.order_products_train (product_id);

CREATE INDEX IF NOT EXISTS products_aisle_idx      ON raw.products (aisle_id);
CREATE INDEX IF NOT EXISTS products_department_idx ON raw.products (department_id);

ANALYZE raw.departments;
ANALYZE raw.aisles;
ANALYZE raw.products;
ANALYZE raw.orders;
ANALYZE raw.order_products_prior;
ANALYZE raw.order_products_train;

SELECT 'departments' AS table_name, count(*) AS rows FROM raw.departments
UNION ALL SELECT 'aisles',               count(*) FROM raw.aisles
UNION ALL SELECT 'products',             count(*) FROM raw.products
UNION ALL SELECT 'orders',               count(*) FROM raw.orders
UNION ALL SELECT 'order_products_prior', count(*) FROM raw.order_products_prior
UNION ALL SELECT 'order_products_train', count(*) FROM raw.order_products_train;
