"""New-loan flow.

Two screens that share state via ``app.search_vars`` and ``app.form_vars``:

* :func:`show` -- step 1: pick the equipment to loan out.
* :func:`show_borrower_step` -- step 2: enter / look up the borrower
  and the deposit/donation amounts. Triggers PDF agreement + loan
  creation on submit.

The borrower-selection popup (:func:`_show_borrower_selection`) is
internal to step 2 but lives in this module because step 1 never
opens it directly.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from medicalloan.ui.dialogs import setup_dialog_window
from medicalloan.ui.treeview import auto_size_treeview_columns
from medicalloan.ui.widgets import SearchFrame

# ---------------------------------------------------------------------------
# Step 1 -- equipment picker
# ---------------------------------------------------------------------------

def show(app) -> None:
    """Render step 1: select equipment to loan out."""
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
        text=app.i18n[app.lang]['new_loan_title'],
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

    cols = ['ID', 'Num', 'Name', 'Serial', 'Deposit', 'Description', 'Spacer']
    visual_cols = ['Num', 'Name', 'Serial', 'Deposit', 'Description']
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
    tree.heading('Name', text=app.i18n[app.lang]['col_name'])
    tree.heading('Serial', text=app.i18n[app.lang]['col_serial'])
    tree.heading('Deposit', text=app.i18n[app.lang]['col_deposit'])
    tree.heading('Description', text=app.i18n[app.lang]['col_description'])

    # --- Search frame -----------------------------------------------------
    SearchFrame(
        app.main_frame,
        is_rtl=is_rtl,
        label_text=app.i18n[app.lang]['search_available_eq'],
        hint_text=app.i18n[app.lang]['search_by_eq_name'],
        show_all_text=app.i18n[app.lang]['show_all'],
        search_var=app.search_vars['loan_step1'],
        input_font=app.input_font,
        on_search=lambda term: _search_available_equipment(app, term, tree),
        on_show_all=lambda: _load_available_equipment(app, tree),
    )

    tree_frame.pack(pady=10, fill='both', expand=True, padx=20)
    tree.grid(row=0, column=col_tree, sticky='nsew')
    vsb.grid(row=0, column=col_scroll, sticky='ns')
    hsb.grid(row=1, column=0, columnspan=2, sticky='ew')
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(col_tree, weight=1)

    # --- Action -----------------------------------------------------------
    action_frame = ttk.Frame(app.main_frame)
    action_frame.pack(pady=20)

    ttk.Button(
        action_frame,
        text=app.i18n[app.lang]['loan_this_item'],
        command=lambda: _proceed_to_borrower_step(app, tree),
        style='Action.TButton',
    ).pack()

    _load_available_equipment(app, tree)


def clear_loan_form(app) -> None:
    """Reset step-2 form variables. Public so the App can call it."""
    for key in app.form_vars:
        app.form_vars[key].set("")
    app.search_vars['loan_step2'].set("")


# ---------------------------------------------------------------------------
# Step 1 internals
# ---------------------------------------------------------------------------

def _populate_equipment_tree(app, tree, equipment_list) -> None:
    for item in tree.get_children():
        tree.delete(item)
    for i, eq in enumerate(equipment_list, 1):
        tree.insert('', 'end', values=(
            eq['id'], i, eq['item_name'], eq['serial_number'],
            f"{eq['deposit_amount']:.2f}", eq['description'] or '',
        ))
    auto_size_treeview_columns(tree, is_rtl=app.is_rtl, fallback_size=app.base_font_size)


def _load_available_equipment(app, tree) -> None:
    _populate_equipment_tree(app, tree, app.db.get_available_equipment())


def _search_available_equipment(app, search_term, tree) -> None:
    if not search_term:
        _load_available_equipment(app, tree)
        return
    _populate_equipment_tree(app, tree, app.db.get_available_equipment(search_term))


def _proceed_to_borrower_step(app, tree) -> None:
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("Warning", app.i18n[app.lang]['warn_select_item'])
        return
    item = tree.item(selection[0])
    eq_id = item['values'][0]
    equipment = app.db.get_equipment(eq_id)
    show_borrower_step(app, equipment)


# ---------------------------------------------------------------------------
# Step 2 -- borrower & deposit
# ---------------------------------------------------------------------------

def show_borrower_step(app, equipment) -> None:
    """Render step 2: borrower lookup / entry + deposit form.

    The structure is unchanged from the legacy ``show_borrower_step``:
    a left "borrower" pane and a right "selected equipment" pane,
    both wrapped in LabelFrames with a primary "Confirm & Print
    Agreement" button below.
    """
    app.clear_window()
    app.show_global_controls(app.main_frame, lambda: show_borrower_step(app, equipment))

    is_rtl = app.is_rtl
    anchor_w = 'e' if is_rtl else 'w'
    justify_text = 'right' if is_rtl else 'left'
    label_anchor = 'ne' if is_rtl else 'nw'

    # --- Header -----------------------------------------------------------
    header = ttk.Frame(app.main_frame)
    header.pack(pady=(10, 20), fill='x', padx=20)

    title_side = 'right' if is_rtl else 'left'
    btn_side = 'left' if is_rtl else 'right'

    ttk.Label(
        header,
        text=app.i18n[app.lang]['new_loan_title_step2'],
        style='Subtitle.TLabel',
    ).pack(side=title_side)
    ttk.Button(
        header,
        text=app.i18n[app.lang]['back'],
        command=app.show_new_loan,
    ).pack(side=btn_side)

    # --- Two panes (borrower / item) --------------------------------------
    content_container = ttk.Frame(app.main_frame)
    content_container.pack(fill='x', padx=20)

    pane_borrower = ttk.Frame(content_container)
    pane_item = ttk.Frame(content_container)

    if is_rtl:
        pane_borrower.pack(side='right', fill='both', expand=True, padx=(10, 0))
        pane_item.pack(side='right', fill='both', expand=True, padx=(0, 10))
    else:
        pane_borrower.pack(side='left', fill='both', expand=True, padx=(0, 10))
        pane_item.pack(side='left', fill='both', expand=True, padx=(10, 0))

    # ---- Pane 1: borrower search + form ----
    search_container = ttk.LabelFrame(
        pane_borrower,
        text=app.i18n[app.lang]['search_borrower'],
        padding=10,
        labelanchor=label_anchor,
    )
    search_container.pack(fill='x', pady=(0, 10))

    search_var = app.search_vars['loan_step2']

    if is_rtl:
        ttk.Button(
            search_container,
            text=app.i18n[app.lang]['search_btn'],
            command=lambda: search_borrower_logic(),
        ).grid(row=0, column=0, padx=5)
        entry = ttk.Entry(
            search_container, textvariable=search_var, width=20,
            justify=justify_text, font=app.input_font,
        )
        entry.grid(row=0, column=1, padx=5, sticky='ew')
        search_container.columnconfigure(1, weight=1)
    else:
        entry = ttk.Entry(
            search_container, textvariable=search_var, width=20,
            font=app.input_font,
        )
        entry.grid(row=0, column=0, padx=5, sticky='ew')
        ttk.Button(
            search_container,
            text=app.i18n[app.lang]['search_btn'],
            command=lambda: search_borrower_logic(),
        ).grid(row=0, column=1, padx=5)
        search_container.columnconfigure(0, weight=1)

    ttk.Label(
        search_container,
        text=app.i18n[app.lang]['search_by_id_phone'],
        font=('Helvetica', 9),
        foreground='grey',
    ).grid(row=1, column=0, columnspan=2, sticky=anchor_w, padx=5)

    # Borrower details form
    form_container = ttk.LabelFrame(
        pane_borrower,
        text=app.i18n[app.lang]['borrower_details'],
        padding=10,
        labelanchor=label_anchor,
    )
    form_container.pack(fill='x', expand=False)

    tools_frame = ttk.Frame(form_container)
    tools_frame.pack(fill='x', pady=(0, 10))

    fields_frame = ttk.Frame(form_container)
    fields_frame.pack(fill='x', expand=True)

    borrower_entry_widgets: list[ttk.Entry] = []

    def set_fields_state(state):
        for widget in borrower_entry_widgets:
            widget.config(state=state)

    btn_edit = ttk.Button(
        tools_frame,
        text=app.i18n[app.lang]['btn_edit_details'],
        command=lambda: set_fields_state('normal'),
        width=15,
    )
    btn_change = ttk.Button(
        tools_frame,
        text=app.i18n[app.lang]['btn_change_borrower'],
        command=lambda: on_change_click(),
        width=15,
    )

    def show_edit_buttons():
        # Re-pack from a clean slate so toggling state doesn't stack
        # the same button twice.
        btn_edit.pack_forget()
        btn_change.pack_forget()
        # Side-by-side, equally expanded -- mirrors the legacy "simple
        # centre approach" comment.
        btn_edit.pack(side='left', expand=True, padx=5)
        btn_change.pack(side='left', expand=True, padx=5)

    def hide_edit_buttons():
        btn_edit.pack_forget()
        btn_change.pack_forget()

    def on_change_click():
        clear_loan_form(app)
        borrower_data['borrower_id'] = None
        set_fields_state('normal')
        hide_edit_buttons()
        # Reset the financial fields to their defaults; the form-var
        # clear above wiped them.
        deposit_var.set(str(equipment['deposit_amount']))
        donation_var.set("0")

    # Form fields setup
    f_col_lbl = 1 if is_rtl else 0
    f_col_ent = 0 if is_rtl else 1

    name_var = app.form_vars['name']
    id_var = app.form_vars['id']
    phone1_var = app.form_vars['phone1']
    phone2_var = app.form_vars['phone2']
    address_var = app.form_vars['address']
    deposit_var = app.form_vars['deposit']
    donation_var = app.form_vars['donation']

    if not deposit_var.get():
        deposit_var.set(str(equipment['deposit_amount']))
    if not donation_var.get():
        donation_var.set("0")

    def add_row(parent, row, label_key, var, validator=None):
        ttk.Label(
            parent, text=app.i18n[app.lang][label_key],
        ).grid(row=row, column=f_col_lbl, sticky=anchor_w, pady=5)
        e = ttk.Entry(
            parent, textvariable=var, width=25,
            justify=justify_text, font=app.input_font,
        )
        if validator:
            e.config(validate='key', validatecommand=validator)
        e.grid(row=row, column=f_col_ent, sticky='ew', pady=5)
        borrower_entry_widgets.append(e)

    add_row(fields_frame, 0, 'full_name', name_var)
    add_row(fields_frame, 1, 'id_number', id_var, app.vcmd_id)
    add_row(fields_frame, 2, 'primary_phone', phone1_var, app.vcmd_numbers)
    add_row(fields_frame, 3, 'secondary_phone', phone2_var, app.vcmd_numbers)
    add_row(fields_frame, 4, 'address', address_var)

    fields_frame.columnconfigure(f_col_ent, weight=1)

    # ---- Pane 2: selected equipment + financial details ----
    eq_container = ttk.LabelFrame(
        pane_item,
        text=app.i18n[app.lang]['selected_equipment'],
        padding=10,
        labelanchor=label_anchor,
    )
    eq_container.pack(fill='x', pady=(0, 10))

    ttk.Label(
        eq_container, text=equipment['item_name'], font=('Helvetica', 12, 'bold'),
    ).pack(anchor=anchor_w)
    ttk.Label(
        eq_container,
        text=f"{app.i18n[app.lang]['col_serial']}: {equipment['serial_number']}",
    ).pack(anchor=anchor_w)
    ttk.Label(
        eq_container,
        text=f"{app.i18n[app.lang]['col_deposit']}: {equipment['deposit_amount']:.2f}",
    ).pack(anchor=anchor_w)

    fin_container = ttk.LabelFrame(
        pane_item,
        text=app.i18n[app.lang]['financial_details'],
        padding=10,
        labelanchor=label_anchor,
    )
    fin_container.pack(fill='x')

    def add_fin_row(row, label_key, var):
        ttk.Label(
            fin_container, text=app.i18n[app.lang][label_key],
        ).grid(row=row, column=f_col_lbl, sticky=anchor_w, pady=5)
        ttk.Entry(
            fin_container, textvariable=var, width=25,
            justify=justify_text, font=app.input_font,
        ).grid(row=row, column=f_col_ent, sticky='ew', pady=5)

    add_fin_row(0, 'deposit_paid', deposit_var)
    add_fin_row(1, 'donation', donation_var)

    fin_container.columnconfigure(f_col_ent, weight=1)

    # ---- Action buttons ----
    btn_frame = ttk.Frame(app.main_frame, padding=20)
    btn_frame.pack(fill='x')

    borrower_data: dict[str, int | None] = {'borrower_id': None}

    def confirm_loan_logic():
        try:
            name = name_var.get().strip()
            id_number = id_var.get().strip()
            phone1 = phone1_var.get().strip()

            dep_val = deposit_var.get().strip()
            don_val = donation_var.get().strip()

            deposit = float(dep_val) if dep_val else 0.0
            donation = float(don_val) if don_val else 0.0

            if not name or not id_number or not phone1:
                messagebox.showerror(
                    "Error", app.i18n[app.lang]['err_fill_required'],
                )
                return

            if id_number != '-' and len(id_number) != 9:
                messagebox.showerror(
                    "Error", app.i18n[app.lang]['err_id_format'],
                )
                return

            if borrower_data['borrower_id']:
                borrower_id = borrower_data['borrower_id']
                app.db.update_borrower(
                    borrower_id, name, id_number, phone1,
                    phone2_var.get().strip(), address_var.get().strip(),
                )
            else:
                existing = app.db.get_borrower_by_id_number(id_number)
                if existing:
                    borrower_id = existing['id']
                    app.db.update_borrower(
                        borrower_id, name, id_number, phone1,
                        phone2_var.get().strip(), address_var.get().strip(),
                    )
                else:
                    borrower_id = app.db.add_borrower(
                        name, id_number, phone1,
                        phone2_var.get().strip(), address_var.get().strip(),
                    )

            loan_id = app.db.create_loan(
                borrower_id, equipment['id'], deposit, donation,
            )
            loan_data = app.db.get_loan(loan_id)

            try:
                pdf_path = app.reports.generate_loan_agreement(loan_data, app.lang)
                app.reports.open_pdf(pdf_path)
                messagebox.showinfo(
                    "Success",
                    app.i18n[app.lang]['success_loan_created'].format(id=loan_id),
                )
            except Exception as e:
                messagebox.showwarning(
                    "Warning", f"Loan created, but agreement failed: {e}",
                )

            clear_loan_form(app)
            app.show_dashboard()

        except ValueError:
            messagebox.showerror(
                "Error", app.i18n[app.lang]['err_invalid_deposit_donation'],
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")

    ttk.Button(
        btn_frame,
        text=app.i18n[app.lang]['confirm_print'],
        style='Action.TButton',
        command=confirm_loan_logic,
    ).pack(fill='x', ipady=5)

    # ---- Search-borrower closure ----
    def search_borrower_logic():
        term = search_var.get().strip()
        results = (
            app.db.get_all_borrowers() if not term
            else app.db.search_borrower(term)
        )

        if results:
            # When the user picks one: lock the form fields and reveal
            # the Edit / Change buttons.
            _show_borrower_selection(
                app, results,
                name_var, id_var, phone1_var, phone2_var, address_var,
                borrower_data,
                on_select_callback=lambda: (
                    set_fields_state('disabled'),
                    show_edit_buttons(),
                ),
            )
        else:
            messagebox.showinfo(
                "Not Found", app.i18n[app.lang]['borrower_not_found'],
            )
            borrower_data['borrower_id'] = None
            set_fields_state('normal')
            hide_edit_buttons()

    entry.bind('<Return>', lambda event: search_borrower_logic())


# ---------------------------------------------------------------------------
# Borrower-selection popup (step 2 only)
# ---------------------------------------------------------------------------

def _show_borrower_selection(
    app,
    borrowers,
    name_var,
    id_var,
    phone1_var,
    phone2_var,
    address_var,
    borrower_data,
    on_select_callback=None,
) -> None:
    """Modal dialog listing matching borrowers; double-click style select."""
    dialog = tk.Toplevel(app.root)
    dialog.title(app.i18n[app.lang]['select_borrower_title'])
    dialog.grab_set()

    ttk.Label(
        dialog,
        text=app.i18n[app.lang]['found_borrowers'],
        font=('Helvetica', 12, 'bold'),
    ).pack(pady=10)

    cols = ['ID', 'Num', 'Name', 'IDNum', 'Phone', 'Spacer']
    visual_cols = ['Num', 'Name', 'IDNum', 'Phone']
    if app.is_rtl:
        visual_cols = ['Spacer'] + visual_cols[::-1]

    tree = ttk.Treeview(
        dialog, columns=cols, displaycolumns=visual_cols, show='headings',
    )
    tree.column('Spacer', width=1, stretch=True)
    tree.heading('Spacer', text="")

    tree.heading('ID', text=app.i18n[app.lang]['col_id'])
    tree.heading('Num', text=app.i18n[app.lang]['col_num'])
    tree.heading('Name', text=app.i18n[app.lang]['col_full_name'])
    tree.heading('IDNum', text=app.i18n[app.lang]['col_id_num'])
    tree.heading('Phone', text=app.i18n[app.lang]['col_phone'])

    tree.pack(pady=10, fill='both', expand=True, padx=20)

    for i, borrower in enumerate(borrowers, 1):
        tree.insert('', 'end', values=(
            borrower['id'], i, borrower['full_name'],
            borrower['id_number'], borrower['primary_phone'],
        ))

    auto_size_treeview_columns(tree, is_rtl=app.is_rtl, fallback_size=app.base_font_size)

    def select_borrower():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning(
                "Warning", app.i18n[app.lang]['warn_select_borrower'],
            )
            return

        item = tree.item(selection[0])
        borrower_id = item['values'][0]
        borrower = app.db.get_borrower(borrower_id)

        name_var.set(borrower['full_name'])
        id_var.set(borrower['id_number'])
        phone1_var.set(borrower['primary_phone'])
        phone2_var.set(borrower.get('secondary_phone') or '')
        address_var.set(borrower.get('address') or '')

        borrower_data['borrower_id'] = borrower_id

        if on_select_callback:
            on_select_callback()

        dialog.destroy()

    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=10)

    ttk.Button(
        button_frame, text=app.i18n[app.lang]['select'], command=select_borrower,
    ).pack(side='left', padx=5)
    ttk.Button(
        button_frame, text=app.i18n[app.lang]['cancel'], command=dialog.destroy,
    ).pack(side='left', padx=5)

    setup_dialog_window(dialog, app.root, min_width=600)
