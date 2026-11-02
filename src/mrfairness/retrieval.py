"""Small deterministic retrieval engines with optional transformer support."""

from __future__ import annotations

import hashlib
import math
import time
from collections import Counter, defaultdict

from .data import tokenize


def cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


class BM25:
    def __init__(self, documents: list[str], k1: float = 1.5, b: float = 0.75):
        self.documents = documents
        self.k1 = k1
        self.b = b
        self.tokens = [tokenize(document) for document in documents]
        self.lengths = [len(tokens) for tokens in self.tokens]
        self.average_length = sum(self.lengths) / max(1, len(self.lengths))
        document_frequency: Counter[str] = Counter()
        for tokens in self.tokens:
            document_frequency.update(set(tokens))
        self.idf = {
            term: math.log(1 + (len(self.tokens) - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def score(self, query: str, index: int) -> float:
        query_terms = Counter(tokenize(query))
        document_terms = Counter(self.tokens[index])
        score = 0.0
        for term, query_frequency in query_terms.items():
            if term not in document_terms:
                continue
            frequency = document_terms[term]
            length_factor = 1 - self.b + self.b * self.lengths[index] / max(1, self.average_length)
            numerator = frequency * (self.k1 + 1)
            denominator = frequency + self.k1 * length_factor
            score += self.idf.get(term, 0.0) * numerator / denominator * query_frequency
        return score

    def rank(self, query: str) -> list[tuple[int, float]]:
        scores = [(index, self.score(query, index)) for index in range(len(self.documents))]
        return sorted(scores, key=lambda item: (-item[1], item[0]))


class HashingEncoder:
    """Deterministic local encoder used for smoke tests and offline reproducibility."""

    def __init__(self, dimensions: int = 256, salt: str = "mrfairness"):
        self.dimensions = dimensions
        self.salt = salt

    def encode_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in tokenize(text):
            digest = hashlib.sha256(f"{self.salt}|{token}".encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [self.encode_one(text) for text in texts]


class OptionalSentenceTransformer:
    def __init__(self, model_name: str, fallback_dimensions: int = 256):
        self.requested_model = model_name
        self.actual_model = "hashing-fallback"
        self._fallback = HashingEncoder(fallback_dimensions, salt=model_name)
        self._model = None
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(model_name)
            self.actual_model = model_name
        except Exception as exc:  # optional dependency or model download failure
            self.load_error = f"{type(exc).__name__}: {exc}"

    def encode(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            return self._fallback.encode(texts)
        values = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [list(map(float, row)) for row in values]


def dense_rank(query: str, documents: list[str], encoder) -> list[tuple[int, float]]:
    query_vector = encoder.encode([query])[0]
    document_vectors = encoder.encode(documents)
    scores = [(index, cosine(query_vector, vector)) for index, vector in enumerate(document_vectors)]
    return sorted(scores, key=lambda item: (-item[1], item[0]))


def reciprocal_rank_fusion(rankings: list[list[tuple[int, float]]], constant: int = 60) -> list[tuple[int, float]]:
    fused: defaultdict[int, float] = defaultdict(float)
    for ranking in rankings:
        for rank, (index, _score) in enumerate(ranking, start=1):
            fused[index] += 1.0 / (constant + rank)
    return sorted(fused.items(), key=lambda item: (-item[1], item[0]))


def ranking_metrics(ranking: list[tuple[int, float]], gold_index: int, cutoffs=(1, 5, 10)) -> dict:
    rank = next((position for position, (index, _score) in enumerate(ranking, start=1) if index == gold_index), None)
    result = {f"recall@{cutoff}": int(rank is not None and rank <= cutoff) for cutoff in cutoffs}
    result["rank"] = rank or 0
    result["mrr"] = 1.0 / rank if rank else 0.0
    result["ndcg@10"] = 1.0 / math.log2(rank + 1) if rank and rank <= 10 else 0.0
    return result


def timed(callable_, *args, **kwargs):
    start = time.perf_counter()
    value = callable_(*args, **kwargs)
    return value, (time.perf_counter() - start) * 1000.0

