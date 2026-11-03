########################################################################
#                                                                      #
#                   backend/tests/test_dashboard.py                    #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-03
Last modified on:  2026-11-03

Tests the dashboard's tables, the Tableau, figures and index exports,
the command line and the app. The charts and tiles have their own
tests.

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

import copy
import json
from pathlib import Path

# Third-party
import pytest
from kds.logs import get_logger

# Local
from grounded_qa.config import get_app_settings
from grounded_qa.dashboard.__main__ import main
from grounded_qa.dashboard.app import build_app
from grounded_qa.dashboard.data import frames, load_runs, run_labels
from grounded_qa.dashboard.export import export_figures
from grounded_qa.dashboard.outcome_charts import fig_outcomes
from grounded_qa.dashboard.retrieval_charts import fig_retrieval
from grounded_qa.dashboard.rows import evidence_spans
from grounded_qa.evals.export import export
from grounded_qa.evals.index import build_index
from support import RUN, one_run, two_runs, write_cases

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
# log.debug("Matches Dash 4's warning that its tables will move to a separate package")
TABLE_DEPRECATED = r"ignore:\s*The dash_table.DataTable will be removed:DeprecationWarning"


########################################################################
#                                                                      #
#                           Dashboard tests                            #
#                                                                      #
########################################################################
# log.debug("Defines the test of the tables and the single-run charts")
def test_frames_and_figures(tmp_path: Path) -> None:
    """Checks one run makes a run row, three questions and a citation.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Builds the tables")
    runs_df, questions_df, citations_df = frames(load_runs(one_run(tmp_path)))
    # log.debug("Checks the row counts")
    assert [len(runs_df), len(questions_df), len(citations_df)] == [1, 3, 1]
    # log.debug("Checks the run's label carries its model, mode and start")
    assert runs_df["run"].tolist() == ["test-model keyword 2026-10-15 00:00"]
    # log.debug("Checks the kinds of question are named")
    assert questions_df["case_kind"].tolist() == ["Direct", "Everyday words", "Unanswerable"]
    # log.debug("Checks each question's outcome")
    assert questions_df["outcome"].tolist() == ["Right", "Refused wrongly", "Refused rightly"]
    # log.debug("Checks which questions the sources answer")
    assert questions_df["answerable"].tolist() == [True, True, False]
    # log.debug("Checks the citation's quote was found, and its evidence is unknown without cases")
    assert citations_df[["quote_found", "evidence"]].iloc[0].tolist() == [True, None]
    # log.debug("Checks the outcomes chart draws one run: a trace per outcome held")
    assert len(fig_outcomes(questions_df, list(runs_df["run_id"])).data) == 3
    # log.debug("Checks the retrieval chart takes a single run id")
    assert len(fig_retrieval(runs_df, str(runs_df["run_id"].iloc[0])).data) == 1


# log.debug("Defines the test that citations are marked against the cases' evidence")
def test_citations_mark_evidence(tmp_path: Path) -> None:
    """Checks each citation's mark reproduces its question's precision.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Reads the evidence behind the made-up cases")
    evidence = evidence_spans(write_cases(tmp_path))
    # log.debug("Builds the tables of both runs, citations marked")
    _, questions_df, citations_df = frames(load_runs(two_runs(tmp_path)), evidence)
    # log.debug("Checks the four citations: one in the first run, three in the later")
    assert citations_df["run_id"].tolist() == ["t-2", "t-2", "t-2", "t-1"]
    # log.debug("Checks the everyday question's second citation points past the evidence")
    assert citations_df["evidence"].tolist() == [True, True, False, True]
    # log.debug("Averages the marks per question")
    marked = citations_df.groupby(["run_id", "case_id"])["evidence"].mean()
    # log.debug("Reads each question's stored precision")
    stored = questions_df.set_index(["run_id", "case_id"])["citation_precision"].dropna()
    # log.debug("Checks the marks reproduce the stored precision of every cited question")
    assert marked.to_dict() == stored.to_dict()


