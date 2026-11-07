########################################################################
#                                                                      #
#             backend/src/grounded_qa/mcp_server/server.py             #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-07
Last modified on:  2026-11-07

The approved sources as an MCP server. Any MCP client, such as Claude
Desktop or Claude Code, can search the sources, read a passage or a
whole source, and ask a question that is answered only from them, with
every quote checked, as the API answers it.

Every tool only reads. A search returns passages only from sources the
guard passed, each passage is screened again on its way out, and a
held-back source is listed without its text, so nothing that reads like
orders to a model reaches the client's model. Asking calls the model,
so every MCP client's questions count against one per-minute limit.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Final

# Third-party
from kds.args import required
from kds.llm import BudgetExceededError, TransientError
from kds.logs import get_logger, log_event
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceError, ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

# Local
from grounded_qa import __version__
from grounded_qa.api.state import Services
from grounded_qa.config import MAX_K, SETTINGS
from grounded_qa.core import guard
from grounded_qa.core.models import Answer
from grounded_qa.core.retrieve import Hit
from grounded_qa.core.text import tidy
from grounded_qa.mcp_server.models import FoundPassage, Listed, page

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the number of passages a search returns, from the config")
DEFAULT_K: Final = SETTINGS.retrieval_k

########################################################################
#                                                                      #
#                           Local constants                            #
#                                                                      #
########################################################################
# log.debug("Sets the server's name as people read it")
TITLE = "Grounded Q&A"
# log.debug("Sets what the server tells a client's model about itself")
INSTRUCTIONS = (
    "Approved employment-law sources: U.S. Department of Labor fact sheets on wages, hours and "
    "leave. Use ask for a checked answer with quotes, search_sources to find passages, and "
    "get_passage or a source:// resource to read more. Answers come only from these sources; "
    "when they do not answer a question, ask says so instead of guessing."
)
# log.debug("Sets what search_sources does, as the client's model reads it")
SEARCH = "Finds the passages of the approved sources that best match a query, best first."
# log.debug("Sets what get_passage does")
PASSAGE = "Returns one passage of an approved source by its id, as search_sources gives it."
# log.debug("Sets what list_sources does")
SOURCES = "Lists every approved source with its provenance: publisher, revision date, SHA-256."
# log.debug("Sets what ask does")
ASK = (
    "Answers a question from the approved sources only, with each quote checked against its "
    "passage, or says the sources do not answer it. Calls a model, so it is rate limited."
)
# log.debug("Sets what a source resource holds")
SOURCE = "An approved source as Markdown: its provenance, then its full text."
# log.debug("Sets the address of a source resource")
SOURCE_URI = "source://{source_id}"
# log.debug("Sets the type of a source resource")
MARKDOWN = "text/markdown"
# log.debug("Sets what an MCP client is told when the model cannot answer")
UNAVAILABLE = "the model is unavailable right now; try again later"
# log.debug("Marks a tool that reads, the same way each time, from a closed set")
READ_ONLY = ToolAnnotations(
    read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
)
# log.debug("Marks ask: it reads, but each call is a new model call")
ASKS = ToolAnnotations(
    read_only_hint=True, destructive_hint=False, idempotent_hint=False, open_world_hint=False
)
# log.debug("Describes the query argument")
Query = Annotated[str, Field(description="What to find, in plain words.")]
# log.debug("Describes how many passages a search returns")
Depth = Annotated[int, Field(ge=1, le=MAX_K, description="How many passages to return.")]
# log.debug("Describes the passage id argument")
PassageId = Annotated[str, Field(description="A passage id, as search_sources returns it.")]
# log.debug("Describes the question argument")
Question = Annotated[str, Field(description="The question, in plain words.")]


