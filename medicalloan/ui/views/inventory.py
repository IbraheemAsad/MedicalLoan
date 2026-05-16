"""Inventory screen + Add/Edit/Delete dialogs + summary popup."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from medicalloan.ui.dialogs import setup_dialog_window
from medicalloan.ui.treeview import (
    auto_size_treeview_columns,
    configure_status_tags,
    equipment_display_status,
    status_tag_for,
    translated_status,
)
from medicalloan.ui.widgets import SearchFrame

# ---------------------------------------------------------------------------
# Top-level "Equipment Inventory" view
# ---------------------------------------------------------------------------

def show(app) -> None:
    """Render the inventory list with search, edit/delete/summary actions."""
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
        text=app.i18n[app.lang]['inventory_title'],
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

    cols = ['ID', 'Num', 'Name', 'Serial', 'Status', 'Deposit', 'Description', 'Spacer']
    visual_cols = ['Num', 'Name', 'Serial', 'Status', 'Deposit', 'Description']
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

    configure_status_tags(tree)
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    tree.heading('ID', text=app.i18n[app.lang]['col_id'])
    tree.heading('Num', text=app.i18n[app.lang]['col_num'])
    tree.heading('Name', text=app.i18n[app.lang]['col_name'])
    tree.heading('Serial', text=app.i18n[app.lang]['col_serial'])
    tree.heading('Status', text=app.i18n[app.lang]['col_status'])
    tree.heading('Deposit', text=app.i18n[app.lang]['col_deposit'])
    tree.heading('Description', text=app.i18n[app.lang]['col_description'])

    # --- Search frame (with Add New button) -------------------------------
    SearchFrame(
        app.main_frame,
        is_rtl=is_rtl,
        label_text=app.i18n[app.lang]['search'],
        hint_text=app.i18n[app.lang]['search_by_name_serial'],
        show_all_text=app.i18n[app.lang]['show_all'],
        search_var=app.search_vars['inventory'],
        input_font=app.input_font,
        on_search=lambda term: _search_inventory_items(app, term, tree),
        on_show_all=lambda: _load_inventory(app, tree),
        add_button=(
            app.i18n[app.lang]['add_new_equipment'],
            lambda: _show_add_equipment(app),
        ),
    )

    # --- Pack the treeview after the search frame so order matches legacy
    tree_frame.pack(pady=10, fill='both', expand=True, padx=20)
    tree.grid(row=0, column=col_tree, sticky='nsew')
    vsb.grid(row=0, column=col_scroll, sticky='ns')
    hsb.grid(row=1, column=0, columnspan=2, sticky='ew')
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(col_tree, weight=1)

    # --- Action buttons ---------------------------------------------------
    action_frame = ttk.Frame(app.main_frame)
    action_frame.pack(pady=10, padx=20)
    ttk.Button(
        action_frame,
        text=app.i18n[app.lang]['edit_selected'],
        command=lambda: _edit_equipment(app, tree),
    ).pack(side='left', padx=5)
    ttk.Button(
        action_frame,
        text=app.i18n[app.lang]['delete_selected'],
        command=lambda: _delete_equipment_action(app, tree),
    ).pack(side='left', padx=5)
    ttk.Button(
        action_frame,
        text=app.i18n[app.lang]['view_summary'],
        command=lambda: _show_inventory_summary(app),
    ).pack(side='left', padx=5)

    _load_inventory(app, tree)


# ---------------------------------------------------------------------------
# Internal helpers (load/search/add/edit/delete/summary)
# ---------------------------------------------------------------------------

def _populate_tree(app, tree, equipment_list) -> None:
    """Replace tree contents with ``equipment_list`` rows. Shared by
    ``_load_inventory`` and ``_search_inventory_items`` so the column
    order + status-tag logic stays in one place."""
    for item in tree.get_children():
        tree.delete(item)

    for i, eq in enumerate(equipment_list, 1):
        status = equipment_display_status(eq)
        tree.insert(
            '', 'end',
            values=(
                eq['id'],
                i,
                eq['item_name'],
                eq['serial_number'],
                translated_status(status, app.i18n, app.lang),
                f"{eq['deposit_amount']:.2f}",
                eq['description'] or '',
            ),
            tags=(status_tag_for(status),),
        )

    auto_size_treeview_columns(tree, is_rtl=app.is_rtl, fallback_size=app.base_font_size)


def _load_inventory(app, tree) -> None:
    _populate_tree(app, tree, app.db.get_all_equipment())


def _search_inventory_items(app, search_term, tree) -> None:
    if not search_term:
        _load_inventory(app, tree)
        return
    _populate_tree(app, tree, app.db.search_equipment(search_term))


# ---- Add equipment dialog -------------------------------------------------

def _show_add_equipment(app) -> None:
    dialog = tk.Toplevel(app.root)
    dialog.title(app.i18n[app.lang]['add_eq_title'])
    dialog.grab_set()

    is_rtl = app.is_rtl
    anchor_w = 'e' if is_rtl else 'w'
    col_label = 1 if is_rtl else 0
    col_entry = 0 if is_rtl else 1
    style_label = 'Right.TLabel' if is_rtl else 'TLabel'
    justify_text = 'right' if is_rtl else 'left'

    ttk.Label(
        dialog,
        text=app.i18n[app.lang]['add_eq_title'],
        font=('Helvetica', 14, 'bold'),
    ).pack(pady=10)

    form_frame = ttk.Frame(dialog)
    form_frame.pack(pady=20, padx=20, fill='both')

    name_var = tk.StringVar()
    desc_var = tk.StringVar()
    serial_var = tk.StringVar()
    deposit_var = tk.StringVar()

    for row, (label_key, var) in enumerate([
        ('eq_name', name_var),
        ('eq_desc', desc_var),
        ('eq_serial', serial_var),
        ('eq_deposit', deposit_var),
    ]):
        ttk.Label(
            form_frame,
            text=app.i18n[app.lang][label_key],
            style=style_label,
        ).grid(row=row, column=col_label, sticky=anchor_w, pady=5)
        ttk.Entry(
            form_frame,
            textvariable=var,
            width=40,
            justify=justify_text,
            font=app.input_font,
        ).grid(row=row, column=col_entry, pady=5)

    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=20)

    def save_equipment():
        try:
            name = name_var.get().strip()
            description = desc_var.get().strip()
            serial = serial_var.get().strip()
            deposit = float(deposit_var.get())

            if not name or not serial:
                messagebox.showerror("Error", app.i18n[app.lang]['err_required_fields'])
                return

            app.db.add_equipment(name, description, serial, deposit)
            messagebox.showinfo("Success", app.i18n[app.lang]['success_add'])
            dialog.destroy()
            app.show_inventory()
        except ValueError:
            messagebox.showerror("Error", app.i18n[app.lang]['err_invalid_deposit'])
        except Exception as e:
            messagebox.showerror(
                "Error",
                app.i18n[app.lang]['err_add_fail'].format(e=str(e)),
            )

    ttk.Button(
        button_frame, text=app.i18n[app.lang]['save'], command=save_equipment,
    ).pack(side='left', padx=5)
    ttk.Button(
        button_frame, text=app.i18n[app.lang]['cancel'], command=dialog.destroy,
    ).pack(side='left', padx=5)

    setup_dialog_window(dialog, app.root)


# ---- Edit equipment dialog ------------------------------------------------

def _edit_equipment(app, tree) -> None:
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("Warning", app.i18n[app.lang]['warn_select_item'])
        return

    item = tree.item(selection[0])
    eq_id = item['values'][0]
    equipment = app.db.get_equipment(eq_id)
    if not equipment:
        messagebox.showerror("Error", app.i18n[app.lang]['err_not_found'])
        return

    dialog = tk.Toplevel(app.root)
    dialog.title(app.i18n[app.lang]['edit_eq_title'])
    dialog.grab_set()

    is_rtl = app.is_rtl
    anchor_w = 'e' if is_rtl else 'w'
    col_label = 1 if is_rtl else 0
    col_entry = 0 if is_rtl else 1
    justify_text = 'right' if is_rtl else 'left'
    style_label = 'Right.TLabel' if is_rtl else 'TLabel'

    ttk.Label(
        dialog,
        text=app.i18n[app.lang]['edit_eq_title'],
        font=('Helvetica', 14, 'bold'),
    ).pack(pady=10)

    form_frame = ttk.Frame(dialog)
    form_frame.pack(pady=20, padx=20, fill='both')

    name_var = tk.StringVar(value=equipment['item_name'])
    desc_var = tk.StringVar(value=equipment['description'] or '')
    serial_var = tk.StringVar(value=equipment['serial_number'])
    deposit_var = tk.StringVar(value=str(equipment['deposit_amount']))

    for row, (label_key, var) in enumerate([
        ('eq_name', name_var),
        ('eq_desc', desc_var),
        ('eq_serial', serial_var),
        ('eq_deposit', deposit_var),
    ]):
        ttk.Label(
            form_frame,
            text=app.i18n[app.lang][label_key],
            style=style_label,
        ).grid(row=row, column=col_label, sticky=anchor_w, pady=5)
        ttk.Entry(
            form_frame,
            textvariable=var,
            width=40,
            justify=justify_text,
            font=app.input_font,
        ).grid(row=row, column=col_entry, pady=5)

    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=20)

    def update_equipment():
        try:
            name = name_var.get().strip()
            description = desc_var.get().strip()
            serial = serial_var.get().strip()
            deposit = float(deposit_var.get())

            if not name or not serial:
                messagebox.showerror("Error", app.i18n[app.lang]['err_required_fields'])
                return

            app.db.update_equipment(eq_id, name, description, serial, deposit)
            messagebox.showinfo("Success", app.i18n[app.lang]['success_update'])
            dialog.destroy()
            app.show_inventory()
        except ValueError:
            messagebox.showerror("Error", app.i18n[app.lang]['err_invalid_deposit'])
        except Exception as e:
            messagebox.showerror(
                "Error",
                app.i18n[app.lang]['err_update_fail'].format(e=str(e)),
            )

    ttk.Button(
        button_frame, text=app.i18n[app.lang]['update'], command=update_equipment,
    ).pack(side='left', padx=5)
    ttk.Button(
        button_frame, text=app.i18n[app.lang]['cancel'], command=dialog.destroy,
    ).pack(side='left', padx=5)

    setup_dialog_window(dialog, app.root)


# ---- Delete with confirmation --------------------------------------------

def _delete_equipment_action(app, tree) -> None:
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("Warning", app.i18n[app.lang]['warn_select_item'])
        return

    item = tree.item(selection[0])
    eq_id = item['values'][0]
    eq_name = item['values'][1]

    title = app.i18n[app.lang]['confirm_delete_title']
    msg = app.i18n[app.lang]['confirm_delete_msg'].format(name=eq_name)

    if not messagebox.askyesno(title, msg):
        return

    try:
        app.db.delete_equipment(eq_id)
        messagebox.showinfo(
            app.i18n[app.lang]['success_title'],
            app.i18n[app.lang]['success_delete_msg'],
        )
        _load_inventory(app, tree)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete: {e}")


# ---- Inventory summary popup ---------------------------------------------

def _show_inventory_summary(app) -> None:
    summary = app.db.get_equipment_summary()

    dialog = tk.Toplevel(app.root)
    dialog.title(app.i18n[app.lang]['summary_title'])
    dialog.grab_set()

    ttk.Label(
        dialog,
        text=app.i18n[app.lang]['summary_title'],
        font=('Helvetica', 14, 'bold'),
    ).pack(pady=10)

    tree_frame = ttk.Frame(dialog)
    tree_frame.pack(pady=10, fill='both', expand=True, padx=20)

    cols = ['Num', 'Name', 'Total', 'InStock', 'OnLoan', 'Spacer']
    base_visuals = ['Num', 'Name', 'Total', 'InStock', 'OnLoan']
    visual_cols = ['Spacer'] + base_visuals[::-1] if app.is_rtl else base_visuals

    tree = ttk.Treeview(
        tree_frame, columns=cols, displaycolumns=visual_cols, show='headings',
    )
    tree.column('Spacer', width=1, stretch=True)
    tree.heading('Spacer', text="")

    tree.heading('Num', text=app.i18n[app.lang]['col_num'])
    tree.heading('Name', text=app.i18n[app.lang]['col_name'])
    tree.heading('Total', text=app.i18n[app.lang]['col_total'])
    tree.heading('InStock', text=app.i18n[app.lang]['col_in_stock'])
    tree.heading('OnLoan', text=app.i18n[app.lang]['col_on_loan'])

    tree.column('Total', anchor='center', width=80)
    tree.column('InStock', anchor='center', width=80)
    tree.column('OnLoan', anchor='center', width=80)

    tree.pack(fill='both', expand=True)

    for i, item in enumerate(summary, 1):
        tree.insert('', 'end', values=(
            i,
            item['item_name'],
            item['total_count'],
            item['in_stock'],
            item['on_loan'],
        ))

    auto_size_treeview_columns(tree, is_rtl=app.is_rtl, fallback_size=app.base_font_size)

    ttk.Button(
        dialog, text=app.i18n[app.lang]['close'], command=dialog.destroy,
    ).pack(pady=10)

    setup_dialog_window(dialog, app.root, min_width=600)
