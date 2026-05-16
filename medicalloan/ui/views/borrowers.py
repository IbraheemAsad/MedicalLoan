"""Manage Borrowers screen + history popup + add-borrower dialog."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from medicalloan.ui.dialogs import setup_dialog_window
from medicalloan.ui.treeview import (
    auto_size_treeview_columns,
    configure_status_tags,
    status_tag_for,
    translated_status,
)
from medicalloan.ui.widgets import SearchFrame, form_row

# ---------------------------------------------------------------------------
# Top-level "Manage Borrowers" view
# ---------------------------------------------------------------------------

def show(app) -> None:
    """Render the borrowers list with search + Add / View History."""
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
        text=app.i18n[app.lang]['borrowers_title'],
        style=style_subtitle,
    ).pack(side=side_left)
    ttk.Button(
        header,
        text=app.i18n[app.lang]['back_to_dashboard'],
        command=app.show_dashboard,
    ).pack(side=side_right)

    # --- Treeview ---------------------------------------------------------
    tree_frame = ttk.Frame(app.main_frame)
    vsb = ttk.Scrollbar(tree_frame, orient="vertical")
    hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

    cols = [
        'ID', 'Num', 'Name', 'IDNum', 'Phone1', 'Phone2', 'Address', 'Spacer',
    ]
    visual_cols = ['Num', 'Name', 'IDNum', 'Phone1', 'Phone2', 'Address']
    if is_rtl:
        visual_cols = ['Spacer'] + visual_cols[::-1]

    tree = ttk.Treeview(
        tree_frame,
        columns=cols,
        displaycolumns=visual_cols,
        show='headings',
        height=8,
        yscrollcommand=vsb.set,
        xscrollcommand=hsb.set,
    )
    tree.column('Spacer', width=1, stretch=True)
    tree.heading('Spacer', text="")

    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    tree.heading('ID', text=app.i18n[app.lang]['col_id'])
    tree.heading('Num', text=app.i18n[app.lang]['col_num'])
    tree.heading('Name', text=app.i18n[app.lang]['col_full_name'])
    tree.heading('IDNum', text=app.i18n[app.lang]['col_id_num'])
    tree.heading('Phone1', text=app.i18n[app.lang]['col_primary_phone'])
    tree.heading('Phone2', text=app.i18n[app.lang]['col_secondary_phone'])
    tree.heading('Address', text=app.i18n[app.lang]['col_address'])

    # --- Search frame -----------------------------------------------------
    SearchFrame(
        app.main_frame,
        is_rtl=is_rtl,
        label_text=app.i18n[app.lang]['search'],
        hint_text=app.i18n[app.lang]['search_by_borrower'],
        show_all_text=app.i18n[app.lang]['show_all'],
        search_var=app.search_vars['borrowers'],
        input_font=app.input_font,
        on_search=lambda term: _search_borrowers_list(app, term, tree),
        on_show_all=lambda: _load_all_borrowers(app, tree),
    )

    tree_frame.pack(pady=10, fill='both', expand=True, padx=20)
    tree.grid(row=0, column=col_tree, sticky='nsew')
    vsb.grid(row=0, column=col_scroll, sticky='ns')
    hsb.grid(row=1, column=0, columnspan=2, sticky='ew')
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(col_tree, weight=1)

    # --- Action buttons ---------------------------------------------------
    action_frame = ttk.Frame(app.main_frame)
    action_frame.pack(pady=10)

    ttk.Button(
        action_frame,
        text=app.i18n[app.lang]['btn_add_borrower'],
        command=lambda: _add_borrower_action(app, tree),
    ).pack(side=side_left, padx=5)
    ttk.Button(
        action_frame,
        text=app.i18n[app.lang]['btn_view_history'],
        command=lambda: _view_borrower_history(app, tree),
    ).pack(side=side_left, padx=5)

    _load_all_borrowers(app, tree)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _populate_tree(app, tree, borrowers) -> None:
    for item in tree.get_children():
        tree.delete(item)

    for i, borrower in enumerate(borrowers, 1):
        tree.insert('', 'end', values=(
            borrower['id'], i, borrower['full_name'], borrower['id_number'],
            borrower['primary_phone'],
            borrower.get('secondary_phone') or '',
            borrower.get('address') or '',
        ))

    auto_size_treeview_columns(tree, is_rtl=app.is_rtl, fallback_size=app.base_font_size)


def _load_all_borrowers(app, tree) -> None:
    _populate_tree(app, tree, app.db.get_all_borrowers())


def _search_borrowers_list(app, search_term, tree) -> None:
    if not search_term:
        _load_all_borrowers(app, tree)
        return
    _populate_tree(app, tree, app.db.search_borrower(search_term))


# ---- Loan history popup --------------------------------------------------

def _view_borrower_history(app, tree) -> None:
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("Warning", app.i18n[app.lang]['warn_select_borrower'])
        return

    item = tree.item(selection[0])
    borrower_id = item['values'][0]
    borrower_name = item['values'][1]

    history = app.db.get_borrower_loan_history(borrower_id)

    dialog = tk.Toplevel(app.root)
    dialog.title(app.i18n[app.lang]['history_title'].format(name=borrower_name))

    ttk.Label(
        dialog,
        text=app.i18n[app.lang]['history_for_label'].format(name=borrower_name),
        font=('Helvetica', 14, 'bold'),
    ).pack(pady=10)

    cols = [
        'LoanID', 'Num', 'Equipment', 'LoanDate', 'ReturnDate', 'Status',
        'Deposit', 'Spacer',
    ]
    visual_cols = ['Num', 'Equipment', 'LoanDate', 'ReturnDate', 'Status', 'Deposit']
    if app.is_rtl:
        visual_cols = ['Spacer'] + visual_cols[::-1]

    hist_tree = ttk.Treeview(
        dialog, columns=cols, displaycolumns=visual_cols, show='headings', height=8,
    )
    hist_tree.column('Spacer', width=1, stretch=True)
    hist_tree.heading('Spacer', text="")

    configure_status_tags(hist_tree)

    hist_tree.heading('LoanID', text=app.i18n[app.lang]['col_loan_id'])
    hist_tree.heading('Num', text=app.i18n[app.lang]['col_num'])
    hist_tree.heading('Equipment', text=app.i18n[app.lang]['col_equipment'])
    hist_tree.heading('LoanDate', text=app.i18n[app.lang]['col_loan_date'])
    hist_tree.heading('ReturnDate', text=app.i18n[app.lang]['col_return_date'])
    hist_tree.heading('Status', text=app.i18n[app.lang]['col_status'])
    hist_tree.heading('Deposit', text=app.i18n[app.lang]['col_deposit'])

    # Centered columns
    hist_tree.column('LoanID', anchor='center', width=80)
    hist_tree.column('LoanDate', anchor='center', width=100)
    hist_tree.column('ReturnDate', anchor='center', width=100)
    hist_tree.column('Status', anchor='center', width=100)
    hist_tree.column('Deposit', anchor='center', width=80)

    hist_tree.pack(pady=10, fill='both', expand=True, padx=20)

    for i, loan in enumerate(history, 1):
        loan_date = datetime.strptime(
            loan['loan_date'], '%Y-%m-%d %H:%M:%S',
        ).strftime('%d/%m/%Y')
        return_date = ''
        if loan.get('actual_return_date'):
            return_date = datetime.strptime(
                loan['actual_return_date'], '%Y-%m-%d %H:%M:%S',
            ).strftime('%d/%m/%Y')

        status = loan['loan_status']
        hist_tree.insert(
            '', 'end',
            values=(
                loan['id'], i, loan['equipment_name'], loan_date, return_date,
                translated_status(status, app.i18n, app.lang),
                f"{loan['deposit_paid']:.0f}",
            ),
            tags=(status_tag_for(status),),
        )

    auto_size_treeview_columns(hist_tree, is_rtl=app.is_rtl, fallback_size=app.base_font_size)

    ttk.Button(
        dialog, text=app.i18n[app.lang]['close'], command=dialog.destroy,
    ).pack(pady=10)

    setup_dialog_window(dialog, app.root, min_width=900)


# ---- Add borrower dialog -------------------------------------------------

def _add_borrower_action(app, tree) -> None:
    dialog = tk.Toplevel(app.root)
    dialog.title(app.i18n[app.lang]['title_add_borrower'])
    dialog.grab_set()

    is_rtl = app.is_rtl
    col_entry = 0 if is_rtl else 1

    ttk.Label(
        dialog,
        text=app.i18n[app.lang]['title_add_borrower'],
        font=('Helvetica', 14, 'bold'),
    ).pack(pady=15)

    form_frame = ttk.Frame(dialog, padding=20)
    form_frame.pack(fill='both', expand=True)
    form_frame.columnconfigure(col_entry, weight=1)

    name_var = tk.StringVar()
    id_var = tk.StringVar()
    phone1_var = tk.StringVar()
    phone2_var = tk.StringVar()
    address_var = tk.StringVar()

    form_row(form_frame, 0,
             label_text=app.i18n[app.lang]['full_name'],
             var=name_var, is_rtl=is_rtl, input_font=app.input_font,
             width=35, pady=10)
    form_row(form_frame, 1,
             label_text=app.i18n[app.lang]['id_number'],
             var=id_var, is_rtl=is_rtl, input_font=app.input_font,
             validator=app.vcmd_id, width=35, pady=10)
    form_row(form_frame, 2,
             label_text=app.i18n[app.lang]['primary_phone'],
             var=phone1_var, is_rtl=is_rtl, input_font=app.input_font,
             validator=app.vcmd_numbers, width=35, pady=10)
    form_row(form_frame, 3,
             label_text=app.i18n[app.lang]['secondary_phone'],
             var=phone2_var, is_rtl=is_rtl, input_font=app.input_font,
             validator=app.vcmd_numbers, width=35, pady=10)
    form_row(form_frame, 4,
             label_text=app.i18n[app.lang]['address'],
             var=address_var, is_rtl=is_rtl, input_font=app.input_font,
             width=35, pady=10)

    def save_new_borrower():
        name = name_var.get().strip()
        id_num = id_var.get().strip()
        phone = phone1_var.get().strip()

        if not name or not id_num or not phone:
            messagebox.showerror("Error", app.i18n[app.lang]['err_fill_required'])
            return

        if id_num != '-' and len(id_num) != 9:
            messagebox.showerror("Error", app.i18n[app.lang]['err_id_format'])
            return

        try:
            app.db.add_borrower(
                name, id_num, phone,
                phone2_var.get().strip(),
                address_var.get().strip(),
            )
            messagebox.showinfo(
                "Success", app.i18n[app.lang]['success_borrower_add'],
            )
            dialog.destroy()
            _load_all_borrowers(app, tree)
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Error", app.i18n[app.lang]['err_borrower_exists'],
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")

    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=20)

    ttk.Button(
        btn_frame, text=app.i18n[app.lang]['save'], command=save_new_borrower,
    ).pack(side='left', padx=5)
    ttk.Button(
        btn_frame, text=app.i18n[app.lang]['cancel'], command=dialog.destroy,
    ).pack(side='left', padx=5)

    setup_dialog_window(dialog, app.root)
