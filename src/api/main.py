import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

from src.recommender.knn import ItemKNN
from src.recommender.ranker import CartRecommender
from src.recommender.recipes import RecipeIndex
from src.recommender.search import ProductSearch

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

MODEL_NAME = "BAAI/bge-small-en-v1.5"
ANN_CANDIDATES = 100

state = {}


def make_engine():
    url = (
        f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url, pool_pre_ping=True)


def load_booster():
    path = ROOT / "models" / "ranker.txt"

    if not path.exists():
        print("models/ranker.txt not found - using the simple blend (run scripts/train_ranker.py)")
        return None

    try:
        import lightgbm as lgb
    except ImportError as error:
        raise RuntimeError(
            "models/ranker.txt needs the lightgbm package: pip install lightgbm"
        ) from error

    return lgb.Booster(model_file=str(path))


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = make_engine()

    products = pd.read_sql(
    """
    SELECT
        p.product_id,
        p.product_name,
        p.aisle,
        p.department,
        COALESCE(c.category, p.department) AS category
    FROM raw.v_products p
    LEFT JOIN app.product_categories c
        ON p.product_id = c.product_id
    """,
    engine
    ).set_index("product_id")

    train = pd.read_csv(ROOT / "data/processed/train.csv")
    popularity = train.groupby("product_id")["n_orders"].sum().sort_values(ascending=False)
    knn = ItemKNN().fit(train, history_users=[])

    emb_frame = pd.read_sql("SELECT product_id, embedding::real[] AS embedding FROM app.product_embeddings", engine)
    emb_ids = emb_frame["product_id"].to_numpy()
    emb = np.asarray(emb_frame["embedding"].tolist(), dtype=np.float32)
    meta = pd.read_sql("SELECT product_id, aisle_id, department_id FROM raw.products", engine).set_index("product_id")

    recipes = RecipeIndex.from_db(engine)
    print(f"{len(recipes.recipes)} recipes loaded")

    booster = load_booster()
    recommender = CartRecommender(knn, recipes, emb_ids, emb, meta, popularity, booster=booster)

    state.update(
        engine=engine,
        products=products,
        popularity=popularity,
        knn=knn,
        recipes=recipes,
        recommender=recommender,
        ranker_info=describe_ranker(booster),
        search=ProductSearch(products, popularity, emb_ids, emb),
        model=SentenceTransformer(MODEL_NAME),
    )
    print("API ready")
    yield
    engine.dispose()
    state.clear()


app = FastAPI(title="Product recommender", lifespan=lifespan)


def product_json(product_id, **extra):
    row = state["products"].loc[int(product_id)]
    return {
        "product_id": int(product_id),
        "name": row["product_name"],
        "aisle": row["aisle"],
        "department": row["department"],
        "category": row["category"],
        **extra,
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "products": len(state["products"])}


@app.get("/api/popular")
def popular(limit: int = Query(24, ge=1, le=100)):
    return [product_json(p) for p in state["popularity"].index[:limit]]


@app.get("/api/search")
def search(q: str = Query(..., min_length=1, max_length=200), limit: int = Query(24, ge=1, le=100)):
    vector = state["model"].encode(q.strip(), normalize_embeddings=True)
    literal = "[" + ",".join(f"{x:.6f}" for x in vector) + "]"

    with state["engine"].connect() as conn:
        conn.execute(text("SET LOCAL hnsw.ef_search = 400"))
        rows = conn.execute(
            text(
                """
                SELECT product_id, 1 - (embedding <=> CAST(:q AS vector)) AS similarity
                FROM app.product_embeddings
                ORDER BY embedding <=> CAST(:q AS vector)
                LIMIT :k
                """
            ),
            {"q": literal, "k": ANN_CANDIDATES},
        ).all()

    ranked = state["search"].rank(q, vector, rows, limit=limit)

    return [
        product_json(pid, score=round(score, 3), similarity=round(sim, 3))
        for pid, score, sim in ranked
    ]


