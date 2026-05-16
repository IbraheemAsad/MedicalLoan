"""Dialog helpers shared across views.

Phase 3 introduced :func:`setup_dialog_window`. Phase 5 layered two
small additions on top:

* ``error`` / ``info`` / ``warn`` / ``askyesno`` wrappers that pull
  the dialog *title* from the active i18n table (keys
  ``error_title``, ``success_title``, ``warning_title``,
  ``confirm_title``) so the title bar is no longer "Error" in
  Hebrew/Arabic UIs.
* ``bind_dialog_keys`` -- a one-liner that binds ``<Escape>`` to
  close and (optionally) ``<Return>`` to a confirm action so form
  dialogs feel keyboard-native.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Callable


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


# ---------------------------------------------------------------------------
# Localised messagebox wrappers (Phase 5)
# ---------------------------------------------------------------------------

def _title_for(app, key: str, fallback: str) -> str:
    """Look up a translated title with a sensible fallback.

    The legacy code passed literal English strings as the title arg
    to messagebox calls. Phase 5 adds matching keys to the i18n
    tables (``error_title`` etc.); this helper degrades gracefully if
    a key happens to be missing in some language (returns the English
    fallback rather than raising).
    """
    try:
        return app.i18n[app.lang].get(key, fallback)
    except (AttributeError, KeyError):
        return fallback


def error(app, message: str, *, title_key: str = "error_title") -> None:
    """Localised wrapper for ``messagebox.showerror``."""
    messagebox.showerror(_title_for(app, title_key, "Error"), message)


def info(app, message: str, *, title_key: str = "success_title") -> None:
    """Localised wrapper for ``messagebox.showinfo``."""
    messagebox.showinfo(_title_for(app, title_key, "Success"), message)


def warn(app, message: str, *, title_key: str = "warning_title") -> None:
    """Localised wrapper for ``messagebox.showwarning``."""
    messagebox.showwarning(_title_for(app, title_key, "Warning"), message)


def askyesno(app, message: str, *, title_key: str = "confirm_title") -> bool:
    """Localised wrapper for ``messagebox.askyesno``."""
    return bool(
        messagebox.askyesno(_title_for(app, title_key, "Confirm"), message),
    )


# ---------------------------------------------------------------------------
# Keyboard ergonomics (Phase 5)
# ---------------------------------------------------------------------------

def bind_dialog_keys(
    dialog: tk.Toplevel,
    *,
    on_confirm: Callable[[], None] | None = None,
) -> None:
    """Wire ``Esc`` to close the dialog and optionally ``Enter`` to confirm.

    Skipping ``on_confirm`` (the default) is appropriate for popups
    that are pure information displays (history viewer, summary
    table); they only get the Escape binding so the user can dismiss
    them without reaching for the mouse.
    """
    dialog.bind("<Escape>", lambda _e: dialog.destroy())
    if on_confirm is not None:
        # ``Return`` only fires when the dialog itself has focus, so
        # we add KP_Enter (numeric keypad) too -- some keyboards
        # report it separately.
        dialog.bind("<Return>", lambda _e: on_confirm())
        dialog.bind("<KP_Enter>", lambda _e: on_confirm())
