########################################################################
#                                                                      #
#        backend/src/grounded_qa/dashboard/retrieval_charts.py         #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-03
Last modified on:  2026-11-03

Draws the retrieval chart: recall at k and mean reciprocal rank, a
grouped bar per run on each measure, so a keyword run and a hybrid run
sit side by side. Both come from a run's summary: the shares over its
answerable questions of the evidence found in the passages shown, and
of one over the rank of the first passage holding evidence. The runs'
key sits above all the charts on the page, so the chart carries none.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from collections.abc import Sequence
from typing import Final

# Third-party
import pandas as pd
import plotly.graph_objects as go
from kds.args import missing, required
from kds.logs import get_logger

# Local
from grounded_qa.config import SETTINGS
from grounded_qa.dashboard.theme import THEMES, Theme, hover, shared_layout, top_down
from grounded_qa.dashboard.views import long_labels, present
from grounded_qa.evals.shares import fixed

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the run id column, from the config")
RUN_ID: Final = SETTINGS.columns_run_id
# log.debug("Takes the light scheme's name, from the config")
LIGHT: Final = SETTINGS.charts_light_scheme
# log.debug("Takes the size of chart text, from the config")
FONT_SIZE: Final = SETTINGS.charts_font_size

########################################################################
#                                                                      #
#                           Local constants                            #
#                                                                      #
########################################################################
# Each measure: its column in the runs table, its name on the axis,
# and what it means, for the hover.
# log.debug("Lists the measures drawn, top row first")
MEASURES: Final = (
    ("recall_at_k", "Recall at k", "the share of evidence groups in the passages shown"),
    ("mrr", "MRR", "one over the rank of the first passage holding evidence"),
)
# log.debug("Sets the chart's height above its rows")
BASE: Final = 56
# log.debug("Sets the height one run's bar adds to each measure's row")
BAR_ROOM: Final = 26
# log.debug("Sets the decimals a measure is written with on its bar")
PLACES: Final = 2
# log.debug("Sets the end of the score axis, leaving room for the bars' values")
AXIS_END: Final = 1.14
# log.debug("Sets the ticks of the score axis")
QUARTERS: Final = (0, 0.25, 0.5, 0.75, 1)


########################################################################
#                                                                      #
#                           Retrieval chart                            #
#                                                                      #
########################################################################
# log.debug("Defines the retrieval chart")
def fig_retrieval(
    runs_df: pd.DataFrame | None = None,
    run_ids: str | Sequence[str] | None = None,
    theme: str = LIGHT,
    labels: dict[str, str] | None = None,
) -> go.Figure:
    """Returns recall at k and MRR, a bar per run on each measure.

    Each bar carries its value at its end.

    Args:
        runs_df: The runs table from `frames`. Required.
        run_ids: Up to three runs, the run in focus first. Required.
        theme: The colour scheme, light or dark.
        labels: Each run's name; long labels when None.

    Returns:
        The chart.
    """
    # log.debug("Takes the runs table, which the caller must give")
    runs_df = required(runs_df=runs_df)
    # log.debug("Stops when the caller left out the run ids")
    if run_ids is None:
        # log.debug("Raises the missing-argument error")
        raise missing(run_ids=run_ids)
    # log.debug("Takes the scheme's colours")
    colours = THEMES[theme]
    # log.debug("Keeps the runs the table holds, at most three")
    ids = present(runs_df, run_ids)
    # log.debug("Names each run, from the labels given or the table")
    names = labels or long_labels(runs_df, ids)
    # log.debug("Starts an empty figure")
    fig = go.Figure()
    # log.debug("Adds each run's bars, the run in focus first so it sits on top of each group")
    for index, run_id in enumerate(ids):
        # log.debug("Reads the run's row")
        row = runs_df[runs_df[RUN_ID] == run_id].iloc[0]
        # log.debug("Adds the run's bar on each measure")
        fig.add_trace(_bars(row, index=index, label=names[run_id], colours=colours))
    # log.debug("Groups the bars by measure, lists the measures from the top down, fits the axis")
    fig.update_layout(
        barmode="group",
        bargap=0.42,
        bargroupgap=0.12,
        yaxis=top_down([name for _, name, _ in MEASURES]),
        xaxis=dict(range=[0, AXIS_END], tickvals=list(QUARTERS), tickformat=".2f"),
    )
    # log.debug("Returns the chart in the shared layout, a group of bars per measure")
    return shared_layout(fig, BASE + BAR_ROOM * len(MEASURES) * max(1, len(ids)), colours)


# log.debug("Defines one run's bars")
def _bars(
    row: pd.Series[float] | None = None,
    *,
    index: int | None = None,
    label: str | None = None,
    colours: Theme | None = None,
) -> go.Bar:
    """Returns a run's bar on each measure, its value at the end.

    Args:
        row: The run's row in the runs table. Required.
        index: The run's place among those picked; 0 is in focus.
            Required.
        label: The run's name. Required.
        colours: The scheme to draw in. Required.

    Returns:
        The bars, with their values and hover.
    """
    # log.debug("Takes the row, which the caller must give")
    row = required(row=row)
    # log.debug("Takes the run's place, which the caller must give")
    index = required(index=index)
    # log.debug("Takes the label, which the caller must give")
    label = required(label=label)
    # log.debug("Takes the colours, which the caller must give")
    colours = required(colours=colours)
    # log.debug("Reads each measure's value, a missing one as zero")
    values = [float(row[column]) if pd.notna(row[column]) else 0.0 for column, _, _ in MEASURES]
    # log.debug("Returns the bars")
    return go.Bar(
        x=values,
        y=[name for _, name, _ in MEASURES],
        name=label,
        orientation="h",
        marker=dict(color=colours.runs[index], line=dict(width=0), cornerradius=4),
        text=[fixed(v, PLACES) for v in values],
        textposition="outside",
        textfont=dict(color=colours.ink2, size=FONT_SIZE),
        cliponaxis=False,
        customdata=[meaning for _, _, meaning in MEASURES],
        hovertemplate=hover("<b>%{x:.3f}</b>  %{y}: %{customdata}", label),
        meta=dict(role=f"run-{index}"),
    )