class CartIn(BaseModel):
    product_ids: list[int] = Field(min_length=1, max_length=100)
    k: int = Field(10, ge=1, le=30)


@app.post("/api/recommend")
def recommend(cart: CartIn):
    ids = sorted(set(cart.product_ids))
    unknown = [p for p in ids if p not in state["products"].index]

    if unknown:
        raise HTTPException(status_code=404, detail=f"Unknown product ids: {unknown}")

    recommender = state["recommender"]
    recipes = state["recipes"]

    results, stats = recommender.recommend(ids, k=cart.k)

    products = []
    for position, (pid, score, info, row) in enumerate(results, start=1):
        products.append(
            product_json(
                pid,
                model_rank=position,
                model_score=round(score, 3),
                knn_rank=int(row["knn_rank"]) + 1 if row["in_knn"] else None,
                signals=signals(row),
                reasons=explain(info, row),
            )
        )

    matches = recipes.match(ids, k=4)
    cooking = recipes.details(state["engine"], ids, matches)

    for recipe in cooking:
        for ingredient in recipe["ingredients"]:
            if ingredient["product_id"] is not None:
                ingredient["product"] = product_json(ingredient["product_id"])

    return {
        "model": state["ranker_info"],
        "pipeline": {**stats, "recipes_found": len(cooking), "cart_size": len(ids)},
        "products": products,
        "recipes": cooking,
    }


def signals(row):
    found = []

    if row["in_knn"]:
        found.append(
            {
                "source": "knn",
                "text": f"Co-purchase KNN: #{int(row['knn_rank']) + 1}, linked to {int(row['knn_count'])} cart item(s)",
            }
        )

    if row["in_emb"]:
        found.append(
            {
                "source": "embedding",
                "text": f"Embeddings: #{int(row['emb_rank']) + 1}, similarity {row['emb_centroid']:.2f}",
            }
        )

    if row["in_recipe"]:
        found.append(
            {"source": "recipe", "text": f"Recipes: completes {int(row['recipe_count'])} recipe(s)"}
        )

    return found


def describe_ranker(booster):
    if booster is None:
        return {"active": False, "name": "Simple blend (ranker not loaded)"}

    gains = booster.feature_importance("gain")
    shares = sorted(zip(booster.feature_name(), gains / gains.sum()), key=lambda item: -item[1])

    info = {
        "active": True,
        "name": "LightGBM LambdaRank ranker",
        "trees": booster.num_trees(),
        "features": len(shares),
        "importance": [{"feature": name, "share": round(float(share), 3)} for name, share in shares[:6]],
    }

    metrics_path = ROOT / "models" / "ranker_metrics.json"
    if metrics_path.exists():
        results = json.loads(metrics_path.read_text())["results"]
        wanted = ("Popular products", "Co-purchase KNN", "Hybrid + LightGBM ranker")
        info["evaluation"] = [
            {
                "model": row["model"],
                "precision_at_5": round(row["precision@5"], 3),
                "ndcg_at_5": round(row["ndcg@5"], 3),
            }
            for row in results
            if row["model"] in wanted
        ]

    return info


def product_name(product_id):
    products = state["products"]
    return products.at[product_id, "product_name"] if product_id in products.index else str(product_id)


def explain(info, row):
    reasons = []

    if info["knn_anchor"] is not None and row["knn_rank"] < 25:
        reasons.append(
            {"type": "together", "text": f"Often bought with {product_name(info['knn_anchor'])}"}
        )

    if info["recipe_row"] is not None:
        recipe = state["recipes"].recipes.at[info["recipe_row"], "name"]
        reasons.append({"type": "recipe", "text": f"Needed for “{recipe}”"})

    if info["emb_anchor"] is not None and row["emb_rank"] < 25:
        reasons.append({"type": "similar", "text": f"Similar to {product_name(info['emb_anchor'])}"})

    return reasons or [{"type": "popular", "text": "Popular in the store"}]


app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
