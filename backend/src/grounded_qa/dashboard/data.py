########################################################################
#                                                                      #
#              backend/src/grounded_qa/dashboard/data.py               #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-03
Last modified on:  2026-11-03

Reads the answer runs in the results folder into the three tables the
dashboard and the Tableau export share, and names each run. A run file
is a JSON object with a "summary" key: the live runs and the offline
baseline. The retrieval-only runs, index.json and figures.json sit
beside them and are skipped. A run by the offline stand-in is marked
offline and read only when asked for. The dashboard and the export
(evals/export.py) read the same tables, so they always agree. The
columns are named in the config's [columns] table; rows.py builds the
rows below a run.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Final

# Third-party
import pandas as pd
from kds.args import required
from kds.logs import get_logger

# Local
from grounded_qa.config import SETTINGS
from grounded_qa.dashboard.rows import (
    case_head,
    case_row,
    citation_columns,
    citation_rows,
    mode_of,
)

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the run id column, from the config")
RUN_ID: Final = SETTINGS.columns_run_id
# log.debug("Takes the column of each run's long label, from the config")
RUN: Final = SETTINGS.columns_run
# log.debug("Takes the model column, from the config")
MODEL: Final = SETTINGS.columns_model
# log.debug("Takes the retrieval mode column, from the config")
MODE: Final = SETTINGS.columns_mode
# log.debug("Takes the start time column, from the config")
STARTED_AT: Final = SETTINGS.columns_started_at
# log.debug("Takes the column that says whether a run is live or offline, from the config")
KIND: Final = SETTINGS.columns_kind
# log.debug("Takes the column of the date of a run's list prices, from the config")
PRICES_AS_OF: Final = SETTINGS.columns_prices_as_of
# log.debug("Takes the runs table's cost per question column, from the config")
COST_PER_CASE: Final = SETTINGS.columns_cost_per_case
# log.debug("Takes the provider that means the offline stand-in, from the config")
OFFLINE_PROVIDER: Final = SETTINGS.llm_offline_provider
# log.debug("Takes the encoding run files are read in, from the config")
ENCODING: Final = SETTINGS.text_encoding

########################################################################
#                                                                      #
#                           Local constants                            #
#                                                                      #
########################################################################
# log.debug("Names the kind of run that called a real model")
LIVE: Final = "live"
# log.debug("Names the kind of run the offline stand-in answered")
OFFLINE: Final = "offline"
# log.debug("Names the key only an answer run file has: its summary")
SUMMARY: Final = "summary"
# log.debug("Names the key that holds a run's questions")
RESULTS: Final = "results"
# log.debug("Names the key and column of a run's provider")
PROVIDER: Final = "provider"
# log.debug("Names the key and column of a run's number of questions")
CASE_COUNT: Final = "cases"
# log.debug("Names the key and column of a run's failed questions")
FAILURES: Final = "failures"
# log.debug("Lists the summary measures a run's row carries, in column order")
SUMMARY_COLUMNS: Final = (
    "correct",
    "answered",
    "abstained_correctly",
    "citation_precision",
    "recall_at_k",
    "mrr",
    "dropped",
    "forbidden_hit",
    "latency_p50_ms",
    "latency_p95_ms",
    COST_PER_CASE,
    "cost_total_usd",
    "failure_rate",
)
# log.debug("Sets how much of an ISO time a long label keeps: up to the minute")
TO_THE_MINUTE: Final = 16


