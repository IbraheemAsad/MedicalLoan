"""``ttk.Treeview`` helpers + status-tag plumbing.

This module is a home for small, stateless functions that operate on a
Treeview after it has already been built. Three groups of helpers live
here:

* ``auto_size_treeview_columns`` -- measures the live ``Treeview`` font
  via ``ttk.Style`` (B12) and resizes every column to fit its widest
  cell, with text-vs-numeric anchor inferred from the *logical* column
  id (so RTL still right-aligns text columns and centres numeric
  ones).
* ``configure_status_tags`` / ``status_tag_for`` -- canonical mapping
  from DB status keys (``In-Stock``, ``On-Loan``, ...) to ttk tag
  names + their pastel background colours. Black foreground is forced
  for readability against the pastel backgrounds in dark mode.
* ``equipment_display_status`` / ``translated_status`` -- two small
  pure helpers Phase 2 added when ``is_retired`` was split out from
  ``status``. Kept here so view modules don't need to import the App.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from typing import Any

# --- Status-tag plumbing ---------------------------------------------------

_STATUS_BG: dict[str, str] = {
    'In-Stock': '#d9ead3',     # Light Green
    'On-Loan': '#fce5cd',      # Light Orange
    'Returned': '#d0e0e3',     # Light Blue
    'Not Returned': '#ea9999', # Light Red
    'Lost': '#efefef',         # Light Grey
    'Active': '#fce5cd',       # Light Orange (alias of On-Loan)
}

# Database status -> Tk tag name. The two distinct names that map to
# the same tag ("On-Loan" and "Active") are intentional -- callers may
# see either form depending on which view they came from.
_STATUS_TAG: dict[str, str] = {
    'In-Stock': 'InStock',
    'On-Loan': 'OnLoan',
    'Returned': 'Returned',
    'Not Returned': 'NotReturned',
    'Lost': 'Lost',
    'Active': 'OnLoan',
}


def configure_status_tags(tree: ttk.Treeview) -> None:
    """Register the pastel background tags on ``tree``.

    Foreground is forced to black so text stays readable against the
    pastel backgrounds even in dark mode. Call once per Treeview
    after construction; the tags are scoped to that widget.
    """
    for status_key, tag_name in _STATUS_TAG.items():
        bg = _STATUS_BG.get(status_key)
        if bg:
            tree.tag_configure(tag_name, background=bg, foreground='#000000')


def status_tag_for(status_key: str) -> str:
    """Return the Tk tag name for a DB status key, or ``""`` if unknown."""
    if not status_key:
        return ""
    return _STATUS_TAG.get(status_key, "")


def equipment_display_status(eq: dict) -> str:
    """Return the status string a UI should display for an equipment row.

    Phase 2 introduced ``equipment.is_retired`` as a separate flag, so
    the canonical ``equipment.status`` column only ever holds
    ``In-Stock`` or ``On-Loan``. Most of the UI still wants to surface
    "Lost" for retired items -- we synthesise it here so the
    inventory tree, search, and styling keep working without each
    call site having to know about the flag.
    """
    if eq.get('is_retired'):
        return 'Lost'
    return eq.get('status') or ''


def translated_status(status_key: str, i18n: dict[str, dict[str, Any]], lang: str) -> str:
    """Translate a DB status key into ``lang``, falling back to English."""
    if not status_key:
        return ""
    status_map = i18n.get(lang, {}).get(
        'status_values',
        i18n.get('en', {}).get('status_values', {}),
    )
    return status_map.get(status_key, status_key)


# --- Treeview column auto-sizing ------------------------------------------

# Logical column ids that should be center-aligned (numeric-ish).
_NUMERIC_COL_IDS: frozenset[str] = frozenset({
    'ID', 'LoanID', 'IDNum', 'Phone', 'Phone1', 'Phone2',
    'Total', 'InStock', 'OnLoan', 'Deposit', 'NotReturned', 'Lost', 'Num',
})


def auto_size_treeview_columns(
    tree: ttk.Treeview,
    *,
    is_rtl: bool,
    fallback_size: int,
) -> None:
    """Resize every column of ``tree`` to fit its widest cell.

    The treeview font is read off the live ``ttk.Style`` (B12 fix --
    ``tree.cget('font')`` returns the *style name*, not a font spec,
    which is why the legacy code's bare ``except:`` fallback ran on
    every call). When the style lookup fails (e.g. before the style
    has been configured) we fall back to ``Helvetica`` at
    ``fallback_size`` so column widths still come out roughly right.

    Numeric-looking columns are centred; everything else uses
    ``tk.E`` for RTL, ``tk.W`` for LTR. The synthetic ``Spacer``
    column we use to push content against the language edge is
    skipped entirely.
    """
    try:
        style = ttk.Style()
        font_spec = style.lookup('Treeview', 'font')
        if not font_spec:
            raise KeyError('Treeview font not in style')
        font = tkfont.Font(font=font_spec)
    except (KeyError, tk.TclError):
        font = tkfont.Font(family="Helvetica", size=fallback_size)

    text_anchor = tk.E if is_rtl else tk.W

    for col in tree["columns"]:
        if col == 'Spacer':
            continue

        col_anchor = tk.CENTER if col in _NUMERIC_COL_IDS else text_anchor

        heading_text = tree.heading(col, 'text')
        max_width = font.measure(heading_text) + 10  # heading + padding

        for iid in tree.get_children():
            cell_value = tree.set(iid, col)
            if cell_value:
                cell_width = font.measure(cell_value)
                if cell_width > max_width:
                    max_width = cell_width

        # Clamp to a sensible band so single-character headings don't
        # collapse to ~5px and very long descriptions don't push the
        # tree wider than the window.
        final_width = max(70, min(max_width + 20, 400))
        tree.column(col, width=final_width, stretch=False, anchor=col_anchor)
