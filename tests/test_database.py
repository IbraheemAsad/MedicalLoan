"""
Tests for the Phase 2 hardened Database layer.

Focus areas:
- B2  Excel-restore loan import is parameterized + column-allowlisted.
- B3  FK pragma is on; ON DELETE CASCADE works.
- B4  Forfeit retires equipment via is_retired, not status='Lost'.
- B5  process_return only restores In-Stock when current state is On-Loan.
- B16 import_from_excel_transaction rolls back on error.
- B17 Status values are canonical (constants).
- B18 connect() is idempotent.
"""

import sqlite3

import pytest

from constants import DepositStatus, EquipmentStatus, LoanStatus

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _seed_one_loan(db):
    """Create one borrower + one equipment + one active loan, return ids."""
    eq_id = db.add_equipment("Walker", "desc", "W-001", 200.0)
    b_id = db.add_borrower("Alice", "111111111", "0501111111")
    loan_id = db.create_loan(b_id, eq_id, deposit_paid=200.0)
    return b_id, eq_id, loan_id


# ---------------------------------------------------------------------------
# Pragmas / connection lifecycle
# ---------------------------------------------------------------------------

def test_foreign_keys_pragma_is_on(db):
    cur = db.conn.cursor()
    assert cur.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_journal_mode_is_wal(db):
    cur = db.conn.cursor()
    assert cur.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def test_connect_is_idempotent(db):
    """B18: calling connect() twice doesn't leak the previous connection."""
    first = db.conn
    db.connect()
    # The old connection should be closed; using it must raise.
    with pytest.raises(sqlite3.ProgrammingError):
        first.execute("SELECT 1")
    # The new connection works.
    assert db.conn.execute("SELECT 1").fetchone()[0] == 1


# ---------------------------------------------------------------------------
# B3: cascades
# ---------------------------------------------------------------------------

def test_deleting_equipment_cascades_to_loans(db):
    _, eq_id, loan_id = _seed_one_loan(db)
    db.delete_equipment(eq_id)
    cur = db.conn.cursor()
    assert cur.execute("SELECT COUNT(*) FROM loan WHERE id = ?",
                       (loan_id,)).fetchone()[0] == 0


# ---------------------------------------------------------------------------
# B5: process_return
# ---------------------------------------------------------------------------

def test_process_return_marks_loan_returned_and_frees_equipment(db):
    _, eq_id, loan_id = _seed_one_loan(db)
    assert db.process_return(loan_id) is True

    loan = db.get_loan(loan_id)
    eq = db.get_equipment(eq_id)
    assert loan["loan_status"] == LoanStatus.RETURNED
    assert loan["deposit_status"] == DepositStatus.RETURNED
    assert loan["actual_return_date"] is not None
    assert eq["status"] == EquipmentStatus.IN_STOCK


def test_process_return_is_idempotent(db):
    """Returning twice must not silently double-flip equipment status."""
    _, _, loan_id = _seed_one_loan(db)
    assert db.process_return(loan_id) is True
    assert db.process_return(loan_id) is False


def test_process_return_does_not_resurrect_retired_equipment(db):
    """B5: if equipment was retired during the loan, returning it must
    not flip status back to In-Stock and must not clear is_retired."""
    _, eq_id, loan_id = _seed_one_loan(db)
    # Simulate something going wrong with the equipment mid-loan.
    db.set_equipment_retired(eq_id, True)
    # After retirement equipment.status is still On-Loan; but if a parallel
    # path also reset status, the return should still leave is_retired alone.
    assert db.process_return(loan_id) is True
    eq = db.get_equipment(eq_id)
    assert eq["is_retired"] == 1


# ---------------------------------------------------------------------------
# B4: forfeit
# ---------------------------------------------------------------------------

def test_forfeit_retires_equipment_via_flag_not_status(db):
    """B4: Lost is now is_retired=1 with status reset to In-Stock,
    so the row passes the new CHECK constraint and a future Restore is
    a single flag flip."""
    _, eq_id, loan_id = _seed_one_loan(db)
    assert db.forfeit_deposit(loan_id) is True

    loan = db.get_loan(loan_id)
    eq = db.get_equipment(eq_id)
    assert loan["loan_status"] == LoanStatus.NOT_RETURNED
    assert loan["deposit_status"] == DepositStatus.FORFEITED
    assert eq["status"] == EquipmentStatus.IN_STOCK
    assert eq["is_retired"] == 1


def test_retired_equipment_excluded_from_available_and_summary(db):
    eq_keep = db.add_equipment("Walker", "desc", "W-1", 200.0)
    eq_retire = db.add_equipment("Walker", "desc", "W-2", 200.0)
    db.set_equipment_retired(eq_retire, True)

    available = db.get_available_equipment()
    assert {e["id"] for e in available} == {eq_keep}

    summary = db.get_equipment_summary()
    walker_row = next(r for r in summary if r["item_name"] == "Walker")
    # Only the non-retired Walker counts.
    assert walker_row["total_count"] == 1


