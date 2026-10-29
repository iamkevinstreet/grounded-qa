########################################################################
#                      backend/tests/conftest.py                       #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Test setup: offline, isolated folders, and small #
#                     sources with true hashes for any test to use.    #
########################################################################
"""Shared fixtures: every test is offline and writes to tmp_path."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from kds.logs import get_logger

from grounded_qa.config import AppSettings, get_app_settings

from support import LEAVE_BODY, OVERTIME_BODY, REPO, make_source, write_source

# Module constants
log = get_logger(__name__)


# log.debug("Defines the isolation every test gets")
@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Offline provider, logs in tmp_path, no settings file or .env."""
    # log.debug("Runs from an empty folder, so no .env or settings file is found")
    monkeypatch.chdir(tmp_path)
    # log.debug("Forces the offline provider so no test calls a model")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    # log.debug("Sends log files to the test's own folder")
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    # log.debug("Points the settings file at one that does not exist")
    monkeypatch.setenv("SETTINGS_FILE", str(tmp_path / "absent.toml"))
    # log.debug("Clears any approver token from the environment")
    monkeypatch.delenv("APPROVER_TOKEN", raising=False)
    # log.debug("Clears cached settings before the test")
    get_app_settings.cache_clear()
    # log.debug("Runs the test")
    yield
    # log.debug("Clears cached settings after the test")
    get_app_settings.cache_clear()


# log.debug("Defines settings whose data folders are in tmp_path")
@pytest.fixture
def settings(tmp_path: Path) -> AppSettings:
    """Settings with two small sources and empty samples in tmp_path."""
    # log.debug("Writes the two small sources")
    for source in (make_source("leave", LEAVE_BODY), make_source("overtime", OVERTIME_BODY)):
        # log.debug("Writes one source")
        write_source(tmp_path / "sources", source)
    # log.debug("Creates an empty samples folder")
    (tmp_path / "samples").mkdir()
    # log.debug("Returns settings pointing at those folders")
    return AppSettings(
        data_sources=tmp_path / "sources",
        data_samples=tmp_path / "samples",
        data_results=tmp_path / "results",
        data_audit=tmp_path / "generated" / "audit.sqlite",
        retrieval_k=3,
    )


# log.debug("Defines settings over the real approved corpus")
@pytest.fixture
def real_settings(tmp_path: Path) -> AppSettings:
    """Settings over the repository data; results in tmp_path."""
    # log.debug("Returns settings over the repository's data")
    return AppSettings(
        data_sources=REPO / "data" / "sources",
        data_samples=REPO / "data" / "samples",
        data_cases=REPO / "data" / "evals" / "cases.jsonl",
        data_results=tmp_path / "results",
        data_audit=tmp_path / "generated" / "audit.sqlite",
    )
