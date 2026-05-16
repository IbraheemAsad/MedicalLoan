"""Active-loans PDF report."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate

from medicalloan.i18n import is_rtl as lang_is_rtl
from medicalloan.reports.builder import PdfBuilder, make_data_table
from medicalloan.reports.fonts import font_for_lang, register_fonts
from medicalloan.reports.rtl import maybe_bidi
from medicalloan.reports.strings import get_strings


def _maybe_reverse(row: list[str], is_rtl: bool) -> list[str]:
    return list(reversed(row)) if is_rtl else row


def _format_loan_date(raw: str) -> str:
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(raw or "")


def render(
    active_loans: list[dict[str, Any]],
    output_dir: str,
    lang: str,
) -> str:
    """Render the active-loans report; return the saved file path."""
    register_fonts()

    s = get_strings(lang)
    font = font_for_lang(lang)
    is_rtl = lang_is_rtl(lang)
    b = PdfBuilder(font_name=font, is_rtl=is_rtl)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"loans_report_{timestamp}.pdf")

    elements: list = [
        b.title(s["loans_report_title"]),
        b.body(f"{s['generated_on']}: {datetime.now().strftime('%d/%m/%Y %H:%M')}"),
        b.spacer(0.1),
        b.kv(s["total_active_loans"], str(len(active_loans))),
        b.spacer(0.2),
    ]

    if not active_loans:
        elements.append(b.body(s["no_active_loans"]))
    else:
        headers = [
            s["header_eq_name"],
            s["header_serial"],
            s["header_borrower"],
            s["header_phone"],
            s["header_loan_date"],
            s["header_deposit"],
        ]
        data = [_maybe_reverse([maybe_bidi(h, is_rtl) for h in headers], is_rtl)]

        for loan in active_loans:
            deposit = loan.get("deposit_paid", 0) or 0
            row = [
                maybe_bidi(loan.get("equipment_name", ""), is_rtl),
                str(loan.get("equipment_serial", "")),
                maybe_bidi(loan.get("borrower_name", ""), is_rtl),
                str(loan.get("borrower_phone", "")),
                _format_loan_date(loan.get("loan_date", "")),
                f"\u20aa{deposit:.0f}",
            ]
            data.append(_maybe_reverse(row, is_rtl))

        elements.append(make_data_table(
            data,
            col_widths=[
                1.5 * inch, 1 * inch, 1.3 * inch,
                1 * inch, 0.9 * inch, 0.7 * inch,
            ],
            font_name=font,
        ))

    SimpleDocTemplate(filepath, pagesize=letter).build(elements)
    return filepath
