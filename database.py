"""
Database module for Medical Equipment Loan Management System.

Phase 2 hardening (see .kiro/steering/improvement-plan.md):
- B2:  Excel-restore loan import is parameterized via a column allowlist.
- B3:  PRAGMA foreign_keys=ON + journal_mode=WAL on every connect;
       ON DELETE CASCADE on loan FKs; indexes on hot columns.
- B4:  "Lost" is now a flag on the loan, not a status on the equipment.
       Equipment carries an `is_retired` flag instead.
- B5:  process_return only flips equipment back to In-Stock if it was On-Loan.
- B16: import_from_excel is wrapped in a single transaction by the caller
       (see import_from_excel_transaction()).
- B17: status values come from constants.EquipmentStatus / LoanStatus /
       DepositStatus — no more 'OnLoan' vs 'On-Loan' drift.
- B18: connect() is idempotent (closes any existing connection first).
- WAL: close() runs PRAGMA wal_checkpoint(TRUNCATE) so the -wal/-shm
       files don't grow unbounded across sessions.

Schema migrations are tracked in `schema_version`. Existing 0.1 databases
are migrated forward in-place on first open.
"""

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from constants import (
    ALLOWED_LOAN_COLUMNS,
    DepositStatus,
    EquipmentStatus,
    LoanStatus,
)
from paths import default_db_path

log = logging.getLogger(__name__)

# Bump when schema migrations are added.
CURRENT_SCHEMA_VERSION = 2


