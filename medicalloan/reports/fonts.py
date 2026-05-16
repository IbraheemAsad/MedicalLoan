"""Font registration for PDF reports.

Phase 4 of the improvement plan replaces the old "probe for system Arial,
fall back to Helvetica" dance with a single ``register_fonts()`` that
loads the two TTFs we already ship in ``fonts/`` (DavidLibre for Hebrew,
NotoSansArabic for Arabic). It runs once per process and is idempotent.

A small ``LANG_FONT`` mapping replaces the four ``if is_rtl`` branches
that used to live in ``_get_font_for_lang`` -- callers just look the
language up in the dict and get a font name back.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from typing import Final

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Font names + bundled file lookup
# ---------------------------------------------------------------------------

# Public alias used for the default RTL font and as the fallback for the
# ``LANG_FONT`` map. Hebrew is the institution's primary language so we
# alias DavidLibre as the default.
RTL_FONT_NAME: Final = "RTL_Font"

HEBREW_FONT_NAME: Final = "DavidLibre-Regular"
ARABIC_FONT_NAME: Final = "NotoSansArabic-Regular"
DEFAULT_LATIN_FONT: Final = "Helvetica"
DEFAULT_LATIN_BOLD: Final = "Helvetica-Bold"

_HEBREW_TTF: Final = "DavidLibre-Regular.ttf"
_ARABIC_TTF: Final = "NotoSansArabic-Regular.ttf"

# Per-language font lookup. Anything not in here gets DEFAULT_LATIN_FONT.
LANG_FONT: Final[dict[str, str]] = {
    "he": HEBREW_FONT_NAME,
    "ar": ARABIC_FONT_NAME,
}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_registered = False
_register_lock = threading.Lock()


def _resource_path(*parts: str) -> str:
    """Locate a bundled file whether running from source or PyInstaller.

    PyInstaller sets ``sys._MEIPASS`` to the temp dir it unpacked into;
    in source mode we fall back to the project root (two parents up
    from this file: ``medicalloan/reports/fonts.py`` -> repo root).
    """
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
        )
    return os.path.join(base, *parts)


class FontsMissingError(RuntimeError):
    """Raised when the bundled RTL TTFs cannot be located.

    Phase 4 deliberately fails loudly here rather than silently falling
    back to Helvetica -- a Helvetica fallback renders Hebrew/Arabic as
    boxes, which is worse than a clear error message at startup.
    """


def register_fonts(font_dir: str | None = None) -> None:
    """Register the bundled Hebrew + Arabic TTFs with reportlab.

    Idempotent: subsequent calls are no-ops (and cheap; we just check a
    module-level flag).

    Parameters
    ----------
    font_dir:
        Directory that holds the TTFs. Defaults to ``<repo>/fonts``.

    Raises
    ------
    FontsMissingError
        If either TTF is absent. The previous behaviour silently fell
        back to Helvetica which renders RTL text as boxes -- much worse
        than a clear error.
    """
    global _registered
    if _registered:
        return

    with _register_lock:
        if _registered:
            return

        base = font_dir or _resource_path("fonts")
        hebrew_path = os.path.join(base, _HEBREW_TTF)
        arabic_path = os.path.join(base, _ARABIC_TTF)

        missing = [p for p in (hebrew_path, arabic_path) if not os.path.isfile(p)]
        if missing:
            raise FontsMissingError(
                "Bundled RTL fonts not found. Expected "
                f"{_HEBREW_TTF} and {_ARABIC_TTF} under {base!r}; "
                f"missing: {missing}. Reinstall or ensure the 'fonts/' "
                "folder ships with the application."
            )

        # Hebrew + Arabic + the catch-all RTL_Font alias (which points at
        # the Hebrew TTF; Arabic callers explicitly pick NotoSansArabic).
        pdfmetrics.registerFont(TTFont(HEBREW_FONT_NAME, hebrew_path))
        pdfmetrics.registerFont(TTFont(ARABIC_FONT_NAME, arabic_path))
        pdfmetrics.registerFont(TTFont(RTL_FONT_NAME, hebrew_path))

        log.info("Registered RTL fonts: %s, %s", HEBREW_FONT_NAME, ARABIC_FONT_NAME)
        _registered = True


def font_for_lang(lang: str) -> str:
    """Return the registered font family name to use for ``lang``.

    Falls back to Helvetica for Latin scripts. Assumes
    :func:`register_fonts` has already been called -- callers in this
    package do that in their ``__init__``.
    """
    return LANG_FONT.get(lang, DEFAULT_LATIN_FONT)


def bold_font_for(font_name: str) -> str:
    """Return the bold variant for a registered font.

    The bundled TTFs are regular-only, so bold variants of Hebrew/Arabic
    just reuse the regular face (reportlab will then synthesize bold by
    re-stroking, which looks acceptable in headings). Helvetica has a
    real bold companion that ships with reportlab.
    """
    if font_name == DEFAULT_LATIN_FONT:
        return DEFAULT_LATIN_BOLD
    return font_name


def reset_for_tests() -> None:
    """Test-only hook: forget that we've registered fonts.

    Used by smoke tests that want to verify the registration path runs
    cleanly. Safe to call at any time -- the underlying reportlab cache
    is left as-is (registering the same font twice is a no-op).
    """
    global _registered
    with _register_lock:
        _registered = False
