"""Persisted UI preferences (Phase 5).

Phase 5 of the improvement plan stops hardcoding ``self.lang = 'he'``,
``self.current_theme = 'light'`` and ``base_font_size = 14`` in
``MedicalEquipmentApp.__init__`` and instead reads them from the
``[Preferences]`` section of ``config.ini``. The same section also
holds the last window geometry (``WIDTHxHEIGHT+X+Y``) so the app
restores wherever the operator left it.

Round-trip is intentionally cheap: a tiny dataclass + ``load(config)``
/ ``save(config, prefs, config_path)`` pair. The dataclass clamps
``font_size`` and ignores unknown ``lang`` / ``theme`` values rather
than raising, so an operator hand-editing the .ini can't crash the
app on next launch.
"""

from __future__ import annotations

import configparser
import logging
import re
from dataclasses import dataclass, replace

log = logging.getLogger(__name__)

# Bounds match the +/- buttons in the global control bar; if a stale
# config has 999 we clamp on load.
MIN_FONT_SIZE = 9
MAX_FONT_SIZE = 24
DEFAULT_FONT_SIZE = 14

VALID_LANGS = ("en", "he", "ar")
VALID_THEMES = ("light", "dark")

DEFAULT_LANG = "he"
DEFAULT_THEME = "light"
DEFAULT_GEOMETRY = "1200x700"

SECTION = "Preferences"

# A standard Tk geometry string: ``WIDTHxHEIGHT[+-X+-Y]``. We only
# accept the strict positive form for width/height; X/Y can be
# negative on multi-monitor setups.
_GEOMETRY_RE = re.compile(r"^\d+x\d+(?:[+-]-?\d+[+-]-?\d+)?$")


@dataclass(frozen=True)
class Preferences:
    """Snapshot of the user-tweakable runtime settings.

    Frozen so callers can't accidentally mutate a shared instance.
    Use ``replace(prefs, lang='en')`` to derive a modified copy.
    """

    lang: str = DEFAULT_LANG
    theme: str = DEFAULT_THEME
    font_size: int = DEFAULT_FONT_SIZE
    geometry: str = DEFAULT_GEOMETRY


def _coerce_int(value: str, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _clamp_font(size: int) -> int:
    return max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))


def _validate_geometry(value: str) -> str:
    """Return ``value`` if it's a Tk geometry string, else the default.

    Accepts ``WIDTHxHEIGHT`` or ``WIDTHxHEIGHT+X+Y``. Anything else
    falls back to :data:`DEFAULT_GEOMETRY` -- a corrupted geometry
    string would otherwise make ``Tk.geometry()`` raise on startup.
    """
    if not value:
        return DEFAULT_GEOMETRY
    return value if _GEOMETRY_RE.match(value) else DEFAULT_GEOMETRY


def load(config: configparser.ConfigParser) -> Preferences:
    """Read preferences from the ``[Preferences]`` section.

    Missing section, missing keys, and out-of-range values all fall
    back to the matching default -- the goal is "never crash on
    startup because of a bad .ini".
    """
    if not config.has_section(SECTION):
        return Preferences()

    section = config[SECTION]

    lang = section.get("lang", DEFAULT_LANG)
    if lang not in VALID_LANGS:
        log.warning("Ignoring unknown preferences.lang=%r; using default", lang)
        lang = DEFAULT_LANG

    theme = section.get("theme", DEFAULT_THEME)
    if theme not in VALID_THEMES:
        log.warning("Ignoring unknown preferences.theme=%r; using default", theme)
        theme = DEFAULT_THEME

    font_size = _clamp_font(_coerce_int(section.get("font_size", ""), DEFAULT_FONT_SIZE))
    geometry = _validate_geometry(section.get("geometry", DEFAULT_GEOMETRY))

    return Preferences(
        lang=lang, theme=theme, font_size=font_size, geometry=geometry,
    )


def save(
    config: configparser.ConfigParser,
    prefs: Preferences,
    config_path: str,
) -> None:
    """Persist ``prefs`` into ``config`` and rewrite ``config_path``.

    The ``config`` object is mutated in place so other sections
    (``[General]``, ``[PDF_Terms]``) are preserved verbatim. The file
    is rewritten atomically enough for our needs -- ``configparser``
    just calls ``open(..., 'w')`` -- a partial write would only matter
    if the user pulled the plug mid-save, in which case the worst
    case is "lose your last preference change".
    """
    if not config.has_section(SECTION):
        config.add_section(SECTION)

    config[SECTION]["lang"] = prefs.lang
    config[SECTION]["theme"] = prefs.theme
    config[SECTION]["font_size"] = str(prefs.font_size)
    config[SECTION]["geometry"] = prefs.geometry

    try:
        with open(config_path, "w", encoding="utf-8") as fh:
            config.write(fh)
    except OSError:
        # Saving prefs is best-effort -- if the disk is full or the
        # file is read-only we don't want to crash the running app
        # mid-toggle. The next save attempt will retry.
        log.exception("Could not persist preferences to %s", config_path)


def with_updates(prefs: Preferences, **changes: object) -> Preferences:
    """Return a new ``Preferences`` with the given fields overridden.

    Thin wrapper around :func:`dataclasses.replace` that clamps
    ``font_size`` so callers can pass raw integers from the +/-
    buttons without re-implementing the bounds check.
    """
    if "font_size" in changes:
        changes["font_size"] = _clamp_font(int(changes["font_size"]))  # type: ignore[arg-type]
    return replace(prefs, **changes)
