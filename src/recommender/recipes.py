import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sqlalchemy import text


class RecipeIndex:

    def __init__(self, recipes, recipe_ingredients, links):
        self.recipes = recipes.reset_index(drop=True)

        ingredients = sorted(set(links["ingredient"]))
        self.ing_idx = {name: i for i, name in enumerate(ingredients)}

        products = sorted(set(links["product_id"]))
        self.prod_idx = {int(p): i for i, p in enumerate(products)}

        rows = links["ingredient"].map(self.ing_idx)
        cols = links["product_id"].map(self.prod_idx)
        self.product_to_ingredient = csr_matrix(
            (np.ones(len(links), dtype=np.float32), (rows, cols)),
            shape=(len(ingredients), len(products)),
        )

        primary = links[links["is_primary"]].set_index("ingredient")["product_id"]
        self.primary_product = {ing: int(p) for ing, p in primary.items()}

        row_of = {int(r): i for i, r in enumerate(self.recipes["recipe_id"])}
        buyable = recipe_ingredients[
            ~recipe_ingredients["is_staple"] & recipe_ingredients["ingredient"].isin(self.ing_idx)
        ]
        self.recipe_to_ingredient = csr_matrix(
            (
                np.ones(len(buyable), dtype=np.float32),
                (buyable["recipe_id"].map(row_of), buyable["ingredient"].map(self.ing_idx)),
            ),
            shape=(len(self.recipes), len(ingredients)),
        )
        self.total = np.asarray(self.recipe_to_ingredient.sum(axis=1)).ravel()

        self.recipe_ingredients = {
            int(rid): list(zip(group["ingredient"], group["is_staple"]))
            for rid, group in recipe_ingredients.groupby("recipe_id")
        }

        self.quality = 1.0 + 0.1 * np.log1p(self.recipes["n_reviews"].to_numpy(dtype=np.float32))
        self.ingredient_names = ingredients

    @classmethod
    def from_db(cls, engine):
        recipes = pd.read_sql(
            "SELECT recipe_id, name, minutes, n_steps, n_reviews, rating FROM app.recipes", engine
        )
        recipe_ingredients = pd.read_sql(
            "SELECT recipe_id, ingredient, is_staple FROM app.recipe_ingredients", engine
        )
        links = pd.read_sql(
            "SELECT ingredient, product_id, is_primary FROM app.ingredient_products", engine
        )
        return cls(recipes, recipe_ingredients, links)

    def covered_ingredients(self, product_ids):
        cart = np.zeros(len(self.prod_idx), dtype=np.float32)

        for product in product_ids:
            idx = self.prod_idx.get(int(product))
            if idx is not None:
                cart[idx] = 1.0

        return (self.product_to_ingredient @ cart > 0).astype(np.float32)

    def match(self, product_ids, k=5, max_missing=6):
        covered = self.covered_ingredients(product_ids)

        if not covered.any():
            return []

        have = self.recipe_to_ingredient @ covered
        missing = self.total - have
        usable = (have >= min(2, covered.sum())) & (missing <= max_missing) & (self.total > 0)

        score = np.where(usable, have / np.maximum(self.total, 1) * have * self.quality, 0.0)
        top = np.argsort(-score)[:k]

        return [(int(r), int(have[r]), int(self.total[r]), float(score[r])) for r in top if score[r] > 0]

    def missing_products(self, row, cart_products):
        recipe_id = int(self.recipes.at[row, "recipe_id"])
        cart = {int(p) for p in cart_products}
        covered = self.covered_ingredients(cart)
        result = []

        for ingredient, staple in self.recipe_ingredients.get(recipe_id, []):
            idx = self.ing_idx.get(ingredient)

            if staple or idx is None or covered[idx]:
                continue

            result.append((ingredient, self.primary_product[ingredient]))

        return result

    def candidates(self, product_ids, n_recipes=30):
        cart = {int(p) for p in product_ids}
        found = {}

        for row, have, total, score in self.match(product_ids, k=n_recipes):
            for _, product in self.missing_products(row, cart):
                best, count, share, best_row = found.get(product, (0.0, 0, 0.0, row))
                if score > best:
                    best, best_row = score, row
                found[product] = (best, count + 1, max(share, have / total), best_row)

        return found

    def details(self, engine, cart_products, matches):
        if not matches:
            return []

        ids = [int(self.recipes.at[row, "recipe_id"]) for row, *_ in matches]

        with engine.connect() as conn:
            extra = {
                r[0]: (r[1], r[2])
                for r in conn.execute(
                    text("SELECT recipe_id, description, steps FROM app.recipes WHERE recipe_id = ANY(:ids)"),
                    {"ids": ids},
                )
            }

        covered = self.covered_ingredients(cart_products)
        result = []

        for (row, have, total, score), recipe_id in zip(matches, ids):
            info = self.recipes.iloc[row]
            description, steps = extra.get(recipe_id, ("", []))

            ingredients = []
            for ingredient, staple in self.recipe_ingredients.get(recipe_id, []):
                idx = self.ing_idx.get(ingredient)

                if staple:
                    status = "staple"
                elif idx is None:
                    status = "not_sold"
                elif covered[idx]:
                    status = "have"
                else:
                    status = "missing"

                ingredients.append(
                    {
                        "name": ingredient,
                        "status": status,
                        "product_id": self.primary_product.get(ingredient) if status == "missing" else None,
                    }
                )

            result.append(
                {
                    "recipe_id": recipe_id,
                    "name": info["name"],
                    "minutes": int(info["minutes"]),
                    "rating": float(info["rating"]),
                    "reviews": int(info["n_reviews"]),
                    "have": have,
                    "total": total,
                    "description": description or "",
                    "steps": list(steps or []),
                    "ingredients": ingredients,
                }
            )

        return result
