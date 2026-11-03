########################################################################
#                                                                      #
#              backend/src/grounded_qa/dashboard/tiles.py              #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-03
Last modified on:  2026-11-03

Builds the headline tiles: each measure for the run in focus, and how
it moved against the second run picked. A change that rounds to
nothing at the precision shown is no change; any other gets its
direction, and a colour for whether that is for the better. The
changes are plain differences between the two runs, not tested
against run-to-run noise.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Final, Literal, TypedDict

# Third-party
import pandas as pd
from kds.args import required
from kds.logs import get_logger

# Local
from grounded_qa.config import SETTINGS
from grounded_qa.dashboard.theme import dollars
from grounded_qa.evals.shares import fixed, pct_label

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the run id column, from the config")
RUN_ID: Final = SETTINGS.columns_run_id
# log.debug("Takes the runs table's cost per question column, from the config")
COST_PER_CASE: Final = SETTINGS.columns_cost_per_case
# log.debug("Takes the milliseconds in a second, from the config")
MS_PER_SECOND: Final = SETTINGS.time_ms_per_second

########################################################################
#                                                                      #
#                           Local constants                            #
#                                                                      #
########################################################################
# log.debug("Names a rise")
UP: Final = "up"
# log.debug("Names a fall")
DOWN: Final = "down"
# log.debug("Sets the words for a change that rounds to nothing")
NO_CHANGE: Final = "no change"
# log.debug("Lists the digits that show a change survived rounding")
NONZERO_DIGITS: Final = "123456789"
# log.debug("Sets the smallest difference that is not zero")
TINY: Final = 1e-12
# log.debug("Sets the percentage points in a share of one")
POINTS: Final = 100


########################################################################
#                                                                      #
#                            Headline tiles                            #
#                                                                      #
########################################################################
# log.debug("Defines one headline measure")
@dataclass(frozen=True)
class Tile:
    """One headline measure, in the words the case study uses.

    Attributes:
        column: The runs table column it shows.
        label: What the tile calls it.
        value: How its value is written.
        better: Which way is better, up or down.
        change: How the size of a change is written; like the value
            when None.
    """

    # log.debug("Holds the runs table column")
    column: str
    # log.debug("Holds the tile's label")
    label: str
    # log.debug("Holds how the value is written")
    value: Callable[[float], str]
    # log.debug("Holds which way is better")
    better: Literal["up", "down"]
    # log.debug("Holds how the size of a change is written, when not like the value")
    change: Callable[[float], str] | None = None


# log.debug("Defines one tile as the page shows it")
class TileRow(TypedDict):
    """One tile: its measure, label, value, change and tone.

    The change is None when no second run is picked; good is None when
    there is no change.
    """

    # log.debug("Holds the runs table column")
    measure: str
    # log.debug("Holds the label")
    label: str
    # log.debug("Holds the value as written")
    value: str
    # log.debug("Holds the change as written, with its direction")
    delta: str | None
    # log.debug("Holds whether the change is for the better")
    good: bool | None


# log.debug("Defines how a share is written on a tile")
def _all_or_tenths(share: float | None = None) -> str:
    """Returns a share to one decimal, all as a whole 100%.

    Args:
        share: The share, from 0 to 1. Required.

    Returns:
        The share as a percent: 100% when it is everything, else to
        one decimal.
    """
    # log.debug("Takes the share, which the caller must give")
    share = required(share=share)
    # log.debug("Returns a hundred percent for everything, else one decimal")
    return "100%" if share >= 1 else pct_label(share, 1)


# log.debug("Defines how a change in a share is written")
def _points(size: float | None = None) -> str:
    """Returns the size of a change in a share, in percentage points.

    Args:
        size: The size of the change in a share, from 0 to 1.
            Required.

    Returns:
        The change in percentage points, to one decimal.
    """
    # log.debug("Takes the size, which the caller must give")
    size = required(size=size)
    # log.debug("Returns the points, to one decimal")
    return f"{fixed(size * POINTS, 1)} pts"


# log.debug("Defines how a time in milliseconds is written")
def _seconds(ms: float | None = None) -> str:
    """Returns a time in milliseconds as seconds, to one decimal.

    Args:
        ms: The time, in milliseconds. Required.

    Returns:
        The time in seconds, to one decimal.
    """
    # log.debug("Takes the time, which the caller must give")
    ms = required(ms=ms)
    # log.debug("Returns the seconds")
    return f"{fixed(ms / MS_PER_SECOND, 1)} s"


