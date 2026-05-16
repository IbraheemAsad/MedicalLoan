"""Backwards-compat shim for the Medical Equipment Loan reports module.

Phase 4 of the improvement plan moved the report generators into the
``medicalloan.reports`` subpackage. This file is now a thin re-export
so the existing ``from reports import ReportGenerator`` callsite in
``medicalloan/app.py``, the PyInstaller spec, and any external scripts
keep working unchanged.

For new code prefer ``from medicalloan.reports import ReportGenerator``.
"""

from medicalloan.reports import REPORT_STRINGS, ReportGenerator

__all__ = ["ReportGenerator", "REPORT_STRINGS"]
