"""Excel export / import flows triggered from the dashboard popup.

These were ``MedicalEquipmentApp.export_to_excel`` and
``import_from_excel`` in the old monolith. Behaviour is unchanged --
the export writes a multi-sheet ``.xlsx`` next to wherever the user
chose, and the import wraps every row in a single transaction so a
malformed sheet rolls everything back (B16).

Phase 5 added :func:`restore_from_backup`: a dedicated dialog that
lists the timestamped ``backup_*.db`` files under
``<db_dir>/backups/`` and copies the chosen one over the live
database (after taking a ``pre_restore_*.db`` safety copy).
"""

from __future__ import annotations

import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from medicalloan.ui import dialogs
from medicalloan.ui.dialogs import setup_dialog_window
from services.backup_service import list_backups, restore_backup


def export_to_excel(app) -> None:
    """Export equipment / borrowers / loans to a multi-sheet ``.xlsx``."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=f"System_Backup_{timestamp}.xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Export Data")
        if not filename:
            return

        equip_data = app.db.get_dataframe_data('equipment')
        borrower_data = app.db.get_dataframe_data('borrower')
        loan_data = app.db.get_dataframe_data('loan')

        df_equip = pd.DataFrame(equip_data)
        df_borrower = pd.DataFrame(borrower_data)
        df_loan = pd.DataFrame(loan_data)

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            if not df_equip.empty:
                df_equip.to_excel(writer, sheet_name='Equipment', index=False)
            if not df_borrower.empty:
                df_borrower.to_excel(writer, sheet_name='Borrowers', index=False)
            if not df_loan.empty:
                df_loan.to_excel(writer, sheet_name='Loans', index=False)

        ui_dialogs.info(app, f"Data successfully exported to:\n{filename}")
    except Exception as e:
        ui_dialogs.error(
            app,
            f"Failed to export data: {e}",
            title_key="error_title",
        )


def import_from_excel(app) -> None:
    """Merge an Excel file into the database in a single transaction."""
    filename = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        title="Import Data")
    if not filename:
        return

    confirm = messagebox.askyesno(
        "Confirm Import",
        "Importing will merge data into your database.\n"
        "Existing items (by Serial/ID) will be updated.\n"
        "New items will be added.\n\n"
        "Do you want to proceed?")
    if not confirm:
        return

    try:
        xls = pd.ExcelFile(filename)

        # B16: wrap the entire multi-sheet import in one transaction.
        # If any row trips a CHECK or FK constraint we discard the lot
        # rather than leaving the DB half-imported.
        with app.db.import_from_excel_transaction():
            if 'Borrowers' in xls.sheet_names:
                df_borrower = pd.read_excel(xls, 'Borrowers')
                df_borrower = df_borrower.where(pd.notnull(df_borrower), None)
                for _, row in df_borrower.iterrows():
                    app.db.upsert_borrower_from_dict(row.to_dict())

            if 'Equipment' in xls.sheet_names:
                df_equip = pd.read_excel(xls, 'Equipment')
                df_equip = df_equip.where(pd.notnull(df_equip), None)
                for _, row in df_equip.iterrows():
                    app.db.upsert_equipment_from_dict(row.to_dict())

            # Loans only round-trip when restoring a backup; the IDs
            # must line up with the equipment/borrower rows imported
            # above.
            if 'Loans' in xls.sheet_names:
                df_loan = pd.read_excel(xls, 'Loans')
                df_loan = df_loan.where(pd.notnull(df_loan), None)
                for _, row in df_loan.iterrows():
                    app.db.import_loan_record(row.to_dict())

        ui_dialogs.info(app, "Import completed successfully!")
        app.show_dashboard()

    except Exception as e:
        ui_dialogs.error(
            app,
            f"Failed to import data: {e}",
            title_key="error_title",
        )


# ---------------------------------------------------------------------------
# Restore from backup (Phase 5)
# ---------------------------------------------------------------------------

def restore_from_backup(app) -> None:
    """Open a chooser dialog listing tiered backups; restore on confirm.

    The dialog shows the newest backup first (most relevant for an
    operator who just made a mistake). Selecting one and confirming
    copies it over the live DB after taking a safety copy of the
    current state. The app then closes -- the open SQLite connection
    is now pointing at a stale snapshot, and the cleanest UX is to
    have the operator relaunch on the restored file.
    """
    backup_dir = os.path.join(os.path.dirname(app.db.db_path), 'backups')
    pairs = list_backups(backup_dir) if os.path.isdir(backup_dir) else []

    dialog = tk.Toplevel(app.root)
    dialog.title(app.i18n[app.lang].get('restore_title', 'Restore Backup'))

    ttk.Label(
        dialog,
        text=app.i18n[app.lang].get(
            'restore_select',
            'Select a backup to restore.'),
        wraplength=460,
        justify='center').pack(pady=10, padx=20)

    if not pairs:
        ttk.Label(
            dialog,
            text=app.i18n[app.lang].get(
                'restore_no_backups', 'No backups available.')).pack(pady=20, padx=20)
        ttk.Button(
            dialog,
            text=app.i18n[app.lang]['close'],
            command=dialog.destroy).pack(pady=10)
        setup_dialog_window(dialog, app.root, min_width=420)
        dialogs.bind_dialog_keys(dialog)
        return

    listbox = tk.Listbox(dialog, height=10, width=44)
    for ts, path in pairs:
        listbox.insert('end', f"{ts.strftime('%Y-%m-%d %H:%M:%S')}  -  {os.path.basename(path)}")
    listbox.pack(pady=10, padx=20, fill='both', expand=True)
    listbox.selection_set(0)  # default to most recent

    def do_restore() -> None:
        sel = listbox.curselection()
        if not sel:
            dialogs.warn(app, app.i18n[app.lang].get(
                'warn_select_item', 'Please select an item.'))
            return
        _ts, path = pairs[sel[0]]
        confirm_msg = app.i18n[app.lang].get(
            'confirm_restore_msg',
            'Restore the database from this backup?\n\n{name}').format(name=os.path.basename(path))

        if not dialogs.askyesno(app, confirm_msg):
            return

        try:
            # Close the live DB before swapping the file -- on
            # Windows SQLite can hold a lock that would block the
            # copy.
            try:
                app.db.close()
            except Exception:
                pass
            safety = restore_backup(path, app.db.db_path)
        except Exception as e:
            dialogs.error(
                app,
                app.i18n[app.lang].get(
                    'restore_failed', 'Failed to restore backup: {e}').format(e=e))
            return

        dialogs.info(
            app,
            app.i18n[app.lang].get(
                'restore_success',
                'Database restored from backup.\n\nSafety copy: {safety}').format(safety=safety))
        dialog.destroy()
        # Trigger a clean shutdown so the operator relaunches on the
        # restored DB (avoids any half-cached state from the previous
        # connection).
        app.root.after(100, app.root.destroy)

    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=10)
    ttk.Button(
        btn_frame,
        text=app.i18n[app.lang].get('restore_button', 'Restore Selected'),
        command=do_restore,
        style='Action.TButton').pack(side='left', padx=5)
    ttk.Button(
        btn_frame,
        text=app.i18n[app.lang]['cancel'],
        command=dialog.destroy).pack(side='left', padx=5)

    setup_dialog_window(dialog, app.root, min_width=460)
    dialogs.bind_dialog_keys(dialog, on_confirm=do_restore)
