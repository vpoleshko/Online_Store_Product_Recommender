
import pandas as pd

from src.recommender.baseline import recommend_popular
from src.recommender.evaluation import precision_at_k, f1_at_k


def main():
    train = pd.read_csv("data/processed/train.csv")
    test = pd.read_csv("data/processed/test.csv")

    test_purchases = test[test["event"] == "transaction"]
    actual_purchases = (
        test_purchases.groupby("visitorid")["itemid"]
        .apply(lambda x: set(x))
        .to_dict()
    )

    seen_items = (
        train.groupby("visitorid")["itemid"]
        .apply(lambda x: set(x))
        .to_dict()
    )

    users = set(actual_purchases) & set(seen_items)

    popular_items = (
        train[train["event"] == "transaction"]
        .groupby("itemid")
        .size()
        .sort_values(ascending=False)
        .index.tolist()
    )

    precision_scores = []
    f1_scores = []

    for user in users:
        already_seen = seen_items[user]

        recommendations = [
            item for item in popular_items
            if item not in already_seen
        ][:5]

        actual = actual_purchases[user]

        precision_scores.append(
            precision_at_k(recommendations, actual)
        )
        f1_scores.append(
            f1_at_k(recommendations, actual)
        )

    if not users:
        print("No eligible users found.")
        return

    print(" - BASELINE RESULTS -")
    print("Users evaluated:", len(users))
    print("Precision@5:", round(sum(precision_scores) / len(users), 4))
    print("Macro-F1@5:", round(sum(f1_scores) / len(users), 4))


if __name__ == "__main__":
    main()