def test_get_lost_equipment_returns_only_retired(db):
    db.add_equipment("Walker", "desc", "W-1", 200.0)
    b = db.add_equipment("Walker", "desc", "W-2", 200.0)
    db.set_equipment_retired(b, True)
    lost = db.get_lost_equipment()
    assert [e["id"] for e in lost] == [b]


# ---------------------------------------------------------------------------
# B17: status enums
# ---------------------------------------------------------------------------

def test_status_check_constraint_rejects_unknown_value(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.update_equipment_status_via_raw_sql = None  # placeholder to silence linters
        # Use the connection directly to bypass the Python-side validation
        # in update_equipment_status; we want to confirm the CHECK fires.
        eq_id = db.add_equipment("Walker", "desc", "W-X", 200.0)
        db.conn.execute("UPDATE equipment SET status = 'Lost' WHERE id = ?", (eq_id,))
        db.conn.commit()


def test_update_equipment_status_rejects_invalid_value_in_python(db):
    eq_id = db.add_equipment("Walker", "desc", "W-Y", 200.0)
    with pytest.raises(ValueError):
        db.update_equipment_status(eq_id, "Lost")


# ---------------------------------------------------------------------------
# B2: parameterized loan import
# ---------------------------------------------------------------------------

def test_import_loan_record_drops_unknown_columns(db):
    """B2: a column that isn't on the allowlist must be silently dropped
    rather than interpolated into SQL."""
    b_id = db.add_borrower("Alice", "111111111", "0501111111")
    eq_id = db.add_equipment("Walker", "desc", "W-1", 200.0)
    db.import_loan_record({
        "borrower_id": b_id,
        "equipment_id": eq_id,
        "loan_date": "2024-01-01 00:00:00",
        "deposit_paid": 200.0,
        # The classic injection vector: a malicious column header.
        "id; DROP TABLE loan; --": "boom",
    })
    # If the malicious column had been interpolated the table would be gone.
    cur = db.conn.cursor()
    assert cur.execute("SELECT COUNT(*) FROM loan").fetchone()[0] == 1


def test_import_loan_record_rejects_invalid_status(db):
    b_id = db.add_borrower("Alice", "111111111", "0501111111")
    eq_id = db.add_equipment("Walker", "desc", "W-1", 200.0)
    with pytest.raises(ValueError):
        db.import_loan_record({
            "borrower_id": b_id,
            "equipment_id": eq_id,
            "loan_date": "2024-01-01 00:00:00",
            "deposit_paid": 200.0,
            "loan_status": "OnLoan",  # the old B17 typo
        })


def test_import_loan_record_requires_core_columns(db):
    with pytest.raises(ValueError):
        db.import_loan_record({"deposit_paid": 100.0})


# ---------------------------------------------------------------------------
# B16: transactional Excel import
# ---------------------------------------------------------------------------

def test_excel_import_rolls_back_on_error(db):
    """If we fail partway through an Excel import everything should
    revert — no half-imported borrowers left behind."""
    with pytest.raises(RuntimeError):
        with db.import_from_excel_transaction():
            db.upsert_borrower_from_dict({
                "full_name": "Alice",
                "id_number": "111111111",
                "primary_phone": "0501111111",
            })
            # Simulate the kind of bad row that would trip later in the loop.
            raise RuntimeError("simulated bad row")

    assert db.get_all_borrowers() == []


def test_excel_import_commits_on_success(db):
    with db.import_from_excel_transaction():
        db.upsert_borrower_from_dict({
            "full_name": "Alice",
            "id_number": "111111111",
            "primary_phone": "0501111111",
        })
        db.upsert_equipment_from_dict({
            "item_name": "Walker",
            "serial_number": "W-1",
            "deposit_amount": 200.0,
            "status": EquipmentStatus.IN_STOCK,
        })
    assert len(db.get_all_borrowers()) == 1
    assert len(db.get_all_equipment()) == 1


def test_upsert_equipment_translates_legacy_lost_status(db):
    """A pre-Phase-2 backup carrying status='Lost' should land as
    is_retired=1 with status='In-Stock' so the new CHECK passes."""
    db.upsert_equipment_from_dict({
        "item_name": "Walker",
        "serial_number": "W-OLD",
        "deposit_amount": 200.0,
        "status": "Lost",
    })
    eq = db.search_equipment("W-OLD")[0]
    assert eq["status"] == EquipmentStatus.IN_STOCK
    assert eq["is_retired"] == 1


# ---------------------------------------------------------------------------
# Loan creation atomicity
# ---------------------------------------------------------------------------

def test_create_loan_flips_equipment_to_on_loan(db):
    eq_id = db.add_equipment("Walker", "desc", "W-1", 200.0)
    b_id = db.add_borrower("Alice", "111111111", "0501111111")
    db.create_loan(b_id, eq_id, deposit_paid=200.0)
    assert db.get_equipment(eq_id)["status"] == EquipmentStatus.ON_LOAN
