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
models/         product embeddings, LightGBM ranker (ranker.txt)
src/recommender ML: item-based CF / KNN, popularity baseline, metrics, recipes, hybrid ranker
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

### One-command setup

```bash
scripts/setup_venv.sh && source .venv/bin/activate
scripts/setup_all.sh      # downloads data, fills the database, builds embeddings and recipes
scripts/run_api.sh
```

`setup_all.sh` can be re-run at any time: every step that is already done is skipped.
The first run downloads about 1 GB, and computing the embeddings takes about 10 minutes on a CPU.

### Run the shop (backend + frontend)

Needs: the database with embeddings (`notebooks/03_embeddings.ipynb`), `data/processed/train.csv`,
the recipe tables (see below) and `models/ranker.txt` (committed; without it a simple blend is used).

```bash
scripts/run_api.sh        # http://127.0.0.1:8765  (start-up takes ~1 min: trains KNN, loads the models)
```

The page searches products by text embeddings, you add products to the cart, and after pressing **Buy** the app shows
what else to buy and which recipes the order is close to, with the missing ingredients one click from the cart.
Use `127.0.0.1` rather than `localhost` if another service on your machine listens on the same port.

| Endpoint | Description |
|---|---|
| `GET /api/search?q=...` | hybrid search: pgvector candidates re-ranked by embedding similarity, word match, exact/prefix name match and popularity (weights in `src/recommender/search.py`) |
| `GET /api/popular` | most ordered products |
| `POST /api/recommend` | `{"product_ids": [...], "k": 10}` -> `{"products": [...with reasons], "recipes": [...]}` |

### How the recommendation works

```
cart ─┬─ co-purchase KNN (what is bought together)     ─┐
      ├─ embedding neighbours (what is similar)         ─┼─> candidates ─> LightGBM ranker ─> top-k + reasons
      └─ recipes that the cart nearly covers (missing   ─┘
         ingredients)
cart ───> recipe matching ───────────────────────────────────> "Cook something with your order"
```

One-off preparation (needed once per database):

```bash
docker compose exec -T db psql -U recommender -d recommender < db/init/03_recipes.sql   # tables
docker compose exec -T db psql -U recommender -d recommender < db/sql/classify_products.sql  # categories for the UI
python3 scripts/build_recipes.py     # Food.com recipes -> Postgres, ingredients linked to products via embeddings
python3 scripts/train_ranker.py      # trains and evaluates the ranker, writes models/ranker.txt
```

`build_recipes.py` needs the Food.com files `RAW_recipes.csv` and `RAW_interactions.csv`
(Kaggle `shuyangli94/food-com-recipes-and-user-interactions`) in `data/raw/foodcom/`.
Recipes are kept if their rating is at least 4.0 (3+ reviews) and at least 80% of their ingredients can be bought in the store.

Ranker results on 3000 held-out Instacart baskets (a random 30-70% of the basket is the "cart", the rest must be predicted):

| Model | Precision@5 | NDCG@5 |
|---|---|---|
| Popular products | 0.060 | 0.122 |
| Co-purchase KNN | 0.070 | 0.135 |
| Embedding similarity | 0.004 | 0.007 |
| KNN + embeddings (rank fusion) | 0.068 | 0.126 |
| **Hybrid + LightGBM ranker** | **0.081** | **0.166** |

Embeddings alone predict almost nothing here because Instacart baskets contain complements and re-orders,
not look-alikes. Recipes are not measurable on this dataset (nobody bought "for a recipe"), so they are a product feature,
not a metric gain.

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
