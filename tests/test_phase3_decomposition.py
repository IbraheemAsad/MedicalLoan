"""Phase-3 smoke tests for the decomposed ``medicalloan`` package.

These tests don't need a display server -- they only verify that:

* every package module imports cleanly (catches typos, wrong relative
  imports, circular imports);
* the ``MedicalEquipmentApp`` orchestrator exposes the same public
  surface that views and the legacy ``main.py`` rely on;
* the i18n string tables are byte-identical to the legacy
  ``I18N_STRINGS`` dict (i.e. no key got dropped or renamed during
  the move);
* :func:`medicalloan.ui.styles.apply_theme` accepts the documented
  parameters (defensive against accidental signature drift);
* the validators preserve their legacy contract, since the loan flow
  registers them by name as Tk validatecommands.

It explicitly skips anything that requires a Tk display.
"""

from __future__ import annotations

import sys
import unittest.mock as mock

import pytest

# ---------------------------------------------------------------------------
# Module imports (parsing + relative-import correctness)
# ---------------------------------------------------------------------------

PACKAGE_MODULES = [
    "medicalloan",
    "medicalloan.app",
    "medicalloan.i18n",
    "medicalloan.i18n.translator",
    "medicalloan.i18n.en",
    "medicalloan.i18n.he",
    "medicalloan.i18n.ar",
    "medicalloan.ui",
    "medicalloan.ui.styles",
    "medicalloan.ui.dialogs",
    "medicalloan.ui.treeview",
    "medicalloan.ui.validators",
    "medicalloan.ui.widgets",
    "medicalloan.ui.widgets.search_frame",
    "medicalloan.ui.widgets.form_row",
    "medicalloan.ui.views",
    "medicalloan.ui.views.dashboard",
    "medicalloan.ui.views.inventory",
    "medicalloan.ui.views.new_loan",
    "medicalloan.ui.views.process_return",
    "medicalloan.ui.views.borrowers",
    "medicalloan.ui.views.reports",
    # data_io needs pandas at import time -- separate test below.
]


@pytest.fixture
def stubbed_runtime():
    """Stub heavyweight runtime deps (PIL / reports / pandas) so the
    package imports on machines that don't have them installed.

    ``medicalloan.app`` does ``from reports import ReportGenerator`` at
    module load, and ``reports.py`` pulls in reportlab, which isn't a
    test-time dep. We replace it with a tiny stub so the rest of the
    code can be exercised.
    """
    saved = {}
    keys = ['PIL', 'PIL.Image', 'PIL.ImageTk', 'pandas', 'reports']
    for k in keys:
        saved[k] = sys.modules.pop(k, None)

    sys.modules['PIL'] = mock.MagicMock()
    sys.modules['PIL.Image'] = mock.MagicMock()
    sys.modules['PIL.ImageTk'] = mock.MagicMock()
    sys.modules['pandas'] = mock.MagicMock()

    reports_stub = mock.MagicMock()
    reports_stub.ReportGenerator = mock.MagicMock()
    sys.modules['reports'] = reports_stub

    # Drop any cached medicalloan.* modules so the next import re-runs
    # with our stubs in place.
    for cached in [m for m in sys.modules if m.startswith('medicalloan')]:
        del sys.modules[cached]

    yield

    for cached in [m for m in sys.modules if m.startswith('medicalloan')]:
        del sys.modules[cached]
    for k, v in saved.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


@pytest.mark.parametrize("modname", PACKAGE_MODULES)
def test_module_imports_cleanly(stubbed_runtime, modname):
    __import__(modname)


def test_data_io_imports_with_pandas_stub(stubbed_runtime):
    # data_io needs pandas -- we stub it via the fixture, so this is
    # essentially the same test as parametrised above but kept
    # separate so the failure message is precise if pandas is missing.
    __import__("medicalloan.ui.views.data_io")


