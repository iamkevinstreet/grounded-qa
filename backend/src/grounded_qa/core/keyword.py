########################################################################
#               backend/src/grounded_qa/core/keyword.py                #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Ranks passages by the words they share with a    #
#                     question, using BM25; needs no model or network. #
########################################################################
"""BM25 keyword ranking over passages.

BM25 scores a passage higher for each question term it contains,
more for rare terms than common ones, with diminishing returns for
repeats (k1) and a correction for long passages (b). It is the
baseline every retrieval change here is measured against.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from kds.logs import get_logger

from grounded_qa.core.text import terms

# Module constants
log = get_logger(__name__)
# log.debug("Sets BM25's smoothing, which keeps every term's idf positive")
SMOOTHING = 0.5


# log.debug("Defines a BM25 index over a fixed list of texts")
@dataclass(frozen=True)
class Bm25:
    """Term counts, lengths and term rarity for a list of texts."""

    # log.debug("Holds each text's term counts")
    counts: tuple[Counter[str], ...]
    # log.debug("Holds each text's length in terms")
    lengths: tuple[int, ...]
    # log.debug("Holds each term's inverse document frequency")
    idf: dict[str, float]
    # log.debug("Holds the mean text length")
    average: float
    # log.debug("Holds the term-frequency saturation, k1")
    k1: float
    # log.debug("Holds the length normalisation, b")
    b: float

    # log.debug("Defines how the index is built from texts")
    @classmethod
    def build(cls, texts: list[str], *, k1: float, b: float) -> Bm25:
        """Count each text's terms and each term's rarity."""
        # log.debug("Counts the terms in each text")
        counts = tuple(Counter(terms(text)) for text in texts)
        # log.debug("Counts how many texts contain each term")
        frequency = Counter(term for count in counts for term in count)
        # log.debug("Notes how many texts there are")
        total = len(counts)
        # log.debug("Measures each text's length in terms")
        lengths = tuple(sum(count.values()) for count in counts)
        # log.debug("Returns the index with the standard BM25 idf")
        return cls(
            counts=counts,
            lengths=lengths,
            idf={
                t: math.log(1 + (total - n + SMOOTHING) / (n + SMOOTHING))
                for t, n in frequency.items()
            },
            average=(sum(lengths) / total) if total else 0.0,
            k1=k1,
            b=b,
        )

    # log.debug("Defines one text's score for a question's terms")
    def score(self, index: int, query: list[str]) -> float:
        """Return the BM25 score of text `index` for the query terms."""
        # log.debug("Takes the text's term counts")
        count = self.counts[index]
        # log.debug("Scales the saturation by the text's relative length")
        norm = self.k1 * (1 - self.b + self.b * self.lengths[index] / (self.average or 1))
        # log.debug("Returns the sum over the query terms the text holds")
        return sum(
            self.idf[term] * count[term] * (self.k1 + 1) / (count[term] + norm)
            for term in query
            if term in count
        )

    # log.debug("Defines the ranking of every text for a question")
    def rank(self, question: str, limit: int) -> list[tuple[int, float]]:
        """Return up to `limit` (index, score) pairs, best first.

        Texts that share no term with the question are left out, so an
        off-topic question can come back with nothing.
        """
        # log.debug("Turns the question into search terms")
        query = terms(question)
        # log.debug("Scores every text")
        scored = [(index, self.score(index, query)) for index in range(len(self.counts))]
        # log.debug("Keeps texts that matched, best first, ties by order")
        ranked = sorted(((i, s) for i, s in scored if s > 0), key=lambda pair: (-pair[1], pair[0]))
        # log.debug("Returns the best `limit` of them")
        return ranked[:limit]
