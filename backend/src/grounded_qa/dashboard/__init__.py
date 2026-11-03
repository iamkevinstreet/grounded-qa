########################################################################
#                                                                      #
#            backend/src/grounded_qa/dashboard/__init__.py             #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-03
Last modified on:  2026-11-03

The evaluation dashboard: compare runs and see which questions went
wrong.

Run it with `python -m grounded_qa.dashboard`. The modules: data (run
files to tables, which the Tableau export shares), views (what the
dashboard shows from those tables), theme, the charts (outcome_charts,
retrieval_charts, run_charts), tiles, layout, page, app, and export
(the figures the case study draws). Nothing is imported here, so
reading the tables does not load Dash.
"""
