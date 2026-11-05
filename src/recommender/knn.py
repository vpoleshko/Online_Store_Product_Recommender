
import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors


class ItemKNN:
    def __init__(self, n_neighbors=20, max_items=5000):
        self.n_neighbors = n_neighbors
        self.max_items = max_items

    def fit(self, train):
        events = train[
            train["event"].isin(
                ["view", "addtocart", "transaction"]
            )
        ].copy()

        self.popular_items = (
            train[train["event"] == "transaction"]
            .groupby("itemid")
            .size()
            .sort_values(ascending=False)
            .index.tolist()
        )

        popular = (
            events.groupby("itemid")["visitorid"]
            .nunique()
            .nlargest(self.max_items)
            .index
        )

        events = events[events["itemid"].isin(popular)]

        interactions = events[
            ["visitorid", "itemid"]
        ].drop_duplicates()

        user_codes, users = pd.factorize(
            interactions["visitorid"]
        )

        item_codes, items = pd.factorize(
            interactions["itemid"]
        )

        self.items = np.asarray(items)

        self.item_to_idx = {
            item: i
            for i, item in enumerate(self.items)
        }

        self.matrix = csr_matrix(
            (
                np.ones(
                    len(interactions),
                    dtype=np.float32
                ),
                (item_codes, user_codes)
            ),
            shape=(len(items), len(users))
        )

        self.model = NearestNeighbors(
            metric="cosine",
            algorithm="brute",
            n_neighbors=min(
                self.n_neighbors + 1,
                len(items)
            )
        )

        self.model.fit(self.matrix)

        history = train.sort_values("timestamp")

        self.user_history = (
            history.groupby("visitorid")["itemid"]
            .apply(list)
            .to_dict()
        )

        print(f"KNN trained on {len(items)} items")

        return self

    def recommend(self, user_id, k=5):
        history = self.user_history.get(user_id, [])

        seen = set(history)

        recent = list(
            dict.fromkeys(reversed(history))
        )[:30]

        seed_indices = [
            self.item_to_idx[item]
            for item in recent
            if item in self.item_to_idx
        ]

        scores = {}

        if seed_indices:
            distances, indices = self.model.kneighbors(
                self.matrix[seed_indices],
                return_distance=True
            )

            for position, (
                neighbor_ids,
                neighbor_distances
            ) in enumerate(zip(indices, distances)):

                recency_weight = 1.0

                for idx, distance in zip(
                    neighbor_ids,
                    neighbor_distances
                ):
                    item = int(self.items[idx])

                    if item in seen:
                        continue

                    similarity = max(
                        0.0,
                        1.0 - float(distance)
                    )

                    if similarity <= 0:
                        continue

                    score = similarity * recency_weight

                    scores[item] = (
                        scores.get(item, 0.0)
                        + score
                    )

        recommendations = sorted(
            scores,
            key=lambda item: (-scores[item], item)
        )[:k]

        selected = set(recommendations)

        if len(recommendations) < k:
            for item in self.popular_items:
                item = int(item)

                if item in seen or item in selected:
                    continue

                recommendations.append(item)
                selected.add(item)

                if len(recommendations) == k:
                    break

        return [int(item) for item in recommendations]
