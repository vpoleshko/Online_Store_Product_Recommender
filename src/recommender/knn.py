import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix
from sklearn.preprocessing import normalize


class ItemKNN:

    def __init__(
        self,
        n_neighbors=20,
        max_items=20000,
        recency_decay=0.9,
        max_seeds=30,
        chunk_size=500,
    ):
        self.n_neighbors = n_neighbors
        self.max_items = max_items
        self.recency_decay = recency_decay
        self.max_seeds = max_seeds
        self.chunk_size = chunk_size

    def fit(self, train, history_users=None):
        self.popular_items = (
            train.groupby("product_id")["n_orders"]
            .sum()
            .sort_values(ascending=False)
            .index.tolist()
        )

        top = set(self.popular_items[: self.max_items])
        pairs = train[train["product_id"].isin(top)]

        user_codes, users = pd.factorize(pairs["user_id"])
        item_codes, items = pd.factorize(pairs["product_id"])

        self.items = np.asarray(items)
        self.item_to_idx = {int(item): i for i, item in enumerate(self.items)}

        matrix = csr_matrix(
            (
                np.log1p(pairs["n_orders"].to_numpy(dtype=np.float32)),
                (item_codes, user_codes),
            ),
            shape=(len(items), len(users)),
        )
        matrix = normalize(matrix, norm="l2", axis=1).tocsr()

        self._build_neighbors(matrix)
        self._build_history(train, history_users)

        print(f"KNN trained on {len(items)} products")

        return self

    def _build_neighbors(self, matrix):
        n_items = matrix.shape[0]
        k = min(self.n_neighbors + 1, n_items)

        self.neighbor_idx = np.zeros((n_items, k), dtype=np.int32)
        self.neighbor_sim = np.zeros((n_items, k), dtype=np.float32)

        matrix_t = matrix.T.tocsr()

        for start in range(0, n_items, self.chunk_size):
            stop = min(start + self.chunk_size, n_items)
            sims = (matrix[start:stop] @ matrix_t).toarray()

            top = np.argpartition(-sims, k - 1, axis=1)[:, :k]
            top_sims = np.take_along_axis(sims, top, axis=1)

            order = np.argsort(-top_sims, axis=1)
            self.neighbor_idx[start:stop] = np.take_along_axis(top, order, axis=1)
            self.neighbor_sim[start:stop] = np.take_along_axis(top_sims, order, axis=1)

    def _build_history(self, train, history_users):
        history = train
        if history_users is not None:
            history = history[history["user_id"].isin(set(history_users))]

        history = history.sort_values(
            ["user_id", "last_order_number"], ascending=[True, False]
        )

        self.user_history = (
            history.groupby("user_id")["product_id"].apply(list).to_dict()
        )

    def recommend(self, user_id, k=5):
        recent = self.user_history.get(user_id, [])[: self.max_seeds]

        scores = {}
        weight = 1.0

        for product in recent:
            idx = self.item_to_idx.get(int(product))

            if idx is not None:
                for neighbor, sim in zip(self.neighbor_idx[idx], self.neighbor_sim[idx]):
                    if sim <= 0:
                        continue

                    item = int(self.items[neighbor])
                    scores[item] = scores.get(item, 0.0) + float(sim) * weight

            weight *= self.recency_decay

        recommendations = sorted(
            scores, key=lambda item: (-scores[item], item)
        )[:k]

        selected = set(recommendations)

        if len(recommendations) < k:
            for item in self.popular_items:
                item = int(item)

                if item in selected:
                    continue

                recommendations.append(item)
                selected.add(item)

                if len(recommendations) == k:
                    break

        return [int(item) for item in recommendations]