# log.debug("Defines the test of the Tableau export")
def test_export_writes_three_csvs(tmp_path: Path) -> None:
    """Checks the export writes runs, questions and citations as CSV.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Exports the live run with its cases")
    written = export(one_run(tmp_path), write_cases(tmp_path), tmp_path / "out")
    # log.debug("Checks the three files, in order")
    assert [p.name for p in written] == ["runs.csv", "questions.csv", "citations.csv"]
    # log.debug("Reads the questions file")
    questions = (tmp_path / "out" / "questions.csv").read_text(encoding="utf-8").splitlines()
    # log.debug("Checks it has a header and three rows")
    assert len(questions) == 4
    # log.debug("Checks the header names the columns the brief asks for")
    assert all(
        column in questions[0].split(",")
        for column in ("case_id", "case_kind", "answerable", "outcome", "correct", "latency_ms")
    )
    # log.debug("Reads the citations file")
    citations = (tmp_path / "out" / "citations.csv").read_text(encoding="utf-8").splitlines()
    # log.debug("Checks its header, and its one row with the quote found and marked as evidence")
    assert citations[0].endswith("passage_id,doc_id,title,section,quote_found,evidence")
    # log.debug("Checks the row")
    assert citations[1].endswith("leave#1,leave,Test source leave,Using leave,True,True")


# log.debug("Defines the test of the parts the case study restyles")
def test_export_figures_carries_roles(tmp_path: Path) -> None:
    """Checks each trace says its part, for the case study to restyle.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Exports the figures of both runs")
    payload = export_figures(two_runs(tmp_path), tmp_path / "figures.json")
    # log.debug("Checks the four figures, in order")
    assert [f["name"] for f in payload["figures"]] == ["outcomes", "retrieval", "latency", "cost"]
    # log.debug("Checks the runs, newest first, named by mode and start")
    assert payload["runs"] == [
        {"run_id": "t-2", "label": "hybrid, Oct 15, 01:00 UTC"},
        {"run_id": "t-1", "label": "keyword, Oct 15, 00:00 UTC"},
    ]
    # log.debug("Checks every trace has a part")
    assert all(trace["meta"]["role"] for f in payload["figures"] for trace in f["spec"]["data"])
    # log.debug("Checks the outcome traces say their run too, the run in focus first")
    assert [t["meta"]["run"] for t in payload["figures"][0]["spec"]["data"]][::3] == [
        "run-0",
        "run-1",
    ]
    # log.debug("Checks each figure carries its title")
    assert payload["figures"][2]["spec"]["layout"]["title"]["text"] == "Seconds per question"


# log.debug("Defines the test that the export keeps the latest three runs")
def test_export_figures_keeps_three_runs(tmp_path: Path) -> None:
    """Checks the figures draw up to three runs, newest first.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Writes two runs")
    results = two_runs(tmp_path)
    # log.debug("Copies the run for a third")
    third = copy.deepcopy(RUN)
    # log.debug("Starts it last")
    third["started_at"] = "2026-10-15T02:00:00+00:00"
    # log.debug("Writes it")
    (results / "t-3.json").write_text(json.dumps(third), encoding="utf-8")
    # log.debug("Copies the run for a fourth, older than all")
    fourth = {**third, "started_at": "2026-10-14T02:00:00+00:00"}
    # log.debug("Writes it")
    (results / "t-0.json").write_text(json.dumps(fourth), encoding="utf-8")
    # log.debug("Exports the figures")
    payload = export_figures(results, tmp_path / "figures.json")
    # log.debug("Checks the three latest runs, newest first")
    assert [r["run_id"] for r in payload["runs"]] == ["t-3", "t-2", "t-1"]
    # log.debug("Lists the parts of the time chart's traces")
    roles = [trace["meta"]["role"] for trace in payload["figures"][2]["spec"]["data"]]
    # log.debug("Checks each run has its part")
    assert roles == ["run-0", "run-1", "run-2"]


# log.debug("Defines the test that the export needs live runs")
def test_export_figures_needs_live_runs(tmp_path: Path) -> None:
    """Checks an empty folder is refused, saying what to do.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Exports from a folder that does not exist")
    with pytest.raises(FileNotFoundError, match="no live runs"):
        # log.debug("Tries the export")
        export_figures(tmp_path / "nowhere", tmp_path / "figures.json")


