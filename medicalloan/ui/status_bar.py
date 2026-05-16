"""Status bar shown along the bottom of every screen (Phase 5).

The status bar is a single thin strip that surfaces three pieces of
information the operator otherwise has to dig for:

* Current language code (en / he / ar). Useful when a screenshot
  ends up in a bug report.
* DB path. Helps when an operator opens the app twice and isn't
  sure which database they're looking at.
* Unread error count -- byte offset of ``app_errors.log`` is stored
  in ``config.ini`` (``[Preferences].errors_seen_offset``), and we
  show the size in bytes that's accumulated since then. Clicking
  the count "marks read" by recording the current size as the new
  offset.
"""

from __future__ import annotations

import configparser
import os
import tkinter as tk
from tkinter import ttk

# Same section name as ``preferences.SECTION``; we only care about the
# one offset key here so duplicating the literal keeps this module
# free of circular imports back into ``preferences``.
PREF_SECTION = "Preferences"
OFFSET_KEY = "errors_seen_offset"


def unread_error_bytes(log_path: str, seen_offset: int) -> int:
    """Return the number of bytes appended since ``seen_offset``.

    Returns 0 if the log doesn't exist or if it's been rotated
    (current size < ``seen_offset``). In the rotation case we treat
    everything as read because the operator wouldn't have a sensible
    way to view the old log anyway.

    .. note::
       Defined at module top-level so tests can import it without
       pulling in Tkinter (the rest of this module imports
       ``tkinter`` for the actual rendering).
    """
    try:
        size = os.path.getsize(log_path)
    except OSError:
        return 0
    delta = size - max(0, seen_offset)
    return delta if delta > 0 else 0


def _read_offset(config: configparser.ConfigParser) -> int:
    if not config.has_section(PREF_SECTION):
        return 0
    raw = config[PREF_SECTION].get(OFFSET_KEY, "0")
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 0


def _write_offset(
    config: configparser.ConfigParser,
    config_path: str,
    new_offset: int,
) -> None:
    if not config.has_section(PREF_SECTION):
        config.add_section(PREF_SECTION)
    config[PREF_SECTION][OFFSET_KEY] = str(max(0, int(new_offset)))
    try:
        with open(config_path, "w", encoding="utf-8") as fh:
            config.write(fh)
    except OSError:
        # Best-effort -- if we can't persist the offset the next
        # launch will just show the same byte count again.
        pass


def show(app, parent: tk.Misc) -> ttk.Frame:
    """Render the status bar into ``parent`` and return the frame.

    Reads ``app.config`` for the persisted seen-offset and
    ``app.error_log_path`` for the location of ``app_errors.log``.
    Re-reads the byte count on every call (i.e. every screen change)
    rather than polling, which is good enough for the kind of
    long-lived shell session the app runs in.
    """
    bar = ttk.Frame(parent)
    bar.pack(side="bottom", fill="x", padx=4, pady=2)

    log_path = getattr(app, "error_log_path", "")
    seen_offset = _read_offset(app.config)
    unread = unread_error_bytes(log_path, seen_offset) if log_path else 0

    lang_label = app.i18n[app.lang].get("status_lang", "Lang")
    db_label = app.i18n[app.lang].get("status_db", "DB")
    errors_label = app.i18n[app.lang].get("status_unread_errors", "Errors")

    # Compact layout: ``Lang: en  |  DB: /path/medical_equipment.db``
    # on the leading side; the unread-errors button on the trailing
    # side so it's always in the same screen corner regardless of
    # text direction.
    leading_side = "right" if app.is_rtl else "left"
    trailing_side = "left" if app.is_rtl else "right"

    info_text = (
        f"{lang_label}: {app.lang}  |  "
        f"{db_label}: {os.path.basename(app.db.db_path)}"
    )
    ttk.Label(bar, text=info_text, style="Small.TLabel").pack(
        side=leading_side, padx=8,
    )

    if unread > 0:
        # Render the byte count rather than a fake "message count"
        # because the log isn't structured per-error.
        text = f"{errors_label}: {unread} B  ✕"

        def mark_read() -> None:
            try:
                size = os.path.getsize(log_path)
            except OSError:
                size = 0
            config_path = getattr(app, "config_path", None)
            if config_path:
                _write_offset(app.config, config_path, size)
            # Visually clear: just remove the button. Full status bar
            # repaints on the next view change.
            btn.destroy()

        btn = ttk.Button(
            bar, text=text, style="Font.TButton", command=mark_read,
        )
        btn.pack(side=trailing_side, padx=8)

    return bar
