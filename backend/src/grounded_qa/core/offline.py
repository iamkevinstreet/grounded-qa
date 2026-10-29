########################################################################
#               backend/src/grounded_qa/core/offline.py                #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

The offline stand-in for a model, used when [llm] provider is "fake".
It is not a model: it reads the fenced passages and the question from
the prompt, finds the sentence that shares the most search terms with
the question, and answers with that sentence as a quote, or abstains
when no sentence shares enough. That lets the service, its tests and
the offline evaluation run end to end with no key and no network, and
gives the live model a simple baseline to beat.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

import re
from typing import Any, Final

# Third-party
from kds.args import required
from kds.llm import Message, ModelAdapter
from kds.llm.fake import FakeProvider
from kds.logs import get_logger

# Local
from grounded_qa.config import SETTINGS, AppSettings
from grounded_qa.core.chunk import SENTENCE_RE
from grounded_qa.core.models import Draft, DraftCitation
from grounded_qa.core.text import terms, word_count

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the provider name that selects the stand-in, from the config")
FAKE: Final = SETTINGS.llm_offline_provider

########################################################################
#                           Local constants                            #
########################################################################
# log.debug("Matches one fenced passage; captures its id and text")
PASSAGE_RE = re.compile(r'<passage id="(?P<id>[^"]+)"[^>]*>\n(?P<text>.*?)\n</passage>', re.DOTALL)
# log.debug("Matches the question at the end of the prompt")
QUESTION_RE = re.compile(r"\nQuestion: (?P<question>.+)\Z", re.DOTALL)
# log.debug("Sets the fewest shared terms an answer needs")
MIN_SHARED = 2
# log.debug("Sets the fewest words in a sentence worth quoting")
MIN_WORDS = 6
# log.debug("Sets the abstention the stand-in gives")
NOT_COVERED = "The passages do not cover this question."
# log.debug("Names the stand-in's model; the kds price table prices it at zero")
STAND_IN = "fake-model"


########################################################################
#                           Offline stand-in                           #
########################################################################
# log.debug("Defines the stand-in's answer to one prompt")
def respond(messages: list[Message] | None = None) -> dict[str, Any]:
    """Returns a Draft quoting the best-matching sentence.

    Args:
        messages: The conversation the adapter sends; its last message
            holds the fenced passages and the question. Required.

    Returns:
        A Draft as a dict: the sentence as the answer and its quote,
        or an abstention.
    """
    # log.debug("Takes the messages, which the caller must give")
    messages = required(messages=messages)
    # log.debug("Reads the last message, which holds passages and question")
    prompt = messages[-1].content
    # log.debug("Finds the question")
    found = QUESTION_RE.search(prompt)
    # log.debug("Turns the question into a set of search terms")
    wanted = set(terms(found["question"])) if found else set()
    # log.debug("Scores every sentence of every passage")
    scored = [
        (len(wanted & set(terms(sentence))), passage["id"], sentence)
        for passage in PASSAGE_RE.finditer(prompt)
        for sentence in _sentences(passage["text"])
    ]
    # log.debug("Picks the sentence sharing the most terms, first on ties")
    best = max(scored, key=lambda row: row[0], default=(0, "", ""))
    # log.debug("Abstains when no sentence shares enough terms")
    if best[0] < MIN_SHARED:
        # log.debug("Returns the abstention")
        return Draft(answer=NOT_COVERED, abstain=True).model_dump()
    # log.debug("Returns the sentence as the answer and its quote")
    return Draft(
        answer=f"{best[2]} [1]",
        citations=[DraftCitation(passage_id=best[1], quote=best[2])],
        abstain=False,
    ).model_dump()


# log.debug("Defines the adapter the service and evaluation use")
def adapter_for(settings: AppSettings | None = None) -> ModelAdapter:
    """Returns the configured model, or the stand-in for "fake".

    Args:
        settings: The settings that name the provider and model.
            Required.

    Returns:
        An adapter for the configured provider, or one around the
        stand-in, priced at zero.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Uses the stand-in when the provider is fake")
    if settings.llm_provider == FAKE:
        # log.debug("Returns an adapter around the stand-in, free and named as such")
        return ModelAdapter(FakeProvider(responder=respond), model=STAND_IN, settings=settings)
    # log.debug("Returns an adapter for the configured provider")
    return ModelAdapter(settings=settings)


# log.debug("Defines the sentences of a passage worth quoting")
def _sentences(text: str | None = None) -> list[str]:
    """Returns each sentence long enough to quote, line by line.

    Args:
        text: A passage's text. Required.

    Returns:
        Each sentence of six words or more, list marks removed.
    """
    # log.debug("Takes the text, which the caller must give")
    text = required(text=text)
    # log.debug("Splits lines, then sentences, and drops list markers")
    pieces = [
        piece.strip().lstrip("-").strip()
        for line in text.splitlines()
        for piece in SENTENCE_RE.split(line)
    ]
    # log.debug("Returns the pieces long enough to quote")
    return [piece for piece in pieces if word_count(piece) >= MIN_WORDS]
