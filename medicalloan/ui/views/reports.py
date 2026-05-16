"""Reports screen + the two PDF generation handlers it triggers."""

from __future__ import annotations

from tkinter import ttk

from medicalloan.ui import dialogs as ui_dialogs


def show(app) -> None:
    """Render the reports menu (two large buttons)."""
    app.clear_window()
    app.show_global_controls(app.main_frame, lambda: show(app))

    is_rtl = app.is_rtl
    side_left = 'right' if is_rtl else 'left'
    side_right = 'left' if is_rtl else 'right'
    style_subtitle = 'Right.Subtitle.TLabel' if is_rtl else 'Subtitle.TLabel'

    # --- Header -----------------------------------------------------------
    header = ttk.Frame(app.main_frame)
    header.pack(pady=10, fill='x', padx=20)

    ttk.Label(
        header,
        text=app.i18n[app.lang]['reports_title'],
        style=style_subtitle).pack(side=side_left)
    ttk.Button(
        header,
        text=app.i18n[app.lang]['back_to_dashboard'],
        command=app.show_dashboard).pack(side=side_right)

    # --- Body -------------------------------------------------------------
    report_frame = ttk.Frame(app.main_frame)
    report_frame.pack(pady=50)

    ttk.Label(
        report_frame,
        text=app.i18n[app.lang]['reports_select'],
        font=('Helvetica', 14)).grid(row=0, column=0, columnspan=2, pady=20)

    col_1 = 1 if is_rtl else 0
    col_2 = 0 if is_rtl else 1

    ttk.Button(
        report_frame,
        text=app.i18n[app.lang]['btn_inventory_report'],
        command=lambda: generate_inventory_report(app),
        style='Large.TButton',
        width=30).grid(row=1, column=col_1, padx=20, pady=15)

    ttk.Button(
        report_frame,
        text=app.i18n[app.lang]['btn_loans_report'],
        command=lambda: generate_loans_report(app),
        style='Large.TButton',
        width=30).grid(row=1, column=col_2, padx=20, pady=15)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_inventory_report(app) -> None:
    """Render the full-inventory PDF and open it."""
    try:
        summary = app.db.get_equipment_summary()
        lost_items = app.db.get_lost_equipment()
        pdf_path = app.reports.generate_inventory_report(summary, lost_items, app.lang)
        app.reports.open_pdf(pdf_path)
        ui_dialogs.info(app, app.i18n[app.lang]['success_report'].format(path=pdf_path))
    except Exception as e:
        ui_dialogs.error(app, app.i18n[app.lang]['err_report_fail'].format(e=str(e)))


def generate_loans_report(app) -> None:
    """Render the active-loans PDF and open it."""
    try:
        active_loans = app.db.get_active_loans()
        pdf_path = app.reports.generate_loans_report(active_loans, app.lang)
        app.reports.open_pdf(pdf_path)
        ui_dialogs.info(app, app.i18n[app.lang]['success_report'].format(path=pdf_path))
    except Exception as e:
        ui_dialogs.error(app, app.i18n[app.lang]['err_report_fail'].format(e=str(e)))