class Database:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path if db_path is not None else default_db_path()
        self.conn: sqlite3.Connection | None = None
        # Tracks nesting depth of import_from_excel_transaction so the
        # per-call commits in the upsert helpers don't break atomic imports.
        self._tx_depth = 0
        self.connect()
        self._ensure_schema()
        # Re-apply pragmas: `PRAGMA foreign_keys = ON` only takes effect
        # outside an active transaction, and the migration path runs DDL
        # inside one. Re-applying after commit makes sure the connection
        # the rest of the app uses has FKs enforced.
        self._apply_pragmas(self.conn)

    def _commit(self) -> None:
        """Commit unless we're inside an outer transaction wrapper.

        Per-method commits make the simple call sites (single equipment
        edit, single borrower add) feel transactional. But during a bulk
        Excel import we want one big atomic transaction, so the outer
        wrapper bumps `_tx_depth` and these inner commits no-op.
        """
        if self._tx_depth == 0 and self.conn is not None:
            self.conn.commit()

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the database connection.

        Idempotent (B18): if a connection already exists it is closed first
        so we don't leak handles on reconnect.
        """
        if self.conn is not None:
            try:
                self.conn.close()
            except sqlite3.Error as e:
                log.warning("Closing previous connection failed: %s", e)
            self.conn = None

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._apply_pragmas(self.conn)

    @staticmethod
    def _apply_pragmas(conn: sqlite3.Connection) -> None:
        """Apply per-connection pragmas (B3).

        SQLite resets foreign_keys per connection, so this runs every time.
        WAL is a database-level setting but applying it via PRAGMA is cheap
        and lets a fresh DB pick it up on first open.
        """
        cur = conn.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        cur.execute('PRAGMA journal_mode = WAL')
        cur.execute('PRAGMA synchronous = NORMAL')

    def close(self) -> None:
        """Close the database connection, checkpointing WAL first.

        Without the checkpoint the `-wal` file can grow across sessions until
        the next "passive" checkpoint happens to occur. TRUNCATE is the
        strongest variant; it's safe because we hold the only connection.
        """
        if self.conn is None:
            return
        try:
            self.conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        except sqlite3.Error as e:
            log.warning("WAL checkpoint on close failed: %s", e)
        try:
            self.conn.close()
        finally:
            self.conn = None

    @contextmanager
    def transaction(self):
        """Context manager for atomic multi-statement work (B16).

        Using `with self.conn:` directly auto-commits on success and rolls
        back on exception, but only if you go through the connection. This
        wrapper makes intent explicit at call sites.
        """
        assert self.conn is not None, "Database is closed"
        try:
            with self.conn:
                yield self.conn
        except Exception:
            log.exception("Transaction rolled back")
            raise

    # ------------------------------------------------------------------
    # Schema setup + migrations
    # ------------------------------------------------------------------

    def _ensure_schema(self) -> None:
        """Create tables on first run; migrate forward on subsequent runs."""
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        ''')
        cursor.execute('SELECT MAX(version) FROM schema_version')
        row = cursor.fetchone()
        current = row[0] if row and row[0] is not None else 0

        if current == 0:
            # Two cases:
            # (a) Brand new DB: no existing tables. Create v2 schema.
            # (b) Pre-Phase-2 DB: equipment/borrower/loan exist but
            #     schema_version was never written. Treat as v1 and
            #     migrate forward.
            cursor.execute('''
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name = 'equipment'
            ''')
            if cursor.fetchone() is None:
                self._create_v2_schema(cursor)
            else:
                self._migrate_v1_to_v2(cursor)
            cursor.execute('INSERT INTO schema_version (version) VALUES (?)',
                           (CURRENT_SCHEMA_VERSION,))
            self.conn.commit()
            return

        # Future: forward migrations from a recorded version go here.
        if current < CURRENT_SCHEMA_VERSION:
            # No newer migrations defined yet beyond v2.
            cursor.execute('INSERT INTO schema_version (version) VALUES (?)',
                           (CURRENT_SCHEMA_VERSION,))
            self.conn.commit()

    @staticmethod
    def _create_v2_schema(cursor: sqlite3.Cursor) -> None:
        cursor.executescript(f'''
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                description TEXT,
                serial_number TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT '{EquipmentStatus.IN_STOCK}'
                    CHECK (status IN ('{EquipmentStatus.IN_STOCK}',
                                      '{EquipmentStatus.ON_LOAN}')),
                deposit_amount REAL NOT NULL,
                is_retired INTEGER NOT NULL DEFAULT 0
                    CHECK (is_retired IN (0, 1)),
                created_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS borrower (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                id_number TEXT UNIQUE NOT NULL,
                primary_phone TEXT NOT NULL,
                secondary_phone TEXT,
                address TEXT,
                created_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS loan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                borrower_id INTEGER NOT NULL,
                equipment_id INTEGER NOT NULL,
                loan_date TEXT NOT NULL,
                deposit_paid REAL NOT NULL,
                deposit_status TEXT NOT NULL DEFAULT '{DepositStatus.HELD}'
                    CHECK (deposit_status IN ('{DepositStatus.HELD}',
                                              '{DepositStatus.RETURNED}',
                                              '{DepositStatus.FORFEITED}')),
                expected_return_date TEXT,
                actual_return_date TEXT,
                donation_amount REAL DEFAULT 0,
                loan_status TEXT NOT NULL DEFAULT '{LoanStatus.ACTIVE}'
                    CHECK (loan_status IN ('{LoanStatus.ACTIVE}',
                                           '{LoanStatus.RETURNED}',
                                           '{LoanStatus.NOT_RETURNED}')),
                notes TEXT,
                FOREIGN KEY (borrower_id) REFERENCES borrower(id) ON DELETE CASCADE,
                FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_loan_borrower    ON loan(borrower_id);
            CREATE INDEX IF NOT EXISTS idx_loan_equipment   ON loan(equipment_id);
            CREATE INDEX IF NOT EXISTS idx_loan_status      ON loan(loan_status);
            CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status);
        ''')

    def _migrate_v1_to_v2(self, cursor: sqlite3.Cursor) -> None:
        """Migrate a pre-Phase-2 database in place.

        Changes:
        - Add equipment.is_retired and backfill from old status='Lost'.
        - Reset equipment.status to In-Stock for retired rows so the new
          CHECK constraint passes; the loan's deposit_status='Forfeited'
          carries the "this didn't come back" signal forward.
        - Replace equipment table to install the new CHECK on status.
        - Replace loan table to install ON DELETE CASCADE + CHECKs.
        - Add the new indexes.
        """
        log.info("Migrating database from v1 to v2 at %s", self.db_path)

        # FK enforcement is on; turn it off for the duration of the table
        # rebuild so we can copy across without tripping referential checks.
        cursor.execute('PRAGMA foreign_keys = OFF')

        # --- equipment ----------------------------------------------------
        cursor.execute('''
            CREATE TABLE equipment_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                description TEXT,
                serial_number TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'In-Stock'
                    CHECK (status IN ('In-Stock', 'On-Loan')),
                deposit_amount REAL NOT NULL,
                is_retired INTEGER NOT NULL DEFAULT 0
                    CHECK (is_retired IN (0, 1)),
                created_date TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            INSERT INTO equipment_new
                (id, item_name, description, serial_number, status,
                 deposit_amount, is_retired, created_date)
            SELECT
                id, item_name, description, serial_number,
                CASE WHEN status = 'Lost' THEN 'In-Stock' ELSE status END,
                deposit_amount,
                CASE WHEN status = 'Lost' THEN 1 ELSE 0 END,
                created_date
            FROM equipment
        ''')
        cursor.execute('DROP TABLE equipment')
        cursor.execute('ALTER TABLE equipment_new RENAME TO equipment')

        # --- loan ---------------------------------------------------------
        # status_values had 'Active' map to 'OnLoan' in some i18n entries
        # and 'On-Loan' in others (B17). The DB itself stored 'Active' /
        # 'Returned' / 'Not Returned' so no row rewrite is needed here —
        # we just want CHECKs and CASCADE.
        cursor.execute('''
            CREATE TABLE loan_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                borrower_id INTEGER NOT NULL,
                equipment_id INTEGER NOT NULL,
                loan_date TEXT NOT NULL,
                deposit_paid REAL NOT NULL,
                deposit_status TEXT NOT NULL DEFAULT 'Held'
                    CHECK (deposit_status IN ('Held', 'Returned', 'Forfeited')),
                expected_return_date TEXT,
                actual_return_date TEXT,
                donation_amount REAL DEFAULT 0,
                loan_status TEXT NOT NULL DEFAULT 'Active'
                    CHECK (loan_status IN ('Active', 'Returned', 'Not Returned')),
                notes TEXT,
                FOREIGN KEY (borrower_id) REFERENCES borrower(id) ON DELETE CASCADE,
                FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            INSERT INTO loan_new
                (id, borrower_id, equipment_id, loan_date, deposit_paid,
                 deposit_status, expected_return_date, actual_return_date,
                 donation_amount, loan_status, notes)
            SELECT
                id, borrower_id, equipment_id, loan_date, deposit_paid,
                deposit_status, expected_return_date, actual_return_date,
                donation_amount, loan_status, notes
            FROM loan
        ''')
        cursor.execute('DROP TABLE loan')
        cursor.execute('ALTER TABLE loan_new RENAME TO loan')

        # Indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loan_borrower    ON loan(borrower_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loan_equipment   ON loan(equipment_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loan_status      ON loan(loan_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status)')

        cursor.execute('PRAGMA foreign_keys = ON')

    # ------------------------------------------------------------------
    # Equipment
    # ------------------------------------------------------------------

    def add_equipment(self, item_name: str, description: str, serial_number: str,
                      deposit_amount: float) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO equipment (item_name, description, serial_number,
                                   deposit_amount, created_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (item_name, description, serial_number, deposit_amount, _now()))
        self._commit()
        return cursor.lastrowid

    def get_equipment(self, equipment_id: int) -> dict | None:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM equipment WHERE id = ?', (equipment_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_equipment(self) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM equipment ORDER BY item_name')
        return [dict(row) for row in cursor.fetchall()]

    def search_equipment(self, search_term: str) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM equipment
            WHERE item_name LIKE ? OR serial_number LIKE ?
            ORDER BY item_name
        ''', (f'%{search_term}%', f'%{search_term}%'))
        return [dict(row) for row in cursor.fetchall()]

    def get_available_equipment(self, item_name: str | None = None) -> list[dict]:
        """Equipment that is in stock and not retired."""
        cursor = self.conn.cursor()
        if item_name:
            cursor.execute('''
                SELECT * FROM equipment
                WHERE status = ? AND is_retired = 0 AND item_name LIKE ?
                ORDER BY item_name
            ''', (EquipmentStatus.IN_STOCK, f'%{item_name}%'))
        else:
            cursor.execute('''
                SELECT * FROM equipment
                WHERE status = ? AND is_retired = 0
                ORDER BY item_name
            ''', (EquipmentStatus.IN_STOCK,))
        return [dict(row) for row in cursor.fetchall()]

    def update_equipment_status(self, equipment_id: int, status: str) -> None:
        if status not in EquipmentStatus.ALL:
            raise ValueError(f"Invalid equipment status: {status!r}")
        cursor = self.conn.cursor()
        cursor.execute('UPDATE equipment SET status = ? WHERE id = ?',
                       (status, equipment_id))
        self._commit()

    def update_equipment(self, equipment_id: int, item_name: str, description: str,
                         serial_number: str, deposit_amount: float) -> None:
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE equipment
            SET item_name = ?, description = ?, serial_number = ?, deposit_amount = ?
            WHERE id = ?
        ''', (item_name, description, serial_number, deposit_amount, equipment_id))
        self._commit()

    def set_equipment_retired(self, equipment_id: int, retired: bool) -> None:
        """Toggle the retired flag (B4 — Lost is no longer a status)."""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE equipment SET is_retired = ? WHERE id = ?',
                       (1 if retired else 0, equipment_id))
        self._commit()

    def get_equipment_summary(self) -> list[dict]:
        """Counts for the active (non-retired) inventory."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT
                item_name,
                COUNT(*) AS total_count,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS in_stock,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS on_loan
            FROM equipment
            WHERE is_retired = 0
            GROUP BY item_name
            ORDER BY item_name
        ''', (EquipmentStatus.IN_STOCK, EquipmentStatus.ON_LOAN))
        return [dict(row) for row in cursor.fetchall()]

    def get_lost_equipment(self) -> list[dict]:
        """Equipment marked as retired (formerly status='Lost')."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM equipment
            WHERE is_retired = 1
            ORDER BY item_name
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def delete_equipment(self, equipment_id: int) -> None:
        """Delete equipment and its loan history.

        With ON DELETE CASCADE in place this is a single statement, but the
        old API took two — keep the public method for callers in main.py.
        """
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM equipment WHERE id = ?', (equipment_id,))
        self._commit()

    # ------------------------------------------------------------------
    # Borrower
    # ------------------------------------------------------------------

    def add_borrower(self, full_name: str, id_number: str, primary_phone: str,
                     secondary_phone: str | None = None,
                     address: str | None = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO borrower (full_name, id_number, primary_phone,
                                  secondary_phone, address, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (full_name, id_number, primary_phone, secondary_phone, address, _now()))
        self._commit()
        return cursor.lastrowid

    def get_borrower(self, borrower_id: int) -> dict | None:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM borrower WHERE id = ?', (borrower_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def search_borrower(self, search_term: str) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM borrower
            WHERE full_name LIKE ? OR id_number LIKE ? OR primary_phone LIKE ?
            ORDER BY full_name
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        return [dict(row) for row in cursor.fetchall()]

    def get_borrower_by_id_number(self, id_number: str) -> dict | None:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM borrower WHERE id_number = ?', (id_number,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_borrower(self, borrower_id: int, full_name: str, id_number: str,
                        primary_phone: str, secondary_phone: str | None = None,
                        address: str | None = None) -> None:
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE borrower
            SET full_name = ?, id_number = ?, primary_phone = ?,
                secondary_phone = ?, address = ?
            WHERE id = ?
        ''', (full_name, id_number, primary_phone, secondary_phone, address, borrower_id))
        self._commit()

    def get_all_borrowers(self) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM borrower ORDER BY full_name')
        return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Loan
    # ------------------------------------------------------------------

    def create_loan(self, borrower_id: int, equipment_id: int, deposit_paid: float,
                    donation_amount: float = 0,
                    expected_return_date: str | None = None,
                    notes: str | None = None) -> int:
        """Create a loan + flip equipment to On-Loan in one transaction."""
        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO loan (borrower_id, equipment_id, loan_date, deposit_paid,
                                  donation_amount, expected_return_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (borrower_id, equipment_id, _now(), deposit_paid,
                  donation_amount, expected_return_date, notes))
            loan_id = cursor.lastrowid
            cursor.execute('UPDATE equipment SET status = ? WHERE id = ?',
                           (EquipmentStatus.ON_LOAN, equipment_id))
        return loan_id

    def get_loan(self, loan_id: int) -> dict | None:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT
                l.*,
                b.full_name              AS borrower_name,
                b.id_number              AS borrower_id_number,
                b.primary_phone          AS borrower_phone,
                b.secondary_phone        AS borrower_secondary_phone,
                b.address                AS borrower_address,
                e.item_name              AS equipment_name,
                e.serial_number          AS equipment_serial,
                e.description            AS equipment_description
            FROM loan l
            JOIN borrower  b ON l.borrower_id  = b.id
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.id = ?
        ''', (loan_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_active_loans(self) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT
                l.*,
                b.full_name      AS borrower_name,
                b.id_number      AS borrower_id_number,
                b.primary_phone  AS borrower_phone,
                e.item_name      AS equipment_name,
                e.serial_number  AS equipment_serial
            FROM loan l
            JOIN borrower  b ON l.borrower_id  = b.id
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.loan_status = ?
            ORDER BY l.loan_date DESC
        ''', (LoanStatus.ACTIVE,))
        return [dict(row) for row in cursor.fetchall()]

    def search_active_loans(self, search_term: str) -> list[dict]:
        cursor = self.conn.cursor()
        like = f'%{search_term}%'
        cursor.execute('''
            SELECT
                l.*,
                b.full_name      AS borrower_name,
                b.id_number      AS borrower_id_number,
                b.primary_phone  AS borrower_phone,
                e.item_name      AS equipment_name,
                e.serial_number  AS equipment_serial
            FROM loan l
            JOIN borrower  b ON l.borrower_id  = b.id
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.loan_status = ?
              AND (b.full_name LIKE ? OR b.id_number LIKE ?
                   OR e.item_name LIKE ? OR e.serial_number LIKE ?)
            ORDER BY l.loan_date DESC
        ''', (LoanStatus.ACTIVE, like, like, like, like))
        return [dict(row) for row in cursor.fetchall()]

    def process_return(self, loan_id: int) -> bool:
        """Mark a loan returned and free the equipment.

        B5: only flip equipment back to In-Stock if its current status is
        On-Loan. If something else has taken it (e.g. it was retired) we
        leave the equipment row alone and just close the loan.
        """
        loan = self.get_loan(loan_id)
        if not loan or loan['loan_status'] != LoanStatus.ACTIVE:
            return False

        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE loan
                SET actual_return_date = ?,
                    loan_status        = ?,
                    deposit_status     = ?
                WHERE id = ?
            ''', (_now(), LoanStatus.RETURNED, DepositStatus.RETURNED, loan_id))

            cursor.execute('''
                UPDATE equipment
                SET status = ?
                WHERE id = ? AND status = ?
            ''', (EquipmentStatus.IN_STOCK, loan['equipment_id'],
                  EquipmentStatus.ON_LOAN))
        return True

    def forfeit_deposit(self, loan_id: int) -> bool:
        """Forfeit the deposit and retire the equipment (B4).

        Equipment is flagged retired rather than mutated to status='Lost'.
        Status itself is reset to In-Stock so the row stays internally
        consistent with the CHECK constraint and so a later "Restore"
        is one flag flip rather than a status reset.
        """
        loan = self.get_loan(loan_id)
        if not loan or loan['loan_status'] != LoanStatus.ACTIVE:
            return False

        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE loan
                SET loan_status    = ?,
                    deposit_status = ?
                WHERE id = ?
            ''', (LoanStatus.NOT_RETURNED, DepositStatus.FORFEITED, loan_id))

            cursor.execute('''
                UPDATE equipment
                SET status = ?, is_retired = 1
                WHERE id = ?
            ''', (EquipmentStatus.IN_STOCK, loan['equipment_id']))
        return True

    def get_borrower_loan_history(self, borrower_id: int) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT
                l.*,
                e.item_name     AS equipment_name,
                e.serial_number AS equipment_serial
            FROM loan l
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.borrower_id = ?
            ORDER BY l.loan_date DESC
        ''', (borrower_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_all_loans(self) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT
                l.*,
                b.full_name      AS borrower_name,
                b.id_number      AS borrower_id_number,
                b.primary_phone  AS borrower_phone,
                e.item_name      AS equipment_name,
                e.serial_number  AS equipment_serial
            FROM loan l
            JOIN borrower  b ON l.borrower_id  = b.id
            JOIN equipment e ON l.equipment_id = e.id
            ORDER BY l.loan_date DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Bulk import / export
    # ------------------------------------------------------------------

    def get_dataframe_data(self, table_name: str) -> list[dict]:
        """Fetch all rows from one of the canonical tables, for export."""
        # Whitelist guards an unsanitized identifier (B2-adjacent).
        allowed = {'equipment', 'borrower', 'loan'}
        if table_name not in allowed:
            raise ValueError(f"Unknown table for export: {table_name!r}")
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT * FROM {table_name}')
        return [dict(row) for row in cursor.fetchall()]

    def upsert_borrower_from_dict(self, data: dict) -> None:
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM borrower WHERE id_number = ?',
                       (data['id_number'],))
        if cursor.fetchone():
            cursor.execute('''
                UPDATE borrower
                SET full_name = ?, primary_phone = ?,
                    secondary_phone = ?, address = ?
                WHERE id_number = ?
            ''', (data['full_name'], data['primary_phone'],
                  data.get('secondary_phone'), data.get('address'),
                  data['id_number']))
        else:
            cursor.execute('''
                INSERT INTO borrower (full_name, id_number, primary_phone,
                                      secondary_phone, address, created_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['full_name'], data['id_number'], data['primary_phone'],
                  data.get('secondary_phone'), data.get('address'), _now()))
        self._commit()

    def upsert_equipment_from_dict(self, data: dict) -> None:
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM equipment WHERE serial_number = ?',
                       (data['serial_number'],))
        # Sanitize incoming status — pre-Phase-2 backups may carry 'Lost'.
        status = data.get('status', EquipmentStatus.IN_STOCK)
        is_retired = 1 if status == 'Lost' else int(bool(data.get('is_retired', 0)))
        if status not in EquipmentStatus.ALL:
            status = EquipmentStatus.IN_STOCK

        if cursor.fetchone():
            cursor.execute('''
                UPDATE equipment
                SET item_name = ?, description = ?,
                    deposit_amount = ?, status = ?, is_retired = ?
                WHERE serial_number = ?
            ''', (data['item_name'], data.get('description'),
                  data['deposit_amount'], status, is_retired,
                  data['serial_number']))
        else:
            cursor.execute('''
                INSERT INTO equipment
                    (item_name, description, serial_number, status,
                     deposit_amount, is_retired, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (data['item_name'], data.get('description'),
                  data['serial_number'], status, data['deposit_amount'],
                  is_retired, _now()))
        self._commit()

    def import_loan_record(self, data: dict) -> None:
        """Restore a loan row from a backup spreadsheet.

        B2: previously this f-string'd column names from the Excel header
        straight into the SQL. Now we filter against ALLOWED_LOAN_COLUMNS
        and use a fixed parameterized statement; anything else is dropped.
        """
        clean: dict[str, object] = {
            k: v for k, v in data.items() if k in ALLOWED_LOAN_COLUMNS
        }
        # Required columns to make the row meaningful.
        for required in ('borrower_id', 'equipment_id', 'loan_date',
                         'deposit_paid'):
            if required not in clean or clean[required] in (None, ''):
                raise ValueError(f"Missing required loan column: {required}")

        # Reject unknown status values rather than letting the CHECK trip.
        if clean.get('loan_status') and clean['loan_status'] not in LoanStatus.ALL:
            raise ValueError(f"Invalid loan_status: {clean['loan_status']!r}")
        if clean.get('deposit_status') and clean['deposit_status'] not in DepositStatus.ALL:
            raise ValueError(f"Invalid deposit_status: {clean['deposit_status']!r}")

        keys = list(clean.keys())
        columns = ', '.join(keys)
        placeholders = ', '.join('?' for _ in keys)
        sql = f'INSERT OR REPLACE INTO loan ({columns}) VALUES ({placeholders})'
        cursor = self.conn.cursor()
        cursor.execute(sql, [clean[k] for k in keys])
        self._commit()

    @contextmanager
    def import_from_excel_transaction(self):
        """Wrap a multi-sheet Excel import in a single transaction (B16).

        Use:
            with db.import_from_excel_transaction():
                for row in borrowers: db.upsert_borrower_from_dict(row)
                for row in equipment: db.upsert_equipment_from_dict(row)
                for row in loans:     db.import_loan_record(row)

        Inside the block `_tx_depth > 0`, so the per-call `_commit()`s in
        the upsert/import helpers become no-ops and the outer COMMIT here
        is the one that lands. On exception we ROLLBACK and the partial
        import is discarded.
        """
        assert self.conn is not None, "Database is closed"
        # End any implicit transaction in flight before starting an explicit one.
        self.conn.commit()
        self.conn.execute('BEGIN')
        self._tx_depth += 1
        try:
            yield self.conn
        except Exception:
            self._tx_depth -= 1
            self.conn.execute('ROLLBACK')
            log.exception("Excel import rolled back")
            raise
        else:
            self._tx_depth -= 1
            self.conn.execute('COMMIT')


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
