"""Phase-4 smoke tests for the decomposed ``medicalloan.reports`` package.

These tests verify the public surface stays compatible with what the
rest of the app calls (``ReportGenerator(...).generate_*``) and that
each renderer actually produces a non-empty PDF for every supported
language.

Skipped when ``reportlab`` isn't installed -- the package is a runtime
dependency but our CI lint matrix runs without it.
"""

from __future__ import annotations

import os

import pytest

# Skip the entire module if reportlab (or one of the bidi helpers)
# isn't on this interpreter -- keeps the test relevant on minimal CI
# runners that only do linting.
pytest.importorskip("reportlab")


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

LOAN_DATA = {
    "id": 42,
    "loan_date": "2026-05-16 10:30:00",
    "borrower_name": "Yossi Cohen",
    "borrower_id_number": "123456789",
    "borrower_phone": "0501234567",
    "borrower_secondary_phone": "0507654321",
    "borrower_address": "1 Hayarkon St, Tel Aviv",
    "equipment_name": "Aluminium Walker",
    "equipment_serial": "WLK-2026-001",
    "equipment_description": "Lightweight folding walker",
    "deposit_paid": 200.0,
    "donation_amount": 50.0,
}

EQUIPMENT_SUMMARY = [
    {"item_name": "Walker", "total_count": 5, "in_stock": 3, "on_loan": 2},
    {"item_name": "Wheelchair", "total_count": 4, "in_stock": 1, "on_loan": 3},
]

LOST_ITEMS = [
    {
        "item_name": "Crutches",
        "serial_number": "CR-2024-007",
        "created_date": "2024-03-12 14:05:00",
    },
]

ACTIVE_LOANS = [
    {
        "equipment_name": "Walker",
        "equipment_serial": "WLK-2026-001",
        "borrower_name": "Yossi Cohen",
        "borrower_phone": "0501234567",
        "loan_date": "2026-05-16 10:30:00",
        "deposit_paid": 200,
    },
    {
        "equipment_name": "Wheelchair",
        "equipment_serial": "WC-2026-003",
        "borrower_name": "Sara Levi",
        "borrower_phone": "0529876543",
        "loan_date": "2026-05-15 09:00:00",
        "deposit_paid": 350,
    },
]

LANGS = ["en", "he", "ar"]


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

EXPECTED_METHODS = {
    "generate_loan_agreement",
    "generate_inventory_report",
    "generate_loans_report",
    "open_pdf",
}


def test_public_class_surface_matches_legacy_api():
    from medicalloan.reports import ReportGenerator

    actual = {m for m in dir(ReportGenerator) if not m.startswith("_")}
    missing = EXPECTED_METHODS - actual
    assert not missing, f"ReportGenerator missing methods: {missing}"


def test_legacy_root_module_reexports_class():
    """``from reports import ReportGenerator`` must keep working."""
    from medicalloan.reports import ReportGenerator as PkgClass

    import reports as legacy

    assert legacy.ReportGenerator is PkgClass
    assert legacy.REPORT_STRINGS is not None


def test_strings_have_same_keys_for_all_languages():
    from medicalloan.reports.strings import REPORT_STRINGS

    en_keys = set(REPORT_STRINGS["en"])
    for lang in ("he", "ar"):
        assert set(REPORT_STRINGS[lang]) == en_keys, (
            f"{lang} keys differ from en"
        )


# ---------------------------------------------------------------------------
# Font registration
# ---------------------------------------------------------------------------

def test_register_fonts_is_idempotent():
    from medicalloan.reports.fonts import register_fonts, reset_for_tests

    reset_for_tests()
    register_fonts()
    register_fonts()  # second call must not raise


def test_font_for_lang_uses_lang_font_map():
    from medicalloan.reports.fonts import (
        ARABIC_FONT_NAME,
        DEFAULT_LATIN_FONT,
        HEBREW_FONT_NAME,
        font_for_lang,
    )

    assert font_for_lang("he") == HEBREW_FONT_NAME
    assert font_for_lang("ar") == ARABIC_FONT_NAME
    assert font_for_lang("en") == DEFAULT_LATIN_FONT
    assert font_for_lang("klingon") == DEFAULT_LATIN_FONT


