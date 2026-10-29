########################################################################
#                 backend/src/grounded_qa/api/state.py                 #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

The services every route shares, built once at startup, and the
dependency that hands them out.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, cast

# Third-party
from fastapi import Request
from kds.args import required
from kds.llm import ModelAdapter
from kds.logs import get_logger

# Local
from grounded_qa.api.limits import RateLimiter
from grounded_qa.config import SETTINGS, AppSettings
from grounded_qa.core.answer import Answerer
from grounded_qa.core.audit import AuditLog
from grounded_qa.core.embed import Embedder, LocalEmbedder
from grounded_qa.core.library import Library
from grounded_qa.core.offline import adapter_for

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the name of the mode that needs no embedding model, from the config")
KEYWORD: Final = SETTINGS.retrieval_keyword_mode


########################################################################
#                           Shared services                            #
########################################################################
# log.debug("Defines the services the routes share")
@dataclass(frozen=True)
class Services:
    """Everything a route needs, built once per app."""

    # log.debug("Holds the settings")
    settings: AppSettings
    # log.debug("Holds the approved sources and their index")
    library: Library
    # log.debug("Holds the answerer")
    answerer: Answerer
    # log.debug("Holds the per-client limit on questions")
    limiter: RateLimiter
    # log.debug("Holds the model adapter, for the health report")
    adapter: ModelAdapter


# log.debug("Defines how the services are built at startup")
def build_services(
    settings: AppSettings | None = None,
    adapter: ModelAdapter | None = None,
    embedder: Embedder | None = None,
) -> Services:
    """Builds the library, model adapter and answerer from settings.

    Tests pass an adapter and an embedder; the service builds both
    from settings.

    Args:
        settings: The settings to build from. Required.
        adapter: The model adapter; built from the settings when None.
        embedder: The embedding model; when None, the local model is
            loaded if the retrieval mode searches by meaning.

    Returns:
        The services, for the app's state.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Loads the embedding model only when the mode needs it")
    vectors = embedder or (
        LocalEmbedder(settings.retrieval_model) if settings.retrieval_mode != KEYWORD else None
    )
    # log.debug("Reads and indexes the approved sources")
    library = Library(settings, AuditLog(settings.data_audit), vectors)
    # log.debug("Uses the given adapter, or the configured model")
    model = adapter or adapter_for(settings)
    # log.debug("Returns the services")
    return Services(
        settings=settings,
        library=library,
        answerer=Answerer(library, model, settings, mode=library.mode),
        limiter=RateLimiter(settings.api_asks_per_minute),
        adapter=model,
    )


# log.debug("Defines the dependency routes declare to get the services")
def services(request: Request) -> Services:  # fixed: FastAPI's dependency signature
    """Returns the services the app built at startup.

    Args:
        request: The request, which FastAPI passes.

    Returns:
        The services in the app's state.
    """
    # log.debug("Returns them from the app's state")
    return cast(Services, request.app.state.services)
