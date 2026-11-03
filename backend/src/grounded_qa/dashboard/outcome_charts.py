########################################################################
#                                                                      #
#         backend/src/grounded_qa/dashboard/outcome_charts.py          #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-03
Last modified on:  2026-11-03

Draws the outcomes chart: for each kind of question, a stacked bar of
how the questions ended, a panel per run on one scale. Green is right
and amber is wrong, as on the site; a refusal is hatched, since the
service said nothing; an answer that should have been a refusal is in
full ink, the worst outcome for a legal tool. The kinds are listed in
the order the config names them, and the outcomes stacked in theirs.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Final

# Third-party
import pandas as pd
import plotly.graph_objects as go
from kds.args import missing, required
from kds.logs import get_logger
from plotly.subplots import make_subplots

# Local
from grounded_qa.config import SETTINGS
from grounded_qa.dashboard.theme import THEMES, Theme, hover, shared_layout
from grounded_qa.dashboard.views import long_labels, present

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the run id column, from the config")
RUN_ID: Final = SETTINGS.columns_run_id
# log.debug("Takes the kind of question column, from the config")
CASE_KIND: Final = SETTINGS.columns_case_kind
# log.debug("Takes the column that says how a question ended, from the config")
OUTCOME: Final = SETTINGS.columns_outcome
# log.debug("Takes the name of each kind of question, from the config")
KIND_LABELS: Final = SETTINGS.labels_kinds
# log.debug("Takes the words for each outcome, in stack order, from the config")
OUTCOME_LABELS: Final = SETTINGS.labels_outcomes
# log.debug("Takes the outcome of an answer with every expected fact, from the config")
RIGHT: Final = SETTINGS.outcomes_right
# log.debug("Takes the outcome of an answer without every expected fact, from the config")
MISSED: Final = SETTINGS.outcomes_missed
# log.debug("Takes the outcome of an answerable question refused, from the config")
REFUSED_WRONGLY: Final = SETTINGS.outcomes_refused_wrongly
# log.debug("Takes the outcome of an unanswerable question refused, from the config")
REFUSED_RIGHTLY: Final = SETTINGS.outcomes_refused_rightly
# log.debug("Takes the outcome of an unanswerable question answered, from the config")
SHOULD_HAVE_REFUSED: Final = SETTINGS.outcomes_should_have_refused
# log.debug("Takes the outcome of a question the run could not finish, from the config")
FAILED: Final = SETTINGS.outcomes_failed
# log.debug("Takes the light scheme's name, from the config")
LIGHT: Final = SETTINGS.charts_light_scheme
# log.debug("Takes the size of chart text, from the config")
FONT_SIZE: Final = SETTINGS.charts_font_size
# log.debug("Takes the size of value-axis ticks and small notes, from the config")
TICK_SIZE: Final = SETTINGS.charts_tick_size
# log.debug("Takes the margin every chart keeps at its edges, from the config")
EDGE: Final = SETTINGS.charts_edge
# log.debug("Takes the colour that lets the card show through, from the config")
CLEAR: Final = SETTINGS.charts_clear
# log.debug("Takes the edge titles and the key line up on, from the config")
LEFT: Final = SETTINGS.charts_align

########################################################################
#                                                                      #
#                           Local constants                            #
#                                                                      #
########################################################################
# log.debug("Maps each outcome to the name of the theme colour it is drawn in")
COLOUR_OF: Final = {
    RIGHT: "right",
    REFUSED_RIGHTLY: "right",
    MISSED: "miss",
    REFUSED_WRONGLY: "miss",
    SHOULD_HAVE_REFUSED: "ink",
    FAILED: "ink3",
}
# log.debug("Lists the outcomes drawn hatched: the refusals, where the service said nothing")
HATCHED: Final = frozenset({REFUSED_RIGHTLY, REFUSED_WRONGLY})
# log.debug("Sets the hatching: thin diagonal lines")
HATCH: Final = "/"
# log.debug("Sets the chart's height above its rows")
BASE: Final = 72
# log.debug("Sets the height of each kind's row")
ROW: Final = 34
# log.debug("Sets the room the panel titles take above the rows")
TITLE_ROOM: Final = 24
# log.debug("Sets the room each further line of a panel title takes")
LINE_ROOM: Final = 16
# log.debug("Sets the longest line of a panel title; a longer one breaks at a comma")
WRAP_AT: Final = 28
# log.debug("Sets what parts of a run's name are joined with, where a title may break")
JOIN: Final = ", "
# log.debug("Sets the line break in a title")
BREAK: Final = "<br>"
# log.debug("Sets the room the count axis and the key take below the rows")
KEY_ROOM: Final = 60
# log.debug("Sets the edge of the figure the key is placed against")
CONTAINER: Final = "container"
# log.debug("Sets the gap between panels, as a share of the width")
PANEL_GAP: Final = 0.035
# log.debug("Sets the room the count axis leaves past the longest bar")
HEADROOM: Final = 1.04
# log.debug("Sets the smallest text a segment may carry; smaller is hidden")
MIN_TEXT: Final = 10
# log.debug("Sets the chart's height when no run picked is held")
EMPTY_HEIGHT: Final = 200


