import argparse
from pathlib import Path

import numpy as np
import pandas as pd

CHUNK = 5_000_000


def aggregate(chunk: pd.DataFrame) -> pd.DataFrame:
    return chunk.groupby(["user_id", "product_id"], as_index=False).agg(
        n_orders=("order_id", "size"),
        last_order_number=("order_number", "max"),
    )


def combine(parts: list) -> pd.DataFrame:
    table = (
        pd.concat(parts, ignore_index=True)
        .groupby(["user_id", "product_id"], as_index=False)
        .agg(n_orders=("n_orders", "sum"), last_order_number=("last_order_number", "max"))
    )
    return table.astype("int32")


def build_train_tables(raw: Path):
    """User x product tables from `prior` orders.

    train:       all prior orders (n_orders, last_order_number per user x product)
    train_final: all prior orders except each user's last prior order
    validation:  products of each user's last prior order (labels for tuning)
    """
    orders = pd.read_csv(raw / "orders.csv", usecols=["order_id", "user_id", "order_number", "eval_set"])

    user_of = np.zeros(orders["order_id"].max() + 1, dtype="int32")
    number_of = np.zeros_like(user_of)
    user_of[orders["order_id"].to_numpy()] = orders["user_id"].to_numpy()
    number_of[orders["order_id"].to_numpy()] = orders["order_number"].to_numpy()

    last_prior = np.zeros(orders["user_id"].max() + 1, dtype="int32")
    per_user = orders[orders["eval_set"] == "prior"].groupby("user_id")["order_number"].max()
    last_prior[per_user.index.to_numpy()] = per_user.to_numpy()

    train_parts, final_parts, validation_parts = [], [], []
    reader = pd.read_csv(
        raw / "order_products__prior.csv",
        usecols=["order_id", "product_id"],
        dtype="int32",
        chunksize=CHUNK,
    )
    for chunk in reader:
        chunk["user_id"] = user_of[chunk["order_id"].to_numpy()]
        chunk["order_number"] = number_of[chunk["order_id"].to_numpy()]
        is_last = (chunk["order_number"] == last_prior[chunk["user_id"].to_numpy()]).to_numpy()

        train_parts.append(aggregate(chunk))
        final_parts.append(aggregate(chunk[~is_last]))
        validation_parts.append(chunk.loc[is_last, ["user_id", "product_id"]].drop_duplicates())

    validation = pd.concat(validation_parts, ignore_index=True).drop_duplicates().astype("int32")
    return combine(train_parts), combine(final_parts), validation


def build_test(raw: Path) -> pd.DataFrame:
    """Products of each user's last order (the order labelled `train` in Instacart)."""
    orders = pd.read_csv(raw / "orders.csv", usecols=["order_id", "user_id", "eval_set"])
    last = orders[orders["eval_set"] == "train"][["order_id", "user_id"]]
    lines = pd.read_csv(raw / "order_products__train.csv", usecols=["order_id", "product_id"])
    return lines.merge(last, on="order_id")[["user_id", "product_id"]].astype("int32")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("data/processed"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    train, train_final, validation = build_train_tables(args.raw)
    test = build_test(args.raw)

    train.to_csv(args.out / "train.csv", index=False)
    test.to_csv(args.out / "test.csv", index=False)
    train_final.to_csv(args.out / "train_final.csv", index=False)
    validation.to_csv(args.out / "validation.csv", index=False)

    print("Train (all prior orders):", train.shape, "users:", train["user_id"].nunique())
    print("Test (last orders):", test.shape, "users:", test["user_id"].nunique())
    print("Train final (prior without last prior order):", train_final.shape, "users:", train_final["user_id"].nunique())
    print("Validation (last prior order):", validation.shape, "users:", validation["user_id"].nunique())


if __name__ == "__main__":
    main()
