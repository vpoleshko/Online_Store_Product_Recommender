# Online_Store_Product_Recommender
Personalized product recommendations for online stores.

Dataset: [Retailrocket recommender system dataset](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset).

## Structure

```
db/init/        SQL run on first postgres start (schemas, raw tables)
db/sql/         SQL used by scripts (CSV import, indexes)
data/raw/       downloaded CSVs (git-ignored)
data/processed/ intermediate datasets (git-ignored)
notebooks/      Jupyter notebooks (EDA, experiments)
models/         trained models (git-ignored)
src/recommender ML: item-based CF / KNN
src/api         backend API
frontend/       UI
scripts/        sh scripts (run from Git Bash / WSL / Linux / macOS)
```

## Quick start

Requires Docker, Python 3.10+, bash (on Windows: Git Bash or WSL).

```bash
cp .env.example .env            # optional, scripts create it automatically
scripts/setup_venv.sh           # .venv + requirements.txt
source .venv/bin/activate       # Windows Git Bash: source .venv/Scripts/activate

scripts/up.sh                   # start postgres
scripts/download_data.sh        # Kaggle -> data/raw/*.csv
scripts/import_data.sh          # data/raw -> postgres (raw schema)

jupyter lab notebooks/
```

Other scripts:

| Script | What it does |
|---|---|
| `scripts/psql.sh` | psql shell inside the container |
| `scripts/down.sh` | stop containers, keep data |
| `scripts/reset_db.sh` | delete the DB volume and recreate schema from `db/init` |

## Database

| Table | Source | Rows (approx.) |
|---|---|---|
| `raw.events` | events.csv | 2.7M |
| `raw.item_properties` | item_properties_part1/2.csv | 20M |
| `raw.category_tree` | category_tree.csv | 1.7K |

`raw.v_events` — events with `ts` converted to `timestamptz`.
Schema `app` is reserved for application tables (users, survey, recommendations).

Connection: `postgresql://recommender:recommender@localhost:5432/recommender`
