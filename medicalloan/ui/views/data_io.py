"""Excel export / import flows triggered from the dashboard popup.

These were ``MedicalEquipmentApp.export_to_excel`` and
``import_from_excel`` in the old monolith. Behaviour is unchanged --
the export writes a multi-sheet ``.xlsx`` next to wherever the user
chose, and the import wraps every row in a single transaction so a
malformed sheet rolls everything back (B16).
"""

from __future__ import annotations

from datetime import datetime
from tkinter import filedialog, messagebox

import pandas as pd


def export_to_excel(app) -> None:
    """Export equipment / borrowers / loans to a multi-sheet ``.xlsx``."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=f"System_Backup_{timestamp}.xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Export Data",
        )
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

        messagebox.showinfo(
            "Success", f"Data successfully exported to:\n{filename}",
        )
    except Exception as e:
        messagebox.showerror("Export Error", f"Failed to export data: {e}")


def import_from_excel(app) -> None:
    """Merge an Excel file into the database in a single transaction."""
    filename = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        title="Import Data",
    )
    if not filename:
        return

    confirm = messagebox.askyesno(
        "Confirm Import",
        "Importing will merge data into your database.\n"
        "Existing items (by Serial/ID) will be updated.\n"
        "New items will be added.\n\n"
        "Do you want to proceed?",
    )
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

        messagebox.showinfo("Success", "Import completed successfully!")
        app.show_dashboard()

    except Exception as e:
        messagebox.showerror("Import Error", f"Failed to import data: {e}")
