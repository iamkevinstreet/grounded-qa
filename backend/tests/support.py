########################################################################
#                       backend/tests/support.py                       #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Helpers tests share: small sources with true     #
#                     hashes, and where the repository's data is.      #
########################################################################
"""Test helpers; fixtures live in conftest.py."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kds.logs import get_logger

from grounded_qa.core import sources
from grounded_qa.core.sources import Source

# Module constants
log = get_logger(__name__)
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


# log.debug("Defines a helper that builds a source with a true hash")
def make_source(source_id: str, body: str, **fields: Any) -> Source:
    """Return a valid Source; `fields` override the front matter."""
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
def write_source(folder: Path, source: Source) -> Path:
    """Write `source` as a document in `folder`; return its path."""
    # log.debug("Creates the folder")
    folder.mkdir(parents=True, exist_ok=True)
    # log.debug("Names the file for the id")
    path = folder / f"{source.id}.md"
    # log.debug("Writes the document")
    path.write_text(sources.render(source), encoding="utf-8")
    # log.debug("Returns the path")
    return path
