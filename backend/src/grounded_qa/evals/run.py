########################################################################
#                 backend/src/grounded_qa/evals/run.py                 #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

Runs an evaluation from the command line and writes its results:
answers end to end, or retrieval alone.

    python -m grounded_qa.evals.run answers --mode keyword
    python -m grounded_qa.evals.run retrieval --modes keyword hybrid

Both search the approved sources plus the synthetic documents in
data/samples, which plant the prompt injections the cases test.
Results go to [data] results as JSON and Markdown.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from functools import partial
from typing import Any, Final

# Third-party
from kds.args import missing, required
from kds.evals import load_cases, run_eval
from kds.logs import get_logger, setup_logging

# Local
from grounded_qa.config import SETTINGS, AppSettings, Mode, get_app_settings
from grounded_qa.core.answer import Answerer
from grounded_qa.core.chunk import Passage, split_all
from grounded_qa.core.embed import Embedder, LocalEmbedder
from grounded_qa.core.offline import adapter_for
from grounded_qa.core.retrieve import Retriever
from grounded_qa.core.sources import load_dir
from grounded_qa.evals import retrieval
from grounded_qa.evals.score import score

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the name of the mode that needs no embedding model, from the config")
KEYWORD: Final = SETTINGS.retrieval_keyword_mode
# log.debug("Takes the encoding that turns text into bytes, from the config")
ENCODING: Final = SETTINGS.text_encoding
# log.debug("Lists the retrieval modes a run can use")
MODES: tuple[Mode, ...] = ("keyword", "semantic", "hybrid")

########################################################################
#                           Local constants                            #
########################################################################
# log.debug("Sets the time format in result file names")
STAMP = "%Y%m%dT%H%M%SZ"
# log.debug("Names the subcommand for the end-to-end evaluation")
ANSWERS = "answers"
# log.debug("Names the subcommand, and default run name, for retrieval")
RETRIEVAL = "retrieval"
# log.debug("Names the option that names a run")
NAME_OPTION = "--name"


########################################################################
#                           Evaluation runs                            #
########################################################################
# log.debug("Defines settings with a different retrieval mode")
def with_mode(settings: AppSettings | None = None, mode: Mode | None = None) -> AppSettings:
    """Returns a copy of the settings that retrieves in `mode`.

    Args:
        settings: The settings to copy. Required.
        mode: The retrieval mode the copy uses. Required.

    Returns:
        The copy.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Stops when the caller left out the mode")
    if mode is None:
        # log.debug("Raises the missing-argument error")
        raise missing(mode=mode)
    # log.debug("Returns the copy")
    return settings.model_copy(update={"retrieval_mode": mode})


# log.debug("Defines the passages every evaluation searches")
def corpus(settings: AppSettings | None = None) -> list[Passage]:
    """Returns the approved sources and synthetic samples, split.

    Args:
        settings: The settings that name both folders and the passage
            size. Required.

    Returns:
        Every passage of the sources and samples the guard passed.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Reads both folders and splits them as the service does")
    return split_all(
        load_dir(settings.data_sources) + load_dir(settings.data_samples),
        settings.retrieval_passage_words,
    )


# log.debug("Defines the embedder a set of modes needs")
def embedder_for(
    modes: list[Mode] | None = None, settings: AppSettings | None = None
) -> Embedder | None:
    """Returns the local model when any mode searches by meaning.

    Args:
        modes: The retrieval modes the run uses. Required.
        settings: The settings that name the local model. Required.

    Returns:
        The local embedding model, or None when every mode is keyword.
    """
    # log.debug("Takes the modes, which the caller must give")
    modes = required(modes=modes)
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Loads the model once, only when a mode needs it")
    return LocalEmbedder(settings.retrieval_model) if set(modes) - {KEYWORD} else None


# log.debug("Defines the end-to-end evaluation")
def run_answers(
    settings: AppSettings | None = None,
    mode: Mode | None = None,
    name: str | None = None,
    limit: int | None = None,
) -> str:
    """Answers every case and scores it; returns the summary line.

    Args:
        settings: The settings to run with. Required.
        mode: The retrieval mode. Required.
        name: The run's name, for its result files. Required.
        limit: How many cases to run, from the first; all when None.

    Returns:
        The run's name, its case and failure counts, and its summary
        as JSON.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Stops when the caller left out the mode")
    if mode is None:
        # log.debug("Raises the missing-argument error")
        raise missing(mode=mode)
    # log.debug("Takes the name, which the caller must give")
    name = required(name=name)
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
    # log.debug("Answers and scores every case, then writes the results")
    run = run_eval(
        name=name,
        cases=cases,
        adapter=adapter,
        system_fn=lambda case: answerer.ask(case.input["question"]),
        scorer_fn=partial(score, passages=by_id, canaries=configured.eval_canaries),
        out_dir=configured.data_results,
    )
    # log.debug("Returns a one-line summary")
    return f"{name}: {run.cases} cases, {run.failures} failures, {json.dumps(run.summary)}"


# log.debug("Defines the retrieval evaluation")
def run_retrieval(
    settings: AppSettings | None = None, modes: list[Mode] | None = None, name: str | None = None
) -> str:
    """Scores retrieval for each mode; writes JSON and Markdown.

    Args:
        settings: The settings to run with. Required.
        modes: The retrieval modes to score. Required.
        name: The run's name, for its result files. Required.

    Returns:
        The Markdown table of the scores.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Takes the modes, which the caller must give")
    modes = required(modes=modes)
    # log.debug("Takes the name, which the caller must give")
    name = required(name=name)
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
def _record(settings: AppSettings | None = None) -> dict[str, Any]:
    """Returns the retrieval settings that shape the results.

    Args:
        settings: The settings the run used. Required.

    Returns:
        The passage size, the ranking constants and the embedding
        model.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
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
    """Builds the parser with the answers and retrieval subcommands.

    Returns:
        The parser.
    """
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
    """Runs the chosen evaluation and prints its summary.

    Args:
        argv: The command's arguments; the process's own when None.

    Returns:
        The exit status: 0.
    """
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
