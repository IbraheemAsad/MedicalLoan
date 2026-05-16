"""Reusable RTL-aware search frame.

Phase 3 of the improvement plan extracted this widget out of the four
near-identical ~50-line blocks the original ``main.py`` had at the top
of ``show_inventory``, ``show_new_loan``, ``show_process_return`` and
``show_borrowers``. Each of those views needs the same layout:

* a ``Search:`` label,
* a stretching entry box,
* a hint label below the entry box,
* a ``Show All`` button that appears only while the user has typed
  something, and
* (inventory only) an extra primary "Add New ..." action button on
  the trailing edge.

The visual order flips depending on whether the current language is
RTL or LTR. Callers supply a single ``on_search`` function that takes
the current search term; the widget itself owns showing/hiding the
"Show All" button based on whether the term is empty.
"""

from __future__ import annotations

from collections.abc import Callable
from tkinter import ttk
from typing import Any

# Type alias for the search callback. ``term`` is whatever the user has
# typed (already stripped of leading/trailing whitespace? no -- raw, to
# keep parity with the legacy code that passed ``search_var.get()``).
SearchCallback = Callable[[str], Any]


class SearchFrame(ttk.Frame):
    """A row containing ``[Search:] [entry] [Show All]? [Add New]?``.

    Parameters
    ----------
    parent:
        Parent widget. The frame packs itself into ``parent`` via
        ``pack(fill='x', ...)`` -- callers don't need to call ``pack``
        themselves.
    is_rtl:
        Mirror the layout for right-to-left languages.
    label_text:
        Text for the leading ``Search:`` label.
    hint_text:
        Smaller hint shown below the entry, e.g. "Search by name or
        serial...". Pass an empty string to hide it.
    show_all_text:
        Label for the "Show All" button.
    search_var:
        Persistent ``tk.StringVar`` shared with the App so the term
        survives language/font reloads.
    input_font:
        The live ``tkfont.Font`` used by all entries (so font-size
        controls take effect).
    on_search:
        Called on every ``<KeyRelease>`` *and* once at construction
        time if ``search_var`` is non-empty. Receives the current
        search term as its only argument.
    on_show_all:
        Called when the user clicks "Show All". Use this to reset the
        treeview to its full unfiltered state. ``search_var`` is
        cleared *before* this is invoked.
    add_button:
        Optional ``(label, command)`` tuple. When provided, an
        ``Action.TButton`` styled "Add New ..." button is laid out on
        the trailing edge (just like the inventory screen).
    pady:
        Vertical padding to give the frame inside its parent.
    padx:
        Horizontal padding (default 20 to match the legacy layout).
    """

    def __init__(
        self,
        parent: ttk.Widget,
        *,
        is_rtl: bool,
        label_text: str,
        hint_text: str,
        show_all_text: str,
        search_var,
        input_font,
        on_search: SearchCallback,
        on_show_all: Callable[[], Any],
        add_button: tuple[str, Callable[[], Any]] | None = None,
        pady: int = 10,
        padx: int = 20,
    ) -> None:
        super().__init__(parent)
        self.pack(pady=pady, fill='x', padx=padx)

        self._search_var = search_var
        self._on_search = on_search
        self._on_show_all = on_show_all

        anchor_w = 'e' if is_rtl else 'w'
        style_entry = 'Right.TEntry' if is_rtl else 'TEntry'
        hint_style = 'Right.Small.TLabel' if is_rtl else 'Small.TLabel'

        # ---- Compute grid columns for the chosen layout ----
        # Two layouts are supported, mirrored for RTL:
        #
        #   without Add New: [Label] [Entry] [Show All] [Spacer]
        #   with    Add New: [Label] [Entry] [Show All] [Add New] [Spacer]
        if add_button is None:
            if is_rtl:
                # Spacer(0) | Show(1) | Entry(2) | Label(3)
                col_spacer, col_btn_show, col_entry, col_lbl = 0, 1, 2, 3
                col_btn_add = None
            else:
                # Label(0) | Entry(1) | Show(2) | Spacer(3)
                col_lbl, col_entry, col_btn_show, col_spacer = 0, 1, 2, 3
                col_btn_add = None
        else:
            if is_rtl:
                # Spacer(0) | Add(1) | Show(2) | Entry(3) | Label(4)
                col_spacer = 0
                col_btn_add = 1
                col_btn_show = 2
                col_entry = 3
                col_lbl = 4
            else:
                # Label(0) | Entry(1) | Show(2) | Add(3) | Spacer(4)
                col_lbl = 0
                col_entry = 1
                col_btn_show = 2
                col_btn_add = 3
                col_spacer = 4

        # The spacer column eats remaining horizontal space.
        self.grid_columnconfigure(col_spacer, weight=1)

        # ---- 1. Search label ----
        ttk.Label(self, text=label_text).grid(
            row=0, column=col_lbl, padx=5, sticky=anchor_w,
        )

        # ---- 2. Entry box ----
        self.entry = ttk.Entry(
            self,
            textvariable=search_var,
            width=20,
            style=style_entry,
            font=input_font,
        )
        self.entry.grid(row=0, column=col_entry, padx=5, sticky=anchor_w)

        # ---- 3. Hint label (below entry) ----
        if hint_text:
            ttk.Label(self, text=hint_text, style=hint_style).grid(
                row=1, column=col_entry, padx=5, sticky=anchor_w,
            )

        # ---- 4. Optional Add New button ----
        if add_button is not None and col_btn_add is not None:
            add_label, add_cmd = add_button
            ttk.Button(
                self,
                text=add_label,
                command=add_cmd,
                style='Action.TButton',
            ).grid(row=0, column=col_btn_add, rowspan=2, padx=5)

        # ---- 5. Show All button (initially hidden) ----
        self._col_btn_show = col_btn_show
        self._show_all_btn = ttk.Button(
            self,
            text=show_all_text,
            command=self._handle_show_all,
        )

        self.entry.bind("<KeyRelease>", self._on_key_release)

        # If the persistent search_var already had content (e.g. user
        # navigated away and back), apply the filter and reveal the
        # Show All button right away.
        if search_var.get():
            self._refresh_show_all()
            self._on_search(search_var.get())

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _on_key_release(self, _event=None) -> None:
        term = self._search_var.get()
        self._on_search(term)
        self._refresh_show_all()

    def _refresh_show_all(self) -> None:
        if self._search_var.get():
            self._show_all_btn.grid(row=0, column=self._col_btn_show, rowspan=2, padx=5)
        else:
            self._show_all_btn.grid_forget()

    def _handle_show_all(self) -> None:
        self._search_var.set('')
        self._on_show_all()
        self._refresh_show_all()