# log.debug("Defines the test of the files that sit beside the live runs")
def test_offline_and_other_files_are_told_apart(tmp_path: Path) -> None:
    """Checks offline runs are marked and asked for; others skipped.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Writes the live run")
    results = one_run(tmp_path)
    # log.debug("Writes an index beside it, which is not a run")
    (results / "index.json").write_text(json.dumps({"runs": ["t-1.json"]}), encoding="utf-8")
    # log.debug("Writes a retrieval-only run beside it, which has no summary")
    (results / "retrieval-1.json").write_text(
        json.dumps({"settings": {}, "results": {"keyword": []}}), encoding="utf-8"
    )
    # log.debug("Writes an offline run a day later, by the stand-in")
    (results / "o-1.json").write_text(
        json.dumps(
            {
                **RUN,
                "model": "fake-model",
                "provider": "fake",
                "started_at": "2026-10-16T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    # log.debug("Reads the live runs alone")
    assert [r["run_id"] for r in load_runs(results)] == ["t-1"]
    # log.debug("Reads every run")
    runs = load_runs(results, offline=True)
    # log.debug("Checks both runs, newest first, each with its kind and mode")
    assert [(r["run_id"], r["kind"], r["mode"]) for r in runs] == [
        ("o-1", "offline", "keyword"),
        ("t-1", "live", "keyword"),
    ]
    # log.debug("Checks a folder that does not exist holds no runs")
    assert load_runs(tmp_path / "nowhere") == []
    # log.debug("Checks the short names lead with the model, since the runs mix, and mark offline")
    assert run_labels(frames(runs)[0], ["o-1", "t-1"]) == {
        "o-1": "fake-model, keyword, Oct 16, 00:00 UTC (offline)",
        "t-1": "test-model, keyword, Oct 15, 00:00 UTC",
    }
    # log.debug("Checks the Tableau export takes the live run when there is one")
    written = export(results, None, tmp_path / "out")
    # log.debug("Checks the runs file holds the one live run")
    assert (written[0].read_text(encoding="utf-8").count("\n")) == 2
    # log.debug("Removes the live run")
    (results / "t-1.json").unlink()
    # log.debug("Checks the export falls back on the offline run")
    assert export(results, None, tmp_path / "out")[0].read_text(encoding="utf-8").count("\n") == 2


# log.debug("Defines the test of the index")
def test_index_lists_live_runs_newest_first(tmp_path: Path) -> None:
    """Checks the index names the live runs, newest first, and figures.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Writes two runs")
    results = two_runs(tmp_path)
    # log.debug("Writes an offline run beside them, which the index leaves out")
    (results / "o-1.json").write_text(json.dumps({**RUN, "provider": "fake"}), encoding="utf-8")
    # log.debug("Checks the runs, newest first, and no figures yet")
    assert build_index(results) == {"runs": ["t-2.json", "t-1.json"], "figures": None}
    # log.debug("Writes the figures")
    export_figures(results, results / "figures.json")
    # log.debug("Checks the index names them, and still lists the same runs")
    assert build_index(results) == {"runs": ["t-2.json", "t-1.json"], "figures": "figures.json"}


# log.debug("Defines the test of the figures command")
def test_command_writes_figures_beside_the_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Checks the figures go beside the runs when no path is given.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
        monkeypatch: pytest's helper for patching the environment and
            objects.
        capsys: pytest's capture of what the test prints.
    """
    # log.debug("Writes two runs")
    results = two_runs(tmp_path)
    # log.debug("Points [data] results at them")
    monkeypatch.setenv("DATA_RESULTS", str(results))
    # log.debug("Forgets any cached settings, so the command reads these")
    get_app_settings.cache_clear()
    # log.debug("Checks the command succeeds")
    assert main(["--export-figures"]) == 0
    # log.debug("Checks it says what it wrote")
    assert "(4 figures for t-2)" in capsys.readouterr().out
    # log.debug("Reads the file it wrote")
    written = json.loads((results / "figures.json").read_text(encoding="utf-8"))
    # log.debug("Checks it holds both runs")
    assert [r["run_id"] for r in written["runs"]] == ["t-2", "t-1"]


# log.debug("Defines the test that the app builds and serves its page")
@pytest.mark.filterwarnings(TABLE_DEPRECATED)
def test_app_builds(tmp_path: Path) -> None:
    """Checks the app lays out its page and serves it in its template.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Builds the app over the live run")
    app = build_app(one_run(tmp_path))
    # log.debug("Checks it has a layout")
    assert app.layout is not None
    # log.debug("Asks it for the page")
    page = app.server.test_client().get("/")
    # log.debug("Checks the page is served")
    assert page.status_code == 200
    # log.debug("Checks it is the site's template, with the app's title")
    assert "<title>Grounded Q&A: evaluation</title>" in page.text
