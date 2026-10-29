########################################################################
#                       backend/tests/support.py                       #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

The helpers and values tests share: where the repository's data is,
an approver token, two small sources, and helpers that build and write
sources with true hashes. Fixtures live in conftest.py.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

from pathlib import Path
from typing import Any

# Third-party
from kds.args import required
from kds.logs import get_logger

# Local
from grounded_qa.core import sources
from grounded_qa.core.sources import Source

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)

########################################################################
#                           Local constants                            #
########################################################################
# log.debug("Points at the repository root, two folders above this one")
REPO = Path(__file__).resolve().parents[2]
# log.debug("Sets a token long enough for the approver check")
TOKEN = "approver-token-for-tests-only-00000000"
# log.debug("Sets the text of a small FMLA source")
LEAVE_BODY = (
    "The FMLA provides job-protected leave.\n\n"
    "## Using leave\n\n"
    "Eligible employees may take up to 12 workweeks of leave in a 12-month period.\n\n"
    "## Pay\n\n"
    "FMLA is job-protected, unpaid leave. Employees may use paid leave at the same time.\n"
)
# log.debug("Sets the text of a small overtime source")
OVERTIME_BODY = (
    "## Requirements\n\n"
    "Covered employees must receive overtime pay for hours worked over 40 in a workweek.\n\n"
    "The overtime requirement may not be waived by agreement between the employer and employees.\n"
)


########################################################################
#                             Test helpers                             #
########################################################################
# log.debug("Defines a helper that builds a source with a true hash")
def make_source(source_id: str | None = None, body: str | None = None, **fields: Any) -> Source:
    """Returns a valid Source; `fields` override the front matter.

    Args:
        source_id: The source's id. Required.
        body: The source's text. Required.
        **fields: Front-matter fields to set instead of the defaults.

    Returns:
        The source, its SHA-256 taken from `body`.
    """
    # log.debug("Takes the source id, which the caller must give")
    source_id = required(source_id=source_id)
    # log.debug("Takes the body, which the caller must give")
    body = required(body=body)
    # log.debug("Returns the source with defaults for every field")
    return Source(
        **{
            "id": source_id,
            "title": f"Test source {source_id}",
            "publisher": "Test publisher",
            "source": f"https://example.com/{source_id}",
            "revised": "January 2026",
            "retrieved": "2026-10-29",
            "license": "Public domain",
            "sha256": sources.digest(body),
            "body": body,
        }
        | fields
    )


# log.debug("Defines a helper that writes a source file")
def write_source(folder: Path | None = None, source: Source | None = None) -> Path:
    """Writes `source` as a document in `folder`; returns its path.

    Args:
        folder: The folder to write into, made if missing. Required.
        source: The source to write. Required.

    Returns:
        The document's path.
    """
    # log.debug("Takes the folder, which the caller must give")
    folder = required(folder=folder)
    # log.debug("Takes the source, which the caller must give")
    source = required(source=source)
    # log.debug("Creates the folder")
    folder.mkdir(parents=True, exist_ok=True)
    # log.debug("Names the file for the id")
    path = folder / f"{source.id}.md"
    # log.debug("Writes the document")
    path.write_text(sources.render(source), encoding="utf-8")
    # log.debug("Returns the path")
    return path
