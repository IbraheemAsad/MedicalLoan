"""Process Return (Check-In) screen.

Lists active loans, lets the user either accept the equipment back
(``process_return``) or mark the loan as non-returned and forfeit the
deposit (``forfeit_deposit``).
"""

from __future__ import annotations

from datetime import datetime
from tkinter import messagebox, ttk

from medicalloan.ui import dialogs as ui_dialogs

from medicalloan.ui.treeview import auto_size_treeview_columns
from medicalloan.ui.widgets import SearchFrame


def show(app) -> None:
    """Render the process-return screen."""
    app.clear_window()
    app.show_global_controls(app.main_frame, lambda: show(app))

    is_rtl = app.is_rtl
    side_left = 'right' if is_rtl else 'left'
    side_right = 'left' if is_rtl else 'right'
    style_subtitle = 'Right.Subtitle.TLabel' if is_rtl else 'Subtitle.TLabel'
    col_tree = 1 if is_rtl else 0
    col_scroll = 0 if is_rtl else 1

    # --- Header -----------------------------------------------------------
    header = ttk.Frame(app.main_frame)
    header.pack(pady=10, fill='x', padx=20)

    ttk.Label(
        header,
        text=app.i18n[app.lang]['return_title'],
        style=style_subtitle).pack(side=side_left)
    ttk.Button(
        header,
        text=app.i18n[app.lang]['back_to_dashboard'],
        command=app.show_dashboard).pack(side=side_right)

    # --- Treeview (built first so the SearchFrame closure can reference it)
    tree_frame = ttk.Frame(app.main_frame)

    vsb = ttk.Scrollbar(tree_frame, orient="vertical")
    hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

    cols = [
        'LoanID', 'Num', 'Equipment', 'Serial', 'Borrower', 'Phone',
        'LoanDate', 'Deposit', 'Spacer',
    ]
    visual_cols = [
        'Num', 'Equipment', 'Serial', 'Borrower', 'Phone', 'LoanDate', 'Deposit',
    ]
    if is_rtl:
        visual_cols = ['Spacer'] + visual_cols[::-1]

    tree = ttk.Treeview(
        tree_frame,
        columns=cols,
        displaycolumns=visual_cols,
        show='headings',
        height=8,
        yscrollcommand=vsb.set,
        xscrollcommand=hsb.set)
    tree.column('Spacer', width=1, stretch=True)
    tree.heading('Spacer', text="")

    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    tree.heading('LoanID', text=app.i18n[app.lang]['col_loan_id'])
    tree.heading('Num', text=app.i18n[app.lang]['col_num'])
    tree.heading('Equipment', text=app.i18n[app.lang]['col_equipment'])
    tree.heading('Serial', text=app.i18n[app.lang]['col_serial'])
    tree.heading('Borrower', text=app.i18n[app.lang]['col_borrower'])
    tree.heading('Phone', text=app.i18n[app.lang]['col_phone'])
    tree.heading('LoanDate', text=app.i18n[app.lang]['col_loan_date'])
    tree.heading('Deposit', text=app.i18n[app.lang]['col_deposit'])

    # --- Search frame -----------------------------------------------------
    SearchFrame(
        app.main_frame,
        is_rtl=is_rtl,
        label_text=app.i18n[app.lang]['search_active_loans'],
        hint_text=app.i18n[app.lang]['search_by_loan'],
        show_all_text=app.i18n[app.lang]['show_all'],
        search_var=app.search_vars['return'],
        input_font=app.input_font,
        on_search=lambda term: _search_active_loans_list(app, term, tree),
        on_show_all=lambda: _load_active_loans(app, tree))

    tree_frame.pack(pady=10, fill='both', expand=True, padx=20)
    tree.grid(row=0, column=col_tree, sticky='nsew')
    vsb.grid(row=0, column=col_scroll, sticky='ns')
    hsb.grid(row=1, column=0, columnspan=2, sticky='ew')
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(col_tree, weight=1)

    # --- Action buttons ---------------------------------------------------
    action_frame = ttk.Frame(app.main_frame)
    action_frame.pack(pady=20)

    ttk.Button(
        action_frame,
        text=app.i18n[app.lang]['btn_process_return_action'],
        command=lambda: _process_selected_return(app, tree),
        style='Action.TButton').pack(side=side_left, padx=5)
    ttk.Button(
        action_frame,
        text=app.i18n[app.lang]['btn_forfeit_deposit'],
        command=lambda: _forfeit_selected_deposit(app, tree)).pack(side=side_left, padx=5)

    _load_active_loans(app, tree)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _populate_tree(app, tree, loans) -> None:
    for item in tree.get_children():
        tree.delete(item)

    for i, loan in enumerate(loans, 1):
        loan_date = datetime.strptime(
            loan['loan_date'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        tree.insert('', 'end', values=(
            loan['id'], i,
            loan['equipment_name'], loan['equipment_serial'],
            loan['borrower_name'], loan['borrower_phone'],
            loan_date, f"{loan['deposit_paid']:.0f}"))

    auto_size_treeview_columns(tree, is_rtl=app.is_rtl, fallback_size=app.base_font_size)


def _load_active_loans(app, tree) -> None:
    _populate_tree(app, tree, app.db.get_active_loans())


def _search_active_loans_list(app, search_term, tree) -> None:
    if not search_term:
        _load_active_loans(app, tree)
        return
    _populate_tree(app, tree, app.db.search_active_loans(search_term))


def _process_selected_return(app, tree) -> None:
    selection = tree.selection()
    if not selection:
        ui_dialogs.warn(app, app.i18n[app.lang]['warn_select_loan'])
        return

    item = tree.item(selection[0])
    loan_id = item['values'][0]
    deposit_amount = item['values'][6]

    if not messagebox.askyesno(
        app.i18n[app.lang]['confirm_return_title'],
        app.i18n[app.lang]['confirm_return_msg'].format(amount=deposit_amount)):
        return

    try:
        success = app.db.process_return(loan_id)
        if success:
            ui_dialogs.info(app, app.i18n[app.lang]['success_return'].format(amount=deposit_amount))
            app.show_process_return()
        else:
            ui_dialogs.error(app, app.i18n[app.lang]['err_return_fail'])
    except Exception as e:
        ui_dialogs.error(app, app.i18n[app.lang]['err_generic'].format(e=str(e)))


def _forfeit_selected_deposit(app, tree) -> None:
    selection = tree.selection()
    if not selection:
        ui_dialogs.warn(app, app.i18n[app.lang]['warn_select_loan'])
        return

    item = tree.item(selection[0])
    loan_id = item['values'][0]
    deposit_amount = item['values'][6]

    if not messagebox.askyesno(
        app.i18n[app.lang]['confirm_forfeit_title'],
        app.i18n[app.lang]['confirm_forfeit_msg'].format(amount=deposit_amount)):
        return

    try:
        success = app.db.forfeit_deposit(loan_id)
        if success:
            ui_dialogs.info(app, app.i18n[app.lang]['success_forfeit'].format(amount=deposit_amount))
            app.show_process_return()
        else:
            ui_dialogs.error(app, app.i18n[app.lang]['err_forfeit_fail'])
    except Exception as e:
        ui_dialogs.error(app, app.i18n[app.lang]['err_generic'].format(e=str(e)))
