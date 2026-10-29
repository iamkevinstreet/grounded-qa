########################################################################
#                     backend/tests/test_audit.py                      #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Tests the audit log records changes in order and #
#                     refuses any edit or deletion of its rows.        #
########################################################################
"""Tests for grounded_qa.core.audit."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest
from kds.logs import get_logger

from grounded_qa.core.audit import AuditLog

# Module constants
log = get_logger(__name__)
# log.debug("Sets a fixed time, so entries are predictable")
FIXED = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)


# log.debug("Defines the test that changes come back newest first")
def test_entries_are_newest_first(tmp_path: Path) -> None:
    """Two changes come back newest first, with the clock's time."""
    # log.debug("Opens a log with a fixed clock")
    audit = AuditLog(tmp_path / "audit.sqlite", clock=lambda: FIXED)
    # log.debug("Records an add")
    audit.record("add", "one", "a" * 64, "req-1")
    # log.debug("Records a remove")
    audit.record("remove", "one", "a" * 64, "req-2")
    # log.debug("Reads them back")
    entries = audit.entries(10)
    # log.debug("Checks the order, actions and time")
    assert [(e.action, e.request_id, e.at) for e in entries] == [
        ("remove", "req-2", "2026-10-29T12:00:00+00:00"),
        ("add", "req-1", "2026-10-29T12:00:00+00:00"),
    ]


# log.debug("Defines the edits the database itself must refuse")
@pytest.mark.parametrize(
    "statement",
    ["UPDATE source_changes SET source_id = 'x'", "DELETE FROM source_changes"],
)
def test_rows_cannot_be_changed_or_deleted(tmp_path: Path, statement: str) -> None:
    """Triggers make the log append-only, even to direct SQL."""
    # log.debug("Opens a log and records one change")
    path = tmp_path / "audit.sqlite"
    # log.debug("Records the change")
    AuditLog(path).record("add", "one", "a" * 64, "req-1")
    # log.debug("Opens the database directly")
    with closing(sqlite3.connect(path)) as db:
        # log.debug("Expects the trigger to abort the statement")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            # log.debug("Tries the edit")
            db.execute(statement)


# log.debug("Defines the test that reopening does not migrate twice")
def test_reopening_keeps_rows_and_schema(tmp_path: Path) -> None:
    """Opening an existing log applies no migration again."""
    # log.debug("Records a change in a new log")
    AuditLog(tmp_path / "audit.sqlite").record("add", "one", "a" * 64, "req-1")
    # log.debug("Checks a second open still sees the row")
    assert len(AuditLog(tmp_path / "audit.sqlite").entries(10)) == 1
