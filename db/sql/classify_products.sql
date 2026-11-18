\set ON_ERROR_STOP on
\timing on


CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.product_categories (
    product_id INTEGER PRIMARY KEY REFERENCES raw.products(product_id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    classification_source TEXT NOT NULL DEFAULT 'automatic'
);

WITH source AS (
    SELECT
        p.product_id,
        lower(p.product_name) AS name,
        lower(a.aisle) AS aisle,
        lower(d.department) AS department
    FROM raw.products p
    JOIN raw.aisles a ON a.aisle_id = p.aisle_id
    JOIN raw.departments d ON d.department_id = p.department_id
),
classified AS (
    SELECT
        product_id,
        CASE
            WHEN department = 'meat seafood' THEN
                CASE
                    WHEN name ~ '(shrimp|prawn|salmon|tuna|tilapia|cod|halibut|trout|sardine|anchov|crab|lobster|scallop|clam|mussel|oyster|squid|octopus|seafood|fish|pollock|mahi|flounder|haddock|snapper|catfish|swordfish|herring|mackerel|sole fillet|ceviche|calamari)'
                        THEN 'Seafood'
                    WHEN name ~ '(bacon|beef|pork|chicken|turkey|sausage|ham|steak|lamb|veal|meatball|hot dog|brisket|prosciutto|pepperoni|salami|duck|buffalo|bison|ribs|ground meat|ground chuck|poultry|pastrami|chorizo|pancetta)'
                        THEN 'Meat'
                    WHEN aisle ~ '(seafood|fish)'
                        THEN 'Seafood'
                    WHEN aisle ~ '(meat|poultry|bacon|sausage|hot dog)'
                        THEN 'Meat'
                    ELSE 'Meat & Seafood'
                END

            WHEN department = 'produce' THEN
                CASE
                    WHEN aisle ~ '(fruit|berries)' THEN 'Fruit'
                    WHEN aisle ~ '(vegetable|herb|salad|greens)' THEN 'Vegetables'
                    ELSE 'Produce'
                END

            WHEN department = 'dairy eggs' THEN
                CASE
                    WHEN aisle ~ 'egg' THEN 'Eggs'
                    ELSE 'Dairy'
                END

            WHEN department = 'frozen' THEN
                CASE
                    WHEN aisle ~ '(seafood|fish)'
                         AND name ~ '(shrimp|salmon|tuna|cod|fish|seafood|prawn|tilapia|crab|scallop)'
                        THEN 'Seafood'
                    WHEN aisle ~ '(meat|seafood)'
                         AND name ~ '(chicken|beef|bacon|sausage|pork|turkey|meatball|steak)'
                        THEN 'Meat'
                    ELSE 'Frozen Foods'
                END

            WHEN department = 'bakery' THEN 'Bakery'
            WHEN department = 'beverages' THEN 'Beverages'
            WHEN department = 'snacks' THEN 'Snacks'
            WHEN department = 'breakfast' THEN 'Breakfast'
            WHEN department = 'pantry' THEN 'Pantry'
            WHEN department = 'canned goods' THEN 'Canned Goods'
            WHEN department = 'deli' THEN 'Deli'
            WHEN department = 'dry goods pasta' THEN 'Pasta & Grains'
            WHEN department = 'household' THEN 'Household'
            WHEN department = 'personal care' THEN 'Personal Care'
            WHEN department = 'babies' THEN 'Baby Products'
            WHEN department = 'pets' THEN 'Pet Supplies'
            WHEN department = 'international' THEN 'International Foods'
            WHEN department = 'alcohol' THEN 'Alcohol'
            WHEN department = 'bulk' THEN 'Bulk Foods'

            ELSE initcap(department)
        END AS category
    FROM source
)

INSERT INTO app.product_categories (
    product_id,
    category,
    classification_source
)
SELECT product_id, category, 'automatic'
FROM classified

ON CONFLICT (product_id) DO UPDATE
SET
    category = EXCLUDED.category,
    classification_source = 'automatic'
WHERE app.product_categories.classification_source = 'automatic';


SELECT
    category,
    COUNT(*) AS products
FROM app.product_categories
GROUP BY category
ORDER BY products DESC, category;
