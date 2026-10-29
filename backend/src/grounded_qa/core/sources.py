########################################################################
#               backend/src/grounded_qa/core/sources.py                #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Reads and writes approved source documents:      #
#                     front matter, a SHA-256 check, safe file paths.  #
########################################################################
"""Source documents: Markdown with provenance front matter.

Each document starts with a block of `key: value` lines between `---`
fences: its title, publisher, source URL, revision date, retrieval
date, licence, and the SHA-256 of the text below the block. A document
whose text no longer matches its hash is refused, so an edit to a
source can never go unnoticed.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from kds.logs import get_logger
from pydantic import BaseModel, Field, ValidationError

from grounded_qa.core import guard

# Module constants
log = get_logger(__name__)
# log.debug("Matches a safe source id: lowercase letters, digits, dashes")
ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
# log.debug("Matches a SHA-256 written as 64 hex characters")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
# log.debug("Sets the line that opens the front matter")
OPEN = "---\n"
# log.debug("Sets the lines that close it and start the text")
CLOSE = "\n---\n\n"
# log.debug("Sets the separator between a key and its value")
KEY_SEP = ": "
# log.debug("Lists the keys every front matter must hold, in order")
FIELDS = ("title", "publisher", "source", "revised", "retrieved", "license", "sha256")
# log.debug("Sets the file extension of a source document")
SUFFIX = ".md"
# log.debug("Names the folder guide that is not itself a source")
README = "README.md"
# log.debug("Sets the encoding source files are read and written in")
ENCODING = "utf-8"


# log.debug("Defines the error for a document that cannot be accepted")
class SourceError(ValueError):
    """A source document is malformed, altered or unsafe to store."""


# log.debug("Defines one approved source document")
class Source(BaseModel, frozen=True):
    """A source document, its provenance, and any flagged lines."""

    # log.debug("Holds the id, which is also the file name")
    id: str
    # log.debug("Holds the document's title")
    title: str
    # log.debug("Holds who published it")
    publisher: str
    # log.debug("Holds where it was published")
    source: str = Field(pattern=r"^https://")
    # log.debug("Holds the revision date the publisher states")
    revised: str
    # log.debug("Holds the day it was copied")
    retrieved: str
    # log.debug("Holds the terms it may be used under")
    license: str
    # log.debug("Holds the SHA-256 of its text")
    sha256: str = Field(pattern=SHA_RE.pattern)
    # log.debug("Holds the text, Markdown below the front matter")
    body: str
    # log.debug("Holds lines the guard found that give orders to a model")
    flagged: tuple[str, ...] = ()

    # log.debug("Defines the document's length in words")
    @property
    def words(self) -> int:
        """Return the number of words in the text."""
        # log.debug("Returns the word count")
        return len(self.body.split())


# log.debug("Defines the SHA-256 of a text")
def digest(body: str) -> str:
    """Return the hex SHA-256 of the text as UTF-8."""
    # log.debug("Returns the hex digest")
    return hashlib.sha256(body.encode(ENCODING)).hexdigest()


# log.debug("Defines the check on a source id")
def check_id(source_id: str) -> str:
    """Return the id if it is safe as a file name; raise otherwise."""
    # log.debug("Refuses an id that is not lowercase letters, digits, dashes")
    if not ID_RE.fullmatch(source_id):
        # log.debug("Raises with the rule the id broke")
        msg = "a source id is 1-64 lowercase letters, digits or dashes, not starting with a dash"
        # log.debug("Raises it")
        raise SourceError(msg)
    # log.debug("Returns the id")
    return source_id


# log.debug("Defines the file path of a source, kept inside its folder")
def path_for(folder: Path, source_id: str) -> Path:
    """Return the file for `source_id`; refuse any path that escapes."""
    # log.debug("Resolves the folder to an absolute path")
    root = folder.resolve()
    # log.debug("Builds the file path from the checked id")
    path = (root / f"{check_id(source_id)}{SUFFIX}").resolve()
    # log.debug("Refuses a path outside the folder, whatever the id held")
    if path.parent != root:
        # log.debug("Raises for the escaping path")
        msg = f"source id {source_id!r} points outside the sources folder"
        # log.debug("Raises it")
        raise SourceError(msg)
    # log.debug("Returns the path")
    return path


# log.debug("Defines how a document's text is read into a Source")
def parse(source_id: str, text: str) -> Source:
    """Read front matter and text; check the text against its hash.

    Raises:
        SourceError: The front matter is missing or incomplete, or the
            text does not match its SHA-256.
    """
    # log.debug("Refuses a document without front matter")
    if not text.startswith(OPEN) or CLOSE not in text:
        # log.debug("Words the error")
        msg = f"{source_id}: a source starts with front matter between --- lines"
        # log.debug("Raises it")
        raise SourceError(msg)
    # log.debug("Splits the front matter from the text")
    head, body = text[len(OPEN) :].split(CLOSE, 1)
    # log.debug("Reads each key: value line")
    meta = dict(line.split(KEY_SEP, 1) for line in head.splitlines() if KEY_SEP in line)
    # log.debug("Finds any required key that is missing")
    missing = [key for key in FIELDS if not meta.get(key, "").strip()]
    # log.debug("Refuses incomplete front matter")
    if missing:
        # log.debug("Words the error with the missing keys")
        msg = f"{source_id}: front matter lacks {missing}"
        # log.debug("Raises it")
        raise SourceError(msg)
    # log.debug("Refuses text that no longer matches its hash")
    if digest(body) != meta["sha256"].strip():
        # log.debug("Words the error")
        msg = f"{source_id}: the text does not match its sha256; was it edited?"
        # log.debug("Raises it")
        raise SourceError(msg)
    # log.debug("Builds the source, which checks the URL and hash formats")
    try:
        # log.debug("Returns the source with any flagged lines")
        return Source(
            id=check_id(source_id),
            body=body,
            flagged=tuple(guard.flag(body)),
            **{key: meta[key].strip() for key in FIELDS},
        )
    except ValidationError as error:
        # log.debug("Reports a malformed field as a source error")
        raise SourceError(f"{source_id}: {error.errors()[0]['msg']}") from error


# log.debug("Defines how a Source is written back as a document")
def render(source: Source) -> str:
    """Return the document text: front matter, then the text."""
    # log.debug("Writes each front-matter key on its own line")
    head = "\n".join(f"{key}{KEY_SEP}{getattr(source, key)}" for key in FIELDS)
    # log.debug("Returns the fenced front matter and the text")
    return f"{OPEN}{head}{CLOSE}{source.body}"


# log.debug("Defines how one document file is read")
def load(path: Path) -> Source:
    """Read and check the document at `path`, named for its id."""
    # log.debug("Parses the file, named for its id")
    return parse(path.stem, path.read_text(encoding=ENCODING))


# log.debug("Defines how a folder of documents is read")
def load_dir(folder: Path) -> list[Source]:
    """Read every document in `folder`, sorted by id.

    Raises:
        SourceError: Any document fails its checks; one bad source
            stops the service rather than being skipped silently.
    """
    # log.debug("Returns each Markdown file but the folder's README")
    return [load(path) for path in sorted(folder.glob(f"*{SUFFIX}")) if path.name != README]
