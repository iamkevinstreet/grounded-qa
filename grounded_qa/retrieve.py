"""Hybrid retrieval: keyword (BM25) and embedding similarity, merged by reciprocal rank fusion."""

from __future__ import annotations

import math
import re
from collections.abc import Callable

from rank_bm25 import BM25Okapi

from grounded_qa.ingest import Section

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.casefold())


class Retriever:
    def __init__(
        self, sections: list[Section], embed: Callable[[list[str]], list[list[float]]] | None = None
    ):
        self.sections = sections
        self._bm25 = BM25Okapi([tokenize(s.heading + " " + s.text) for s in sections]) if sections else None
        self._embed = embed
        self._has_vectors = bool(sections) and all(s.embedding is not None for s in sections)

    def keyword(self, query: str, k: int) -> list[tuple[Section, float]]:
        if not self._bm25:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [(self.sections[i], float(scores[i])) for i in order if scores[i] > 0]

    def semantic(self, query: str, k: int) -> list[tuple[Section, float]]:
        if not (self._embed and self._has_vectors):
            return []
        q = self._embed([query])[0]
        scored = [(s, _cosine(q, s.embedding or [])) for s in self.sections]
        scored.sort(key=lambda t: -t[1])
        return scored[:k]

    def retrieve(self, query: str, k: int = 5, mode: str = "hybrid") -> list[Section]:
        if mode == "keyword":
            return [s for s, _ in self.keyword(query, k)]
        if mode == "semantic":
            return [s for s, _ in self.semantic(query, k)]
        fused: dict[str, float] = {}
        by_id: dict[str, Section] = {}
        for ranking in (self.keyword(query, k * 2), self.semantic(query, k * 2)):
            for rank, (s, _) in enumerate(ranking, start=1):
                fused[s.id] = fused.get(s.id, 0.0) + 1.0 / (60 + rank)
                by_id[s.id] = s
        return [by_id[i] for i in sorted(fused, key=lambda i: -fused[i])[:k]]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
