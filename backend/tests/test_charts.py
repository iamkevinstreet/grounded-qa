########################################################################
#                                                                      #
#                     backend/tests/test_charts.py                     #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-03
Last modified on:  2026-11-03

Tests the dashboard's charts and tiles: what a comparison of two runs
draws, what the outcomes chart counts, how the time axis fits the
questions, and how the tiles write a change.

Each test writes its own small runs under tmp_path and passes the
folders explicitly, so none depends on the current folder or settings.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from pathlib import Path

# Third-party
from kds.logs import get_logger

# Local
from grounded_qa.dashboard.data import frames, load_runs
from grounded_qa.dashboard.outcome_charts import fig_outcomes
from grounded_qa.dashboard.retrieval_charts import fig_retrieval
from grounded_qa.dashboard.run_charts import fig_cost, fig_latency
from grounded_qa.dashboard.tiles import tile_rows
from grounded_qa.dashboard.views import wrong_rows
from support import two_runs, write_run

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)


########################################################################
#                                                                      #
#                         Chart and tile tests                         #
#                                                                      #
########################################################################
# log.debug("Defines the test of a two-run comparison")
def test_comparison_draws_each_run(tmp_path: Path) -> None:
    """Checks every chart draws the runs picked, the focus run first.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Builds the tables of both runs")
    runs_df, questions_df, _ = frames(load_runs(two_runs(tmp_path)))
    # log.debug("Picks both, newest first: t-2, then t-1")
    ids = list(runs_df["run_id"])
    # log.debug("Draws the outcomes chart")
    fig = fig_outcomes(questions_df, ids)
    # log.debug("Checks a panel per run, titled by the run's name, which fits on one line")
    assert [note.text for note in fig.layout.annotations] == [
        "test-model hybrid 2026-10-15 01:00",
        "test-model keyword 2026-10-15 00:00",
    ]
    # log.debug("Checks a trace per outcome held in each panel, the run in focus first")
    assert [(t.meta["run"], t.meta["role"]) for t in fig.data] == [
        ("run-0", "right"),
        ("run-0", "refused_wrongly"),
        ("run-0", "refused_rightly"),
        ("run-1", "right"),
        ("run-1", "refused_wrongly"),
        ("run-1", "refused_rightly"),
    ]
    # log.debug("Checks the key names each outcome once, from the first panel")
    assert [t.name for t in fig.data if t.showlegend] == [
        "Right",
        "Refused wrongly",
        "Refused rightly",
    ]
    # log.debug("Checks the retrieval chart has a bar group per run, in focus first")
    assert [t.meta["role"] for t in fig_retrieval(runs_df, ids).data] == ["run-0", "run-1"]
    # log.debug("Checks the time chart has a row per run, in focus first")
    assert [t.meta["role"] for t in fig_latency(questions_df, ids).data] == ["run-0", "run-1"]
    # log.debug("Checks the cost chart has a bar per run, with the list prices' date in its hover")
    cost = fig_cost(runs_df, ids)
    # log.debug("Checks the bars")
    assert [t.meta["role"] for t in cost.data] == ["run-0", "run-1"]
    # log.debug("Checks the date")
    assert list(cost.data[0].customdata) == ["2026-10-15"]
    # log.debug("Checks the wrong-questions table lists the earlier run's refusal only")
    assert [(r["run_id"], r["case_id"]) for r in wrong_rows(questions_df, ids)] == [
        ("t-1", "q-everyday")
    ]


# log.debug("Defines the test of what the outcomes chart counts")
def test_outcomes_count_each_kind(tmp_path: Path) -> None:
    """Checks each kind's bar stacks its questions by how they ended.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Builds the tables of both runs")
    _, questions_df, _ = frames(load_runs(two_runs(tmp_path)))
    # log.debug("Draws the earlier run alone")
    fig = fig_outcomes(questions_df, "t-1")
    # log.debug("Checks the kinds, from the top down, in the config's order")
    assert list(fig.layout.yaxis.categoryarray) == ["Direct", "Everyday words", "Unanswerable"]
    # log.debug("Reads each outcome's count on each kind")
    counts = {t.meta["role"]: list(t.x) for t in fig.data}
    # log.debug("Checks the direct question was right, the everyday one refused wrongly")
    assert counts == {
        "right": [1, 0, 0],
        "refused_wrongly": [0, 1, 0],
        "refused_rightly": [0, 0, 1],
    }
    # log.debug("Checks the hover knows how many questions each kind has")
    assert list(fig.data[0].customdata) == [1, 1, 1]
    # log.debug("Checks a run alone has no panel title")
    assert not fig.layout.annotations


