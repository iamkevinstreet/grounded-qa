########################################################################
#                  backend/grounded_qa/core/audit.py                   #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Records every change to the approved sources in  #
#                     an append-only SQLite log: what, when, which id. #
########################################################################
"""The audit log of source changes.

One row per change: when, add or remove, which source, the SHA-256 of
its text, and the request id that ties it to the service logs. Triggers
refuse any UPDATE or DELETE, so the log can only grow. The schema
changes only through the numbered migrations below.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from kds.logs import get_logger
from pydantic import BaseModel

# Module constants
log = get_logger(__name__)
# log.debug("Lists the changes the log records")
Action = Literal["add", "remove"]
# log.debug("Lists the schema migrations, applied in order, never edited")
MIGRATIONS = (
    """
    CREATE TABLE source_changes (
        id INTEGER PRIMARY KEY,
        at TEXT NOT NULL,
        action TEXT NOT NULL CHECK (action IN ('add', 'remove')),
        source_id TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        request_id TEXT NOT NULL
    );
    CREATE TRIGGER source_changes_no_update BEFORE UPDATE ON source_changes
    BEGIN SELECT RAISE(ABORT, 'the audit log is append-only'); END;
    CREATE TRIGGER source_changes_no_delete BEFORE DELETE ON source_changes
    BEGIN SELECT RAISE(ABORT, 'the audit log is append-only'); END;
    """,
)
# log.debug("Lists the columns a row is read with, in order")
COLUMNS = ("id", "at", "action", "source_id", "sha256", "request_id")
# log.debug("Sets the precision of each change's time")
TIMESPEC = "seconds"


# log.debug("Defines one recorded change")
class AuditEntry(BaseModel, frozen=True):
    """One change to the approved sources."""

    # log.debug("Holds the row number, in the order changes happened")
    id: int
    # log.debug("Holds when it happened, in UTC")
    at: str
    # log.debug("Holds whether a source was added or removed")
    action: Action
    # log.debug("Holds which source")
    source_id: str
    # log.debug("Holds the SHA-256 of the source's text")
    sha256: str
    # log.debug("Holds the request id, to find the change in the logs")
    request_id: str


# log.debug("Defines the clock changes are timed by")
def utc_now() -> datetime:
    """Return the current time in UTC."""
    # log.debug("Returns now, in UTC")
    return datetime.now(UTC)


# log.debug("Defines the audit log")
class AuditLog:
    """An append-only SQLite log of source changes."""

    # log.debug("Defines the constructor, which brings the schema up to date")
    def __init__(self, path: Path, clock: Callable[[], datetime] = utc_now) -> None:
        """Open the log at `path`; create and migrate it as needed."""
        # log.debug("Keeps the database path")
        self.path = path
        # log.debug("Keeps the clock, which tests replace")
        self.clock = clock
        # log.debug("Creates the database's folder")
        path.parent.mkdir(parents=True, exist_ok=True)
        # log.debug("Applies any migration not yet applied")
        self._migrate()

    # log.debug("Defines one recorded change")
    def record(self, action: Action, source_id: str, sha256: str, request_id: str) -> AuditEntry:
        """Append one change and return it as stored."""
        # log.debug("Takes the change's time from the clock")
        at = self.clock().isoformat(timespec=TIMESPEC)
        # log.debug("Opens the database and a transaction")
        with closing(sqlite3.connect(self.path)) as db, db:
            # log.debug("Inserts the row with bound parameters, never formatted SQL")
            cursor = db.execute(
                "INSERT INTO source_changes (at, action, source_id, sha256, request_id)"
                " VALUES (?, ?, ?, ?, ?)",
                (at, action, source_id, sha256, request_id),
            )
        # log.debug("Returns the change with its row number")
        return AuditEntry(
            id=cursor.lastrowid or 0,
            at=at,
            action=action,
            source_id=source_id,
            sha256=sha256,
            request_id=request_id,
        )

    # log.debug("Defines the latest changes, newest first")
    def entries(self, limit: int) -> list[AuditEntry]:
        """Return up to `limit` changes, newest first."""
        # log.debug("Opens the database")
        with closing(sqlite3.connect(self.path)) as db:
            # log.debug("Reads the newest rows")
            rows = db.execute(
                "SELECT id, at, action, source_id, sha256, request_id"
                " FROM source_changes ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        # log.debug("Returns each row as an entry")
        return [AuditEntry.model_validate(dict(zip(COLUMNS, row, strict=True))) for row in rows]

    # log.debug("Defines the schema migrations")
    def _migrate(self) -> None:
        """Apply, in order, each migration newer than the database."""
        # log.debug("Opens the database")
        with closing(sqlite3.connect(self.path)) as db:
            # log.debug("Reads the schema version the database is at")
            version = int(db.execute("PRAGMA user_version").fetchone()[0])
            # log.debug("Applies each newer migration and records its number")
            for number, script in enumerate(MIGRATIONS[version:], start=version + 1):
                # log.debug("Runs the migration, then stamps the version")
                db.executescript(f"BEGIN; {script} PRAGMA user_version = {number:d}; COMMIT;")
                # log.debug("Logs the migration")
                log.info("audit log migrated to version %d", number)
