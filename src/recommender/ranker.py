import numpy as np
import pandas as pd

FEATURES = [
    "knn_sum", "knn_max", "knn_count", "knn_rank",
    "emb_centroid", "emb_max", "emb_rank",
    "recipe_score", "recipe_count", "recipe_share",
    "in_knn", "in_emb", "in_recipe",
    "log_pop", "same_aisle", "same_dept", "cart_size",
]

MISSING_RANK = 100


class CartRecommender:

    def __init__(self, knn, recipes, emb_ids, emb, meta, popularity, booster=None, n_knn=50, n_emb=50):
        self.knn = knn
        self.recipes = recipes
        self.emb_ids = np.asarray(emb_ids)
        self.emb = emb
        self.emb_idx = {int(p): i for i, p in enumerate(self.emb_ids)}
        self.aisle = meta["aisle_id"].to_dict()
        self.dept = meta["department_id"].to_dict()
        self.log_pop = np.log1p(popularity).to_dict()
        self.booster = booster
        self.n_knn = n_knn
        self.n_emb = n_emb

    def _knn_scores(self, cart):
        sums, maxes, counts, anchors = {}, {}, {}, {}
        knn = self.knn

        for product in cart:
            idx = knn.item_to_idx.get(product)
            if idx is None:
                continue

            for neighbor, sim in zip(knn.neighbor_idx[idx], knn.neighbor_sim[idx]):
                item = int(knn.items[neighbor])

                if item in cart or sim <= 0:
                    continue

                sim = float(sim)
                sums[item] = sums.get(item, 0.0) + sim
                counts[item] = counts.get(item, 0) + 1

                if sim > maxes.get(item, 0.0):
                    maxes[item] = sim
                    anchors[item] = product

        order = sorted(sums, key=lambda i: -sums[i])[: self.n_knn]
        return {item: (sums[item], maxes[item], counts[item], rank, anchors[item]) for rank, item in enumerate(order)}

    def _emb_scores(self, cart):
        rows = [self.emb_idx[p] for p in cart if p in self.emb_idx]

        if not rows:
            return {}, None, None

        cart_emb = self.emb[rows]
        centroid = cart_emb.mean(axis=0)
        centroid /= np.linalg.norm(centroid) + 1e-9

        sims = self.emb @ centroid
        sims[rows] = -1.0

        top = np.argpartition(-sims, self.n_emb)[: self.n_emb]
        top = top[np.argsort(-sims[top])]

        return {int(self.emb_ids[j]): rank for rank, j in enumerate(top)}, centroid, (rows, cart_emb)

    def candidates(self, cart):
        cart = [int(p) for p in dict.fromkeys(cart)]
        cart_set = set(cart)

        knn = self._knn_scores(cart_set)
        emb_rank, centroid, cart_info = self._emb_scores(cart)
        recipe = self.recipes.candidates(cart) if self.recipes is not None else {}

        pool = set(knn) | set(emb_rank) | set(recipe)
        pool -= cart_set

        if not pool:
            return pd.DataFrame(columns=["product_id"] + FEATURES), {}

        cart_aisles = pd.Series([self.aisle.get(p) for p in cart]).value_counts().to_dict()
        cart_depts = pd.Series([self.dept.get(p) for p in cart]).value_counts().to_dict()

        rows, info = [], {}

        for product in pool:
            k = knn.get(product)
            r = recipe.get(product)
            e = self.emb_idx.get(product)

            emb_centroid = emb_max = np.nan
            emb_anchor = None

            if e is not None and centroid is not None:
                emb_centroid = float(self.emb[e] @ centroid)
                sims = cart_info[1] @ self.emb[e]
                best = int(np.argmax(sims))
                emb_max = float(sims[best])
                emb_anchor = int(self.emb_ids[cart_info[0][best]])

            rows.append(
                {
                    "product_id": product,
                    "knn_sum": k[0] if k else 0.0,
                    "knn_max": k[1] if k else 0.0,
                    "knn_count": k[2] if k else 0,
                    "knn_rank": k[3] if k else MISSING_RANK,
                    "emb_centroid": emb_centroid,
                    "emb_max": emb_max,
                    "emb_rank": emb_rank.get(product, MISSING_RANK),
                    "recipe_score": r[0] if r else 0.0,
                    "recipe_count": r[1] if r else 0,
                    "recipe_share": r[2] if r else 0.0,
                    "in_knn": int(k is not None),
                    "in_emb": int(product in emb_rank),
                    "in_recipe": int(r is not None),
                    "log_pop": self.log_pop.get(product, 0.0),
                    "same_aisle": cart_aisles.get(self.aisle.get(product), 0),
                    "same_dept": cart_depts.get(self.dept.get(product), 0),
                    "cart_size": len(cart),
                }
            )
            info[product] = {
                "knn_anchor": k[4] if k else None,
                "emb_anchor": emb_anchor,
                "recipe_row": r[3] if r else None,
            }

        return pd.DataFrame(rows), info

    def recommend(self, cart, k=10, max_per_aisle=3, max_similarity=0.95):
        frame, info = self.candidates(cart)

        stats = {
            "candidates": int(len(frame)),
            "from_knn": int(frame["in_knn"].sum()) if not frame.empty else 0,
            "from_embeddings": int(frame["in_emb"].sum()) if not frame.empty else 0,
            "from_recipes": int(frame["in_recipe"].sum()) if not frame.empty else 0,
            "ranker": "lightgbm" if self.booster is not None else "blend",
            "skipped_by_rules": 0,
        }

        if frame.empty:
            return [], stats

        if self.booster is not None:
            scores = self.booster.predict(frame[FEATURES])
        else:
            scores = (
                frame["knn_sum"] + 0.5 * frame["recipe_score"] + 0.2 * frame["emb_centroid"].fillna(0)
            ).to_numpy()

        ids = frame["product_id"].to_numpy()
        emb_max = frame["emb_max"].to_numpy()

        chosen, per_aisle = [], {}

        for i in np.argsort(-scores):
            aisle = self.aisle.get(int(ids[i]))

            if emb_max[i] > max_similarity or per_aisle.get(aisle, 0) >= max_per_aisle:
                stats["skipped_by_rules"] += 1
                continue

            per_aisle[aisle] = per_aisle.get(aisle, 0) + 1
            chosen.append(i)

            if len(chosen) == k:
                break

        results = [(int(ids[i]), float(scores[i]), info[int(ids[i])], frame.iloc[i]) for i in chosen]
        return results, stats
