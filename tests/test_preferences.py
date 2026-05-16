"""Tests for ``medicalloan.preferences`` (Phase 5)."""

from __future__ import annotations

import configparser
from pathlib import Path

from medicalloan import preferences as prefs_mod


def test_load_returns_defaults_when_section_missing():
    config = configparser.ConfigParser()
    prefs = prefs_mod.load(config)

    assert prefs.lang == prefs_mod.DEFAULT_LANG
    assert prefs.theme == prefs_mod.DEFAULT_THEME
    assert prefs.font_size == prefs_mod.DEFAULT_FONT_SIZE
    assert prefs.geometry == prefs_mod.DEFAULT_GEOMETRY


def test_load_reads_valid_values_from_section():
    config = configparser.ConfigParser()
    config.read_dict({
        "Preferences": {
            "lang": "en",
            "theme": "dark",
            "font_size": "16",
            "geometry": "1280x720+50+25",
        },
    })
    prefs = prefs_mod.load(config)

    assert prefs.lang == "en"
    assert prefs.theme == "dark"
    assert prefs.font_size == 16
    assert prefs.geometry == "1280x720+50+25"


def test_load_clamps_out_of_range_font_size():
    too_big = configparser.ConfigParser()
    too_big.read_dict({"Preferences": {"font_size": "999"}})
    assert prefs_mod.load(too_big).font_size == prefs_mod.MAX_FONT_SIZE

    too_small = configparser.ConfigParser()
    too_small.read_dict({"Preferences": {"font_size": "1"}})
    assert prefs_mod.load(too_small).font_size == prefs_mod.MIN_FONT_SIZE


def test_load_falls_back_on_unknown_lang_and_theme():
    config = configparser.ConfigParser()
    config.read_dict({
        "Preferences": {"lang": "klingon", "theme": "neon"},
    })
    prefs = prefs_mod.load(config)

    assert prefs.lang == prefs_mod.DEFAULT_LANG
    assert prefs.theme == prefs_mod.DEFAULT_THEME


def test_load_falls_back_on_garbage_geometry():
    config = configparser.ConfigParser()
    config.read_dict({"Preferences": {"geometry": "not-a-geometry"}})
    assert prefs_mod.load(config).geometry == prefs_mod.DEFAULT_GEOMETRY


def test_save_round_trip_preserves_other_sections(tmp_path: Path):
    config_path = tmp_path / "config.ini"
    config = configparser.ConfigParser()
    config.read_dict({
        "General": {"institution_name": "Test Hospital"},
        "PDF_Terms": {"term1": "1. test"},
    })

    prefs = prefs_mod.Preferences(
        lang="ar", theme="dark", font_size=18, geometry="900x600+10+20",
    )
    prefs_mod.save(config, prefs, str(config_path))

    # Re-read from disk to make sure save() actually wrote the file.
    reloaded = configparser.ConfigParser()
    reloaded.read(config_path, encoding="utf-8")

    assert reloaded["General"]["institution_name"] == "Test Hospital"
    assert reloaded["PDF_Terms"]["term1"] == "1. test"
    assert prefs_mod.load(reloaded) == prefs


def test_with_updates_clamps_font_size():
    base = prefs_mod.Preferences()
    bumped = prefs_mod.with_updates(base, font_size=999)
    assert bumped.font_size == prefs_mod.MAX_FONT_SIZE


def test_with_updates_overrides_lang_only():
    base = prefs_mod.Preferences(font_size=16)
    out = prefs_mod.with_updates(base, lang="en")
    assert out.lang == "en"
    assert out.font_size == 16  # untouched
