########################################################################
#                backend/src/grounded_qa/core/embed.py                 #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

Turns text into vectors for search by meaning: the `Embedder` interface
retrieval depends on, and a local model behind it. Because retrieval
depends on the interface, not on a library, tests pass a small
stand-in and the real model is chosen once, from the settings.
`LocalEmbedder` runs BAAI/bge-small-en-v1.5 on the CPU through
fastembed (the optional `local` extra); it downloads the model, about
67 MB, the first time, and needs no API key.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any, Protocol

# Third-party
from kds.args import required
from kds.logs import get_logger

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)

########################################################################
#                           Local constants                            #
########################################################################
# log.debug("Sets the message when the optional model is not installed")
MISSING = (
    "semantic and hybrid retrieval need the local extra: "
    "uv sync --project backend --extra local (or set [retrieval] mode = keyword)"
)


########################################################################
#                              Embeddings                              #
########################################################################
# log.debug("Defines what any embedder must offer")
class Embedder(Protocol):
    """Turns questions and passages into comparable vectors."""

    # log.debug("Names the model, for logs and results")
    name: str

    # log.debug("Defines the vectors for questions")
    def queries(self, texts: list[str] | None = None) -> list[list[float]]:
        """Returns one vector per question.

        Args:
            texts: The questions. Required.

        Returns:
            One vector per question, in order.
        """

    # log.debug("Defines the vectors for passages")
    def passages(self, texts: list[str] | None = None) -> list[list[float]]:
        """Returns one vector per passage.

        Args:
            texts: The passages' search texts. Required.

        Returns:
            One vector per passage, in order.
        """


# log.debug("Defines the error for a missing optional install")
class MissingExtraError(RuntimeError):
    """The optional embedding model is not installed."""


# log.debug("Defines the local embedding model")
class LocalEmbedder:
    """A small embedding model run on the CPU through fastembed."""

    # log.debug("Defines the constructor, which loads the model")
    def __init__(self, model: str | None = None) -> None:
        """Loads `model`, downloading it on first use.

        Args:
            model: The fastembed model's name, as in [retrieval] model.
                Required.

        Raises:
            MissingExtraError: When fastembed is not installed.
        """
        # log.debug("Takes the model, which the caller must give")
        model = required(model=model)
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
    def queries(self, texts: list[str] | None = None) -> list[list[float]]:
        """Returns one vector per question, with the query prefix.

        Args:
            texts: The questions. Required.

        Returns:
            One vector per question, in order.
        """
        # log.debug("Takes the texts, which the caller must give")
        texts = required(texts=texts)
        # log.debug("Returns the question vectors as plain lists")
        return _lists(self._model.query_embed(texts))

    # log.debug("Defines the vectors for passages")
    def passages(self, texts: list[str] | None = None) -> list[list[float]]:
        """Returns one vector per passage.

        Args:
            texts: The passages' search texts. Required.

        Returns:
            One vector per passage, in order.
        """
        # log.debug("Takes the texts, which the caller must give")
        texts = required(texts=texts)
        # log.debug("Returns the passage vectors as plain lists")
        return _lists(self._model.passage_embed(texts))


# log.debug("Defines the similarity of two vectors")
def cosine(a: list[float] | None = None, b: list[float] | None = None) -> float:
    """Returns the cosine of the angle between two vectors, -1 to 1.

    Args:
        a: One vector. Required.
        b: The other vector, of the same length. Required.

    Returns:
        The cosine similarity; 0 when either vector is all zeros.
    """
    # log.debug("Takes the first vector, which the caller must give")
    a = required(a=a)
    # log.debug("Takes the second vector, which the caller must give")
    b = required(b=b)
    # log.debug("Multiplies the vectors' lengths")
    norms = math.hypot(*a) * math.hypot(*b)
    # log.debug("Returns the normalised dot product, or 0 for a zero vector")
    return sum(x * y for x, y in zip(a, b, strict=True)) / norms if norms else 0.0


# log.debug("Defines how model output becomes plain lists")
def _lists(vectors: Iterable[Any] | None = None) -> list[list[float]]:
    """Returns numpy vectors as lists of floats.

    Args:
        vectors: The model's vectors, numpy arrays or any iterables of
            numbers. Required.

    Returns:
        The vectors as lists of floats.
    """
    # log.debug("Takes the vectors, which the caller must give")
    vectors = required(vectors=vectors)
    # log.debug("Converts each vector")
    return [[float(x) for x in vector] for vector in vectors]
