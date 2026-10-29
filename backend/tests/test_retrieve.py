########################################################################
#                    backend/tests/test_retrieve.py                    #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Tests BM25, rank fusion, the three modes, and    #
#                     the error when the embedding model is missing.   #
########################################################################
"""Tests for grounded_qa.core.keyword, retrieve and embed."""

from __future__ import annotations

import builtins
from typing import Any

import pytest
from kds.logs import get_logger

from grounded_qa.config import AppSettings
from grounded_qa.core.chunk import Passage, split_all
from grounded_qa.core.embed import LocalEmbedder, MissingExtraError, cosine
from grounded_qa.core.keyword import Bm25
from grounded_qa.core.retrieve import Retriever, fuse

from support import LEAVE_BODY, OVERTIME_BODY, make_source

# Module constants
log = get_logger(__name__)


# log.debug("Defines a stand-in embedder that counts a few topic words")
class TopicEmbedder:
    """Embeds text as counts of three topic words; enough to rank."""

    # log.debug("Names the stand-in")
    name = "topic-stand-in"

    # log.debug("Defines the vectors for questions")
    def queries(self, texts: list[str]) -> list[list[float]]:
        """Return topic counts for each question."""
        # log.debug("Returns the counts")
        return [self._count(t) for t in texts]

    # log.debug("Defines the vectors for passages")
    def passages(self, texts: list[str]) -> list[list[float]]:
        """Return topic counts for each passage."""
        # log.debug("Returns the counts")
        return [self._count(t) for t in texts]

    # log.debug("Defines the count of the topic words")
    @staticmethod
    def _count(text: str) -> list[float]:
        """Count words about leave, pay and time."""
        # log.debug("Lowercases the text once")
        lower = text.lower()
        # log.debug("Returns one count per topic")
        return [
            float(sum(lower.count(w) for w in ("leave", "absence", "time off"))),
            float(sum(lower.count(w) for w in ("overtime", "pay", "wage"))),
            float(sum(lower.count(w) for w in ("week", "hour", "day"))),
        ]


# log.debug("Defines the passages of the two small sources")
def _passages() -> list[Passage]:
    """Return the passages of the leave and overtime sources."""
    # log.debug("Splits both sources")
    return split_all(
        [make_source("leave", LEAVE_BODY), make_source("overtime", OVERTIME_BODY)], 180
    )


# log.debug("Defines the test that BM25 ranks the matching text first")
def test_bm25_ranks_the_matching_text_first() -> None:
    """The text sharing rare terms ranks first; no match, no rank."""
    # log.debug("Builds an index over three texts")
    index = Bm25.build(
        ["leave for a child", "overtime pay rules", "leave and pay"], k1=1.2, b=0.75
    )
    # log.debug("Checks the overtime question ranks the overtime text first")
    assert index.rank("overtime rules", 3)[0][0] == 1
    # log.debug("Checks an unrelated question ranks nothing")
    assert index.rank("weather in Atlanta", 3) == []


# log.debug("Defines the test of reciprocal rank fusion")
def test_fuse_rewards_agreement() -> None:
    """A passage both rankings place high beats one only ranked once."""
    # log.debug("Fuses two rankings that agree on passage 2")
    fused = fuse([[2, 0, 1], [2, 1]], rrf_k=60)
    # log.debug("Checks passage 2 wins")
    assert fused[0][0] == 2
    # log.debug("Checks its score is two shares of 1/61")
    assert fused[0][1] == pytest.approx(2 / 61)


# log.debug("Defines the test of keyword mode")
def test_keyword_mode_finds_the_overtime_passage(settings: AppSettings) -> None:
    """Keyword search finds the passage sharing the words."""
    # log.debug("Builds a keyword retriever")
    retriever = Retriever(_passages(), settings)
    # log.debug("Searches for the waiver question")
    hits = retriever.search("Can overtime be waived by agreement?")
    # log.debug("Checks the overtime passage ranks first with a keyword rank")
    assert hits[0].passage.doc_id == "overtime" and hits[0].keyword_rank == 1


# log.debug("Defines the test of hybrid mode")
def test_hybrid_mode_ranks_with_both(settings: AppSettings) -> None:
    """Hybrid search records each passage's rank in both rankings."""
    # log.debug("Builds a hybrid retriever with the stand-in embedder")
    hybrid = settings.model_copy(update={"retrieval_mode": "hybrid"})
    # log.debug("Searches with words both rankers use")
    hits = Retriever(_passages(), hybrid, TopicEmbedder()).search("unpaid leave weeks")
    # log.debug("Checks the top hit was ranked by both")
    assert hits[0].keyword_rank is not None and hits[0].semantic_rank is not None


# log.debug("Defines the test that meaning needs an embedder")
def test_semantic_mode_needs_an_embedder(settings: AppSettings) -> None:
    """Semantic mode without an embedder fails fast."""
    # log.debug("Copies the settings to semantic mode")
    semantic = settings.model_copy(update={"retrieval_mode": "semantic"})
    # log.debug("Expects the error")
    with pytest.raises(ValueError, match="needs an embedder"):
        # log.debug("Builds the retriever")
        Retriever(_passages(), semantic)


# log.debug("Defines the test of the missing optional install")
def test_local_embedder_explains_a_missing_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without fastembed the error says how to install it."""
    # log.debug("Keeps the real import")
    real_import = builtins.__import__

    # log.debug("Defines an import that fails only for fastembed")
    def fail_fastembed(name: str, *args: Any, **kwargs: Any) -> Any:
        """Raise ImportError for fastembed; import anything else."""
        # log.debug("Fails the optional import")
        if name == "fastembed":
            # log.debug("Raises as if it were not installed")
            raise ImportError(name)
        # log.debug("Imports anything else as usual")
        return real_import(name, *args, **kwargs)

    # log.debug("Swaps in the failing import")
    monkeypatch.setattr(builtins, "__import__", fail_fastembed)
    # log.debug("Expects the explanation")
    with pytest.raises(MissingExtraError, match="--extra local"):
        # log.debug("Builds the embedder")
        LocalEmbedder("BAAI/bge-small-en-v1.5")


# log.debug("Defines the test of cosine similarity")
def test_cosine() -> None:
    """Same direction is 1, opposite is -1, a zero vector is 0."""
    # log.debug("Checks the same direction")
    assert cosine([1, 2], [2, 4]) == pytest.approx(1.0)
    # log.debug("Checks the opposite direction")
    assert cosine([1, 0], [-1, 0]) == pytest.approx(-1.0)
    # log.debug("Checks a zero vector")
    assert cosine([0, 0], [1, 1]) == 0.0
