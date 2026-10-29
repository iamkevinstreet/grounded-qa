########################################################################
#                 backend/src/grounded_qa/__init__.py                  #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           The grounded Q&A package: answers from approved  #
#                     sources only, with every quote checked.          #
########################################################################
"""grounded_qa: answers employment-law questions from approved sources.

core/ holds the logic (sources, retrieval, answers, checks), api/ the
HTTP service, and evals/ the evaluation that measures it.
"""

from __future__ import annotations

from kds.logs import get_logger

# Module constants
log = get_logger(__name__)
# log.debug("Sets the package version, kept equal to pyproject.toml")
__version__ = "0.1.0"
