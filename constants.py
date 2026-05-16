"""
Domain constants and status values for Medical Equipment Loan Management System.

Using plain string-valued classes (not Enum) so the values flow into SQLite
without needing custom adapters and are easy to inspect in raw queries.

These string values are CANONICAL: they must match what is stored in the
database (`equipment.status`, `loan.loan_status`, `loan.deposit_status`).
Changing a value here is a schema migration.
"""


class EquipmentStatus:
    """Operational state of a piece of equipment.

    NOTE: 'Retired' (a permanent flag indicating the item is no longer
    loanable, e.g. after a forfeited loan) is tracked on
    `equipment.is_retired` instead of overloading this status field.
    See B4 in the improvement plan.
    """
    IN_STOCK = 'In-Stock'
    ON_LOAN = 'On-Loan'

    ALL = (IN_STOCK, ON_LOAN)


class LoanStatus:
    """Lifecycle state of a loan record."""
    ACTIVE = 'Active'
    RETURNED = 'Returned'
    NOT_RETURNED = 'Not Returned'  # forfeited / equipment never came back

    ALL = (ACTIVE, RETURNED, NOT_RETURNED)


class DepositStatus:
    """Lifecycle state of the deposit attached to a loan."""
    HELD = 'Held'
    RETURNED = 'Returned'
    FORFEITED = 'Forfeited'

    ALL = (HELD, RETURNED, FORFEITED)


# ---------------------------------------------------------------------------
# Allowlists for tables and columns that may be interpolated into SQL.
# These exist to make import paths (Excel restore) safe by construction:
# anything not on the list is silently dropped before reaching `cursor.execute`.
# See B2 in the improvement plan.
# ---------------------------------------------------------------------------

ALLOWED_TABLE_NAMES = ('equipment', 'borrower', 'loan')

ALLOWED_LOAN_COLUMNS = (
    'id',
    'borrower_id',
    'equipment_id',
    'loan_date',
    'deposit_paid',
    'deposit_status',
    'expected_return_date',
    'actual_return_date',
    'donation_amount',
    'loan_status',
    'notes',
)
