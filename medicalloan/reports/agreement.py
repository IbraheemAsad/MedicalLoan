"""Loan agreement PDF renderer.

The Phase-3 / pre-refactor implementation drew the agreement with raw
``canvas.drawString`` calls, computing y-coordinates by hand. That
worked but every long Hebrew equipment name or Arabic address that
overflowed the line just ran off the page.

Phase 4 reflows the agreement as a stack of flowables built through
:class:`medicalloan.reports.builder.PdfBuilder`. Long values now wrap
naturally because Paragraph does the linebreaking.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate

from medicalloan.i18n import is_rtl as lang_is_rtl
from medicalloan.reports.builder import PdfBuilder
from medicalloan.reports.fonts import font_for_lang, register_fonts
from medicalloan.reports.strings import get_strings


def _format_loan_date(raw: str) -> str:
    """Convert ``YYYY-MM-DD HH:MM:SS`` to ``DD/MM/YYYY``.

    Falls back to the raw string if the format is unexpected -- we
    don't want a malformed timestamp to crash the report.
    """
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(raw or "")


def _terms(strings: dict[str, str], config: Any) -> list[str]:
    """Read terms from config.ini if present, otherwise use translations."""
    if config and "PDF_Terms" in config:
        section = config["PDF_Terms"]
        return [section.get(f"term{i}", strings[f"term{i}"]) for i in range(1, 5)]
    return [strings[f"term{i}"] for i in range(1, 5)]


def render(
    loan_data: dict[str, Any],
    output_dir: str,
    lang: str,
    config: Any | None = None,
) -> str:
    """Render the loan agreement and return the saved file path.

    Parameters
    ----------
    loan_data:
        Same shape that ``Database.get_loan_with_details`` returns.
    output_dir:
        Where to write the PDF; created on demand by the caller.
    lang:
        Language code -- one of ``en``, ``he``, ``ar``.
    config:
        Optional ``configparser.ConfigParser`` (or compatible) holding
        a ``[PDF_Terms]`` section to override the canned terms text.
    """
    register_fonts()  # idempotent

    s = get_strings(lang)
    font = font_for_lang(lang)
    is_rtl = lang_is_rtl(lang)
    b = PdfBuilder(font_name=font, is_rtl=is_rtl)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"loan_agreement_{loan_data['id']}_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)

    elements: list = []

    # --- Title ----------------------------------------------------------
    elements.append(b.title(s["agreement_title"]))

    # --- Date / loan id header -----------------------------------------
    loan_date = _format_loan_date(loan_data["loan_date"])
    elements.append(b.kv(s["date"], loan_date))
    elements.append(b.kv(s["loan_id"], str(loan_data["id"])))
    elements.append(b.hr())

    # --- Borrower information ------------------------------------------
    elements.append(b.heading(s["borrower_info"]))
    elements.append(b.kv(s["name"], loan_data.get("borrower_name", "")))
    elements.append(b.kv(s["id_number"], loan_data.get("borrower_id_number", "")))
    elements.append(b.kv(s["primary_phone"], loan_data.get("borrower_phone", "")))
    if loan_data.get("borrower_secondary_phone"):
        elements.append(b.kv(s["secondary_phone"], loan_data["borrower_secondary_phone"]))
    if loan_data.get("borrower_address"):
        elements.append(b.kv(s["address"], loan_data["borrower_address"]))
    elements.append(b.hr())

    # --- Equipment information -----------------------------------------
    elements.append(b.heading(s["equipment_info"]))
    elements.append(b.kv(s["equipment_name"], loan_data.get("equipment_name", "")))
    elements.append(b.kv(s["serial_number"], loan_data.get("equipment_serial", "")))
    if loan_data.get("equipment_description"):
        elements.append(b.kv(s["description"], loan_data["equipment_description"]))
    elements.append(b.hr())

    # --- Financial information -----------------------------------------
    elements.append(b.heading(s["financial_info"]))
    deposit = loan_data.get("deposit_paid", 0) or 0
    elements.append(b.kv(s["deposit_amount"], f"\u20aa{deposit:.2f}"))
    donation = loan_data.get("donation_amount", 0) or 0
    if donation > 0:
        elements.append(b.kv(s["donation"], f"\u20aa{donation:.2f}"))

    # --- Terms ----------------------------------------------------------
    elements.append(b.spacer(0.2))
    elements.append(b.heading(s["terms_title"]))
    for term in _terms(s, config):
        elements.append(b.body(term))

    # --- Signatures + footer -------------------------------------------
    elements.append(b.spacer(0.3))
    elements.append(b.signature_line(s["borrower_sig"]))
    elements.append(b.signature_line(s["staff_sig"]))
    elements.append(b.spacer(0.3))
    elements.append(b.small(s["footer1"]))

    SimpleDocTemplate(filepath, pagesize=letter).build(elements)
    return filepath
