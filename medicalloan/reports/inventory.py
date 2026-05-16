"""Full-inventory PDF report.

Two tables:

1. Active inventory grouped by item name with totals row.
2. Lost / retired equipment (only rendered when there's something to
   show).
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate

from medicalloan.i18n import is_rtl as lang_is_rtl
from medicalloan.reports.builder import (
    BRAND_RED,
    PdfBuilder,
    make_data_table,
)
from medicalloan.reports.fonts import font_for_lang, register_fonts
from medicalloan.reports.rtl import maybe_bidi
from medicalloan.reports.strings import get_strings


def _maybe_reverse(row: list[str], is_rtl: bool) -> list[str]:
    """Mirror a row left-to-right for RTL languages.

    Reportlab tables are always laid out LTR; for Hebrew/Arabic we
    reverse each row so the visual order matches the document
    direction.
    """
    return list(reversed(row)) if is_rtl else row


def _format_created_date(raw: Any) -> str:
    """Trim a ``YYYY-MM-DD HH:MM:SS`` timestamp to just the date."""
    try:
        return str(raw).split(" ")[0]
    except (AttributeError, IndexError, TypeError):
        return str(raw or "")


def render(
    equipment_summary: list[dict[str, Any]],
    lost_items: list[dict[str, Any]],
    output_dir: str,
    lang: str,
) -> str:
    """Render the full-inventory report; return the saved file path."""
    register_fonts()

    s = get_strings(lang)
    font = font_for_lang(lang)
    is_rtl = lang_is_rtl(lang)
    b = PdfBuilder(font_name=font, is_rtl=is_rtl)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"inventory_report_{timestamp}.pdf")

    elements: list = [b.title(s["inventory_report_title"])]

    # --- Generated-on line ---------------------------------------------
    elements.append(
        b.body(f"{s['generated_on']}: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    )
    elements.append(b.spacer(0.2))

    # --- Active-inventory table ----------------------------------------
    headers = [
        s["header_eq_name"],
        s["header_total"],
        s["header_in_stock"],
        s["header_on_loan"],
    ]
    data = [_maybe_reverse([maybe_bidi(h, is_rtl) for h in headers], is_rtl)]

    t_items = t_stock = t_loan = 0
    for item in equipment_summary:
        row = [
            maybe_bidi(item["item_name"], is_rtl),
            str(item["total_count"]),
            str(item["in_stock"]),
            str(item["on_loan"]),
        ]
        data.append(_maybe_reverse(row, is_rtl))
        t_items += item["total_count"]
        t_stock += item["in_stock"]
        t_loan += item["on_loan"]

    total_label = maybe_bidi(s["total_row"], is_rtl)
    data.append(_maybe_reverse([total_label, str(t_items), str(t_stock), str(t_loan)], is_rtl))

    elements.append(make_data_table(
        data,
        col_widths=[3.5 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch],
        font_name=font,
        total_row=True,
    ))

    # --- Lost-items section --------------------------------------------
    if lost_items:
        elements.append(b.spacer(0.4))
        elements.append(b.subtitle(s["lost_report_title"]))

        lost_headers = [s["header_eq_name"], s["header_serial"], s["header_date_added"]]
        lost_data = [_maybe_reverse(
            [maybe_bidi(h, is_rtl) for h in lost_headers], is_rtl,
        )]

        for item in lost_items:
            row = [
                maybe_bidi(item["item_name"], is_rtl),
                str(item.get("serial_number", "")),
                _format_created_date(item.get("created_date", "")),
            ]
            lost_data.append(_maybe_reverse(row, is_rtl))

        elements.append(make_data_table(
            lost_data,
            col_widths=[3.5 * inch, 2 * inch, 1.7 * inch],
            font_name=font,
            header_color=BRAND_RED,
        ))

    SimpleDocTemplate(filepath, pagesize=letter).build(elements)
    return filepath
