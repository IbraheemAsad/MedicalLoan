"""
Tests for the v1 -> v2 schema migration.

We construct a database that looks like a Phase 1 install (no schema_version
table, equipment.status='Lost' rows, loans referencing them) and then open it
via Database() to confirm the migration runs cleanly and produces the
shape Phase 2 expects.
"""

import sqlite3

from database import Database


def _build_v1(path: str) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            description TEXT,
            serial_number TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'In-Stock',
            deposit_amount REAL NOT NULL,
            created_date TEXT NOT NULL
        );
        CREATE TABLE borrower (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            id_number TEXT UNIQUE NOT NULL,
            primary_phone TEXT NOT NULL,
            secondary_phone TEXT,
            address TEXT,
            created_date TEXT NOT NULL
        );
        CREATE TABLE loan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            borrower_id INTEGER NOT NULL,
            equipment_id INTEGER NOT NULL,
            loan_date TEXT NOT NULL,
            deposit_paid REAL NOT NULL,
            deposit_status TEXT NOT NULL DEFAULT 'Held',
            expected_return_date TEXT,
            actual_return_date TEXT,
            donation_amount REAL DEFAULT 0,
            loan_status TEXT NOT NULL DEFAULT 'Active',
            notes TEXT,
            FOREIGN KEY (borrower_id) REFERENCES borrower(id),
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        );

        INSERT INTO equipment (item_name, serial_number, status, deposit_amount, created_date)
            VALUES ('Walker', 'W-001', 'In-Stock', 200, '2024-01-01 00:00:00');
        INSERT INTO equipment (item_name, serial_number, status, deposit_amount, created_date)
            VALUES ('Wheelchair', 'WC-001', 'On-Loan', 500, '2024-01-01 00:00:00');
        INSERT INTO equipment (item_name, serial_number, status, deposit_amount, created_date)
            VALUES ('Crutches', 'CR-001', 'Lost', 100, '2024-01-01 00:00:00');

        INSERT INTO borrower (full_name, id_number, primary_phone, created_date)
            VALUES ('Alice', '111111111', '0501111111', '2024-01-01 00:00:00');

        INSERT INTO loan (borrower_id, equipment_id, loan_date, deposit_paid)
            VALUES (1, 2, '2024-02-01 00:00:00', 500);
        """
    )
    conn.commit()
    conn.close()


def test_v1_to_v2_migration_backfills_is_retired_and_resets_status(tmp_path):
    db_path = tmp_path / "legacy.db"
    _build_v1(str(db_path))

    db = Database(str(db_path))
    try:
        eq = {row["serial_number"]: row for row in db.get_all_equipment()}

        # The Lost row carries forward as is_retired=1, status reset to In-Stock.
        assert eq["CR-001"]["is_retired"] == 1
        assert eq["CR-001"]["status"] == "In-Stock"

        # Untouched rows are unchanged.
        assert eq["W-001"]["is_retired"] == 0
        assert eq["W-001"]["status"] == "In-Stock"
        assert eq["WC-001"]["is_retired"] == 0
        assert eq["WC-001"]["status"] == "On-Loan"

        # FK pragma is on after migration.
        assert db.conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        # Cascade now works (it didn't before Phase 2).
        db.delete_equipment(eq["WC-001"]["id"])
        loan_count = db.conn.execute(
            "SELECT COUNT(*) FROM loan WHERE equipment_id = ?",
            (eq["WC-001"]["id"],),
        ).fetchone()[0]
        assert loan_count == 0

        # Re-opening the migrated DB doesn't trigger another migration.
        db.close()
        db2 = Database(str(db_path))
        version = db2.conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        assert version == 2
        db2.close()
    finally:
        if db.conn is not None:
            db.close()
