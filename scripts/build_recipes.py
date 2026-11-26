import argparse
import ast
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "BAAI/bge-small-en-v1.5"

NON_FOOD_DEPARTMENTS = {"household", "personal care", "pets", "babies", "other", "missing"}

STAPLES = {
    "salt", "water", "pepper", "black pepper", "salt and pepper", "ice", "ice cubes",
    "boiling water", "warm water", "cold water", "hot water", "kosher salt", "sea salt",
    "cooking spray", "nonstick cooking spray", "ground black pepper", "white pepper",
    "fresh ground black pepper", "freshly ground black pepper", "salt & pepper",
    "table salt", "coarse salt", "cold water", "ice water", "lukewarm water",
}

GENERIC_WORDS = {
    "organic", "natural", "pure", "fresh", "original", "classic", "premium", "real", "100",
    "all", "large", "medium", "small", "style", "brand", "the", "and", "of", "with", "in", "a",
}

DESCRIPTOR_WORDS = {
    "fresh", "freshly", "dried", "dry", "chopped", "minced", "sliced", "diced", "large", "small",
    "medium", "ripe", "finely", "coarsely", "frozen", "canned", "packed", "softened", "melted",
    "uncooked", "raw", "of", "to", "taste", "for", "or", "and",
}
STAPLE_WORDS = {"salt", "pepper", "black", "white", "ground", "fresh", "freshly", "water", "ice", "and", "cracked", "coarse", "kosher", "sea", "table"}

ALIASES = {
    "butter": "unsalted butter",
    "oil": "vegetable oil",
    "egg yolk": "eggs",
    "egg yolks": "eggs",
    "egg white": "eggs",
    "egg whites": "eggs",
    "celery ribs": "celery",
    "gingerroot": "ginger",
    "cooked chicken": "chicken breast",
    "plain flour": "all purpose flour",
    "icing sugar": "powdered sugar",
    "orange zest": "oranges",
    "orange rind": "oranges",
    "lemon zest": "lemons",
    "lemon rind": "lemons",
    "prepared mustard": "yellow mustard",
    "baking potatoes": "russet potatoes",
    "red pepper flakes": "crushed red pepper",
    "crushed red pepper flakes": "crushed red pepper",
    "sweet red pepper": "red bell pepper",
    "splenda sugar substitute": "sweetener",
}

MIN_SIMILARITY = 0.62
STRONG_SIMILARITY = 0.78
SCORE_MARGIN = 0.05
CANDIDATES = 40
MAX_PRODUCTS_PER_INGREDIENT = 8
MIN_MAPPED_SHARE = 0.8
MIN_REVIEWS = 3
MIN_RATING = 4.0
MIN_INGREDIENTS = 3
MAX_MINUTES = 240


