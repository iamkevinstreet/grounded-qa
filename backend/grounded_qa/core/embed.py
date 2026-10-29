########################################################################
#                  backend/grounded_qa/core/embed.py                   #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Turns text into vectors for search by meaning:   #
#                     the interface, and a local model behind it.      #
########################################################################
"""Embedders: the interface semantic search depends on, and one model.

Retrieval depends on the `Embedder` protocol, not on a library, so
tests pass a small stand-in and the real model is chosen once, in
config. `LocalEmbedder` runs BAAI/bge-small-en-v1.5 on the CPU through
fastembed (the optional `local` extra); it downloads the model, about
67 MB, the first time, and needs no API key.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any, Protocol

from kds.logs import get_logger

# Module constants
log = get_logger(__name__)
# log.debug("Sets the message when the optional model is not installed")
MISSING = (
    "semantic and hybrid retrieval need the local extra: "
    "uv sync --project backend --extra local (or set [retrieval] mode = keyword)"
)


# log.debug("Defines what any embedder must offer")
class Embedder(Protocol):
    """Turns questions and passages into comparable vectors."""

    # log.debug("Names the model, for logs and results")
    name: str

    # log.debug("Defines the vectors for questions")
    def queries(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per question."""

    # log.debug("Defines the vectors for passages")
    def passages(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per passage."""


# log.debug("Defines the error for a missing optional install")
class MissingExtraError(RuntimeError):
    """The optional embedding model is not installed."""


# log.debug("Defines the local embedding model")
class LocalEmbedder:
    """A small embedding model run on the CPU through fastembed."""

    # log.debug("Defines the constructor, which loads the model")
    def __init__(self, model: str) -> None:
        """Load `model`, downloading it on first use.

        Raises:
            MissingExtraError: fastembed is not installed.
        """
        # log.debug("Tries the optional import")
        try:
            # log.debug("Imports fastembed only when this embedder is built")
            from fastembed import TextEmbedding  # noqa: PLC0415 - optional extra
        except ImportError as error:
            # log.debug("Explains how to install it")
            raise MissingExtraError(MISSING) from error
        # log.debug("Keeps the model's name")
        self.name = model
        # log.debug("Loads the model")
        self._model = TextEmbedding(model_name=model)

    # log.debug("Defines the vectors for questions")
    def queries(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per question, with the query prefix."""
        # log.debug("Returns the question vectors as plain lists")
        return _lists(self._model.query_embed(texts))

    # log.debug("Defines the vectors for passages")
    def passages(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per passage."""
        # log.debug("Returns the passage vectors as plain lists")
        return _lists(self._model.passage_embed(texts))


# log.debug("Defines the similarity of two vectors")
def cosine(a: list[float], b: list[float]) -> float:
    """Return the cosine of the angle between two vectors, -1 to 1."""
    # log.debug("Multiplies the vectors' lengths")
    norms = math.hypot(*a) * math.hypot(*b)
    # log.debug("Returns the normalised dot product, or 0 for a zero vector")
    return sum(x * y for x, y in zip(a, b, strict=True)) / norms if norms else 0.0


# log.debug("Defines how model output becomes plain lists")
def _lists(vectors: Iterable[Any]) -> list[list[float]]:
    """Return numpy vectors as lists of floats."""
    # log.debug("Converts each vector")
    return [[float(x) for x in vector] for vector in vectors]
