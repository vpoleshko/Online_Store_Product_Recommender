
import pandas as pd

from src.recommender.knn import ItemKNN
from src.recommender.evaluation import precision_at_k, f1_at_k


def main():
    train = pd.read_csv("data/processed/train.csv")
    test = pd.read_csv("data/processed/test.csv")

    actual_purchases = (
        test[test["event"] == "transaction"]
        .groupby("visitorid")["itemid"]
        .apply(set)
        .to_dict()
    )

    seen_items = (
        train.groupby("visitorid")["itemid"]
        .apply(set)
        .to_dict()
    )

    purchased_items = (
        train[train["event"] == "transaction"]
        .groupby("visitorid")["itemid"]
        .apply(set)
        .to_dict()
    )

    users = sorted(set(actual_purchases) & set(seen_items))

    if not users:
        print("No users available for evaluation.")
        return

    popular_items = (
        train[train["event"] == "transaction"]
        .groupby("itemid")
        .size()
        .sort_values(ascending=False)
        .index.tolist()
    )

    knn = ItemKNN()
    knn.fit(train)

    baseline_precision = []
    baseline_f1 = []
    knn_precision = []
    knn_f1 = []

    users_with_knn_recs = 0

    for user in users:
        actual = actual_purchases[user]
        bought = purchased_items.get(user, set())

        baseline_recs = [
            item for item in popular_items
            if item not in bought
        ][:5]

        # KNN
        knn_recs = knn.recommend(user, k=5)

        if knn_recs:
            users_with_knn_recs += 1

        baseline_precision.append(
            precision_at_k(baseline_recs, actual, 5)
        )
        baseline_f1.append(
            f1_at_k(baseline_recs, actual, 5)
        )

        knn_precision.append(
            precision_at_k(knn_recs, actual, 5)
        )
        knn_f1.append(
            f1_at_k(knn_recs, actual, 5)
        )

    bp = sum(baseline_precision) / len(users)
    bf = sum(baseline_f1) / len(users)

    kp = sum(knn_precision) / len(users)
    kf = sum(knn_f1) / len(users)

    improvement = kf - bf

    print("\n - MODEL COMPARISON -")
    print(f"Users evaluated: {len(users)}")
    print(f"KNN coverage: {users_with_knn_recs / len(users):.2%}")

    print(f"\n{'Metric':<20} {'Baseline':<12} {'KNN':<12}")
    print("-" * 44)
    print(f"{'Precision@5':<20} {bp:<12.4f} {kp:<12.4f}")
    print(f"{'Macro-F1@5':<20} {bf:<12.4f} {kf:<12.4f}")

    print(f"\nMacro-F1 improvement: {improvement:+.4f}")

    print(
        "Precision@5 >= 10%:",
        "PASS" if kp >= 0.10 else "FAIL"
    )

    print(
        "F1 improvement >= 0.05:",
        "PASS" if improvement >= 0.05 else "FAIL"
    )


if __name__ == "__main__":
    main()