########################################################################
#                                                                      #
#                            Outcomes chart                            #
#                                                                      #
########################################################################
# log.debug("Defines the outcomes chart")
def fig_outcomes(
    questions: pd.DataFrame | None = None,
    run_ids: str | Sequence[str] | None = None,
    theme: str = LIGHT,
    labels: dict[str, str] | None = None,
) -> go.Figure:
    """Returns how each kind of question ended, a panel per run.

    Every panel is on the same scale, and a segment wide enough
    carries its count.

    Args:
        questions: The questions table from `frames`. Required.
        run_ids: Up to three runs, the run in focus first. Required.
        theme: The colour scheme, light or dark.
        labels: Each run's name for titles and hover; long labels when
            None.

    Returns:
        The chart.
    """
    # log.debug("Takes the questions, which the caller must give")
    questions = required(questions=questions)
    # log.debug("Stops when the caller left out the run ids")
    if run_ids is None:
        # log.debug("Raises the missing-argument error")
        raise missing(run_ids=run_ids)
    # log.debug("Takes the scheme's colours")
    colours = THEMES[theme]
    # log.debug("Keeps the runs the table holds, at most three")
    ids = present(questions, run_ids)
    # log.debug("Draws an empty chart when the table holds none of them")
    if not ids:
        # log.debug("Returns the empty chart")
        return shared_layout(go.Figure(), EMPTY_HEIGHT, colours)
    # log.debug("Counts each run's questions by kind and outcome")
    counts = {r: _counts(questions[questions[RUN_ID] == r]) for r in ids}
    # log.debug("Lists the kinds held, in the order the config names them")
    kinds = _ordered({k for t in counts.values() for k in t.index}, list(KIND_LABELS.values()))
    # log.debug("Lists the outcomes held, by their keys, in stack order")
    held = {label for t in counts.values() for label in t.columns}
    # log.debug("Keeps the keys of the outcomes held")
    outcomes = [k for k, label in OUTCOME_LABELS.items() if label in held]
    # log.debug("Names each run, from the labels given or the table")
    names = labels or long_labels(questions, ids)
    # log.debug("Titles the panels when there are several, long names broken onto two lines")
    titles = [_wrapped(names[r]) for r in ids] if len(ids) > 1 else []
    # log.debug("Draws a panel per run")
    fig = _panels(counts, ids, names, kinds, outcomes, titles=titles, colours=colours)
    # log.debug("Measures the room the titles need: none, or a line and each further line")
    title_room = max((TITLE_ROOM + LINE_ROOM * title.count(BREAK) for title in titles), default=0)
    # log.debug("Applies the shared layout: a row per kind, room for the key and the titles")
    fig = shared_layout(fig, BASE + ROW * len(kinds) + KEY_ROOM + title_room, colours)
    # log.debug("Stacks the segments, keys them along the bottom edge, hides text that cannot fit")
    fig.update_layout(
        barmode="stack",
        showlegend=True,
        legend=dict(yref=CONTAINER, y=0, yanchor="bottom", x=0, xanchor=LEFT, orientation="h"),
        uniformtext=dict(mode="hide", minsize=MIN_TEXT),
        margin=dict(t=title_room + EDGE, b=KEY_ROOM),
    )
    # log.debug("Returns the chart")
    return fig


# log.debug("Defines the counts behind one panel")
def _counts(rows: pd.DataFrame | None = None) -> pd.DataFrame:
    """Returns how many questions of each kind had each outcome.

    Args:
        rows: One run's rows of the questions table. Required.

    Returns:
        The counts: a row per kind and a column per outcome held, in
        the outcomes' words.
    """
    # log.debug("Takes the rows, which the caller must give")
    rows = required(rows=rows)
    # log.debug("Returns the counts, kinds down, outcomes across")
    return pd.crosstab(rows[CASE_KIND], rows[OUTCOME])