# ---------------------------------------------------------------------------
# Render smoke tests
# ---------------------------------------------------------------------------

def _make_generator(tmp_path):
    from medicalloan.reports import ReportGenerator

    return ReportGenerator(output_dir=str(tmp_path))


@pytest.mark.parametrize("lang", LANGS)
def test_loan_agreement_renders_non_empty_pdf(tmp_path, lang):
    gen = _make_generator(tmp_path)
    path = gen.generate_loan_agreement(LOAN_DATA, lang)

    assert os.path.isfile(path)
    assert os.path.getsize(path) > 0
    with open(path, "rb") as fh:
        assert fh.read(4) == b"%PDF"


@pytest.mark.parametrize("lang", LANGS)
def test_inventory_report_renders_non_empty_pdf(tmp_path, lang):
    gen = _make_generator(tmp_path)
    path = gen.generate_inventory_report(EQUIPMENT_SUMMARY, LOST_ITEMS, lang)

    assert os.path.isfile(path)
    assert os.path.getsize(path) > 0
    with open(path, "rb") as fh:
        assert fh.read(4) == b"%PDF"


@pytest.mark.parametrize("lang", LANGS)
def test_loans_report_renders_non_empty_pdf(tmp_path, lang):
    gen = _make_generator(tmp_path)
    path = gen.generate_loans_report(ACTIVE_LOANS, lang)

    assert os.path.isfile(path)
    assert os.path.getsize(path) > 0


def test_loans_report_with_no_active_loans(tmp_path):
    gen = _make_generator(tmp_path)
    path = gen.generate_loans_report([], "en")
    assert os.path.getsize(path) > 0


def test_inventory_report_with_no_lost_items(tmp_path):
    gen = _make_generator(tmp_path)
    path = gen.generate_inventory_report(EQUIPMENT_SUMMARY, [], "en")
    assert os.path.getsize(path) > 0


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------

def test_pdf_builder_returns_paragraphs_for_text_methods():
    from reportlab.platypus import HRFlowable, Paragraph, Spacer

    from medicalloan.reports.builder import PdfBuilder
    from medicalloan.reports.fonts import DEFAULT_LATIN_FONT, register_fonts

    register_fonts()
    b = PdfBuilder(font_name=DEFAULT_LATIN_FONT, is_rtl=False)

    assert isinstance(b.title("Hello"), Paragraph)
    assert isinstance(b.subtitle("Hello"), Paragraph)
    assert isinstance(b.heading("Hello"), Paragraph)
    assert isinstance(b.body("Hello"), Paragraph)
    assert isinstance(b.kv("Name", "Walker"), Paragraph)
    assert isinstance(b.spacer(0.1), Spacer)
    assert isinstance(b.hr(), HRFlowable)


def test_make_data_table_accepts_total_row_flag(tmp_path):
    from reportlab.lib.units import inch
    from reportlab.platypus import Table

    from medicalloan.reports.builder import make_data_table
    from medicalloan.reports.fonts import DEFAULT_LATIN_FONT, register_fonts

    register_fonts()
    data = [
        ["Name", "Total"],
        ["Walker", "5"],
        ["TOTAL", "5"],
    ]
    table = make_data_table(
        data, [3 * inch, 1 * inch],
        font_name=DEFAULT_LATIN_FONT, total_row=True,
    )
    assert isinstance(table, Table)


# ---------------------------------------------------------------------------
# bidi helpers
# ---------------------------------------------------------------------------

def test_bidi_shape_is_safe_on_empty_and_latin():
    from medicalloan.reports.rtl import bidi_shape, maybe_bidi

    assert bidi_shape("") == ""
    # Latin strings come out unchanged in either direction.
    assert maybe_bidi("Hello", is_rtl=False) == "Hello"
    # On RTL, empty string round-trips.
    assert maybe_bidi("", is_rtl=True) == ""
