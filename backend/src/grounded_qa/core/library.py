########################################################################
#               backend/src/grounded_qa/core/library.py                #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

The approved sources and the search index over them: anyone may read
them, only an approver changes them, and each change is audited.
Adding or removing a source is an approver's action (the API checks
who is asking); the library checks the document, refuses one the
guard flags, writes or deletes the file, records the change in the
audit log, and rebuilds the index, all under one lock.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import Final

# Third-party
from kds.args import required
from kds.logs import get_logger, log_event
from pydantic import BaseModel, Field

# Local
from grounded_qa.config import SETTINGS, AppSettings
from grounded_qa.core import sources
from grounded_qa.core.audit import AuditLog
from grounded_qa.core.chunk import split_all
from grounded_qa.core.embed import Embedder
from grounded_qa.core.retrieve import Hit, Retriever
from grounded_qa.core.sources import Source, SourceError

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the encoding that turns text into bytes, from the config")
ENCODING: Final = SETTINGS.text_encoding

########################################################################
#                           Local constants                            #
########################################################################
# log.debug("Matches one line of front-matter text, with no line breaks")
ONE_LINE = r"^[^\r\n]+$"
# log.debug("Sets the longest title, publisher or licence, in characters")
MAX_FIELD_CHARS = 200


########################################################################
#                            Source library                            #
########################################################################
# log.debug("Defines the error for an id already in use")
class SourceExistsError(SourceError):
    """A source with this id is already approved."""


# log.debug("Defines a new document as an approver submits it")
class NewSource(BaseModel):
    """The fields an approver gives; the hash and dates are ours."""

    # log.debug("Holds the id, which becomes the file name")
    id: str = Field(pattern=sources.ID_RE.pattern)
    # log.debug("Holds the title")
    title: str = Field(min_length=1, max_length=MAX_FIELD_CHARS, pattern=ONE_LINE)
    # log.debug("Holds the publisher")
    publisher: str = Field(min_length=1, max_length=MAX_FIELD_CHARS, pattern=ONE_LINE)
    # log.debug("Holds the HTTPS address it was published at")
    source: str = Field(max_length=500, pattern=r"^https://[^\s]+$")
    # log.debug("Holds the revision date the publisher states")
    revised: str = Field(min_length=1, max_length=40, pattern=ONE_LINE)
    # log.debug("Holds the licence it may be used under")
    license: str = Field(min_length=1, max_length=MAX_FIELD_CHARS, pattern=ONE_LINE)
    # log.debug("Holds the text, as Markdown")
    body: str = Field(min_length=1)


