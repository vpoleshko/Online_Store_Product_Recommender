import pandas as pd

from src.recommender.baseline import popular_products, recommend_popular
from src.recommender.knn import ItemKNN


def make_train():
    rows = []
    for user in (1, 2, 3):
        rows += [(user, 1, 2, 5), (user, 2, 1, 4)]
    for user in (4, 5, 6):
        rows += [(user, 3, 2, 5), (user, 4, 1, 4)]
    rows.append((7, 1, 1, 3))
    return pd.DataFrame(rows, columns=["user_id", "product_id", "n_orders", "last_order_number"])


def test_knn_recommends_co_purchased_product():
    knn = ItemKNN(n_neighbors=3).fit(make_train())

    assert 2 in knn.recommend(7, k=2)
    assert 3 not in knn.recommend(7, k=2)


def test_knn_falls_back_to_popular_for_unknown_user():
    train = make_train()
    knn = ItemKNN(n_neighbors=3).fit(train)

    assert knn.recommend(999, k=3) == recommend_popular(popular_products(train), k=3)


def test_popular_products_excludes_requested_items():
    popular = popular_products(make_train())

    assert recommend_popular(popular, exclude={popular[0]}, k=2) == popular[1:3]
