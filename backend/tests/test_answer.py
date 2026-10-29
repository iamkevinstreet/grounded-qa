########################################################################
#                     backend/tests/test_answer.py                     #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

Tests each way a question can end: answered, not covered, unverified, or
no passages at all.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

from typing import Any

# Third-party
from kds.args import required
from kds.llm import ModelAdapter
from kds.llm.fake import FakeProvider
from kds.logs import get_logger

# Local
from grounded_qa.config import AppSettings
from grounded_qa.core.answer import UNVERIFIED_TEXT, Answerer
from grounded_qa.core.chunk import split_all
from grounded_qa.core.offline import adapter_for
from grounded_qa.core.retrieve import Retriever
from support import LEAVE_BODY, OVERTIME_BODY, make_source

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)

########################################################################
#                           Local constants                            #
########################################################################
# log.debug("Sets the question most tests ask")
QUESTION = "How many workweeks of leave can eligible employees take?"
# log.debug("Sets a quote that is in the leave source")
GOOD_QUOTE = "Eligible employees may take up to 12 workweeks of leave"


########################################################################
#                             Answer tests                             #
########################################################################
# log.debug("Defines an answerer over the two small sources")
def _answerer(settings: AppSettings | None = None, *drafts: Any) -> tuple[Answerer, FakeProvider]:
    """Returns an answerer whose model gives `drafts` in order.

    Args:
        settings: Settings over the two small test sources. Required.
        *drafts: What the fake model returns, one draft per call.

    Returns:
        The answerer, and the fake provider, for its record of calls.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Scripts the model's drafts")
    provider = FakeProvider(list(drafts))
    # log.debug("Indexes the two small sources")
    retriever = Retriever(
        split_all([make_source("leave", LEAVE_BODY), make_source("overtime", OVERTIME_BODY)], 180),
        settings,
    )
    # log.debug("Returns the answerer and the provider, for call counts")
    return Answerer(
        retriever, ModelAdapter(provider, model="fake-model"), settings, mode="keyword"
    ), provider


# log.debug("Defines the test of a checked answer")
def test_checked_answer_is_returned(settings: AppSettings) -> None:
    """A quote found in its passage makes an answered outcome.

    Args:
        settings: Settings over the two small test sources.
    """
    # log.debug("Scripts a draft with a true quote")
    answerer, _ = _answerer(
        settings,
        {
            "answer": "Up to 12 workweeks [1].",
            "citations": [{"passage_id": "leave#2", "quote": GOOD_QUOTE}],
            "abstain": False,
        },
    )
    # log.debug("Asks the question")
    answer = answerer.ask(QUESTION)
    # log.debug("Checks the outcome, text and citation details")
    assert (answer.outcome, answer.answer, answer.citations[0].doc_id) == (
        "answered",
        "Up to 12 workweeks [1].",
        "leave",
    )


# log.debug("Defines the test that an invented quote is withheld")
def test_invented_quote_withholds_the_answer(settings: AppSettings) -> None:
    """A quote not in its passage leaves nothing checked: unverified.

    Args:
        settings: Settings over the two small test sources.
    """
    # log.debug("Scripts a draft whose quote was changed")
    answerer, _ = _answerer(
        settings,
        {
            "answer": "Up to 16 workweeks [1].",
            "citations": [{"passage_id": "leave#2", "quote": "may take up to 16 workweeks"}],
            "abstain": False,
        },
    )
    # log.debug("Asks the question")
    answer = answerer.ask(QUESTION)
    # log.debug("Checks the draft never reaches the reader")
    assert (answer.outcome, answer.answer, answer.dropped) == ("unverified", UNVERIFIED_TEXT, 1)


# log.debug("Defines the test that a failed claim is removed")
def test_failed_claim_is_removed_and_the_rest_kept(settings: AppSettings) -> None:
    """One bad citation removes its claim; the checked claim stays.

    Args:
        settings: Settings over the two small test sources.
    """
    # log.debug("Scripts a draft with one false and one true citation")
    answerer, _ = _answerer(
        settings,
        {
            "answer": "Leave is paid [1]. Leave lasts 12 workweeks [2].",
            "citations": [
                {"passage_id": "leave#3", "quote": "FMLA is job-protected, paid leave"},
                {"passage_id": "leave#2", "quote": GOOD_QUOTE},
            ],
            "abstain": False,
        },
    )
    # log.debug("Asks the question")
    answer = answerer.ask(QUESTION)
    # log.debug("Checks only the checked claim remains, renumbered")
    assert (answer.answer, answer.dropped, len(answer.citations)) == (
        "Leave lasts 12 workweeks [1].",
        1,
        1,
    )


# log.debug("Defines the test that only shown passages may be cited")
def test_citing_an_unshown_passage_fails(settings: AppSettings) -> None:
    """A citation of a passage the model was not shown is dropped.

    Args:
        settings: Settings over the two small test sources.
    """
    # log.debug("Scripts a draft citing a made-up passage id")
    answerer, _ = _answerer(
        settings,
        {
            "answer": "Twelve [1].",
            "citations": [{"passage_id": "other#9", "quote": GOOD_QUOTE}],
            "abstain": False,
        },
    )
    # log.debug("Asks the question")
    answer = answerer.ask(QUESTION)
    # log.debug("Checks the answer is withheld")
    assert answer.outcome == "unverified"


# log.debug("Defines the test of the model's own abstention")
def test_model_abstention_is_kept(settings: AppSettings) -> None:
    """When the model says the passages do not cover it, we say so.

    Args:
        settings: Settings over the two small test sources.
    """
    # log.debug("Scripts an abstention")
    answerer, _ = _answerer(
        settings, {"answer": "The passages do not cover this.", "citations": [], "abstain": True}
    )
    # log.debug("Asks a question the passages do not cover")
    answer = answerer.ask("How much overtime is owed on holidays?")
    # log.debug("Checks the outcome")
    assert answer.outcome == "not_covered"


# log.debug("Defines the test that no passages means no model call")
def test_no_passages_means_no_model_call(settings: AppSettings) -> None:
    """A question sharing no words with the sources costs nothing.

    Args:
        settings: Settings over the two small test sources.
    """
    # log.debug("Builds an answerer with no scripted drafts")
    answerer, provider = _answerer(settings)
    # log.debug("Asks an off-topic question")
    answer = answerer.ask("What is the weather in Atlanta?")
    # log.debug("Checks the outcome and that the model was never called")
    assert (answer.outcome, provider.calls) == ("no_passages", [])


# log.debug("Defines the test that an unreadable draft is withheld")
def test_unreadable_draft_is_unverified(settings: AppSettings) -> None:
    """Two answers that are not the Draft shape end as unverified.

    Args:
        settings: Settings over the two small test sources.
    """
    # log.debug("Scripts two answers that are not JSON")
    answerer, _ = _answerer(settings, "not json", "still not json")
    # log.debug("Asks the question")
    answer = answerer.ask(QUESTION)
    # log.debug("Checks the outcome")
    assert answer.outcome == "unverified"


# log.debug("Defines the test of the offline stand-in")
def test_offline_stand_in_answers_and_abstains(settings: AppSettings) -> None:
    """The stand-in quotes the best sentence, or abstains.

    Args:
        settings: Settings over the two small test sources.
    """
    # log.debug("Builds the stand-in adapter from settings")
    adapter = adapter_for(settings)
    # log.debug("Builds an answerer around it")
    answerer = Answerer(
        Retriever(split_all([make_source("leave", LEAVE_BODY)], 180), settings),
        adapter,
        settings,
        mode="keyword",
    )
    # log.debug("Asks a covered question")
    covered = answerer.ask(QUESTION)
    # log.debug("Asks a question sharing only one word")
    uncovered = answerer.ask("Is leave required in Antarctica?")
    # log.debug("Checks it answered for free, then abstained")
    assert (covered.outcome, adapter.spent_usd, uncovered.abstained) == ("answered", 0.0, True)
