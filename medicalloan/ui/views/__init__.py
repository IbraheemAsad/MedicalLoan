"""One module per screen.

Each module exposes a top-level ``show(app)`` function (sometimes also
helper ``load_*``/``search_*`` functions called from within the screen)
that the orchestrator in :mod:`medicalloan.app` invokes when the user
navigates to that view.
"""