# log.debug("Defines the order of the categories held")
def _ordered(held: set[str] | None = None, named: list[str] | None = None) -> list[str]:
    """Returns the categories held, the named ones first in their order.

    Args:
        held: The categories the tables hold. Required.
        named: The categories in the order the config names them.
            Required.

    Returns:
        The named categories held, in the config's order, then any
        others in alphabetical order.
    """
    # log.debug("Takes the categories held, which the caller must give")
    held = required(held=held)
    # log.debug("Takes the named order, which the caller must give")
    named = required(named=named)
    # log.debug("Returns the named ones held first, then the rest")
    return [c for c in named if c in held] + sorted(c for c in held if c not in named)


# log.debug("Defines how a long panel title breaks onto two lines")
def _wrapped(name: str | None = None) -> str:
    """Returns the run's name, broken at its commas into short lines.

    Args:
        name: The run's name. Required.

    Returns:
        The name, with a line break wherever the next part would run
        a line past the limit.
    """
    # log.debug("Takes the name, which the caller must give")
    name = required(name=name)
    # log.debug("Starts with the first part on the first line")
    lines = [name.split(JOIN)[0]]
    # log.debug("Adds each further part to the line, or starts a new one when it would run long")
    for part in name.split(JOIN)[1:]:
        # log.debug("Starts a new line when the part would not fit")
        if len(lines[-1]) + len(JOIN) + len(part) > WRAP_AT:
            # log.debug("Puts the part on its own line")
            lines.append(part)
        else:
            # log.debug("Joins the part to the line")
            lines[-1] += JOIN + part
    # log.debug("Returns the lines, broken")
    return BREAK.join(lines)


# log.debug("Defines the chart's panels")
def _panels(
    counts: dict[str, pd.DataFrame] | None = None,
    ids: list[str] | None = None,
    names: dict[str, str] | None = None,
    kinds: list[str] | None = None,
    outcomes: list[str] | None = None,
    *,
    titles: list[str] | None = None,
    colours: Theme | None = None,
) -> go.Figure:
    """Returns a panel per run, side by side on one kind axis.

    The first panel's segments make the key.

    Args:
        counts: Each run's counts from `_counts`, by run id. Required.
        ids: The runs to draw, the run in focus first. Required.
        names: Each run's name, for the hover. Required.
        kinds: The kinds, in the order they are listed. Required.
        outcomes: The outcomes held, in stack order. Required.
        titles: The panels' titles, in the runs' order; none when the
            panels carry no titles. Required.
        colours: The scheme to draw in. Required.

    Returns:
        The figure with a panel per run.
    """
    # log.debug("Takes the counts, which the caller must give")
    counts = required(counts=counts)
    # log.debug("Takes the run ids, which the caller must give")
    ids = required(ids=ids)
    # log.debug("Takes the runs' names, which the caller must give")
    names = required(names=names)
    # log.debug("Takes the kinds, which the caller must give")
    kinds = required(kinds=kinds)
    # log.debug("Takes the outcomes, which the caller must give")
    outcomes = required(outcomes=outcomes)
    # log.debug("Takes the titles, which the caller must give")
    titles = required(titles=titles)
    # log.debug("Takes the colours, which the caller must give")
    colours = required(colours=colours)
    # log.debug("Lays the panels out in one row, sharing the kind axis")
    fig = make_subplots(
        rows=1,
        cols=len(ids),
        shared_yaxes=True,
        horizontal_spacing=PANEL_GAP,
        subplot_titles=titles or None,
    )
    # log.debug("Squares each run's counts: every kind and every outcome held, zero where none")
    squared = {
        r: counts[r].reindex(
            index=kinds, columns=[OUTCOME_LABELS[k] for k in outcomes], fill_value=0
        )
        for r in ids
    }
    # log.debug("Finds the most questions of one kind in any run, which sets the scale")
    top = max(int(table.sum(axis=1).max()) for table in squared.values())
    # log.debug("Fills each panel with its run's stacked bars")
    for col, run_id in enumerate(ids, start=1):
        # log.debug("Takes the run's counts")
        held = squared[run_id]
        # log.debug("Adds a trace per outcome, the first panel's making the key")
        for key in outcomes:
            # log.debug("Adds the outcome's segments")
            fig.add_trace(
                _segments(held, key, index=col - 1, label=names[run_id], colours=colours),
                row=1,
                col=col,
            )
    # log.debug("Lists the kinds from the top down and puts every panel on the same scale")
    fig.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=kinds)
    # log.debug("Sets the count axis, the same on every panel, with whole-number ticks")
    fig.update_xaxes(range=[0, top * HEADROOM], tickformat="d", tickfont=dict(size=TICK_SIZE))
    # log.debug("Puts each panel's title over the panel's left edge")
    _place_titles(fig, colours)
    # log.debug("Returns the panels")
    return fig