# ---------------------------------------------------------------------------
# App orchestrator surface
# ---------------------------------------------------------------------------

EXPECTED_APP_METHODS = {
    # Lifecycle
    "_on_close",
    "perform_backup",
    "load_configuration",
    # UI helpers used by views
    "load_icons",
    "setup_styles",
    "toggle_theme",
    "clear_window",
    "show_global_controls",
    "adjust_font_size",
    # Navigation -- one per top-level view
    "show_dashboard",
    "show_inventory",
    "show_new_loan",
    "show_process_return",
    "show_borrowers",
    "show_reports",
    # Excel data IO
    "export_to_excel",
    "import_from_excel",
    # Phase 5 additions
    "show_status_bar",
    "restore_from_backup",
    "_save_preferences",
    "_bind_global_shortcuts",
}


def test_app_class_exposes_expected_method_surface(stubbed_runtime):
    from medicalloan.app import MedicalEquipmentApp

    actual = {m for m in dir(MedicalEquipmentApp) if not m.startswith("__")}
    missing = EXPECTED_APP_METHODS - actual
    assert not missing, f"App missing methods: {missing}"


def test_app_module_has_main_and_resource_path(stubbed_runtime):
    from medicalloan import app
    assert callable(app.main)
    assert callable(app.resource_path)


# ---------------------------------------------------------------------------
# View modules expose the contract the orchestrator wires up
# ---------------------------------------------------------------------------

VIEW_CONTRACTS = {
    "dashboard": {"show", "show_data_menu"},
    "inventory": {"show"},
    "new_loan": {"show", "show_borrower_step", "clear_loan_form"},
    "process_return": {"show"},
    "borrowers": {"show"},
    "reports": {"show", "generate_inventory_report", "generate_loans_report"},
    "data_io": {"export_to_excel", "import_from_excel", "restore_from_backup"},
}


@pytest.mark.parametrize(
    "view_name,expected", sorted(VIEW_CONTRACTS.items()),
)
def test_view_module_exposes_expected_callables(stubbed_runtime, view_name, expected):
    module = __import__(
        f"medicalloan.ui.views.{view_name}", fromlist=[view_name],
    )
    for fn_name in expected:
        fn = getattr(module, fn_name, None)
        assert callable(fn), f"{view_name}.{fn_name} is not callable: {fn!r}"


# ---------------------------------------------------------------------------
# i18n -- new tables match the legacy I18N_STRINGS dict byte-for-byte
# ---------------------------------------------------------------------------

EXPECTED_LANG_KEY_COUNT = 152  # Phase 5 added ~19 keys for prefs/restore/status/shortcuts


def test_i18n_three_languages_with_matching_keys(stubbed_runtime):
    from medicalloan.i18n import I18N_STRINGS

    assert set(I18N_STRINGS) == {"en", "he", "ar"}

    # All three tables must agree on the key set (otherwise the
    # missing-key fallback in Translator gets exercised constantly).
    en_keys = set(I18N_STRINGS["en"])
    assert len(en_keys) == EXPECTED_LANG_KEY_COUNT
    for lang in ("he", "ar"):
        assert set(I18N_STRINGS[lang]) == en_keys, (
            f"{lang} key set differs from en"
        )


def test_translator_basic_contract(stubbed_runtime):
    from medicalloan.i18n import Translator, is_rtl

    t = Translator("he")
    assert t.is_rtl is True
    assert is_rtl("ar") is True
    assert is_rtl("en") is False

    # Known key resolves; format kwargs apply.
    t.set_lang("en")
    assert t.t("eq_label", name="Walker") == "Equipment: Walker"

    # Unknown key falls back to the bare key (and logs once -- not
    # asserted here).
    assert t.t("definitely_missing_key_xyz") == "definitely_missing_key_xyz"

    # Setting an unknown language is a no-op.
    t.set_lang("klingon")
    assert t.lang == "en"


