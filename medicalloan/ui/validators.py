"""Tk entry validation predicates.

These return ``True``/``False`` and are meant to be wrapped via
``root.register(callable)`` and used as ``validatecommand`` on a
``ttk.Entry`` with ``validate='key'``. ``%P`` is the proposed value
of the entry *after* the keystroke would be applied.
"""

from __future__ import annotations


def numbers_only(p: str) -> bool:
    """Allow digits, the empty string, or a single ``-`` literal.

    The single ``-`` is the override sentinel the rest of the app
    uses to mean "skip / not provided" (see ``id_number`` validation
    in the loan flow).
    """
    if p in ("", "-"):
        return True
    return p.isdigit()


def id_input(p: str) -> bool:
    """Allow up to 9 digits, the empty string, or a single ``-``.

    Israeli ID numbers are exactly 9 digits; this only enforces the
    upper bound during typing -- the final length check happens in
    ``confirm_loan_logic``/``add_borrower_action`` so users can still
    *delete* down to a shorter value while editing.
    """
    if p in ("", "-"):
        return True
    return p.isdigit() and len(p) <= 9