########################################################################
#                                                                      #
#                              MCP server                              #
#                                                                      #
########################################################################
# log.debug("Defines the tools the server offers")
class LibraryTools:
    """The library's tools, reading the services when called."""

    # log.debug("Defines the constructor")
    def __init__(self, services: Callable[[], Services] | None = None) -> None:
        """Keeps how to reach the services.

        Args:
            services: Returns the services; the API's exist only once it
                has started, so they are looked up at each call.
                Required.
        """
        # log.debug("Takes the lookup, which the caller must give")
        services = required(services=services)
        # log.debug("Keeps it")
        self.services = services

    # log.debug("Defines the search tool")
    def search_sources(  # fixed: an MCP tool's signature is its schema
        self, query: Query, k: Depth = DEFAULT_K
    ) -> list[FoundPassage]:
        """Returns the best passages for the query, best first.

        Args:
            query: What to find.
            k: How many passages to return.

        Returns:
            The passages, each with its score.
        """
        # log.debug("Checks the query as the API checks a question")
        query = self._checked(query)
        # log.debug("Returns the screened passages of the search")
        return [FoundPassage.of(h.passage, h.score) for h in self._screened(query, k)]

    # log.debug("Defines the passage tool")
    def get_passage(  # fixed: an MCP tool's signature is its schema
        self, passage_id: PassageId
    ) -> FoundPassage:
        """Returns one passage by its id.

        Args:
            passage_id: The passage's id.

        Returns:
            The passage.

        Raises:
            ToolError: No indexed passage has the id, or the guard
                flags its text.
        """
        # log.debug("Looks the passage up")
        try:
            # log.debug("Finds it in the library's index")
            passage = self.services().library.passage(passage_id)
        except KeyError:
            # log.debug("Tells the client there is no such passage")
            raise ToolError("no passage with that id") from None
        # log.debug("Withholds a passage the guard flags")
        if guard.flag(passage.text):
            # log.debug("Tells the client it is withheld")
            raise ToolError("that passage is held back")
        # log.debug("Returns the passage")
        return FoundPassage.of(passage)

    # log.debug("Defines the listing tool")
    def list_sources(self) -> list[Listed]:
        """Returns every approved source's listing, sorted by id.

        Returns:
            The listings, without any source's text.
        """
        # log.debug("Returns a listing per source")
        return [Listed.of(source) for source in self.services().library.approved()]

    # log.debug("Defines the ask tool")
    def ask(self, question: Question) -> Answer:  # fixed: an MCP tool's signature is its schema
        """Answers the question from the approved sources, or abstains.

        Args:
            question: The question.

        Returns:
            The checked answer, or an abstention that says why.

        Raises:
            ToolError: The question is out of bounds, the MCP clients
                have asked too often, or the model cannot answer.
        """
        # log.debug("Checks the question as the API does")
        question = self._checked(question)
        # log.debug("Reads the services")
        svc = self.services()
        # log.debug("Refuses once the MCP clients have used up the minute")
        if not svc.limiter.allow(svc.settings.mcp_client):
            # log.debug("Tells the client to wait")
            raise ToolError("too many questions; wait a minute")
        # log.debug("Answers, telling the client when the model cannot")
        try:
            # log.debug("Returns the checked answer")
            return svc.answerer.ask(question)
        except (TransientError, BudgetExceededError) as error:
            # log.debug("Logs the error's type only")
            log_event(log, "mcp.model_unavailable", error=type(error).__name__)
            # log.debug("Tells the client")
            raise ToolError(UNAVAILABLE) from None

    # log.debug("Defines the source resource")
    def source(self, source_id: str) -> str:  # fixed: an MCP resource's signature is its address
        """Returns one approved source as a Markdown page.

        Args:
            source_id: The source's id, from the resource's address.

        Returns:
            The page: provenance, then the text unless held back.

        Raises:
            ResourceError: No source has this id.
        """
        # log.debug("Looks the source up")
        try:
            # log.debug("Returns its page")
            return page(self.services().library.get(source_id))
        except KeyError:
            # log.debug("Tells the client there is no such source")
            raise ResourceError("no source with that id") from None

    # log.debug("Defines the check every question and query gets")
    def _checked(self, text: str | None = None) -> str:
        """Returns the text tidied, once its length is within bounds.

        Args:
            text: The question or query as the client sent it.
                Required.

        Returns:
            The text, one line, words one space apart.

        Raises:
            ToolError: It is shorter or longer than the API allows.
        """
        # log.debug("Takes the text, which the caller must give")
        text = required(text=text)
        # log.debug("Tidies it as the API does")
        tidied = tidy(text)
        # log.debug("Reads the length limits")
        settings = self.services().settings
        # log.debug("Refuses text outside the limits")
        if not settings.api_min_question_chars <= len(tidied) <= settings.api_max_question_chars:
            # log.debug("Tells the client the limits")
            raise ToolError(
                f"a question is {settings.api_min_question_chars} to "
                f"{settings.api_max_question_chars} characters"
            )
        # log.debug("Returns the tidied text")
        return tidied

    # log.debug("Defines a search whose passages are screened on the way out")
    def _screened(self, query: str | None = None, k: int | None = None) -> list[Hit]:
        """Returns the search's passages that the guard does not flag.

        Args:
            query: The tidied query. Required.
            k: How many passages to search for. Required.

        Returns:
            The passages, best first, any the guard flags left out.
        """
        # log.debug("Takes the query, which the caller must give")
        query = required(query=query)
        # log.debug("Takes the depth, which the caller must give")
        k = required(k=k)
        # log.debug("Searches the library")
        hits = self.services().library.search(query, k)
        # log.debug("Keeps the passages the guard does not flag")
        kept = [hit for hit in hits if not guard.flag(hit.passage.text)]
        # log.debug("Logs any passage held back on the way out")
        if len(kept) < len(hits):
            # log.debug("Logs how many were held back")
            log_event(log, "mcp.passages_withheld", count=len(hits) - len(kept))
        # log.debug("Returns the passages kept")
        return kept


# log.debug("Defines the server built on the tools")
def build_server(services: Callable[[], Services] | None = None) -> MCPServer:
    """Returns the MCP server, its tools and its source resource.

    Call setup_logging() first: the SDK sets up console logging of its
    own when nothing else has.

    Args:
        services: Returns the services the tools read. Required.

    Returns:
        The server, ready to run over stdio or Streamable HTTP.
    """
    # log.debug("Builds the tools on the services lookup")
    tools = LibraryTools(required(services=services))
    # log.debug("Creates the server, named and described for clients")
    server = MCPServer(
        name=SETTINGS.mcp_name, title=TITLE, version=__version__, instructions=INSTRUCTIONS
    )
    # log.debug("Offers the search")
    server.tool(name="search_sources", description=SEARCH, annotations=READ_ONLY)(
        tools.search_sources
    )
    # log.debug("Offers the passage lookup")
    server.tool(name="get_passage", description=PASSAGE, annotations=READ_ONLY)(tools.get_passage)
    # log.debug("Offers the source listing")
    server.tool(name="list_sources", description=SOURCES, annotations=READ_ONLY)(
        tools.list_sources
    )
    # log.debug("Offers the checked answer")
    server.tool(name="ask", description=ASK, annotations=ASKS)(tools.ask)
    # log.debug("Offers each approved source as a resource")
    server.resource(SOURCE_URI, mime_type=MARKDOWN, description=SOURCE)(tools.source)
    # log.debug("Returns the server")
    return server