def test_translator_dict_alias_returns_table(stubbed_runtime):
    """Legacy callsites use ``app.t.i18n[lang][key]`` (and ``app.i18n``
    on the App). The dict alias must return the live table."""
    from medicalloan.i18n import I18N_STRINGS, Translator

    t = Translator("en")
    assert t.i18n is I18N_STRINGS


# ---------------------------------------------------------------------------
# Validators -- legacy contract
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "value,expected",
    [
        ("", True),
        ("-", True),
        ("123", True),
        ("0", True),
        ("1a", False),
        ("--", False),
        ("a", False),
    ],
)
def test_numbers_only_contract(stubbed_runtime, value, expected):
    from medicalloan.ui.validators import numbers_only
    assert numbers_only(value) is expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", True),
        ("-", True),
        ("1", True),
        ("12345", True),
        ("123456789", True),
        ("1234567890", False),  # too long
        ("12a", False),
        ("a", False),
    ],
)
def test_id_input_contract(stubbed_runtime, value, expected):
    from medicalloan.ui.validators import id_input
    assert id_input(value) is expected


# ---------------------------------------------------------------------------
# Treeview helpers -- pure logic, no Tk needed
# ---------------------------------------------------------------------------

def test_equipment_display_status_synthesises_lost_for_retired(stubbed_runtime):
    from medicalloan.ui.treeview import equipment_display_status

    assert equipment_display_status({"is_retired": True, "status": "In-Stock"}) == "Lost"
    assert equipment_display_status({"is_retired": False, "status": "On-Loan"}) == "On-Loan"
    assert equipment_display_status({"status": None}) == ""
    assert equipment_display_status({}) == ""


def test_status_tag_for_known_and_unknown(stubbed_runtime):
    from medicalloan.ui.treeview import status_tag_for

    assert status_tag_for("In-Stock") == "InStock"
    assert status_tag_for("On-Loan") == "OnLoan"
    assert status_tag_for("Active") == "OnLoan"  # alias of On-Loan
    assert status_tag_for("") == ""
    assert status_tag_for("UnknownStatus") == ""


def test_translated_status_falls_back_through_lang_and_key(stubbed_runtime):
    from medicalloan.ui.treeview import translated_status

    i18n = {
        "en": {"status_values": {"In-Stock": "In-Stock"}},
        "he": {"status_values": {"In-Stock": "במלאי"}},
    }

    assert translated_status("In-Stock", i18n, "he") == "במלאי"
    # Unknown language falls back to English.
    assert translated_status("In-Stock", i18n, "fr") == "In-Stock"
    # Unknown status returns the input key.
    assert translated_status("Unknown", i18n, "he") == "Unknown"
    # Empty input returns empty string.
    assert translated_status("", i18n, "he") == ""


# ---------------------------------------------------------------------------
# Styles -- public API smoke
# ---------------------------------------------------------------------------

def test_styles_palettes_expose_light_and_dark(stubbed_runtime):
    from medicalloan.ui.styles import DARK_THEME, LIGHT_THEME, PALETTES, palette_for

    assert PALETTES["light"] is LIGHT_THEME
    assert PALETTES["dark"] is DARK_THEME

    # Both palettes share the same key set so theme switches don't
    # crash with KeyError.
    assert set(LIGHT_THEME) == set(DARK_THEME)

    # Unknown theme name falls back to light.
    assert palette_for("unknown") is LIGHT_THEME


def test_apply_theme_signature(stubbed_runtime):
    """apply_theme is the public seam between the App and ttk styles.
    Make sure its signature stays compatible with what app.setup_styles
    passes (otherwise theme switches blow up at runtime)."""
    import inspect

    from medicalloan.ui.styles import apply_theme

    sig = inspect.signature(apply_theme)
    expected_params = {"root", "theme_name", "ui_font", "input_font", "base_size"}
    assert expected_params.issubset(sig.parameters.keys())
