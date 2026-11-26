import argparse
import json
import os
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.recommender.knn import ItemKNN
from src.recommender.ranker import FEATURES, CartRecommender
from src.recommender.recipes import RecipeIndex

MODELS_DIR = ROOT / "models"


def make_engine():
    load_dotenv(ROOT / ".env")
    url = (
        f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def load_embeddings(engine):
    frame = pd.read_sql("SELECT product_id, embedding::real[] AS embedding FROM app.product_embeddings", engine)
    return frame["product_id"].to_numpy(), np.asarray(frame["embedding"].tolist(), dtype=np.float32)


def load_baskets(raw_dir, n, rng):
    orders = pd.read_csv(raw_dir / "order_products__train.csv", usecols=["order_id", "product_id"])
    baskets = orders.groupby("order_id")["product_id"].apply(list)
    baskets = baskets[baskets.map(len).between(4, 40)]
    pick = rng.choice(len(baskets), size=min(n, len(baskets)), replace=False)
    return [baskets.iloc[i] for i in pick]


def split_basket(basket, rng):
    items = list(rng.permutation(basket))
    size = int(np.clip(round(len(items) * rng.uniform(0.3, 0.7)), 2, len(items) - 1))
    return [int(p) for p in items[:size]], {int(p) for p in items[size:]}


def build_dataset(recommender, baskets, rng, label=""):
    frames, groups, hidden_sizes = [], [], []
    started = time.time()

    for i, basket in enumerate(baskets):
        cart, hidden = split_basket(basket, rng)
        frame, _ = recommender.candidates(cart)

        if frame.empty:
            continue

        frame["label"] = frame["product_id"].isin(hidden).astype(int)
        frame["group"] = i
        frame["hidden"] = len(hidden)
        frames.append(frame)

        if (i + 1) % 2000 == 0:
            print(f"  {label}: {i + 1}/{len(baskets)} baskets, {time.time() - started:.0f}s")

    return pd.concat(frames, ignore_index=True)


def metrics(frame, score, name, k=5):
    frame = frame.assign(score=score)
    precision, recall, hit, ndcg = [], [], [], []
    discounts = 1.0 / np.log2(np.arange(2, k + 2))

    for _, g in frame.groupby("group", sort=False):
        top = g.nlargest(k, "score")["label"].to_numpy()
        top10 = g.nlargest(10, "score")["label"].sum()
        hidden = g["hidden"].iloc[0]

        precision.append(top.sum() / k)
        recall.append(top10 / hidden)
        hit.append(float(top.sum() > 0))

        ideal = np.sort(g["label"].to_numpy())[::-1][:k]
        dcg = (top * discounts[: len(top)]).sum()
        idcg = (ideal * discounts[: len(ideal)]).sum()
        ndcg.append(dcg / idcg if idcg > 0 else 0.0)

    return {
        "model": name,
        f"precision@{k}": float(np.mean(precision)),
        "recall@10": float(np.mean(recall)),
        f"hit@{k}": float(np.mean(hit)),
        f"ndcg@{k}": float(np.mean(ndcg)),
    }


def main(args):
    rng = np.random.default_rng(args.seed)
    engine = make_engine()
    raw_dir = ROOT / "data/raw"

    train_csv = pd.read_csv(ROOT / "data/processed/train.csv")
    popularity = train_csv.groupby("product_id")["n_orders"].sum()

    print("fitting KNN...")
    knn = ItemKNN().fit(train_csv, history_users=[])

    print("loading embeddings and recipes...")
    emb_ids, emb = load_embeddings(engine)
    meta = pd.read_sql("SELECT product_id, aisle_id, department_id FROM raw.products", engine).set_index("product_id")
    recipes = RecipeIndex.from_db(engine)

    recommender = CartRecommender(knn, recipes, emb_ids, emb, meta, popularity)

    total = args.train + args.val + args.test
    baskets = load_baskets(raw_dir, total, rng)
    parts = {
        "train": baskets[: args.train],
        "val": baskets[args.train : args.train + args.val],
        "test": baskets[args.train + args.val :],
    }

    data = {}
    for name, part in parts.items():
        print(f"building {name} set ({len(part)} baskets)...")
        data[name] = build_dataset(recommender, part, rng, name)
        print(f"  {len(data[name])} candidate rows, positive rate {data[name]['label'].mean():.3f}")

    def groups(frame):
        return frame.groupby("group", sort=False).size().to_numpy()

    print("training LightGBM ranker...")
    ranker = lgb.LGBMRanker(
        objective="lambdarank",
        n_estimators=600,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=50,
        subsample=0.8,
        subsample_freq=1,
        colsample_bytree=0.8,
        verbose=-1,
    )
    ranker.fit(
        data["train"][FEATURES], data["train"]["label"], group=groups(data["train"]),
        eval_set=[(data["val"][FEATURES], data["val"]["label"])], eval_group=[groups(data["val"])],
        eval_at=[5], callbacks=[lgb.early_stopping(40, verbose=False)],
    )
    print(f"best iteration: {ranker.best_iteration_}")

    test = data["test"]
    popularity_score = test["log_pop"].to_numpy()
    rrf = 1.0 / (60 + test["knn_rank"]) + 0.3 / (60 + test["emb_rank"])

    results = [
        metrics(test, popularity_score, "Popular products"),
        metrics(test, test["knn_sum"].to_numpy(), "Co-purchase KNN"),
        metrics(test, test["emb_centroid"].fillna(0).to_numpy(), "Embedding similarity"),
        metrics(test, rrf.to_numpy(), "KNN + embeddings (rank fusion)"),
        metrics(test, ranker.predict(test[FEATURES]), "Hybrid + LightGBM ranker"),
    ]

    table = pd.DataFrame(results).set_index("model")
    print("\n" + table.round(4).to_string())

    pool_recall = test.groupby("group").apply(lambda g: g["label"].sum() / g["hidden"].iloc[0]).mean()
    print(f"\ncandidate pool recall (upper bound): {pool_recall:.3f}")

    importance = pd.Series(ranker.booster_.feature_importance("gain"), index=FEATURES).sort_values(ascending=False)
    print("\nfeature importance (gain share):")
    print((importance / importance.sum()).round(3).to_string())

    MODELS_DIR.mkdir(exist_ok=True)
    ranker.booster_.save_model(str(MODELS_DIR / "ranker.txt"))
    (MODELS_DIR / "ranker_metrics.json").write_text(
        json.dumps({"results": results, "pool_recall": float(pool_recall), "baskets": vars(args)}, indent=2)
    )
    print(f"\nsaved {MODELS_DIR / 'ranker.txt'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=int, default=12000)
    parser.add_argument("--val", type=int, default=2000)
    parser.add_argument("--test", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=42)
    main(parser.parse_args())
