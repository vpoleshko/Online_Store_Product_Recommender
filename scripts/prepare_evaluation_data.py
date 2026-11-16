import argparse
from pathlib import Path

import numpy as np
import pandas as pd

CHUNK = 5_000_000


def build_train(raw: Path) -> pd.DataFrame:
    """User x product table from all prior orders: how many orders contained
    the product and in which (latest) order the user bought it last."""
    orders = pd.read_csv(
        raw / "orders.csv",
        usecols=["order_id", "user_id", "order_number"],
        dtype="int32",
    )
    user_of = np.zeros(orders["order_id"].max() + 1, dtype="int32")
    number_of = np.zeros_like(user_of)
    user_of[orders["order_id"].to_numpy()] = orders["user_id"].to_numpy()
    number_of[orders["order_id"].to_numpy()] = orders["order_number"].to_numpy()

    parts = []
    reader = pd.read_csv(
        raw / "order_products__prior.csv",
        usecols=["order_id", "product_id"],
        dtype="int32",
        chunksize=CHUNK,
    )
    for chunk in reader:
        chunk["user_id"] = user_of[chunk["order_id"].to_numpy()]
        chunk["order_number"] = number_of[chunk["order_id"].to_numpy()]
        parts.append(
            chunk.groupby(["user_id", "product_id"], as_index=False).agg(
                n_orders=("order_id", "size"),
                last_order_number=("order_number", "max"),
            )
        )

    train = (
        pd.concat(parts, ignore_index=True)
        .groupby(["user_id", "product_id"], as_index=False)
        .agg(n_orders=("n_orders", "sum"), last_order_number=("last_order_number", "max"))
    )
    return train.astype("int32")


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

    train = build_train(args.raw)
    test = build_test(args.raw)

    train.to_csv(args.out / "train.csv", index=False)
    test.to_csv(args.out / "test.csv", index=False)

    print("Train (user x product pairs from prior orders):", train.shape)
    print("Train users:", train["user_id"].nunique())
    print("Test (products in last orders):", test.shape)
    print("Test users:", test["user_id"].nunique())


if __name__ == "__main__":
    main()
