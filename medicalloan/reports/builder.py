"""Flowable + style helpers shared by the report renderers.

The plan calls for two things from this module:

* A tiny ``PdfBuilder`` that hides the ``if is_rtl`` branches that
  used to be sprinkled all over ``reports.py``. Methods like
  :py:meth:`PdfBuilder.kv` and :py:meth:`PdfBuilder.heading` always
  return a Flowable (Paragraph / Spacer / HR) -- so callers can build
  the agreement out of ``elements.append(b.kv(...))`` calls instead of
  ``canvas.drawString`` / ``canvas.drawRightString`` pairs.

* A ``TableStyleBuilder`` factory for the inventory / loans tables so
  the long ``TableStyle([...])`` literals don't get duplicated.

Sticking to flowables (Paragraph + Table) means Arabic addresses and
long Hebrew equipment names wrap cleanly without us having to compute
text widths manually -- one of the motivating goals of Phase 4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from medicalloan.reports.fonts import bold_font_for
from medicalloan.reports.rtl import maybe_bidi


# ---------------------------------------------------------------------------
# Brand palette -- kept in one place so tweaking colours doesn't mean a
# global find-and-replace across every report.
# ---------------------------------------------------------------------------

BRAND_BLUE: Final = colors.HexColor("#1f4788")
BRAND_BLUE_LIGHT: Final = colors.HexColor("#d9e2f3")
BRAND_RED: Final = colors.firebrick
HEADER_TEXT: Final = colors.whitesmoke


# ---------------------------------------------------------------------------
# PdfBuilder
# ---------------------------------------------------------------------------

@dataclass
class PdfBuilder:
    """Builds Paragraph flowables with the right font + alignment.

    Created once per render with the language's font and direction;
    every method returns a new flowable so the rendering modules just
    do ``elements.append(b.heading(...))``.
    """

    font_name: str
    is_rtl: bool

    # Cached -- ``getSampleStyleSheet()`` is a non-trivial call.
    def __post_init__(self) -> None:
        self._sheet = getSampleStyleSheet()
        self._bold_font = bold_font_for(self.font_name)
        self._align_default = TA_RIGHT if self.is_rtl else TA_LEFT

    # ----- core building blocks ----------------------------------------
    def _shape(self, text: str) -> str:
        return maybe_bidi(text, self.is_rtl)

    def title(self, text: str, *, color=BRAND_BLUE) -> Paragraph:
        """Big centred title -- one per page."""
        style = ParagraphStyle(
            "PdfBuilderTitle",
            parent=self._sheet["Heading1"],
            fontName=self._bold_font,
            fontSize=18,
            textColor=color,
            alignment=TA_CENTER,
            spaceAfter=18,
        )
        return Paragraph(self._shape(text), style)

    def subtitle(self, text: str, *, color=BRAND_RED) -> Paragraph:
        """Section subtitle (e.g. 'Lost / Retired Equipment')."""
        style = ParagraphStyle(
            "PdfBuilderSubtitle",
            parent=self._sheet["Heading2"],
            fontName=self._bold_font,
            fontSize=14,
            textColor=color,
            alignment=self._align_default,
            spaceAfter=10,
        )
        return Paragraph(self._shape(text), style)

    def heading(self, text: str) -> Paragraph:
        """In-flow heading (Borrower Information / Equipment / etc.)."""
        style = ParagraphStyle(
            "PdfBuilderHeading",
            parent=self._sheet["Heading3"],
            fontName=self._bold_font,
            fontSize=13,
            alignment=self._align_default,
            spaceBefore=8,
            spaceAfter=4,
        )
        return Paragraph(self._shape(text), style)

    def body(self, text: str) -> Paragraph:
        """Regular body line."""
        style = ParagraphStyle(
            "PdfBuilderBody",
            parent=self._sheet["Normal"],
            fontName=self.font_name,
            fontSize=11,
            alignment=self._align_default,
            spaceAfter=2,
        )
        return Paragraph(self._shape(text), style)

    def small(self, text: str) -> Paragraph:
        """Small footer-style line."""
        style = ParagraphStyle(
            "PdfBuilderSmall",
            parent=self._sheet["Normal"],
            fontName=self.font_name,
            fontSize=9,
            alignment=TA_CENTER,
        )
        return Paragraph(self._shape(text), style)

    def kv(self, label: str, value: str) -> Paragraph:
        """Render a labelled value line (``Name: Walker``).

        The label is bold; the value is regular. Direction follows the
        builder's ``is_rtl`` setting -- callers don't have to think
        about which side the value goes on.
        """
        text = f"<b>{label}:</b> {value}"
        style = ParagraphStyle(
            "PdfBuilderKv",
            parent=self._sheet["Normal"],
            fontName=self.font_name,
            fontSize=11,
            alignment=self._align_default,
            spaceAfter=2,
        )
        return Paragraph(self._shape(text), style)

    # ----- whitespace / dividers ---------------------------------------
    def spacer(self, height: float = 0.2) -> Spacer:
        """Vertical whitespace, in inches."""
        return Spacer(1, height * inch)

    def hr(self) -> HRFlowable:
        """Horizontal rule across the page width."""
        return HRFlowable(width="100%", thickness=0.5, color=colors.grey,
                          spaceBefore=4, spaceAfter=4)

    def signature_line(self, label: str) -> Paragraph:
        """Render the ``Borrower Signature: ____ Date: ____`` line."""
        text = f"{label}: _______________________&nbsp;&nbsp;&nbsp;&nbsp;Date: _____________"
        style = ParagraphStyle(
            "PdfBuilderSig",
            parent=self._sheet["Normal"],
            fontName=self.font_name,
            fontSize=11,
            alignment=self._align_default,
            spaceBefore=24,
        )
        return Paragraph(self._shape(text), style)


# ---------------------------------------------------------------------------
# Table styling
# ---------------------------------------------------------------------------

def make_data_table(
    data: list[list[str]],
    col_widths: list[float],
    *,
    font_name: str,
    header_color=BRAND_BLUE,
    total_row: bool = False,
) -> Table:
    """Build a styled report table.

    Parameters
    ----------
    data:
        Header row + data rows + (optional) totals row.
    col_widths:
        Column widths in points (callers pass ``inch * x``).
    font_name:
        Body font; the bold variant is used for the header (and totals
        row when ``total_row=True``).
    header_color:
        Header background. Use :data:`BRAND_RED` for the lost-items
        table.
    total_row:
        When true, the last row is rendered as a totals row (light
        blue background, bold font).
    """
    bold = bold_font_for(font_name)

    style_cmds: list[tuple] = [
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_TEXT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), bold),
        ("FONTNAME", (0, 1), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]

    if total_row:
        style_cmds.extend([
            ("BACKGROUND", (0, -1), (-1, -1), BRAND_BLUE_LIGHT),
            ("FONTNAME", (0, -1), (-1, -1), bold),
        ])

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle(style_cmds))
    return table
