########################################################################
#                                                                      #
#                  backend/src/grounded_qa/config.py                   #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-11-08

Loads the service's settings, the one place they are read: the shared
kds settings plus the service's own data, retrieval, answer, evaluation,
API and dashboard settings, and the values two of its files share.
SETTINGS holds them, built once, for the values modules bind when they
load; code that tests run with other settings takes those settings as a
parameter.

Each field is a `[section] key` in config/config.toml, joined by an
underscore: `[retrieval] mode` is `retrieval_mode`, which the
environment variable RETRIEVAL_MODE overrides. A nested table is one
field: `[labels.kinds]` is `labels_kinds`. The approver token, the only
secret this service adds, lives in config/.env as APPROVER_TOKEN.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Final, Literal

# Third-party
from kds.logs import get_logger
from kds.settings import Settings
from pydantic import Field, SecretStr, field_validator

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)

########################################################################
#                                                                      #
#                           Local constants                            #
#                                                                      #
########################################################################
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
# log.debug("Names the mode that ranks by shared words alone, the default")
KEYWORD_MODE: Final = "keyword"
# log.debug("Sets the milliseconds in a second")
MS_PER_SECOND = 1000
# log.debug("Sets the address that means this machine only")
LOCALHOST: Final = "127.0.0.1"
# log.debug("Sets the highest port number")
MAX_PORT = 65535
# log.debug("Sets the most runs a chart compares: one per step of the run ramp")
MAX_RUNS = 3
# log.debug("Sets the size of chart text, in pixels")
FONT_SIZE = 12
# log.debug("Sets the decimals a cost is written with")
COST_PLACES = 4
# log.debug("Names the service, as spans and MCP clients show it")
NAME = "grounded-qa"
# log.debug("Names each kind of question, by its tag, in the order the charts list them")
KIND_NAMES: Final = {
    "direct": "Direct",
    "paraphrased": "Everyday words",
    "unanswerable": "Unanswerable",
    "adversarial": "Adversarial",
}
# log.debug("Names how a question can end, in the order the outcome chart stacks them")
OUTCOME_NAMES: Final = {
    "right": "Right",
    "missed": "Missed a fact",
    "refused_wrongly": "Refused wrongly",
    "refused_rightly": "Refused rightly",
    "should_have_refused": "Should have refused",
    "failed": "Failed",
}