########################################################################
#                                                                      #
#                              Run tables                              #
#                                                                      #
########################################################################
# log.debug("Defines how the run files are read")
def load_runs(results: Path | None = None, *, offline: bool = False) -> list[dict[str, Any]]:
    """Returns the answer runs in the folder, newest first.

    Args:
        results: The results folder. Required.
        offline: Whether to read the offline stand-in's runs as well.

    Returns:
        Each run file's contents, with its file stem as run_id, its
        kind (live or offline) and its retrieval mode, sorted by start
        time. A folder that does not exist holds no runs.
    """
    # log.debug("Takes the results folder, which the caller must give")
    results = required(results=results)
    # log.debug("Starts with no runs")
    runs: list[dict[str, Any]] = []
    # log.debug("Reads each JSON file in name order")
    for path in sorted(results.glob("*.json")):
        # log.debug("Parses the file")
        run = json.loads(path.read_text(encoding=ENCODING))
        # log.debug("Skips the retrieval runs, index.json, figures.json and anything else")
        if SUMMARY not in run:
            # log.debug("Moves to the next file")
            continue
        # log.debug("Marks the run live, or offline when the stand-in answered")
        kind = OFFLINE if run[PROVIDER] == OFFLINE_PROVIDER else LIVE
        # log.debug("Leaves an offline run out unless they are wanted")
        if kind == OFFLINE and not offline:
            # log.debug("Moves to the next file")
            continue
        # log.debug("Names the run after its file")
        run[RUN_ID] = path.stem
        # log.debug("Keeps the kind")
        run[KIND] = kind
        # log.debug("Reads the retrieval mode from the first saved answer")
        run[MODE] = mode_of(run[RESULTS])
        # log.debug("Keeps the run")
        runs.append(run)
    # log.debug("Puts the newest first; runs that started together keep their order")
    runs.sort(key=lambda run: run[STARTED_AT], reverse=True)
    # log.debug("Returns the runs")
    return runs


