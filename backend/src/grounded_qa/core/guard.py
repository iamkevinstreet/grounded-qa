########################################################################
#                backend/src/grounded_qa/core/guard.py                 #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Finds text in a document that reads like orders  #
#                     to an AI model, so it can be refused or held.    #
########################################################################
"""The ingest guard: flags instruction-like text in source documents.

A source document is data. Text in it that addresses a model ("ignore
your previous instructions") is a prompt injection, so the approver is
shown it and the document is kept out of answers. This is the first
of three defences; the prompt and the quote check are the others.

The patterns name AI systems outright, because employment documents
are full of job titles ("works as an assistant"); a bare "assistant"
is no sign of anything. A test keeps every approved source unflagged.
"""

from __future__ import annotations

import re

from kds.logs import get_logger

# Module constants
log = get_logger(__name__)
# log.debug("Lists patterns of text that gives orders to a model")
PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(ignore|disregard|forget|override)\b[^.\n]{0,40}"
        r"\b(instructions?|prompts?|rules|directions)\b",
        r"\byou are now\b",
        r"\b(system|developer) (prompt|message)\b",
        r"\b(new|updated|revised) instructions?\s*:",
        r"\bas an? (ai|language) (model|assistant|system)\b",
        r"\b(ai|chatbot|llm|language model)s?\b[^.\n]{0,40}"
        r"\b(must|should|shall)\b[^.\n]{0,20}"
        r"\b(say|state|answer|respond|reply|tell|report|include)\b",
        r"</?\s*(system|instructions?|prompt|passages?)\s*>",
    )
)
# log.debug("Sets how much of a flagged line is shown to the approver")
SHOWN_CHARS = 160


# log.debug("Defines the check that finds instruction-like lines")
def flag(text: str) -> list[str]:
    """Return each line of `text` that reads like orders to a model."""
    # log.debug("Returns every matching line, shortened for display")
    return [
        line.strip()[:SHOWN_CHARS]
        for line in text.splitlines()
        if any(pattern.search(line) for pattern in PATTERNS)
    ]
