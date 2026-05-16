"""Dashboard screen + the Excel data-management popup.

Tiny screen: the language/font/theme bar at the top, a title and
subtitle, a 3x2 grid of large buttons, plus a side popup launched by
the last button.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from medicalloan.ui.dialogs import setup_dialog_window


def show(app) -> None:
    """Render the dashboard into ``app.main_frame``."""
    app.clear_window()
    app.show_global_controls(app.main_frame, lambda: show(app))

    is_rtl = app.is_rtl
    title = ttk.Label(
        app.main_frame,
        text=app.i18n[app.lang]['dashboard_title'],
        style='Title.TLabel',
    )
    title.pack(pady=20)

    subtitle = ttk.Label(
        app.main_frame,
        text=app.i18n[app.lang]['dashboard_subtitle'],
        style='Subtitle.TLabel',
    )
    subtitle.pack(pady=10)

    button_frame = ttk.Frame(app.main_frame)
    button_frame.pack(pady=30)

    # NOTE: "Excel Export / Import" is intentionally hardcoded here; the
    # legacy main.py never added an i18n key for it. Leaving it as-is
    # keeps Phase 3 behaviour-identical; a follow-up can localise it.
    buttons = [
        (app.i18n[app.lang]['btn_new_loan'],
         lambda: _navigate(app, 'new_loan'),
         app.icon_new_loan),
        (app.i18n[app.lang]['btn_process_return'],
         lambda: _navigate(app, 'process_return'),
         app.icon_process_return),
        (app.i18n[app.lang]['btn_search_inventory'],
         lambda: _navigate(app, 'inventory'),
         app.icon_search_inventory),
        (app.i18n[app.lang]['btn_manage_borrowers'],
         lambda: _navigate(app, 'borrowers'),
         app.icon_manage_borrowers),
        (app.i18n[app.lang]['btn_generate_reports'],
         lambda: _navigate(app, 'reports'),
         app.icon_generate_reports),
        ("Excel Export / Import",
         lambda: show_data_menu(app),
         app.icon_generate_reports),
    ]

    for i, (text, command, icon) in enumerate(buttons):
        row = i // 2
        col = i % 2
        grid_col = 1 - col if is_rtl else col
        btn = ttk.Button(
            button_frame,
            text=text,
            command=command,
            style='Large.TButton',
            width=25,
            image=icon,
            compound=tk.TOP,
        )
        btn.grid(row=row, column=grid_col, padx=20, pady=15)


def show_data_menu(app) -> None:
    """Modal popup with Export / Import / Close buttons."""
    dialog = tk.Toplevel(app.root)
    dialog.title("Data Management")
    setup_dialog_window(dialog, app.root, min_width=300)

    ttk.Label(
        dialog,
        text="Excel Data Management",
        font=('Helvetica', 12, 'bold'),
    ).pack(pady=15)

    ttk.Button(
        dialog,
        text="📤 Export Database to Excel",
        command=lambda: [dialog.destroy(), app.export_to_excel()],
        style='Action.TButton',
        width=25,
    ).pack(pady=10)

    ttk.Button(
        dialog,
        text="📥 Import Database from Excel",
        command=lambda: [dialog.destroy(), app.import_from_excel()],
        style='TButton',
        width=25,
    ).pack(pady=10)

    ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)


def _navigate(app, target: str) -> None:
    """Dispatch to another top-level view via ``app.show_<name>()``."""
    getattr(app, f'show_{target}')()
