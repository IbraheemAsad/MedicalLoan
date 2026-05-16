"""Public orchestrator for the report renderers.

Keeps the same surface the rest of the app already uses (see
``medicalloan/app.py`` and ``medicalloan/ui/views/reports.py``):

* ``ReportGenerator(output_dir, config)``
* ``.generate_loan_agreement(loan_data, lang)``
* ``.generate_inventory_report(equipment_summary, lost_items, lang)``
* ``.generate_loans_report(active_loans, lang)``
* ``.open_pdf(filepath)``

so Phase 4 is a drop-in replacement for the old monolithic class.
"""

from __future__ import annotations

import logging
import os
import platform
import subprocess
from typing import Any

from medicalloan.reports import agreement as _agreement
from medicalloan.reports import inventory as _inventory
from medicalloan.reports import loans as _loans
from medicalloan.reports.fonts import register_fonts
from medicalloan.reports.strings import REPORT_STRINGS

log = logging.getLogger(__name__)


class ReportGenerator:
    """Coordinates the per-report renderers under ``medicalloan.reports``.

    Constructing the generator registers the bundled fonts once. The
    individual render functions each call :func:`register_fonts`
    defensively too, but doing it up front means a missing-fonts
    failure surfaces at app startup rather than the first time someone
    clicks "Generate report".
    """

    # Re-exported so callers that used to do
    # ``from reports import REPORT_STRINGS`` keep working.
    strings = REPORT_STRINGS

    def __init__(self, output_dir: str = "reports", config: Any | None = None) -> None:
        self.output_dir = output_dir
        self.config = config
        os.makedirs(self.output_dir, exist_ok=True)
        register_fonts()

    # ------------------------------------------------------------------
    # Renderers
    # ------------------------------------------------------------------
    def generate_loan_agreement(
        self, loan_data: dict[str, Any], lang: str = "en",
    ) -> str:
        """Render a loan agreement PDF and return the file path."""
        return _agreement.render(loan_data, self.output_dir, lang, self.config)

    def generate_inventory_report(
        self,
        equipment_summary: list[dict[str, Any]],
        lost_items: list[dict[str, Any]],
        lang: str = "en",
    ) -> str:
        """Render the full-inventory PDF and return the file path."""
        return _inventory.render(equipment_summary, lost_items, self.output_dir, lang)

    def generate_loans_report(
        self, active_loans: list[dict[str, Any]], lang: str = "en",
    ) -> str:
        """Render the active-loans PDF and return the file path."""
        return _loans.render(active_loans, self.output_dir, lang)

    # ------------------------------------------------------------------
    # OS integration
    # ------------------------------------------------------------------
    def open_pdf(self, filepath: str) -> None:
        """Open a generated PDF with the platform's default viewer.

        Best-effort: errors are logged but not re-raised. The UI will
        still show the "Report saved at <path>" success dialog so the
        operator can open the file manually if the launch fails.
        """
        system = platform.system()
        try:
            if system == "Windows":
                # ``startfile`` only exists on Windows; mypy would
                # complain in cross-platform mode, hence the getattr.
                getattr(os, "startfile")(filepath)
            elif system == "Darwin":
                subprocess.run(["open", filepath], check=False)
            else:
                subprocess.run(["xdg-open", filepath], check=False)
        except Exception as exc:  # noqa: BLE001 - report-open is best-effort
            log.warning("Could not open PDF %s: %s", filepath, exc)
