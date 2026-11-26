CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.recipes (
    recipe_id   INT  PRIMARY KEY,
    name        TEXT NOT NULL,
    minutes     INT,
    n_steps     INT,
    n_reviews   INT,
    rating      REAL,
    description TEXT,
    steps       TEXT[]
);

CREATE TABLE IF NOT EXISTS app.recipe_ingredients (
    recipe_id  INT     NOT NULL REFERENCES app.recipes(recipe_id) ON DELETE CASCADE,
    ingredient TEXT    NOT NULL,
    is_staple  BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (recipe_id, ingredient)
);

CREATE TABLE IF NOT EXISTS app.ingredient_products (
    ingredient TEXT    NOT NULL,
    product_id INT     NOT NULL,
    similarity REAL    NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (ingredient, product_id)
);

CREATE INDEX IF NOT EXISTS ingredient_products_product_idx
    ON app.ingredient_products (product_id);
