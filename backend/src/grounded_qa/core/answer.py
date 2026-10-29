########################################################################
#                backend/src/grounded_qa/core/answer.py                #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Answers a question from the approved sources     #
#                     only and abstains when they do not cover it.     #
########################################################################
"""The answerer: retrieve, draft, check, and return only what held.

1. Retrieve the passages most likely to answer the question.
2. Ask the model for an answer as JSON: text, citations, abstain.
3. Check every quote against the passage it cites; remove claims
   whose citations all failed.
4. Return the answer only if a checked citation still supports it;
   otherwise return an abstention that says why.
"""

from __future__ import annotations

import logging
from typing import Protocol

from kds.llm import ModelAdapter, StructuredOutputError
from kds.logs import current_request_id, get_logger, log_event

from grounded_qa.config import AppSettings
from grounded_qa.core import prompt
from grounded_qa.core.models import Answer, Citation, Draft, Outcome, Retrieved
from grounded_qa.core.retrieve import Hit
from grounded_qa.core.verify import find_quote, prune

# Module constants
log = get_logger(__name__)
# log.debug("Sets the reply when nothing in the sources matched at all")
NO_PASSAGES_TEXT = "Nothing in the approved sources matches this question."
# log.debug("Sets the reply when no quote could be found in its passage")
UNVERIFIED_TEXT = (
    "I could not check an answer against the approved sources, so I am not giving one. "
    "Try rephrasing the question."
)
# log.debug("Names the outcome when no citation survived the check")
UNVERIFIED: Outcome = "unverified"


# log.debug("Defines what the answerer needs from retrieval")
class Searcher(Protocol):
    """Anything that finds passages for a question."""

    # log.debug("Defines the search the answerer calls")
    def search(self, question: str, k: int | None = None) -> list[Hit]:
        """Return the best passages for the question, best first."""


# log.debug("Defines the answerer")
class Answerer:
    """Answers questions from what a searcher finds, checked."""

    # log.debug("Defines the constructor")
    def __init__(
        self, searcher: Searcher, adapter: ModelAdapter, settings: AppSettings, *, mode: str
    ) -> None:
        """Keep the searcher, model adapter and settings."""
        # log.debug("Keeps the searcher")
        self.searcher = searcher
        # log.debug("Keeps the model adapter")
        self.adapter = adapter
        # log.debug("Keeps the settings")
        self.settings = settings
        # log.debug("Keeps the retrieval mode, for the record")
        self.mode = mode
        # log.debug("Fills in the rules once")
        self.system = prompt.system_prompt(
            min_quote_words=settings.answer_min_quote_words, max_words=settings.answer_max_words
        )

    # log.debug("Defines one question, start to finish")
    def ask(self, question: str) -> Answer:
        """Return a checked answer to `question`, or an abstention."""
        # log.debug("Finds the passages most likely to answer")
        hits = self.searcher.search(question)
        # log.debug("Abstains without a model call when nothing matched")
        if not hits:
            # log.debug("Returns the no-passages abstention")
            return self._answer(question, NO_PASSAGES_TEXT, "no_passages", hits)
        # log.debug("Asks the model for a draft in the Draft shape")
        try:
            # log.debug("Calls the model with the rules and fenced passages")
            draft, completion = self.adapter.complete_json(
                prompt.user_message(question, hits), Draft, system=self.system
            )
        except StructuredOutputError:
            # log.debug("Treats an unreadable draft as unchecked")
            log_event(log, "answer.unreadable", logging.WARNING, passages=len(hits))
            # log.debug("Returns the unverified abstention")
            return self._answer(question, UNVERIFIED_TEXT, UNVERIFIED, hits)
        # log.debug("Checks each citation and numbers the ones that pass")
        citations, renumber = self._check(draft, hits)
        # log.debug("Keeps only the claims a checked citation supports")
        text = prune(draft.answer, renumber)
        # log.debug("Names the outcome from the draft and the checks")
        outcome = self._outcome(draft, citations)
        # log.debug("Logs the outcome without the question's text")
        log_event(
            log,
            "answer.done",
            outcome=outcome,
            cited=len(citations),
            dropped=len(draft.citations) - len(citations),
            passages=[h.passage.id for h in hits],
            model=completion.model,
            cost_usd=completion.cost_usd,
            latency_ms=completion.latency_ms,
        )
        # log.debug("Returns the answer, or the unverified abstention")
        return self._answer(
            question,
            UNVERIFIED_TEXT if outcome == UNVERIFIED else text,
            outcome,
            hits,
            citations=citations,
            dropped=len(draft.citations) - len(citations),
            model=completion.model,
        )

    # log.debug("Defines the check of a draft's citations")
    def _check(self, draft: Draft, hits: list[Hit]) -> tuple[list[Citation], dict[int, int]]:
        """Return the citations that pass, and old-to-new numbers."""
        # log.debug("Indexes the passages the model was shown")
        shown = {h.passage.id: h.passage for h in hits}
        # log.debug("Starts the passing citations")
        passed: list[Citation] = []
        # log.debug("Starts the map from draft numbers to new numbers")
        renumber: dict[int, int] = {}
        # log.debug("Walks the draft's citations in [n] order")
        for number, cited in enumerate(draft.citations, start=1):
            # log.debug("Finds the passage the citation names")
            passage = shown.get(cited.passage_id)
            # log.debug("Finds the quote, unless the passage was never shown")
            spans, problem = (
                find_quote(cited.quote, passage.text, self.settings.answer_min_quote_words)
                if passage is not None
                else ((), "cites a passage that was not shown")
            )
            # log.debug("Logs and skips a citation that failed")
            if problem is not None or passage is None:
                # log.debug("Logs the failure without the quote's text")
                log_event(
                    log, "answer.citation_dropped", passage_id=cited.passage_id, problem=problem
                )
                # log.debug("Moves to the next citation")
                continue
            # log.debug("Gives the passing citation the next new number")
            renumber[number] = len(passed) + 1
            # log.debug("Keeps the citation with its source details")
            passed.append(
                Citation(
                    n=renumber[number],
                    passage_id=passage.id,
                    doc_id=passage.doc_id,
                    title=passage.title,
                    section=passage.section,
                    url=passage.url,
                    revised=passage.revised,
                    quote=cited.quote.strip(),
                    passage=passage.text,
                    spans=spans,
                )
            )
        # log.debug("Returns the passing citations and the number map")
        return passed, renumber

    # log.debug("Defines the outcome of a checked draft")
    def _outcome(self, draft: Draft, citations: list[Citation]) -> Outcome:
        """Return not_covered, answered, or unverified."""
        # log.debug("Keeps the model's own abstention")
        if draft.abstain:
            # log.debug("Returns not covered")
            return "not_covered"
        # log.debug("Returns answered only when a citation passed")
        return "answered" if citations else UNVERIFIED

    # log.debug("Defines how the returned answer is assembled")
    def _answer(
        self,
        question: str,
        text: str,
        outcome: Outcome,
        hits: list[Hit],
        **extra: object,
    ) -> Answer:
        """Return the Answer with the record of what was retrieved."""
        # log.debug("Returns the answer with the passages and identifiers")
        return Answer.model_validate(
            {
                "question": question,
                "answer": text,
                "outcome": outcome,
                "retrieved": [
                    Retrieved(passage_id=h.passage.id, doc_id=h.passage.doc_id, score=h.score)
                    for h in hits
                ],
                "prompt_version": prompt.VERSION,
                "mode": self.mode,
                "request_id": current_request_id(),
                **extra,
            }
        )
