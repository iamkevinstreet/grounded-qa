########################################################################
#                backend/src/grounded_qa/core/answer.py                #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

Answers a question from the approved sources only and abstains when they
do not cover it.

1. Retrieve the passages most likely to answer the question.
2. Ask the model for an answer as JSON: text, citations, abstain.
3. Check every quote against the passage it cites; remove claims
   whose citations all failed.
4. Return the answer only if a checked citation still supports it;
   otherwise return an abstention that says why.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

import logging
from typing import Protocol

# Third-party
from kds.args import missing, required
from kds.llm import ModelAdapter, StructuredOutputError
from kds.logs import current_request_id, get_logger, log_event

# Local
from grounded_qa.config import AppSettings
from grounded_qa.core import prompt
from grounded_qa.core.models import Answer, Citation, Draft, Outcome, Retrieved
from grounded_qa.core.retrieve import Hit
from grounded_qa.core.verify import find_quote, prune

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)

########################################################################
#                           Local constants                            #
########################################################################
# log.debug("Sets the reply when nothing in the sources matched at all")
NO_PASSAGES_TEXT = "Nothing in the approved sources matches this question."
# log.debug("Sets the reply when no quote could be found in its passage")
UNVERIFIED_TEXT = (
    "I could not check an answer against the approved sources, so I am not giving one. "
    "Try rephrasing the question."
)
# log.debug("Names the outcome when no citation survived the check")
UNVERIFIED: Outcome = "unverified"


########################################################################
#                           Grounded answers                           #
########################################################################
# log.debug("Defines what the answerer needs from retrieval")
class Searcher(Protocol):
    """Anything that finds passages for a question."""

    # log.debug("Defines the search the answerer calls")
    def search(self, question: str | None = None, k: int | None = None) -> list[Hit]:
        """Returns the best passages for the question, best first.

        Args:
            question: The question to find passages for. Required.
            k: How many passages to return; the configured number when
                None.

        Returns:
            The best passages, best first.
        """


# log.debug("Defines the answerer")
class Answerer:
    """Answers questions from what a searcher finds, checked."""

    # log.debug("Defines the constructor")
    def __init__(
        self,
        searcher: Searcher | None = None,
        adapter: ModelAdapter | None = None,
        settings: AppSettings | None = None,
        *,
        mode: str | None = None,
    ) -> None:
        """Keeps the searcher, model adapter and settings.

        Args:
            searcher: What finds the passages: the library, or a
                retriever in the evaluation. Required.
            adapter: The model adapter the drafts come from. Required.
            settings: The settings for the prompt's limits and the
                quote check. Required.
            mode: The retrieval mode, recorded with each answer.
                Required.
        """
        # log.debug("Takes the searcher, which the caller must give")
        searcher = required(searcher=searcher)
        # log.debug("Takes the adapter, which the caller must give")
        adapter = required(adapter=adapter)
        # log.debug("Takes the settings, which the caller must give")
        settings = required(settings=settings)
        # log.debug("Takes the mode, which the caller must give")
        mode = required(mode=mode)
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
    def ask(self, question: str | None = None) -> Answer:
        """Returns a checked answer to `question`, or an abstention.

        Args:
            question: The question to answer. Required.

        Returns:
            The answer with its checked citations, or an abstention
            that says why.
        """
        # log.debug("Takes the question, which the caller must give")
        question = required(question=question)
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
    def _check(
        self, draft: Draft | None = None, hits: list[Hit] | None = None
    ) -> tuple[list[Citation], dict[int, int]]:
        """Returns the citations that pass, and old-to-new numbers.

        Args:
            draft: The model's draft. Required.
            hits: The passages the model was shown, best first.
                Required.

        Returns:
            The citations whose quotes were found in their passages,
            numbered from 1, and a map from each one's number in the
            draft to its new number.
        """
        # log.debug("Takes the draft, which the caller must give")
        draft = required(draft=draft)
        # log.debug("Takes the passages found, which the caller must give")
        hits = required(hits=hits)
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
    def _outcome(
        self, draft: Draft | None = None, citations: list[Citation] | None = None
    ) -> Outcome:
        """Returns not_covered, answered, or unverified.

        Args:
            draft: The model's draft. Required.
            citations: The citations that passed the check. Required.

        Returns:
            not_covered when the model abstained, answered when a
            citation passed, else unverified.
        """
        # log.debug("Takes the draft, which the caller must give")
        draft = required(draft=draft)
        # log.debug("Takes the citations, which the caller must give")
        citations = required(citations=citations)
        # log.debug("Keeps the model's own abstention")
        if draft.abstain:
            # log.debug("Returns not covered")
            return "not_covered"
        # log.debug("Returns answered only when a citation passed")
        return "answered" if citations else UNVERIFIED

    # log.debug("Defines how the returned answer is assembled")
    def _answer(
        self,
        question: str | None = None,
        text: str | None = None,
        outcome: Outcome | None = None,
        hits: list[Hit] | None = None,
        **extra: object,
    ) -> Answer:
        """Returns the Answer with the record of what was retrieved.

        Args:
            question: The question as asked. Required.
            text: The answer's text, or why there is none. Required.
            outcome: How the question ended. Required.
            hits: The passages the model was shown. Required.
            **extra: Further Answer fields: the citations, how many
                were dropped, and the model.

        Returns:
            The answer, validated.
        """
        # log.debug("Takes the question, which the caller must give")
        question = required(question=question)
        # log.debug("Takes the text, which the caller must give")
        text = required(text=text)
        # log.debug("Stops when the caller left out the outcome")
        if outcome is None:
            # log.debug("Raises the missing-argument error")
            raise missing(outcome=outcome)
        # log.debug("Takes the passages found, which the caller must give")
        hits = required(hits=hits)
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
