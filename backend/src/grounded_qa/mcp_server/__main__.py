########################################################################
#                                                                      #
#            backend/src/grounded_qa/mcp_server/__main__.py            #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-07
Last modified on:  2026-11-07

Runs the MCP server over stdio, for a client that starts it as a
command, such as Claude Desktop or Claude Code:

    uv run --project backend python -m grounded_qa.mcp_server

The protocol has stdout to itself, so logs go to stderr and the day's
file, as the API's do.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from typing import Final

# Third-party
from kds.logs import flush_spans, get_logger, log_event, setup_logging, setup_spans

# Local
from grounded_qa import __version__
from grounded_qa.api.state import build_services
from grounded_qa.config import get_app_settings
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
# log.debug("Names the transport a client that starts the server uses")
STDIO: Final = "stdio"


########################################################################
#                                                                      #
#                           MCP entry point                            #
#                                                                      #
########################################################################
# log.debug("Defines the entry point")
def main() -> None:
    """Builds the services once and serves them over stdio."""
    # log.debug("Reads the settings once")
    settings = get_app_settings()
    # log.debug("Sets up JSON logging, to stderr and the day's file")
    setup_logging(settings)
    # log.debug("Turns spans on, when they have somewhere to go")
    setup_spans(settings, service=settings.spans_service, version=__version__)
    # log.debug("Builds the library, model adapter and answerer")
    services = build_services(settings)
    # log.debug("Logs that the server is starting, and over what")
    log_event(log, "mcp.start", version=__version__, transport=STDIO)
    # log.debug("Serves until the client closes the connection")
    try:
        # log.debug("Runs the server over stdio")
        build_server(lambda: services).run(STDIO)
    finally:
        # log.debug("Sends any spans still waiting")
        flush_spans()


# log.debug("Runs main when the module is run as a script")
if __name__ == "__main__":
    # log.debug("Starts the server")
    main()
