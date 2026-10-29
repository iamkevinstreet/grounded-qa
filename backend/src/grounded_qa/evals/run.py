########################################################################
#                 backend/src/grounded_qa/evals/run.py                 #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Runs the evaluations and writes their results:   #
#                     answers end to end, or retrieval alone.          #
########################################################################
"""Run an evaluation from the command line.

    python -m grounded_qa.evals.run answers --mode keyword
    python -m grounded_qa.evals.run retrieval --modes keyword hybrid

Both search the approved sources plus the synthetic documents in
data/samples, which plant the prompt injections the cases test.
Results go to [data] results as JSON and Markdown.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from typing import Any

from kds.evals import EvalCase, load_cases, run_eval
from kds.logs import get_logger, setup_logging

from grounded_qa.config import AppSettings, Mode, get_app_settings
from grounded_qa.core.answer import Answerer
from grounded_qa.core.chunk import Passage, split_all
from grounded_qa.core.embed import Embedder, LocalEmbedder
from grounded_qa.core.models import Answer
from grounded_qa.core.offline import adapter_for
from grounded_qa.core.retrieve import Retriever
from grounded_qa.core.sources import load_dir
from grounded_qa.evals import retrieval
from grounded_qa.evals.score import score

# Module constants
log = get_logger(__name__)
# log.debug("Lists the retrieval modes a run can use")
MODES: tuple[Mode, ...] = ("keyword", "semantic", "hybrid")
# log.debug("Names the mode that needs no embedding model")
KEYWORD: Mode = "keyword"
# log.debug("Sets the time format in result file names")
STAMP = "%Y%m%dT%H%M%SZ"
# log.debug("Sets the encoding result files are written in")
ENCODING = "utf-8"
# log.debug("Names the subcommand for the end-to-end evaluation")
ANSWERS = "answers"
# log.debug("Names the subcommand, and default run name, for retrieval")
RETRIEVAL = "retrieval"
# log.debug("Names the option that names a run")
NAME_OPTION = "--name"


# log.debug("Defines settings with a different retrieval mode")
def with_mode(settings: AppSettings, mode: Mode) -> AppSettings:
    """Return a copy of the settings that retrieves in `mode`."""
    # log.debug("Returns the copy")
    return settings.model_copy(update={"retrieval_mode": mode})


# log.debug("Defines the passages every evaluation searches")
def corpus(settings: AppSettings) -> list[Passage]:
    """Return the approved sources and synthetic samples, split."""
    # log.debug("Reads both folders and splits them as the service does")
    return split_all(
        load_dir(settings.data_sources) + load_dir(settings.data_samples),
        settings.retrieval_passage_words,
    )


# log.debug("Defines the embedder a set of modes needs")
def embedder_for(modes: list[Mode], settings: AppSettings) -> Embedder | None:
    """Return the local model when any mode searches by meaning."""
    # log.debug("Loads the model once, only when a mode needs it")
    return LocalEmbedder(settings.retrieval_model) if set(modes) - {KEYWORD} else None


# log.debug("Defines the end-to-end evaluation")
def run_answers(settings: AppSettings, mode: Mode, name: str, limit: int | None) -> str:
    """Answer every case and score it; return the run's summary line."""
    # log.debug("Applies the mode to a copy of the settings")
    configured = with_mode(settings, mode)
    # log.debug("Splits the corpus once")
    passages = corpus(configured)
    # log.debug("Indexes the passages by id, for the scorer")
    by_id = {p.id: p for p in passages}
    # log.debug("Builds the configured model, or the offline stand-in")
    adapter = adapter_for(configured)
    # log.debug("Builds the answerer over a retriever for the mode")
    answerer = Answerer(
        Retriever(passages, configured, embedder_for([mode], configured)),
        adapter,
        configured,
        mode=mode,
    )
    # log.debug("Reads the cases, or the first `limit` of them")
    cases = load_cases(configured.data_cases)[:limit]

    # log.debug("Defines the system under test: one question in, an answer out")
    def system(case: EvalCase) -> Answer:
        """Return the service's answer to the case's question."""
        # log.debug("Returns the answer")
        return answerer.ask(case.input["question"])

    # log.debug("Defines the scorer for one case")
    def scorer(case: EvalCase, answer: Answer) -> dict[str, Any]:
        """Return the case's scores."""
        # log.debug("Returns the scores")
        return score(case, answer, by_id, configured.eval_canaries)

    # log.debug("Runs and writes the evaluation")
    run = run_eval(
        name=name,
        cases=cases,
        adapter=adapter,
        system_fn=system,
        scorer_fn=scorer,
        out_dir=configured.data_results,
    )
    # log.debug("Returns a one-line summary")
    return f"{name}: {run.cases} cases, {run.failures} failures, {json.dumps(run.summary)}"


