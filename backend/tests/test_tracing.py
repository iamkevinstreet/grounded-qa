########################################################################
#                                                                      #
#                    backend/tests/test_tracing.py                     #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-07
Last modified on:  2026-11-07

Tests the spans of a question: one answer span holding the search, the
model call and the quote check, with what each found; and the same
spans under an MCP client's tool call.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

import json

# Third-party
import anyio
from kds.llm import ModelAdapter
from kds.llm.fake import FakeProvider
from kds.logs import get_logger
from mcp import Client
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

# Local
from grounded_qa.api.state import Services, build_services
from grounded_qa.config import AppSettings
from grounded_qa.mcp_server.server import build_server

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
# log.debug("Sets the question every test asks")
QUESTION = "How many workweeks of leave may an employee take?"
# log.debug("Sets the draft the fake model gives, quoting the leave passage")
DRAFT = {
    "answer": "Up to 12 workweeks [1].",
    "citations": [{"passage_id": "leave#2", "quote": "may take up to 12 workweeks of leave"}],
    "abstain": False,
}


########################################################################
#                                                                      #
#                            Tracing tests                             #
#                                                                      #
########################################################################
# log.debug("Defines the services every test asks through")
def _services(settings: AppSettings | None = None) -> Services:
    """Returns services whose fake model drafts the leave answer.

    Args:
        settings: Settings over the two small test sources.

    Returns:
        The services.
    """
    # log.debug("Builds a fake model that drafts the answer once")
    adapter = ModelAdapter(FakeProvider([DRAFT]), model="fake-model", settings=settings)
    # log.debug("Returns the services around it")
    return build_services(settings, adapter)


# log.debug("Defines how spans are found by name")
def _named(spans: InMemorySpanExporter | None = None) -> dict[str, ReadableSpan]:
    """Returns this test's spans by name.

    Args:
        spans: The spans this test records.

    Returns:
        Each span by its name.
    """
    # log.debug("Returns them by name")
    return {span.name: span for span in (spans.get_finished_spans() if spans else ())}


# log.debug("Defines a span's own id")
def _own(span: ReadableSpan | None = None) -> int | None:
    """Returns the span's id.

    Args:
        span: The span.

    Returns:
        Its id, or None without a context.
    """
    # log.debug("Returns the id from the span's context")
    return span.context.span_id if span and span.context else None


# log.debug("Defines a span's parent's id")
def _parent(span: ReadableSpan | None = None) -> int | None:
    """Returns the id of the span's parent.

    Args:
        span: The span.

    Returns:
        The parent's id, or None for a span that starts its trace.
    """
    # log.debug("Returns the parent's id")
    return span.parent.span_id if span and span.parent else None


# log.debug("Defines a span's attributes")
def _attrs(span: ReadableSpan | None = None) -> dict[str, object]:
    """Returns the span's attributes.

    Args:
        span: The span.

    Returns:
        Its attributes by name; empty without any.
    """
    # log.debug("Returns them as a plain table")
    return dict(span.attributes or {}) if span else {}


# log.debug("Defines the test of a question's spans")
def test_a_question_is_one_answer_span_with_its_steps(
    settings: AppSettings, spans: InMemorySpanExporter
) -> None:
    """The search, model call and check sit inside the answer span.

    Args:
        settings: Settings over the two small test sources.
        spans: The spans this test records.
    """
    # log.debug("Asks the question")
    _services(settings).answerer.ask(QUESTION)
    # log.debug("Finds the spans by name")
    named = _named(spans)
    # log.debug("Takes the answer span")
    answer = named["answer"]
    # log.debug("Checks the three steps sit inside it")
    assert {_parent(named[step]) for step in ("retrieval", "chat fake-model", "verify")} == {
        _own(answer)
    }
    # log.debug("Checks how the question ended and what the check kept")
    assert (_attrs(answer)["answer.outcome"], _attrs(named["verify"])["verify.kept"]) == (
        "answered",
        1,
    )
    # log.debug("Reads what the search found")
    found = json.loads(str(_attrs(named["retrieval"])["gen_ai.retrieval.documents"]))
    # log.debug("Checks the leave passage was found first")
    assert found[0]["id"] == "leave#2"


# log.debug("Defines the test of an MCP call's spans")
def test_an_mcp_tool_call_holds_the_answer_span(
    settings: AppSettings, spans: InMemorySpanExporter
) -> None:
    """The SDK's tool span is the answer span's parent.

    Args:
        settings: Settings over the two small test sources.
        spans: The spans this test records.
    """
    # log.debug("Builds the services once")
    services = _services(settings)
    # log.debug("Builds the server on them")
    server = build_server(lambda: services)

    # log.debug("Defines the conversation")
    async def run() -> None:
        """Asks through an MCP client in process."""
        # log.debug("Connects the client")
        async with Client(server) as client:
            # log.debug("Calls ask")
            await client.call_tool("ask", {"question": QUESTION})

    # log.debug("Runs it")
    anyio.run(run)
    # log.debug("Finds the spans by name")
    named = _named(spans)
    # log.debug("Checks the answer span sits inside the tool call's span")
    assert _parent(named["answer"]) == _own(named["tools/call ask"])