# log.debug("Defines the test of the time axis")
def test_time_axis_fits_most_questions(tmp_path: Path) -> None:
    """Checks a slow question is counted beside its row, not drawn.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Makes thirty times between 4 and 5 seconds and one of 16")
    times = [4000 + 37 * i % 900 for i in range(30)] + [16000]
    # log.debug("Writes them as a run")
    write_run(tmp_path / "results", "t-1", "2026-10-15T00:00:00+00:00", times, 0.001)
    # log.debug("Builds the tables")
    runs_df, questions_df, _ = frames(load_runs(tmp_path / "results"))
    # log.debug("Draws the time chart")
    fig = fig_latency(questions_df, list(runs_df["run_id"]))
    # log.debug("Reads the axis range")
    low, high = fig.layout.xaxis.range
    # log.debug("Checks the axis neither starts at zero nor stretches to the slow one")
    assert 3 < low < 4 and high < 8
    # log.debug("Checks the slow one is noted beside the row")
    assert [note.text for note in fig.layout.annotations] == ["1 slower,<br>up to 16.0 s"]
    # log.debug("Checks the slow one's dot is left out, not cut at the edge")
    assert len(fig.data[0].selectedpoints) == 30
    # log.debug("Checks the row names the typical time: the sixteenth of 31, as the summary does")
    assert fig.layout.yaxis.categoryarray[0].endswith("<b>4.4 s</b> typical")


# log.debug("Defines the test of how the tiles write a change")
def test_tiles_write_each_change(tmp_path: Path) -> None:
    """Checks a change gets its direction and tone, or is no change.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Builds the tables of both runs")
    runs_df, _, _ = frames(load_runs(two_runs(tmp_path)))
    # log.debug("Builds the tiles of the later run against the earlier")
    tiles = {tile["measure"]: tile for tile in tile_rows(runs_df, ["t-2", "t-1"])}
    # log.debug("Checks the six tiles, in order")
    assert list(tiles) == [
        "correct",
        "answered",
        "abstained_correctly",
        "citation_precision",
        "latency_p50_ms",
        "cost_per_case_usd",
    ]
    # log.debug("Checks correct went up fifty points, for the better")
    assert (tiles["correct"]["value"], tiles["correct"]["delta"]) == ("100%", "up 50.0 pts")
    # log.debug("Checks that is for the better")
    assert tiles["correct"]["good"] is True
    # log.debug("Checks the refusals did not change")
    assert (tiles["abstained_correctly"]["delta"], tiles["abstained_correctly"]["good"]) == (
        "no change",
        None,
    )
    # log.debug("Checks the higher cost is for the worse")
    assert (tiles["cost_per_case_usd"]["delta"], tiles["cost_per_case_usd"]["good"]) == (
        "up $0.0005",
        False,
    )
    # log.debug("Checks a lone run has no change")
    assert all(tile["delta"] is None for tile in tile_rows(runs_df, ["t-2"]))


# log.debug("Defines the test that a change too small to show is no change")
def test_tiles_call_a_hidden_change_no_change(tmp_path: Path) -> None:
    """Checks a cost change that rounds away is no change; 2 s is up.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Makes forty times between 4 and 4.7 seconds")
    same = [4000 + 53 * i % 700 for i in range(40)]
    # log.debug("Names the results folder")
    results = tmp_path / "results"
    # log.debug("Writes a first run")
    write_run(results, "t-1", "2026-10-15T00:00:00+00:00", same, 0.013363)
    # log.debug("Writes a second run at a cost that rounds the same")
    write_run(results, "t-2", "2026-10-15T01:00:00+00:00", same, 0.013375)
    # log.debug("Writes a third run 2 seconds slower")
    write_run(results, "t-3", "2026-10-15T02:00:00+00:00", [t + 2000 for t in same], 0.013375)
    # log.debug("Builds the tables")
    runs_df, _, _ = frames(load_runs(results))
    # log.debug("Builds the tiles of the second run against the first")
    near = {tile["measure"]: tile for tile in tile_rows(runs_df, ["t-2", "t-1"])}
    # log.debug("Checks a cost change of $0.000012 rounds to nothing at four places")
    assert near["cost_per_case_usd"]["delta"] == "no change"
    # log.debug("Checks no change is neither good nor bad")
    assert near["cost_per_case_usd"]["good"] is None
    # log.debug("Builds the tiles of the third run against the first")
    far = {tile["measure"]: tile for tile in tile_rows(runs_df, ["t-3", "t-1"])}
    # log.debug("Checks 2 s slower is a rise")
    assert far["latency_p50_ms"]["delta"] == "up 2.0 s"
    # log.debug("Checks it is for the worse")
    assert far["latency_p50_ms"]["good"] is False
