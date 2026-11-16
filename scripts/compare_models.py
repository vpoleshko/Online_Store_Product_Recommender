import argparse
from pathlib import Path

import pandas as pd

from src.recommender.baseline import popular_products, recommend_popular, user_frequent_products
from src.recommender.evaluation import f1_at_k, precision_at_k
from src.recommender.knn import ItemKNN

K = 5


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--users", type=int, default=5000, help="evaluation sample size, 0 = all users")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--split",
        choices=["test", "validation"],
        default="test",
        help="validation = train_final.csv / validation.csv (for tuning parameters), test = train.csv / test.csv",
    )
    args = parser.parse_args()

    train_file, test_file = (
        ("train.csv", "test.csv") if args.split == "test" else ("train_final.csv", "validation.csv")
    )
    train = pd.read_csv(args.data_dir / train_file)
    test = pd.read_csv(args.data_dir / test_file)

    actual = test.groupby("user_id")["product_id"].apply(set).to_dict()

    users = sorted(set(actual) & set(train["user_id"].unique()))

    if args.users and len(users) > args.users:
        users = sorted(pd.Series(users).sample(args.users, random_state=args.seed))

    if not users:
        print("No users available for evaluation.")
        return

    popular = popular_products(train)
    frequent = user_frequent_products(train[train["user_id"].isin(set(users))])

    knn = ItemKNN().fit(train, history_users=users)

    scores = {name: {"precision": [], "f1": []} for name in ("Baseline", "Repeat", "KNN")}
    knn_from_neighbors = 0

    for user in users:
        a = actual[user]

        recs = {
            "Baseline": recommend_popular(popular, k=K),
            "Repeat": ([int(p) for p in frequent.get(user, [])] + recommend_popular(popular, k=K))[:K],
            "KNN": knn.recommend(user, k=K),
        }

        seeds_known = any(int(p) in knn.item_to_idx for p in knn.user_history.get(user, [])[: knn.max_seeds])
        knn_from_neighbors += seeds_known

        for name, r in recs.items():
            scores[name]["precision"].append(precision_at_k(r, a, K))
            scores[name]["f1"].append(f1_at_k(r, a, K))

    mean = {n: {m: sum(v) / len(users) for m, v in d.items()} for n, d in scores.items()}
    improvement = mean["KNN"]["f1"] - mean["Baseline"]["f1"]

    print("\n - MODEL COMPARISON -")
    print(f"Users evaluated: {len(users)}")
    print(f"KNN coverage (history seen by the model): {knn_from_neighbors / len(users):.2%}")

    print(f"\n{'Metric':<16} {'Baseline':<12} {'Repeat':<12} {'KNN':<12}")
    print("-" * 52)
    for label, key in (("Precision@5", "precision"), ("Macro-F1@5", "f1")):
        print(
            f"{label:<16} {mean['Baseline'][key]:<12.4f} {mean['Repeat'][key]:<12.4f} {mean['KNN'][key]:<12.4f}"
        )

    print(f"\nMacro-F1 improvement (KNN - Baseline): {improvement:+.4f}")
    print("Precision@5 >= 10%:", "PASS" if mean["KNN"]["precision"] >= 0.10 else "FAIL")
    print("F1 improvement >= 0.005:", "PASS" if improvement >= 0.005 else "FAIL")


if __name__ == "__main__":
    main()
