def popular_products(train):
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
    ranked = train.sort_values(
        ["user_id", "n_orders", "last_order_number"], ascending=[True, False, False]
    )
    return ranked.groupby("user_id")["product_id"].apply(list).to_dict()
