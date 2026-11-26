import numpy as np
import pandas as pd

from src.recommender.search import ProductSearch, tokens


def make_search():
    products = pd.DataFrame(
        {"product_name": ["Liquid Egg Whites", "Egg Nog", "Eggs", "Spaghetti", "Spaghetti Sauce"]},
        index=pd.Index([1, 2, 3, 4, 5], name="product_id"),
    )
    popularity = pd.Series({1: 100, 2: 50, 3: 1000, 4: 800, 5: 700})
    emb_ids = np.array([1, 2, 3, 4, 5])
    emb = np.eye(5, dtype=np.float32)
    return ProductSearch(products, popularity, emb_ids, emb)


def test_tokens_are_stemmed():
    assert tokens("Tomatoes, Berries") == ["tomato", "berry"]


def test_exact_name_beats_closer_embedding():
    search = make_search()
    vector = np.zeros(5, dtype=np.float32)
    ann = [(1, 0.80), (2, 0.78), (3, 0.74)]

    ranked = search.rank("eggs", vector, ann, limit=3)

    assert ranked[0][0] == 3


def test_prefix_finds_products_outside_vector_candidates():
    search = make_search()
    vector = np.zeros(5, dtype=np.float32)

    ranked = search.rank("spag", vector, [(2, 0.2)], limit=3)

    assert {pid for pid, _, _ in ranked[:2]} == {4, 5}


def test_query_without_word_match_falls_back_to_embeddings():
    search = make_search()
    vector = np.zeros(5, dtype=np.float32)

    ranked = search.rank("something sweet", vector, [(2, 0.9), (1, 0.4)], limit=2)

    assert ranked[0][0] == 2
