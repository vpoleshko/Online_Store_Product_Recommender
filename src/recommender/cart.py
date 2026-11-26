def copurchase_items(knn, product_ids, limit=50):
    cart = {int(p) for p in product_ids}
    scores = {}

    for product in cart:
        idx = knn.item_to_idx.get(product)

        if idx is None:
            continue

        for neighbor, sim in zip(knn.neighbor_idx[idx], knn.neighbor_sim[idx]):
            item = int(knn.items[neighbor])

            if item in cart or sim <= 0:
                continue

            scores[item] = scores.get(item, 0.0) + float(sim)

    return sorted(scores, key=lambda item: -scores[item])[:limit]


def fuse(copurchase, similar, k=10, similar_weight=0.3, rrf_k=60):
    scores = {}
    sources = {}

    for rank, item in enumerate(copurchase):
        scores[item] = scores.get(item, 0.0) + 1.0 / (rrf_k + rank)
        sources.setdefault(item, set()).add("purchases")

    for rank, item in enumerate(similar):
        scores[item] = scores.get(item, 0.0) + similar_weight / (rrf_k + rank)
        sources.setdefault(item, set()).add("similar")

    ranked = sorted(scores, key=lambda item: -scores[item])[:k]

    return [(int(item), sorted(sources[item])) for item in ranked]