########################################################################
#                                                                      #
#                           Service settings                           #
#                                                                      #
########################################################################
# log.debug("Defines the service's settings on top of the shared ones")
class AppSettings(Settings):
    """Grounded Q&A settings; config/config.toml lists each one."""

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
    # log.debug("Holds where the CSV files for Tableau go")
    data_export: Path = Path("data/export")
    # log.debug("Holds the name of the figures file in the results folder")
    data_figures: str = "figures.json"

    # log.debug("Holds how passages are found")
    retrieval_mode: Mode = KEYWORD_MODE
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
    # log.debug("Holds the text that joins the headings of a passage's section")
    retrieval_section_separator: str = " > "
    # log.debug("Holds the name of the mode that ranks by shared words alone")
    retrieval_keyword_mode: Mode = KEYWORD_MODE

    # log.debug("Holds the fewest words a citation's quote may have")
    answer_min_quote_words: int = Field(default=4, ge=1)
    # log.debug("Holds the most words an answer may run to")
    answer_max_words: int = Field(default=150, ge=MIN_ANSWER_WORDS)

    # log.debug("Holds phrases planted in data/samples that no answer may repeat")
    eval_canaries: tuple[str, ...] = ("KESTREL-9", "PINEAPPLE-7")
    # log.debug("Holds the field of a case that says whether the sources answer it")
    eval_answerable_field: str = "answerable"
    # log.debug("Holds whether each answered case is also graded by the judge model")
    eval_judge: bool = False
    # log.debug("Holds the judge's own spending limit, on top of the answers' budget")
    eval_judge_budget_usd: float = Field(default=2.0, gt=0)

    # log.debug("Holds the provider name that means the offline stand-in")
    llm_offline_provider: str = "fake"

    # log.debug("Holds the name spans are recorded under")
    spans_service: str = NAME
    # log.debug("Holds what a search span says it looked in")
    spans_source: str = "approved-sources"

    # log.debug("Holds the MCP server's name, as clients list it")
    mcp_name: str = NAME
    # log.debug("Holds where the API serves the MCP server")
    mcp_path: str = "/mcp"
    # log.debug("Holds the name every MCP client's questions count under")
    mcp_client: str = "mcp"

    # log.debug("Holds the address the server listens on; local only by default")
    api_host: str = LOCALHOST
    # log.debug("Holds the port the server listens on")
    api_port: int = Field(default=8000, ge=1, le=MAX_PORT)
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
    # log.debug("Holds the path every route lives under, with its version")
    api_prefix: str = "/api/v1"
    # log.debug("Holds the header that carries each request's id")
    api_request_id_header: str = "X-Request-ID"

    # log.debug("Holds the encoding text is stored, hashed and measured in")
    text_encoding: str = "utf-8"
    # log.debug("Holds the milliseconds in a second, for timings")
    time_ms_per_second: int = MS_PER_SECOND
    # log.debug("Holds how many characters of a SHA-256 the web app shows")
    web_hash_chars: int = Field(default=12, ge=1, le=64)

    # log.debug("Holds the address the dashboard listens on; local only by default")
    dashboard_host: str = LOCALHOST
    # log.debug("Holds the dashboard port")
    dashboard_port: int = Field(default=8050, ge=1, le=MAX_PORT)

    # log.debug("Holds the id of the location, whose first change reads the scheme")
    dashboard_ids_url: str = "url"
    # log.debug("Holds the id of the store that holds the browser's colour scheme")
    dashboard_ids_scheme: str = "scheme"
    # log.debug("Holds the id of the run picker")
    dashboard_ids_runs: str = "runs"
    # log.debug("Holds the id of the runs' key")
    dashboard_ids_legend: str = "legend"
    # log.debug("Holds the id of the headline numbers")
    dashboard_ids_tiles: str = "tiles"
    # log.debug("Holds the id of the outcomes chart")
    dashboard_ids_outcomes: str = "outcomes"
    # log.debug("Holds the id of the retrieval chart")
    dashboard_ids_retrieval: str = "retrieval"
    # log.debug("Holds the id of the time chart")
    dashboard_ids_latency: str = "latency"
    # log.debug("Holds the id of the cost chart")
    dashboard_ids_cost: str = "cost"
    # log.debug("Holds the id of the table of questions that went wrong")
    dashboard_ids_wrong_table: str = "wrong-table"

    # log.debug("Holds the run id column")
    columns_run_id: str = "run_id"
    # log.debug("Holds the column of each run's long label")
    columns_run: str = "run"
    # log.debug("Holds the model column")
    columns_model: str = "model"
    # log.debug("Holds the retrieval mode column")
    columns_mode: str = "mode"
    # log.debug("Holds the start time column")
    columns_started_at: str = "started_at"
    # log.debug("Holds the column that says whether a run is live or offline")
    columns_kind: str = "kind"
    # log.debug("Holds the column of the date of the list prices a run's costs use")
    columns_prices_as_of: str = "prices_as_of"
    # log.debug("Holds the question id column")
    columns_case_id: str = "case_id"
    # log.debug("Holds the kind of question column")
    columns_case_kind: str = "case_kind"
    # log.debug("Holds the column that says how a question ended")
    columns_outcome: str = "outcome"
    # log.debug("Holds the column of each question's time, in milliseconds")
    columns_latency_ms: str = "latency_ms"
    # log.debug("Holds the runs table's cost per question column")
    columns_cost_per_case: str = "cost_per_case_usd"

    # log.debug("Holds the name of the light scheme, which the exported figures use")
    charts_light_scheme: str = "light"
    # log.debug("Holds the name of the dark scheme")
    charts_dark_scheme: str = "dark"
    # log.debug("Holds the most runs a chart compares")
    charts_max_runs: int = Field(default=MAX_RUNS, ge=1)
    # log.debug("Holds the size of chart text")
    charts_font_size: int = FONT_SIZE
    # log.debug("Holds the size of value-axis ticks and small notes")
    charts_tick_size: int = 11
    # log.debug("Holds the margin every chart keeps at its edges")
    charts_edge: int = 8
    # log.debug("Holds the colour that lets the card show through")
    charts_clear: str = "rgba(0,0,0,0)"
    # log.debug("Holds the edge titles and notes line up on")
    charts_align: str = "left"
    # log.debug("Holds the decimals a cost is written with")
    charts_cost_places: int = COST_PLACES
    # log.debug("Holds the tick format of a share axis")
    charts_percent_ticks: str = ".0%"
    # log.debug("Holds the title of the outcomes chart")
    charts_outcomes_title: str = "How each kind of question ended"
    # log.debug("Holds the title of the retrieval chart")
    charts_retrieval_title: str = "Retrieval: recall at k and MRR"
    # log.debug("Holds the title of the time chart")
    charts_latency_title: str = "Seconds per question"
    # log.debug("Holds the title of the cost chart")
    charts_cost_title: str = "Cost per question, at list prices"

    # log.debug("Holds the outcome of a question answered with every expected fact")
    outcomes_right: str = "right"
    # log.debug("Holds the outcome of a question answered without every expected fact")
    outcomes_missed: str = "missed"
    # log.debug("Holds the outcome of an answerable question the service refused")
    outcomes_refused_wrongly: str = "refused_wrongly"
    # log.debug("Holds the outcome of an unanswerable question the service refused")
    outcomes_refused_rightly: str = "refused_rightly"
    # log.debug("Holds the outcome of an unanswerable question the service answered")
    outcomes_should_have_refused: str = "should_have_refused"
    # log.debug("Holds the outcome of a question the run could not finish")
    outcomes_failed: str = "failed"

    # log.debug("Holds the name of each kind of question, by its tag, in chart order")
    labels_kinds: dict[str, str] = Field(default=KIND_NAMES)
    # log.debug("Holds the name of each way a question can end, in stack order")
    labels_outcomes: dict[str, str] = Field(default=OUTCOME_NAMES)

    # log.debug("Holds the approver's bearer token, a secret; unset turns admin off")
    approver_token: SecretStr | None = None

    # log.debug("Defines the check that the approver token is strong enough")
    @field_validator("approver_token")
    @classmethod
    def _strong_token(cls, token: SecretStr | None = None) -> SecretStr | None:
        """Refuses a token short enough to guess.

        Args:
            token: The approver token from the environment or
                config/.env; None when it is unset, which turns the
                approver routes off.

        Returns:
            The token, unchanged.

        Raises:
            ValueError: When the token is shorter than 32 characters.
        """
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
    """Returns the service's settings, built and validated once.

    Tests that change the environment call
    `get_app_settings.cache_clear()`.

    Returns:
        The settings, frozen.
    """
    # log.debug("Builds and validates the settings")
    return AppSettings()


# log.debug("Loads the settings once, for the values modules bind as they load")
SETTINGS: Final = get_app_settings()
