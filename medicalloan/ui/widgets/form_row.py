"""``FormRow`` -- a label + entry pair for ttk grid layouts.

Phase 3 of the improvement plan extracted this helper out of the
duplicated 3-line ``ttk.Label(...).grid()`` / ``ttk.Entry(...).grid()``
pattern that appeared in:

* ``show_add_equipment`` (4 rows)
* ``edit_equipment`` (4 rows)
* ``add_borrower_action`` (5 rows, plus validators)
* ``show_borrower_step`` (5 borrower rows + 2 financial rows)

The helper isn't a ``Frame`` subclass on purpose -- callers already own
a ``form_frame``/``fields_frame`` and want each row to occupy a
specific row index inside that grid (so labels line up vertically and
the column-config-stretch on the entry column works). Returning the
created ``ttk.Entry`` lets the caller wire up state-toggle logic
(see the borrower-search "edit details" mode that disables/re-enables
the same widgets).
"""

from __future__ import annotations

from collections.abc import Callable
from tkinter import ttk


def form_row(
    parent: ttk.Widget,
    row: int,
    *,
    label_text: str,
    var,
    is_rtl: bool,
    input_font,
    validator: tuple[str, ...] | None = None,
    width: int = 40,
    pady: int = 5,
) -> ttk.Entry:
    """Place a labelled entry on row ``row`` of ``parent``'s grid.

    The label and entry are placed in two adjacent columns whose
    indices flip for RTL layouts. The function returns the created
    ``ttk.Entry`` so the caller can keep a reference (e.g. to
    enable/disable it later).

    Parameters
    ----------
    parent:
        Parent widget (typically a ``ttk.Frame`` already configured
        with ``columnconfigure(entry_col, weight=1)`` so entries
        stretch).
    row:
        Grid row index for both the label and the entry.
    label_text:
        Already-translated text for the label.
    var:
        ``tk.StringVar`` (or any ``Variable``) backing the entry.
    is_rtl:
        Mirror the layout for right-to-left languages.
    input_font:
        Live ``tkfont.Font`` used by all entries (so the global
        font-size +/- controls take effect).
    validator:
        Optional ``(register_name, '%P')`` tuple as returned by
        ``app.root.register(callable)``. When provided, the entry is
        configured with ``validate='key'``.
    width:
        Entry width in characters (legacy code used 40 for dialogs and
        25/35 for compact forms -- caller picks).
    pady:
        Vertical padding around the row.
    """
    anchor_w = 'e' if is_rtl else 'w'
    style_label = 'Right.TLabel' if is_rtl else 'TLabel'
    justify_text = 'right' if is_rtl else 'left'
    col_label = 1 if is_rtl else 0
    col_entry = 0 if is_rtl else 1

    ttk.Label(parent, text=label_text, style=style_label).grid(
        row=row, column=col_label, sticky=anchor_w, pady=pady,
    )

    entry = ttk.Entry(
        parent,
        textvariable=var,
        width=width,
        justify=justify_text,
        font=input_font,
    )
    if validator is not None:
        entry.config(validate='key', validatecommand=validator)

    entry.grid(row=row, column=col_entry, pady=pady, sticky='ew')
    return entry


# ``add_row`` is the spelling the legacy show_borrower_step closure
# used. Re-export under the same name so views can move with a 1-line
# rename rather than a 1-line rename + parameter swap.
add_row: Callable[..., ttk.Entry] = form_row


__all__ = ["form_row", "add_row"]
