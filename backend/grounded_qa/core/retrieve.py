########################################################################
#                 backend/grounded_qa/core/retrieve.py                 #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Finds the passages most likely to answer a       #
#                     question: by words, by meaning, or both fused.   #
########################################################################
"""Retrieval: keyword (BM25), semantic (embeddings) or hybrid.

Hybrid mode fuses the two rankings with reciprocal rank fusion: each
passage scores 1 / (rrf_k + rank) in every ranking it appears in, so
a passage both rankers like rises, and neither ranker's raw scores
need to be put on a common scale.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from kds.logs import get_logger

from grounded_qa.config import AppSettings
from grounded_qa.core.chunk import Passage
from grounded_qa.core.embed import Embedder, cosine
from grounded_qa.core.keyword import Bm25

# Module constants
log = get_logger(__name__)
# log.debug("Names the mode that ranks by shared words only")
KEYWORD = "keyword"
# log.debug("Names the mode that ranks by meaning only")
SEMANTIC = "semantic"


# log.debug("Defines one retrieved passage and how it ranked")
@dataclass(frozen=True)
class Hit:
    """A passage, its final score, and its rank in each ranking."""

    # log.debug("Holds the passage")
    passage: Passage
    # log.debug("Holds the score it was ordered by")
    score: float
    # log.debug("Holds its keyword rank from 1, or None if unranked")
    keyword_rank: int | None = None
    # log.debug("Holds its semantic rank from 1, or None if unranked")
    semantic_rank: int | None = None


# log.debug("Defines reciprocal rank fusion")
def fuse(rankings: list[list[int]], rrf_k: int) -> list[tuple[int, float]]:
    """Return (index, fused score) pairs, best first, ties by index."""
    # log.debug("Starts every passage at zero")
    scores: dict[int, float] = defaultdict(float)
    # log.debug("Walks each ranking")
    for ranking in rankings:
        # log.debug("Adds 1 / (rrf_k + rank) for each ranked passage")
        for rank, index in enumerate(ranking, start=1):
            # log.debug("Adds this ranking's share to the passage")
            scores[index] += 1 / (rrf_k + rank)
    # log.debug("Returns the passages by fused score")
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))


# log.debug("Defines the retriever over one fixed set of passages")
class Retriever:
    """Ranks a fixed list of passages against questions."""

    # log.debug("Defines the constructor, which builds the indexes")
    def __init__(
        self, passages: list[Passage], settings: AppSettings, embedder: Embedder | None = None
    ) -> None:
        """Index the passages for the configured mode.

        Raises:
            ValueError: A semantic or hybrid mode has no embedder.
        """
        # log.debug("Keeps the passages, in a fixed order")
        self.passages = tuple(passages)
        # log.debug("Keeps the settings retrieval uses")
        self.settings = settings
        # log.debug("Keeps the mode")
        self.mode = settings.retrieval_mode
        # log.debug("Refuses a mode that needs meaning without an embedder")
        if self.mode != KEYWORD and embedder is None:
            # log.debug("Words the error")
            msg = f"retrieval mode {self.mode!r} needs an embedder"
            # log.debug("Raises it")
            raise ValueError(msg)
        # log.debug("Keeps the embedder for questions")
        self.embedder = embedder
        # log.debug("Builds the keyword index over each passage's search text")
        self.bm25 = Bm25.build(
            [p.search_text for p in self.passages],
            k1=settings.retrieval_bm25_k1,
            b=settings.retrieval_bm25_b,
        )
        # log.debug("Embeds the passages once, when meaning is used")
        self.vectors = (
            embedder.passages([p.search_text for p in self.passages])
            if embedder is not None and self.mode != KEYWORD
            else []
        )

    # log.debug("Defines a search for one question")
    def search(self, question: str, k: int | None = None) -> list[Hit]:
        """Return the best `k` passages for the question, best first."""
        # log.debug("Uses the configured k unless one is given")
        limit = k or self.settings.retrieval_k
        # log.debug("Ranks by shared words unless the mode is semantic")
        keyword = [] if self.mode == SEMANTIC else self._keyword(question)
        # log.debug("Ranks by meaning unless the mode is keyword")
        semantic = [] if self.mode == KEYWORD else self._semantic(question)
        # log.debug("Notes each passage's rank in each ranking")
        ranks = (
            {i: r for r, i in enumerate(keyword, 1)},
            {i: r for r, i in enumerate(semantic, 1)},
        )
        # log.debug("Orders by one ranking, or fuses both in hybrid mode")
        order = self._order(keyword, semantic)
        # log.debug("Returns the best passages with their ranks")
        return [
            Hit(self.passages[i], round(score, 6), ranks[0].get(i), ranks[1].get(i))
            for i, score in order[:limit]
        ]

    # log.debug("Defines the keyword ranking")
    def _keyword(self, question: str) -> list[int]:
        """Return passage indexes by BM25 score, best first."""
        # log.debug("Returns the indexes from the BM25 ranking")
        return [i for i, _ in self.bm25.rank(question, self.settings.retrieval_pool)]

    # log.debug("Defines the semantic ranking")
    def _semantic(self, question: str) -> list[int]:
        """Return passage indexes by cosine similarity, best first."""
        # log.debug("Returns nothing without an embedder")
        if self.embedder is None:
            # log.debug("Returns an empty ranking")
            return []
        # log.debug("Embeds the question")
        query = self.embedder.queries([question])[0]
        # log.debug("Scores every passage against it")
        scored = [(i, cosine(query, vector)) for i, vector in enumerate(self.vectors)]
        # log.debug("Orders by similarity, ties by position")
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        # log.debug("Returns the best indexes")
        return [i for i, _ in scored[: self.settings.retrieval_pool]]

    # log.debug("Defines the final order from the rankings")
    def _order(self, keyword: list[int], semantic: list[int]) -> list[tuple[int, float]]:
        """Return (index, score) pairs in the order hits go out."""
        # log.debug("Fuses the rankings; a single ranking fuses to itself")
        return fuse([r for r in (keyword, semantic) if r], self.settings.retrieval_rrf_k)
