"""Dialog helpers shared across views.

Currently this module exposes a single function -- ``setup_dialog_window`` --
extracted from ``MedicalEquipmentApp.setup_dialog_window``. Future polish
work (Phase 5) will likely add ``confirm()`` and ``ask_yes_no()`` wrappers
that thread translated titles automatically; for now we keep parity with
the legacy behaviour so views can move with a single rename.
"""

from __future__ import annotations

import tkinter as tk


def setup_dialog_window(
    dialog: tk.Toplevel,
    root: tk.Misc,
    *,
    min_width: int = 400,
) -> None:
    """Make ``dialog`` modal and centre it on ``root``'s monitor.

    Mirrors the behaviour of the original
    ``MedicalEquipmentApp.setup_dialog_window`` after the B11 fix:

    1. Make the dialog modal (``transient`` + ``grab_set``) so the
       main window can't be interacted with while it's open.
    2. Auto-size to fit its widgets via ``update_idletasks`` +
       ``winfo_reqwidth/reqheight``, with a configurable minimum
       width.
    3. Centre relative to ``root`` (not the primary monitor) so
       multi-monitor setups place the dialog where the user is
       actually looking.
    """
    # 1. Make modal.
    dialog.transient(root)
    dialog.grab_set()

    # 2. Force a layout pass so reqwidth/reqheight are populated.
    dialog.update_idletasks()
    width = dialog.winfo_reqwidth()
    height = dialog.winfo_reqheight()
    if width < min_width:
        width = min_width

    # 3. Centre on root's current monitor (B11).
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_w = root.winfo_width()
    root_h = root.winfo_height()
    x = root_x + (root_w // 2) - (width // 2)
    y = root_y + (root_h // 2) - (height // 2)

    dialog.geometry(f'{width}x{height}+{x}+{y}')