def make_engine():
    load_dotenv(ROOT / ".env")
    url = (
        f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def insert(engine, table, frame, chunk=10000):
    columns = list(frame.columns)
    statement = text(
        f"INSERT INTO app.{table} ({', '.join(columns)}) VALUES ({', '.join(':' + c for c in columns)})"
    )
    records = frame.astype(object).where(frame.notna(), None).to_dict("records")

    with engine.begin() as conn:
        for start in range(0, len(records), chunk):
            conn.execute(statement, records[start:start + chunk])


def load_products(engine):
    products = pd.read_sql(
        "SELECT p.product_id, p.product_name, p.department, e.embedding::real[] AS embedding "
        "FROM raw.v_products p JOIN app.product_embeddings e USING (product_id)",
        engine,
    )
    products = products[~products["department"].isin(NON_FOOD_DEPARTMENTS)].reset_index(drop=True)
    vectors = np.asarray(products.pop("embedding").tolist(), dtype=np.float32)
    return products, vectors


def match_ingredients(ingredients, products, product_vectors, popularity):
    model = SentenceTransformer(MODEL_NAME)
    queries = [ALIASES.get(i, i) for i in ingredients]
    vectors = model.encode(
        queries, batch_size=256, normalize_embeddings=True, show_progress_bar=True
    ).astype(np.float32)

    popularity = products["product_id"].map(popularity).fillna(0).to_numpy()
    log_pop = np.log1p(popularity)
    product_tokens = [set(tokens(name)) for name in products["product_name"]]
    rows = []

    for start in range(0, len(ingredients), 1000):
        chunk = vectors[start:start + 1000]
        sims = chunk @ product_vectors.T
        top = np.argpartition(-sims, CANDIDATES, axis=1)[:, :CANDIDATES]

        for i in range(len(chunk)):
            all_words = set(tokens(queries[start + i]))
            wanted = all_words - DESCRIPTOR_WORDS
            if not wanted:
                continue

            scored = []
            for j in top[i]:
                coverage = len(wanted & product_tokens[j]) / len(wanted)
                extra = len([t for t in product_tokens[j] - wanted if t not in GENERIC_WORDS])
                score = sims[i, j] + 0.12 * coverage - 0.03 * min(extra, 4) + 0.005 * log_pop[j]
                scored.append((score, j, coverage, extra))

            scored.sort(reverse=True)
            best_score, best_j, best_cov, _ = scored[0]
            similarity = sims[i, best_j]

            if not (best_cov >= 0.99 and similarity >= MIN_SIMILARITY) and not (
                best_cov >= 0.5 and similarity >= STRONG_SIMILARITY
            ):
                continue

            keep = [
                (j, cov) for score, j, cov, extra in scored
                if score >= best_score - SCORE_MARGIN and cov >= best_cov and extra <= 1
            ][:MAX_PRODUCTS_PER_INGREDIENT]

            if best_j not in {j for j, _ in keep}:
                keep.append((best_j, best_cov))

            for j, _ in keep:
                rows.append(
                    (ingredients[start + i], int(products.at[j, "product_id"]),
                     float(sims[i, j]), bool(j == best_j))
                )

    return pd.DataFrame(rows, columns=["ingredient", "product_id", "similarity", "is_primary"])


def is_staple(ingredient):
    words = set(tokens(ingredient))
    return ingredient in STAPLES or (bool(words) and words <= STAPLE_WORDS)


def stem(word):
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("oes"):
        return word[:-2]
    if word.endswith("ss"):
        return word
    if word.endswith("s") and len(word) > 3:
        return word[:-1]
    return word


def tokens(text_):
    return [stem(w) for w in re.findall(r"[a-z]+", text_.lower())]


def main(recipes_path):
    engine = make_engine()
    products, product_vectors = load_products(engine)
    print(f"{len(products)} food products")

    train = pd.read_csv(ROOT / "data/processed/train.csv", usecols=["product_id", "n_orders"])
    popularity = train.groupby("product_id")["n_orders"].sum()

    recipes = pd.read_csv(recipes_path)
    recipes["ingredients"] = recipes["ingredients"].map(ast.literal_eval)
    reviews = (
        pd.read_csv(Path(recipes_path).with_name("RAW_interactions.csv"), usecols=["recipe_id", "rating"])
        .groupby("recipe_id")["rating"].agg(n_reviews="count", rating="mean")
    )
    recipes = recipes.join(reviews, on="id")
    recipes = recipes[(recipes["n_reviews"] >= MIN_REVIEWS) & (recipes["rating"] >= MIN_RATING)]
    recipes = recipes.dropna(subset=["name"])
    recipes["name"] = recipes["name"].str.replace(r"\s+", " ", regex=True).str.strip()
    recipes = recipes[recipes["minutes"].between(1, MAX_MINUTES) & (recipes["name"] != "")]
    print(f"{len(recipes)} recipes")

    counts = pd.Series([i for l in recipes["ingredients"] for i in l]).value_counts()
    staples = {i for i in counts.index if is_staple(i)}
    ingredients = [i for i in counts.index if i not in staples]
    print(f"{len(ingredients)} distinct ingredients to match")

    links = match_ingredients(ingredients, products, product_vectors, popularity)
    mapped = set(links["ingredient"])
    print(f"{len(mapped)} ingredients matched ({counts[list(mapped)].sum() / counts[ingredients].sum():.1%} of usages)")

    def keep(ings):
        real = [i for i in ings if i not in staples]
        if len(real) < MIN_INGREDIENTS:
            return False
        return sum(i in mapped for i in real) / len(real) >= MIN_MAPPED_SHARE

    recipes = recipes[recipes["ingredients"].map(keep)].drop_duplicates("name")
    print(f"{len(recipes)} recipes can be cooked mostly from the store")

    recipes["steps"] = recipes["steps"].map(ast.literal_eval)

    recipes["n_reviews"] = recipes["n_reviews"].astype(int)
    recipes["rating"] = recipes["rating"].round(2)
    recipe_rows = recipes[["id", "name", "minutes", "n_steps", "n_reviews", "rating", "description", "steps"]].rename(
        columns={"id": "recipe_id"}
    )
    recipe_rows["description"] = recipe_rows["description"].fillna("").str.replace(r"\s+", " ", regex=True).str.strip()

    ingredient_rows = (
        recipes[["id", "ingredients"]]
        .explode("ingredients")
        .rename(columns={"id": "recipe_id", "ingredients": "ingredient"})
        .drop_duplicates()
    )
    ingredient_rows["is_staple"] = ingredient_rows["ingredient"].isin(staples)

    used = set(ingredient_rows["ingredient"])
    links = links[links["ingredient"].isin(used)]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE app.ingredient_products, app.recipe_ingredients, app.recipes CASCADE"))

    insert(engine, "recipes", recipe_rows)
    insert(engine, "recipe_ingredients", ingredient_rows)
    insert(engine, "ingredient_products", links)

    print(f"saved {len(recipe_rows)} recipes, {len(ingredient_rows)} ingredient lines, {len(links)} ingredient-product links")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipes", default=str(ROOT / "data/raw/foodcom/RAW_recipes.csv"))
    main(parser.parse_args().recipes)
