def precision_at_k(recommended, actual, k=5):
    if not recommended:
        return 0.0

    hits = len(set(recommended[:k]) & set(actual))
    return hits / k


def f1_at_k(recommended, actual, k=5):
    if not actual:
        return 0.0

    precision = precision_at_k(recommended, actual, k)
    recall = len(set(recommended[:k]) & set(actual)) / len(set(actual))

    if precision + recall == 0:
        return 0.0

    return 2 * precision * recall / (precision + recall)