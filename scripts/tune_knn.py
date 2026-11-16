
import pandas as pd

from src.recommender.knn import ItemKNN
from src.recommender.evaluation import precision_at_k, f1_at_k


def main():
    train = pd.read_csv("data/processed/train_final.csv")
    validation = pd.read_csv("data/processed/validation.csv")

    actual_purchases = (
        validation[validation["event"] == "transaction"]
        .groupby("visitorid")["itemid"]
        .apply(set)
        .to_dict()
    )

    train_users = set(train["visitorid"].unique())
    users = sorted(set(actual_purchases) & train_users)

    if not users:
        print("No users available for validation.")
        return

    results = []

    for max_items in [5000, 10000]:
        for n_neighbors in [10, 20, 50]:
            print(
                f"\nTesting max_items={max_items}, "
                f"n_neighbors={n_neighbors}"
            )

            model = ItemKNN(
                n_neighbors=n_neighbors,
                max_items=max_items
            )
            model.fit(train)

            precision_scores = []
            f1_scores = []

            for user in users:
                recommended = model.recommend(user, k=5)
                actual = actual_purchases[user]

                precision_scores.append(
                    precision_at_k(recommended, actual, 5)
                )
                f1_scores.append(
                    f1_at_k(recommended, actual, 5)
                )

            precision = sum(precision_scores) / len(users)
            macro_f1 = sum(f1_scores) / len(users)

            results.append({
                "max_items": max_items,
                "n_neighbors": n_neighbors,
                "precision_at_5": precision,
                "macro_f1_at_5": macro_f1
            })

            print(f"Precision@5: {precision:.4f}")
            print(f"Macro-F1@5: {macro_f1:.4f}")

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(
        "precision_at_5",
        ascending=False
    )

    print("\n===== ALL RESULTS =====")
    print(results_df.to_string(index=False))

    print("\n===== BEST CONFIGURATION =====")
    print(results_df.iloc[0].to_string())


if __name__ == "__main__":
    main()
