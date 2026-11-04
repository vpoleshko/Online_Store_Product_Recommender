def recommend_popular(events, seen_items, k=5):
    popularity = (
        events[events["event"] == "transaction"]
        .groupby("itemid")
        .size()
        .sort_values(ascending=False)
    )

    return [
        int(item)
        for item in popularity.index
        if item not in seen_items
    ][:k]