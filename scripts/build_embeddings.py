import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
MODEL = "BAAI/bge-small-en-v1.5"


def dsn():
    load_dotenv(ROOT / ".env")
    return (
        f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.environ['POSTGRES_DB']}"
    )


def main(force):
    with psycopg.connect(dsn(), autocommit=True) as conn:
        for statement in (ROOT / "db/init/02_embeddings.sql").read_text().split(";"):
            if statement.strip():
                conn.execute(statement)

        n_products = conn.execute("SELECT count(*) FROM raw.products").fetchone()[0]
        n_embedded = conn.execute("SELECT count(*) FROM app.product_embeddings").fetchone()[0]

        if n_products == 0:
            raise SystemExit("raw.products is empty - run scripts/import_data.sh first")

        if n_embedded == n_products and not force:
            print(f"embeddings already in the database ({n_embedded} products), skipping")
            return

        products = pd.read_sql(
            "SELECT product_id, product_name, aisle, department FROM raw.v_products ORDER BY product_id",
            conn,
        )

    texts = (
        products["product_name"] + ". Aisle: " + products["aisle"] + ". Department: " + products["department"] + "."
    ).tolist()

    model = SentenceTransformer(MODEL)
    embeddings = model.encode(texts, batch_size=128, normalize_embeddings=True, show_progress_bar=True).astype(np.float32)

    (ROOT / "models").mkdir(exist_ok=True)
    np.save(ROOT / "models/product_embeddings_bge_small.npy", embeddings)

    with psycopg.connect(dsn()) as conn:
        register_vector(conn)
        conn.execute("TRUNCATE app.product_embeddings")

        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO app.product_embeddings (product_id, model, embedding) VALUES (%s, %s, %s)",
                [(int(p), MODEL, e) for p, e in zip(products["product_id"], embeddings)],
            )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS product_embeddings_hnsw "
            "ON app.product_embeddings USING hnsw (embedding vector_cosine_ops)"
        )
        conn.execute("ANALYZE app.product_embeddings")

    print(f"saved {len(products)} embeddings ({embeddings.shape[1]} dims)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="recompute even if the table is already filled")
    main(parser.parse_args().force)
