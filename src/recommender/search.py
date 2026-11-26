import re

import numpy as np

GENERIC_WORDS = {
    "organic", "natural", "pure", "fresh", "original", "classic", "premium", "real", "100",
    "all", "large", "medium", "small", "style", "brand", "the", "and", "of", "with", "in", "a",
}

WEIGHTS = {
    "semantic": 1.0,
    "coverage": 0.5,
    "exact": 0.3,
    "prefix": 0.15,
    "extra_words": 0.05,
    "popularity": 0.1,
}


PREFIX_CREDIT = 0.5


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


def tokens(text):
    return [stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())]


class ProductSearch:

    def __init__(self, products, popularity, emb_ids, emb, weights=None, lexical_candidates=50):
        self.names = products["product_name"].to_dict()
        self.tokens = {pid: set(tokens(name)) for pid, name in self.names.items()}
        self.lexical_candidates = lexical_candidates
        self.weights = {**WEIGHTS, **(weights or {})}

        log_pop = np.log1p(popularity.reindex(products.index).fillna(0))
        self.popularity = (log_pop / max(log_pop.max(), 1.0)).to_dict()

        self.emb_idx = {int(p): i for i, p in enumerate(emb_ids)}
        self.emb = emb

        self.index = {}
        for pid, words in self.tokens.items():
            for word in words:
                self.index.setdefault(word, set()).add(pid)

    def _word_matches(self, query_tokens, product_tokens):
        matched = 0.0
        last = len(query_tokens) - 1

        for i, word in enumerate(query_tokens):
            if word in product_tokens:
                matched += 1.0
            elif i == last and len(word) >= 3 and any(t.startswith(word) for t in product_tokens):
                matched += PREFIX_CREDIT

        return matched

    def _candidates_for(self, word, is_last):
        found = set(self.index.get(word, ()))

        if is_last and len(word) >= 3:
            for key, ids in self.index.items():
                if key.startswith(word):
                    found |= ids

        return found

    def _lexical_pool(self, query_tokens):
        last = len(query_tokens) - 1
        sets = [self._candidates_for(word, i == last) for i, word in enumerate(query_tokens)]

        if not sets or not all(sets):
            return []

        pool = set.intersection(*sets)
        return sorted(pool, key=lambda p: -self.popularity.get(p, 0.0))[: self.lexical_candidates]

    def rank(self, query, query_vector, ann, limit=24):
        query_tokens = tokens(query)
        query_set = set(query_tokens)
        lowered = query.strip().lower()
        w = self.weights

        similarity = {int(pid): float(sim) for pid, sim in ann}

        for pid in self._lexical_pool(query_tokens):
            if pid not in similarity and pid in self.emb_idx:
                similarity[pid] = float(self.emb[self.emb_idx[pid]] @ query_vector)

        scored = []

        for pid, sim in similarity.items():
            product_tokens = self.tokens.get(pid, set())
            coverage = self._word_matches(query_tokens, product_tokens) / len(query_tokens) if query_tokens else 0.0
            core = product_tokens - GENERIC_WORDS
            exact = float(bool(query_set) and core == query_set)
            extra = min(len(core - query_set), 4)
            prefix = float(self.names[pid].lower().startswith(lowered))

            score = (
                w["semantic"] * sim
                + w["coverage"] * coverage
                + w["exact"] * exact
                + w["prefix"] * prefix
                - w["extra_words"] * extra * coverage
                + w["popularity"] * self.popularity.get(pid, 0.0)
            )
            scored.append((pid, score, sim))

        scored.sort(key=lambda row: -row[1])
        return scored[:limit]
