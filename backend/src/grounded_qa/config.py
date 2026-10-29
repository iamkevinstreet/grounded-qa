########################################################################
#                  backend/src/grounded_qa/config.py                   #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           The one place settings are read: the shared kds  #
#                     settings plus data, retrieval, answer and API.   #
########################################################################
"""Settings for the grounded Q&A service.

Each field is a `[section] key` in config/settings.toml, joined by an
underscore: `[retrieval] mode` is `retrieval_mode`, which the
environment variable RETRIEVAL_MODE overrides. The approver token, the
only secret this service adds, lives in .env as APPROVER_TOKEN.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from kds.logs import get_logger
from kds.settings import Settings
from pydantic import Field, SecretStr, field_validator

# Module constants
log = get_logger(__name__)
# log.debug("Lists how passages can be found: by words, by meaning, or both")
Mode = Literal["keyword", "semantic", "hybrid"]
# log.debug("Sets the shortest approver token accepted, in characters")
MIN_TOKEN_CHARS = 32
# log.debug("Sets the most passages one question may be shown")
MAX_K = 20
# log.debug("Sets the shortest answer limit worth allowing, in words")
MIN_ANSWER_WORDS = 20
# log.debug("Sets the longest passage allowed, in words")
MAX_PASSAGE_WORDS = 1000
# log.debug("Sets the smallest source size limit allowed, in bytes")
MIN_SOURCE_BYTES = 1000


# log.debug("Defines the service's settings on top of the shared ones")
class AppSettings(Settings):
    """Grounded Q&A settings; config/settings.toml lists each one."""

    # log.debug("Holds the folder of approved source documents")
    data_sources: Path = Path("data/sources")
    # log.debug("Holds the synthetic documents the evaluation adds")
    data_samples: Path = Path("data/samples")
    # log.debug("Holds the evaluation's questions and expected answers")
    data_cases: Path = Path("data/evals/cases.jsonl")
    # log.debug("Holds where evaluation results are written")
    data_results: Path = Path("data/evals/results")
    # log.debug("Holds the append-only log of source changes")
    data_audit: Path = Path("data/generated/audit.sqlite")

    # log.debug("Holds how passages are found")
    retrieval_mode: Mode = "keyword"
    # log.debug("Holds how many passages the model is shown")
    retrieval_k: int = Field(default=6, ge=1, le=MAX_K)
    # log.debug("Holds how many candidates each ranker passes to fusion")
    retrieval_pool: int = Field(default=50, ge=1)
    # log.debug("Holds the rank constant of reciprocal rank fusion")
    retrieval_rrf_k: int = Field(default=60, ge=1)
    # log.debug("Holds BM25's term-frequency saturation, k1")
    retrieval_bm25_k1: float = Field(default=1.2, ge=0)
    # log.debug("Holds BM25's length normalisation, b")
    retrieval_bm25_b: float = Field(default=0.75, ge=0, le=1)
    # log.debug("Holds the local embedding model for semantic retrieval")
    retrieval_model: str = "BAAI/bge-small-en-v1.5"
    # log.debug("Holds the most words one passage may hold")
    retrieval_passage_words: int = Field(default=180, ge=40, le=MAX_PASSAGE_WORDS)

    # log.debug("Holds the fewest words a citation's quote may have")
    answer_min_quote_words: int = Field(default=4, ge=1)
    # log.debug("Holds the most words an answer may run to")
    answer_max_words: int = Field(default=150, ge=MIN_ANSWER_WORDS)

    # log.debug("Holds phrases planted in data/samples that no answer may repeat")
    eval_canaries: tuple[str, ...] = ("KESTREL-9", "PINEAPPLE-7")

    # log.debug("Holds the address the server listens on; local only by default")
    api_host: str = "127.0.0.1"
    # log.debug("Holds the port the server listens on")
    api_port: int = Field(default=8000, ge=1, le=65535)
    # log.debug("Holds the shortest question accepted")
    api_min_question_chars: int = Field(default=3, ge=1)
    # log.debug("Holds the longest question accepted")
    api_max_question_chars: int = Field(default=1000, ge=10)
    # log.debug("Holds the largest source document an approver may add")
    api_max_source_bytes: int = Field(default=200_000, ge=MIN_SOURCE_BYTES)
    # log.debug("Holds how many questions one client may ask a minute")
    api_asks_per_minute: int = Field(default=20, ge=1)
    # log.debug("Holds the browser origins allowed to call the API")
    api_allowed_origins: tuple[str, ...] = ("http://localhost:5173",)

    # log.debug("Holds the approver's bearer token, a secret; unset turns admin off")
    approver_token: SecretStr | None = None

    # log.debug("Defines the check that the approver token is strong enough")
    @field_validator("approver_token")
    @classmethod
    def _strong_token(cls, token: SecretStr | None) -> SecretStr | None:
        """Refuse a token short enough to guess."""
        # log.debug("Refuses a token under the minimum length")
        if token is not None and len(token.get_secret_value()) < MIN_TOKEN_CHARS:
            # log.debug("Words the error with how to make a strong one")
            msg = (
                f"APPROVER_TOKEN needs at least {MIN_TOKEN_CHARS} characters; make one with "
                "python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
            # log.debug("Raises it")
            raise ValueError(msg)
        # log.debug("Returns the token")
        return token


# log.debug("Defines the loader every module calls")
@lru_cache(maxsize=1)
def get_app_settings() -> AppSettings:
    """Return the service's settings, built and validated once."""
    # log.debug("Builds and validates the settings")
    return AppSettings()