# log.debug("Defines the three tidy tables")
def frames(
    runs: list[dict[str, Any]] | None = None,
    evidence: dict[str, list[list[str]]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Returns a row per run, per question, and per citation.

    Args:
        runs: Runs as `load_runs` returns them. Required.
        evidence: Each case's evidence groups from `evidence_spans`,
            to mark the citations whose passage holds evidence; None
            leaves that column unknown.

    Returns:
        The runs, questions and citations tables, in that order.
    """
    # log.debug("Takes the runs, which the caller must give")
    runs = required(runs=runs)
    # log.debug("Starts the run rows")
    run_rows: list[dict[str, Any]] = []
    # log.debug("Starts the question rows")
    case_rows: list[dict[str, Any]] = []
    # log.debug("Starts the citation rows")
    cited_rows: list[dict[str, Any]] = []
    # log.debug("Walks the runs")
    for run in runs:
        # log.debug("Labels the run with its model, mode and start, to the minute")
        label = _long_label(run)
        # log.debug("Adds the run's row")
        run_rows.append(_run_row(run, label))
        # log.debug("Walks the run's questions")
        for case in run[RESULTS]:
            # log.debug("Takes the columns a question's row and its citation rows share")
            head = case_head(run, label, case)
            # log.debug("Adds the question's row")
            case_rows.append(case_row(head, case))
            # log.debug("Adds a row for each citation in the answer")
            cited_rows.extend(citation_rows(head, case, evidence))
    # log.debug("Returns the three tables, the citations with their columns even when empty")
    return (
        pd.DataFrame(run_rows),
        pd.DataFrame(case_rows),
        pd.DataFrame(cited_rows, columns=None if cited_rows else citation_columns()),
    )


# log.debug("Defines the short names of the runs picked")
def run_labels(
    runs_df: pd.DataFrame | None = None, run_ids: Sequence[str] | None = None
) -> dict[str, str]:
    """Returns a short name for each run picked: its mode and start.

    The model leads the name when the runs picked mix models, and an
    offline run says so. Ids the table does not hold are left out.

    Args:
        runs_df: The runs table from `frames`. Required.
        run_ids: The runs picked, in order. Required.

    Returns:
        Each run's short name by its id, in the order picked.
    """
    # log.debug("Takes the runs table, which the caller must give")
    runs_df = required(runs_df=runs_df)
    # log.debug("Takes the run ids, which the caller must give")
    run_ids = required(run_ids=run_ids)
    # log.debug("Lists the run ids the table holds")
    known = set(runs_df[RUN_ID])
    # log.debug("Takes the rows of the runs picked, in the order picked")
    picked = runs_df.set_index(RUN_ID).loc[[r for r in run_ids if r in known]]
    # log.debug("Notes whether the runs picked mix models")
    mixed = picked[MODEL].nunique() > 1
    # log.debug("Returns each run's short name by id")
    return {str(run_id): _short_label(row, mixed=mixed) for run_id, row in picked.iterrows()}


# log.debug("Defines a run's long label")
def _long_label(run: dict[str, Any] | None = None) -> str:
    """Returns the model, mode and start time to the minute.

    Args:
        run: A run, as `load_runs` marks it. Required.

    Returns:
        The model, the mode and the start time to the minute, with
        offline after them for an offline run.
    """
    # log.debug("Takes the run, which the caller must give")
    run = required(run=run)
    # log.debug("Cuts the start time to the minute, with a space for the T")
    stamp = run[STARTED_AT][:TO_THE_MINUTE].replace("T", " ")
    # log.debug("Lists the parts: the model, the mode, the time, and offline when it is")
    parts = (run[MODEL], run[MODE], stamp, OFFLINE if run[KIND] == OFFLINE else "")
    # log.debug("Returns the parts that are not empty, joined")
    return " ".join(part for part in parts if part)


# log.debug("Defines one run's row")
def _run_row(run: dict[str, Any] | None = None, label: str | None = None) -> dict[str, Any]:
    """Returns the run's row: what, when, how many, and its summary.

    Args:
        run: A run, as `load_runs` marks it. Required.
        label: The run's long label. Required.

    Returns:
        The run's id, label, model, provider, mode, start, kind, list
        prices' date, questions and failures, then its summary
        measures; a measure the summary lacks is None.
    """
    # log.debug("Takes the run, which the caller must give")
    run = required(run=run)
    # log.debug("Takes the label, which the caller must give")
    label = required(label=label)
    # log.debug("Reads the run's summary measures")
    summary = run[SUMMARY]
    # log.debug("Returns the row, a measure the summary lacks as None")
    return {
        RUN_ID: run[RUN_ID],
        RUN: label,
        MODEL: run[MODEL],
        PROVIDER: run[PROVIDER],
        MODE: run[MODE],
        STARTED_AT: run[STARTED_AT],
        KIND: run[KIND],
        PRICES_AS_OF: run.get(PRICES_AS_OF),
        CASE_COUNT: run[CASE_COUNT],
        FAILURES: run[FAILURES],
        **{name: summary.get(name) for name in SUMMARY_COLUMNS},
    }


# log.debug("Defines one run's short name")
def _short_label(row: pd.Series[Any] | None = None, *, mixed: bool | None = None) -> str:
    """Returns the run's mode and start in UTC, model first if mixed.

    Args:
        row: The run's row in the runs table. Required.
        mixed: Whether the runs picked mix models. Required.

    Returns:
        The run's mode and its start in UTC, after its model when the
        runs mix models, marked when it is an offline run.
    """
    # log.debug("Takes the row, which the caller must give")
    row = required(row=row)
    # log.debug("Takes whether the runs mix models, which the caller must give")
    mixed = required(mixed=mixed)
    # log.debug("Reads the start time, a trailing Z as UTC")
    when = datetime.fromisoformat(str(row[STARTED_AT]).replace("Z", "+00:00"))
    # log.debug("Writes the month, day, hours and minutes, in UTC")
    stamp = f"{when.strftime('%b')} {when.day}, {when.strftime('%H:%M')} UTC"
    # log.debug("Puts the model first when the runs picked mix models, then the mode")
    label = ", ".join(p for p in (row[MODEL] if mixed else "", str(row[MODE]), stamp) if p)
    # log.debug("Returns the name, marked when the run is an offline run")
    return label + (f" ({OFFLINE})" if row[KIND] == OFFLINE else "")
