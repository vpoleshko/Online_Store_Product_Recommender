def popular_products(train):
    """Product ids ordered by how many orders contained them (most popular first)."""
    return (
        train.groupby("product_id")["n_orders"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )


def recommend_popular(popular, exclude=(), k=5):
    exclude = set(exclude)
    return [int(p) for p in popular if p not in exclude][:k]


def user_frequent_products(train):
    """Per user: products ordered by how often (then how recently) the user bought them."""
    ranked = train.sort_values(
        ["user_id", "n_orders", "last_order_number"], ascending=[True, False, False]
    )
    return ranked.groupby("user_id")["product_id"].apply(list).to_dict()
