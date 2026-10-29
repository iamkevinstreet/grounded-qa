########################################################################
#                 backend/src/grounded_qa/__init__.py                  #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

The grounded Q&A package: answers employment-law questions from
approved sources only, with every quote checked.

core/ holds the logic (sources, retrieval, answers, checks), api/ the
HTTP service, and evals/ the evaluation that measures it.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

# Third-party
from kds.logs import get_logger

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)

########################################################################
#                           Local constants                            #
########################################################################
# log.debug("Sets the package version, kept equal to pyproject.toml")
__version__ = "0.2.0"