# log.debug("Defines the retrieval evaluation")
def run_retrieval(settings: AppSettings, modes: list[Mode], name: str) -> str:
    """Score retrieval for each mode; write JSON and Markdown."""
    # log.debug("Splits the corpus once")
    passages = corpus(settings)
    # log.debug("Reads the cases")
    cases = load_cases(settings.data_cases)
    # log.debug("Loads the embedding model once, if any mode needs it")
    embedder = embedder_for(modes, settings)
    # log.debug("Scores every case under each mode")
    results: dict[str, list[dict[str, Any]]] = {
        mode: retrieval.evaluate(
            cases,
            Retriever(passages, with_mode(settings, mode), embedder),
        )
        for mode in modes
    }
    # log.debug("Names the files by the time now")
    stamp = datetime.now(UTC).strftime(STAMP)
    # log.debug("Renders the table once")
    table = retrieval.to_markdown(results)
    # log.debug("Creates the results folder")
    settings.data_results.mkdir(parents=True, exist_ok=True)
    # log.debug("Writes every row with the settings that produced them")
    (settings.data_results / f"{name}-{stamp}.json").write_text(
        json.dumps({"settings": _record(settings), "results": results}, indent=2), ENCODING
    )
    # log.debug("Writes the table, and again as the latest")
    for path in (f"{name}-{stamp}.md", f"{name}-latest.md"):
        # log.debug("Writes one copy")
        (settings.data_results / path).write_text(f"# Retrieval: {stamp}\n\n{table}", ENCODING)
    # log.debug("Returns the table")
    return table


# log.debug("Defines the settings a retrieval result records")
def _record(settings: AppSettings) -> dict[str, Any]:
    """Return the retrieval settings that shape the results."""
    # log.debug("Returns the passage, ranking and model settings")
    return {
        "passage_words": settings.retrieval_passage_words,
        "pool": settings.retrieval_pool,
        "rrf_k": settings.retrieval_rrf_k,
        "bm25_k1": settings.retrieval_bm25_k1,
        "bm25_b": settings.retrieval_bm25_b,
        "model": settings.retrieval_model,
    }


# log.debug("Defines the command-line parser")
def _parser() -> argparse.ArgumentParser:
    """Build the parser with the answers and retrieval subcommands."""
    # log.debug("Creates the parser")
    parser = argparse.ArgumentParser(prog="grounded_qa.evals.run")
    # log.debug("Adds the subcommand slot")
    sub = parser.add_subparsers(dest="command", required=True)
    # log.debug("Adds answers, with its mode, name and case limit")
    answers = sub.add_parser(ANSWERS, help="answer and score every case")
    # log.debug("Adds the mode option")
    answers.add_argument("--mode", choices=MODES, default=None)
    # log.debug("Adds the run name option")
    answers.add_argument(NAME_OPTION, default=None)
    # log.debug("Adds the case limit option")
    answers.add_argument("--limit", type=int, default=None)
    # log.debug("Adds retrieval, with its modes and name")
    search = sub.add_parser(RETRIEVAL, help="score retrieval alone")
    # log.debug("Adds the modes option")
    search.add_argument("--modes", nargs="+", choices=MODES, default=[KEYWORD])
    # log.debug("Adds the run name option")
    search.add_argument(NAME_OPTION, default=RETRIEVAL)
    # log.debug("Returns the parser")
    return parser


# log.debug("Defines the entry point")
def main(argv: list[str] | None = None) -> int:
    """Run the chosen evaluation and print its summary."""
    # log.debug("Reads the arguments")
    args = _parser().parse_args(argv)
    # log.debug("Reads the settings")
    settings = get_app_settings()
    # log.debug("Sets up logging to the configured folder")
    setup_logging(settings)
    # log.debug("Runs the end-to-end evaluation")
    if args.command == ANSWERS:
        # log.debug("Uses the given mode, or the configured one")
        mode = args.mode or settings.retrieval_mode
        # log.debug("Prints the run's summary")
        print(
            run_answers(settings, mode, args.name or f"{settings.llm_provider}-{mode}", args.limit)
        )
        # log.debug("Returns success")
        return 0
    # log.debug("Prints the retrieval table")
    print(run_retrieval(settings, args.modes, args.name))
    # log.debug("Returns success")
    return 0


# log.debug("Runs main when the module is run as a script")
if __name__ == "__main__":
    # log.debug("Exits with main's status")
    sys.exit(main())