# log.debug("Defines the library")
class Library:
    """The approved sources, their index, and audited changes."""

    # log.debug("Defines the constructor, which reads and indexes the sources")
    def __init__(
        self,
        settings: AppSettings | None = None,
        audit: AuditLog | None = None,
        embedder: Embedder | None = None,
    ) -> None:
        """Reads every source in the sources folder and indexes them.

        Args:
            settings: The settings: the sources folder and how to
                split and search. Required.
            audit: The audit log each change is recorded in. Required.
            embedder: The embedding model for semantic and hybrid
                search; None for keyword search.

        Raises:
            SourceError: A source on disk fails its checks.
        """
        # log.debug("Takes the settings, which the caller must give")
        settings = required(settings=settings)
        # log.debug("Takes the audit log, which the caller must give")
        audit = required(audit=audit)
        # log.debug("Keeps the settings")
        self.settings = settings
        # log.debug("Keeps the audit log")
        self.audit = audit
        # log.debug("Keeps the embedder, used again on each rebuild")
        self.embedder = embedder
        # log.debug("Creates the lock that serialises changes")
        self._lock = threading.Lock()
        # log.debug("Reads every source, by id")
        self._sources = {s.id: s for s in sources.load_dir(settings.data_sources)}
        # log.debug("Builds the index")
        self._retriever = self._index()

    # log.debug("Defines the retrieval mode in use")
    @property
    def mode(self) -> str:
        """Returns keyword, semantic or hybrid.

        Returns:
            The retrieval mode the index searches in.
        """
        # log.debug("Returns the retriever's mode")
        return self._retriever.mode

    # log.debug("Defines how many passages are searchable")
    @property
    def passages(self) -> int:
        """Returns the number of passages in the index.

        Returns:
            How many passages can be searched.
        """
        # log.debug("Returns the count")
        return len(self._retriever.passages)

    # log.debug("Defines the list of approved sources")
    def approved(self) -> list[Source]:
        """Returns every approved source, sorted by id.

        Returns:
            The sources, held-back ones included.
        """
        # log.debug("Returns the sources in id order")
        return [self._sources[key] for key in sorted(self._sources)]

    # log.debug("Defines one source by id")
    def get(self, source_id: str | None = None) -> Source:
        """Returns the source with this id.

        Args:
            source_id: The source's id. Required.

        Returns:
            The source.

        Raises:
            KeyError: No source has this id.
        """
        # log.debug("Takes the source id, which the caller must give")
        source_id = required(source_id=source_id)
        # log.debug("Returns the source; a missing id raises KeyError")
        return self._sources[source_id]

    # log.debug("Defines a search, delegated to the current index")
    def search(self, question: str | None = None, k: int | None = None) -> list[Hit]:
        """Returns the best passages for the question, best first.

        Args:
            question: The question to find passages for. Required.
            k: How many passages to return; the configured number when
                None.

        Returns:
            The best passages, best first.
        """
        # log.debug("Takes the question, which the caller must give")
        question = required(question=question)
        # log.debug("Returns the current retriever's hits")
        return self._retriever.search(question, k)

    # log.debug("Defines an approver adding a source")
    def add(self, new: NewSource | None = None, request_id: str | None = None) -> Source:
        """Checks, stores, audits and indexes a new source.

        Args:
            new: The source as the approver submitted it. Required.
            request_id: The request that adds it, for the audit log.
                Required.

        Returns:
            The stored source, with its hash and retrieval date.

        Raises:
            SourceError: It fails a check, or the guard flags it.
            SourceExistsError: The id is already in use.
        """
        # log.debug("Takes the new source, which the caller must give")
        new = required(new=new)
        # log.debug("Takes the request id, which the caller must give")
        request_id = required(request_id=request_id)
        # log.debug("Builds the document with our hash and today's date")
        text = sources.render(
            Source(
                **new.model_dump(),
                retrieved=datetime.now(UTC).date().isoformat(),
                sha256=sources.digest(new.body),
            )
        )
        # log.debug("Reads it back through the same checks as every source")
        source = sources.parse(new.id, text)
        # log.debug("Refuses a document with instruction-like text")
        if source.flagged:
            # log.debug("Words the error with the lines found")
            msg = f"remove the instruction-like lines first: {list(source.flagged)}"
            # log.debug("Raises it")
            raise SourceError(msg)
        # log.debug("Makes the change under the lock")
        with self._lock:
            # log.debug("Refuses an id already in use")
            if source.id in self._sources:
                # log.debug("Raises for the duplicate id")
                raise SourceExistsError(f"a source with id {source.id!r} already exists")
            # log.debug("Writes the file, failing if it already exists")
            with sources.path_for(self.settings.data_sources, source.id).open(
                "x", encoding=ENCODING
            ) as file:
                # log.debug("Writes the document")
                file.write(text)
            # log.debug("Records the change")
            self.audit.record("add", source.id, source.sha256, request_id)
            # log.debug("Adds the source and rebuilds the index")
            self._sources[source.id] = source
            # log.debug("Swaps in the new index")
            self._retriever = self._index()
        # log.debug("Logs the change")
        log_event(log, "source.added", source_id=source.id, words=source.words)
        # log.debug("Returns the stored source")
        return source

    # log.debug("Defines an approver removing a source")
    def remove(self, source_id: str | None = None, request_id: str | None = None) -> None:
        """Deletes, audits and unindexes a source.

        Args:
            source_id: The id of the source to remove. Required.
            request_id: The request that removes it, for the audit log.
                Required.

        Raises:
            KeyError: No source has this id.
        """
        # log.debug("Takes the source id, which the caller must give")
        source_id = required(source_id=source_id)
        # log.debug("Takes the request id, which the caller must give")
        request_id = required(request_id=request_id)
        # log.debug("Makes the change under the lock")
        with self._lock:
            # log.debug("Takes the source out; a missing id raises KeyError")
            source = self._sources.pop(source_id)
            # log.debug("Deletes its file")
            sources.path_for(self.settings.data_sources, source_id).unlink(missing_ok=True)
            # log.debug("Records the change")
            self.audit.record("remove", source_id, source.sha256, request_id)
            # log.debug("Swaps in an index without it")
            self._retriever = self._index()
        # log.debug("Logs the change")
        log_event(log, "source.removed", source_id=source_id)

    # log.debug("Defines how the index is built from the sources")
    def _index(self) -> Retriever:
        """Returns a retriever over every source the guard passed.

        Returns:
            A retriever over the passages of those sources.
        """
        # log.debug("Returns a retriever over the passages")
        return Retriever(
            split_all(self.approved(), self.settings.retrieval_passage_words),
            self.settings,
            self.embedder,
        )
