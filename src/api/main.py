import os
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

from src.recommender.cart import copurchase_items, fuse
from src.recommender.knn import ItemKNN

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

MODEL_NAME = "BAAI/bge-small-en-v1.5"

state = {}


def make_engine():
    url = (
        f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url, pool_pre_ping=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = make_engine()

    products = pd.read_sql(
        "SELECT product_id, product_name, aisle, department FROM raw.v_products", engine
    ).set_index("product_id")

    train = pd.read_csv(ROOT / "data/processed/train.csv")
    popularity = train.groupby("product_id")["n_orders"].sum().sort_values(ascending=False)
    knn = ItemKNN().fit(train, history_users=[])

    state.update(
        engine=engine,
        products=products,
        popularity=popularity,
        knn=knn,
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
            {"q": literal, "k": limit},
        ).all()

    return [product_json(pid, similarity=round(float(sim), 3)) for pid, sim in rows]


class CartIn(BaseModel):
    product_ids: list[int] = Field(min_length=1, max_length=100)
    k: int = Field(10, ge=1, le=30)


@app.post("/api/recommend")
def recommend(cart: CartIn):
    ids = sorted(set(cart.product_ids))
    unknown = [p for p in ids if p not in state["products"].index]

    if unknown:
        raise HTTPException(status_code=404, detail=f"Unknown product ids: {unknown}")

    together = copurchase_items(state["knn"], ids, limit=50)

    with state["engine"].connect() as conn:
        similar = [
            r[0]
            for r in conn.execute(
                text(
                    """
                    SELECT e.product_id
                    FROM app.product_embeddings e,
                         (SELECT avg(embedding) AS v FROM app.product_embeddings WHERE product_id = ANY(:ids)) q
                    WHERE e.product_id <> ALL(:ids)
                    ORDER BY e.embedding <=> q.v
                    LIMIT 50
                    """
                ),
                {"ids": ids},
            )
        ]

    return [
        product_json(pid, sources=sources)
        for pid, sources in fuse(together, similar, k=cart.k)
    ]


app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