# log.debug("Defines one outcome's segments in one panel")
def _segments(
    held: pd.DataFrame | None = None,
    key: str | None = None,
    *,
    index: int | None = None,
    label: str | None = None,
    colours: Theme | None = None,
) -> go.Bar:
    """Returns one run's segments for one outcome, a bar per kind.

    Args:
        held: The run's counts, a row per kind and a column per
            outcome. Required.
        key: The outcome's key in the config's [outcomes] table.
            Required.
        index: The run's place among those picked; 0 is in focus.
            Required.
        label: The run's name for the hover. Required.
        colours: The scheme to draw in. Required.

    Returns:
        The segments, with their counts and hover.
    """
    # log.debug("Takes the counts, which the caller must give")
    held = required(held=held)
    # log.debug("Takes the outcome's key, which the caller must give")
    key = required(key=key)
    # log.debug("Takes the run's place, which the caller must give")
    index = required(index=index)
    # log.debug("Takes the label, which the caller must give")
    label = required(label=label)
    # log.debug("Takes the colours, which the caller must give")
    colours = required(colours=colours)
    # log.debug("Reads the outcome's colour from the scheme")
    colour = getattr(colours, COLOUR_OF[key])
    # log.debug("Notes whether the outcome is hatched")
    hatched = key in HATCHED
    # log.debug("Counts each kind's questions, for the hover")
    totals = [int(v) for v in held.sum(axis=1)]
    # log.debug("Reads the outcome's counts, under its words, as plain numbers")
    column = [int(v) for v in held[OUTCOME_LABELS[key]]]
    # log.debug("Returns the segments, the key's entry from the first panel only")
    return go.Bar(
        x=column,
        y=list(held.index),
        name=OUTCOME_LABELS[key],
        orientation="h",
        width=0.62,
        legendgroup=key,
        showlegend=index == 0,
        marker=_marker(colour, hatched, colours),
        text=[str(v) for v in column],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color=colours.ink if hatched else colours.surface, size=FONT_SIZE),
        customdata=totals,
        hovertemplate=hover(
            f"<b>{OUTCOME_LABELS[key]}</b>  %{{x}} of %{{customdata}} %{{y}}", label
        ),
        meta=dict(role=key, run=f"run-{index}"),
    )


# log.debug("Defines how a segment is filled")
def _marker(
    colour: str | None = None, hatched: bool | None = None, colours: Theme | None = None
) -> dict[str, Any]:
    """Returns the fill: solid, or hatched in the colour on the surface.

    Args:
        colour: The outcome's colour. Required.
        hatched: Whether the outcome is drawn hatched. Required.
        colours: The scheme to draw in. Required.

    Returns:
        The marker settings.
    """
    # log.debug("Takes the colour, which the caller must give")
    colour = required(colour=colour)
    # log.debug("Takes whether to hatch, which the caller must give")
    hatched = required(hatched=hatched)
    # log.debug("Takes the colours, which the caller must give")
    colours = required(colours=colours)
    # log.debug("Returns a solid fill with a hairline of the surface between segments")
    if not hatched:
        # log.debug("Returns the solid fill")
        return dict(color=colour, line=dict(color=colours.surface, width=1))
    # log.debug("Returns the hatched fill: the colour's lines on the surface, edged in the colour")
    return dict(
        color=colours.surface,
        line=dict(color=colour, width=1),
        pattern=dict(shape=HATCH, fgcolor=colour, bgcolor=colours.surface, size=6, solidity=0.4),
    )


# log.debug("Defines where the panel titles sit")
def _place_titles(fig: go.Figure | None = None, colours: Theme | None = None) -> None:
    """Puts each panel's title over its left edge, in soft ink.

    Args:
        fig: The figure with its panels and their titles. Required.
        colours: The scheme to draw in. Required.
    """
    # log.debug("Takes the figure, which the caller must give")
    fig = required(fig=fig)
    # log.debug("Takes the colours, which the caller must give")
    colours = required(colours=colours)
    # log.debug("Walks the titles; only panel titles are notes so far")
    for i, note in enumerate(fig.layout.annotations, start=1):
        # log.debug("Finds the span of the panel's count axis")
        domain = fig.layout[f"xaxis{'' if i == 1 else i}"].domain
        # log.debug("Moves the title to the panel's left edge")
        note.update(font=dict(color=colours.ink2, size=FONT_SIZE), xanchor=LEFT, x=domain[0])
