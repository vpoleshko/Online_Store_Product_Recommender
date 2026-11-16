from src.recommender.cart import copurchase_items, fuse
from src.recommender.knn import ItemKNN

from tests.test_knn import make_train


def test_copurchase_returns_products_bought_with_cart_items():
    knn = ItemKNN(n_neighbors=3).fit(make_train(), history_users=[])

    assert copurchase_items(knn, [1])[0] == 2
    assert 1 not in copurchase_items(knn, [1])


def test_copurchase_ignores_unknown_products():
    knn = ItemKNN(n_neighbors=3).fit(make_train(), history_users=[])

    assert copurchase_items(knn, [999]) == []


def test_fuse_prefers_purchases_and_reports_sources():
    result = fuse(copurchase=[10, 20], similar=[20, 30], k=3)

    assert [item for item, _ in result][0] == 20
    assert dict(result)[20] == ["purchases", "similar"]
    assert dict(result)[30] == ["similar"]