# Plain-language measures, in the words the case study uses: the
# column, its label, how to write it, which way is better, and how to
# write a change when not like the value.
# log.debug("Lists the six tiles in the order they are shown")
TILES: Final = (
    Tile("correct", "Correct, of the answerable questions", _all_or_tenths, UP, _points),
    Tile("answered", "Answered, of the answerable questions", _all_or_tenths, UP, _points),
    Tile(
        "abstained_correctly",
        "Refused rightly, of the questions the sources do not answer",
        _all_or_tenths,
        UP,
        _points,
    ),
    Tile(
        "citation_precision",
        "Citations to a passage marked as evidence",
        _all_or_tenths,
        UP,
        _points,
    ),
    Tile("latency_p50_ms", "Seconds per question, typical", _seconds, DOWN),
    Tile(COST_PER_CASE, "Cost per question", dollars, DOWN),
)


# log.debug("Defines the tiles for the runs picked")
def tile_rows(
    runs_df: pd.DataFrame | None = None, run_ids: Sequence[str] | None = None
) -> list[TileRow]:
    """Returns each measure for the run in focus, and how it moved.

    It moved against the second run picked.

    Args:
        runs_df: The runs table from `frames`. Required.
        run_ids: The runs picked, the run in focus first. Required.

    Returns:
        A row per tile, in the order shown; none when no run is picked.
    """
    # log.debug("Takes the runs table, which the caller must give")
    runs_df = required(runs_df=runs_df)
    # log.debug("Takes the run ids, which the caller must give")
    run_ids = required(run_ids=run_ids)
    # log.debug("Shows no tiles when no run is picked")
    if not run_ids:
        # log.debug("Returns no rows")
        return []
    # log.debug("Takes the run in focus")
    now = runs_df[runs_df[RUN_ID] == run_ids[0]].iloc[0]
    # log.debug("Takes the run to compare with, when a second is picked")
    then = runs_df[runs_df[RUN_ID] == run_ids[1]].iloc[0] if len(run_ids) > 1 else None
    # log.debug("Returns a row per tile")
    return [_row(tile, now, then) for tile in TILES]


# log.debug("Defines one tile's row")
def _row(
    tile: Tile | None = None,
    now: pd.Series[Any] | None = None,
    then: pd.Series[Any] | None = None,
) -> TileRow:
    """Returns the tile for the run in focus, with its change if any.

    Args:
        tile: The tile. Required.
        now: The run in focus's row of the runs table. Required.
        then: The second run's row, to compare with; None when only
            one run is picked.

    Returns:
        The tile's row, as the page shows it.
    """
    # log.debug("Takes the tile, which the caller must give")
    tile = required(tile=tile)
    # log.debug("Takes the run in focus, which the caller must give")
    now = required(now=now)
    # log.debug("Reads the value, a missing one as zero")
    value = _number(now[tile.column])
    # log.debug("Reads the earlier run's value, when there is one, a missing one as zero")
    before = None if then is None else _number(then[tile.column])
    # log.debug("Writes the change against it")
    delta, good = (None, None) if before is None else _change(tile, value - before)
    # log.debug("Returns the row")
    return TileRow(
        measure=tile.column, label=tile.label, value=tile.value(value), delta=delta, good=good
    )


# log.debug("Defines how a measure is read from the runs table")
def _number(value: Any = None) -> float:
    """Returns a measure as a number, a missing one as zero.

    Args:
        value: The measure from the runs table; None or NaN when the
            run's summary lacks it.

    Returns:
        The measure, or zero.
    """
    # log.debug("Returns zero for a missing measure")
    if value is None or pd.isna(value):
        # log.debug("Returns zero")
        return 0.0
    # log.debug("Returns the number")
    return float(value)


# log.debug("Defines how a change is written and judged")
def _change(tile: Tile | None = None, diff: float | None = None) -> tuple[str, bool | None]:
    """Returns the change as written, and whether it is for the better.

    A change that rounds to nothing has no direction and is neither
    good nor bad.

    Args:
        tile: The tile. Required.
        diff: The run in focus's value less the earlier run's.
            Required.

    Returns:
        The change as written, and True for the better, False for the
        worse, or None for no change.
    """
    # log.debug("Takes the tile, which the caller must give")
    tile = required(tile=tile)
    # log.debug("Takes the difference, which the caller must give")
    diff = required(diff=diff)
    # log.debug("Writes the size of the change as the tile writes it")
    shown = (tile.change or tile.value)(abs(diff))
    # log.debug("Calls a change that rounds to nothing no change")
    if abs(diff) < TINY or not any(digit in NONZERO_DIGITS for digit in shown):
        # log.debug("Returns no change")
        return NO_CHANGE, None
    # log.debug("Returns the direction and size, and whether that is for the better")
    return f"{UP if diff > 0 else DOWN} {shown}", (diff > 0) == (tile.better == UP)
