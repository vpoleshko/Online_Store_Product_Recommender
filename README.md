# Online_Store_Product_Recommender
Personalized product recommendations for online stores.

Dataset: [Instacart Market Basket Analysis](https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis)
(original competition: https://www.kaggle.com/competitions/instacart-market-basket-analysis).

Why Instacart: real shopping baskets, real product names,
aisles and departments, and historical purchase data.

All current models and evaluation results presented
in this project are based exclusively on the Instacart
Market Basket Analysis dataset.

## Structure

```
db/init/        SQL run on first postgres start (schemas, raw tables)
db/sql/         SQL used by scripts (CSV import, indexes)
data/raw/       downloaded CSVs (git-ignored)
data/processed/ train/test tables built from raw (git-ignored)
notebooks/      Jupyter notebooks (EDA, model comparison)
models/         trained models (git-ignored)
src/recommender ML: item-based CF / KNN, popularity baseline, metrics
src/api         FastAPI backend (search, recommendations, serves frontend/)
frontend/       UI (plain HTML/CSS/JS)
tests/          pytest tests
scripts/        sh scripts (run from Git Bash / WSL / Linux / macOS)
```

## Quick start

Requires Docker, Python 3.10+, bash (on Windows: Git Bash or WSL).

```bash
cp .env.example .env            # optional, scripts create it automatically
scripts/setup_venv.sh           # .venv + requirements.txt
source .venv/bin/activate       # Windows Git Bash: source .venv/Scripts/activate

scripts/download_data.sh        # Kaggle -> data/raw/*.csv
scripts/up.sh                   # start postgres
scripts/import_data.sh          # data/raw -> postgres (raw schema)

python3 scripts/prepare_evaluation_data.py   # data/processed/train.csv, test.csv
python3 -m scripts.compare_models            # Baseline vs Repeat vs KNN

jupyter lab notebooks/
```

### Run the shop (backend + frontend)

Needs the database with embeddings (`notebooks/03_embeddings.ipynb`) and `data/processed/train.csv`.

```bash
scripts/run_api.sh        # http://127.0.0.1:8765  (start-up takes ~1 min: trains KNN, loads the model)
```

The page searches products by text embeddings, you add products to the cart, and after pressing **Buy** the app
shows what else to buy (item-based KNN on past orders + embedding similarity).
Use `127.0.0.1` rather than `localhost` if another service on your machine listens on the same port.

| Endpoint | Description |
|---|---|
| `GET /api/search?q=...` | semantic product search (pgvector) |
| `GET /api/popular` | most ordered products |
| `POST /api/recommend` | `{"product_ids": [...], "k": 10}` -> recommendations for the cart |

If the database volume was created for the old dataset, recreate it first: `scripts/reset_db.sh`
(schema is only applied on an empty volume).

Other scripts:

| Script | What it does |
|---|---|
| `scripts/psql.sh` | psql shell inside the container |
| `scripts/down.sh` | stop containers, keep data |
| `scripts/reset_db.sh` | delete the DB volume and recreate schema from `db/init` |

## Database

| Table | Source | Rows (approx.) |
|---|---|---|
| `raw.departments` | departments.csv | 21 |
| `raw.aisles` | aisles.csv | 134 |
| `raw.products` | products.csv | 49.7K |
| `raw.orders` | orders.csv | 3.4M |
| `raw.order_products_prior` | order_products__prior.csv | 32M |
| `raw.order_products_train` | order_products__train.csv | 1.4M |

Views: `raw.v_products` (product + aisle + department names), `raw.v_order_products` (prior + train lines with `eval_set`).
Schema `app` is reserved for application tables (users, survey, recommendations).

Connection: `postgresql://recommender:recommender@localhost:5432/recommender`

## Evaluation setup

- `train.csv` — one row per user x product from all `prior` orders (`n_orders`, `last_order_number`).
- `test.csv` — products of each user's last order (`eval_set = train` in Instacart), used as ground truth.
- Models: `Baseline` (most popular products), `Repeat` (user's most frequently bought products), `KNN` (item-based cosine k-NN with popularity fallback).
- Metrics: Precision@5, Macro-F1@5.
