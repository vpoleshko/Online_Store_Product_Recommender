
import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

EVENT_WEIGHTS = {"view": 1.0, "addtocart": 3.0, "transaction": 5.0}


class ItemKNN:
    def __init__(
        self,
        n_neighbors=20,
        max_items=20000,
        recency_decay=0.9,
        max_seeds=30,
        event_weights=None,
    ):
        self.n_neighbors = n_neighbors
        self.max_items = max_items
        self.recency_decay = recency_decay
        self.max_seeds = max_seeds
        self.event_weights = event_weights or EVENT_WEIGHTS

    def fit(self, train):
        events = train[train["event"].isin(self.event_weights)].copy()
        events["weight"] = events["event"].map(self.event_weights)

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

        interactions = (
            events.groupby(["visitorid", "itemid"], as_index=False)["weight"]
            .max()
        )

        user_codes, users = pd.factorize(interactions["visitorid"])
        item_codes, items = pd.factorize(interactions["itemid"])

        self.items = np.asarray(items)
        self.item_to_idx = {item: i for i, item in enumerate(self.items)}

        self.matrix = csr_matrix(
            (
                interactions["weight"].to_numpy(dtype=np.float32),
                (item_codes, user_codes),
            ),
            shape=(len(items), len(users)),
        )

        self.model = NearestNeighbors(
            metric="cosine",
            algorithm="brute",
            n_neighbors=min(self.n_neighbors + 1, len(items)),
        )
        self.model.fit(self.matrix)

        history = train.sort_values("timestamp")

        self.user_history = (
            history.groupby("visitorid")["itemid"].apply(list).to_dict()
        )

        self.user_purchased = (
            train[train["event"] == "transaction"]
            .groupby("visitorid")["itemid"]
            .apply(set)
            .to_dict()
        )

        print(f"KNN trained on {len(items)} items")

        return self

    def recommend(self, user_id, k=5):
        history = self.user_history.get(user_id, [])
        purchased = self.user_purchased.get(user_id, set())

        recent = list(dict.fromkeys(reversed(history)))[: self.max_seeds]

        seed_indices = []
        seed_weights = []
        weight = 1.0
        for item in recent:
            if item in self.item_to_idx:
                seed_indices.append(self.item_to_idx[item])
                seed_weights.append(weight)
            weight *= self.recency_decay

        scores = {}

        if seed_indices:
            distances, indices = self.model.kneighbors(
                self.matrix[seed_indices], return_distance=True
            )

            for recency_weight, neighbor_ids, neighbor_distances in zip(
                seed_weights, indices, distances
            ):
                for idx, distance in zip(neighbor_ids, neighbor_distances):
                    item = int(self.items[idx])

                    if item in purchased:
                        continue

                    similarity = max(0.0, 1.0 - float(distance))

                    if similarity <= 0:
                        continue

                    scores[item] = (
                        scores.get(item, 0.0) + similarity * recency_weight
                    )

        recommendations = sorted(
            scores, key=lambda item: (-scores[item], item)
        )[:k]

        selected = set(recommendations)

        if len(recommendations) < k:
            for item in self.popular_items:
                item = int(item)

                if item in purchased or item in selected:
                    continue

                recommendations.append(item)
                selected.add(item)

                if len(recommendations) == k:
                    break

        return [int(item) for item in recommendations]
