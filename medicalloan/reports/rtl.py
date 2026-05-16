"""Right-to-left text shaping helpers.

Hebrew and Arabic need two pre-processing steps before reportlab will
render them readably:

1. ``arabic_reshaper`` joins Arabic letters into their initial / medial
   / final / isolated forms (Hebrew passes through unchanged).
2. ``bidi.algorithm.get_display`` reverses the visual order so the
   string reads right-to-left when reportlab lays it out left-to-right.

Both libraries are optional dependencies; if either is missing we degrade
gracefully and emit a single startup warning rather than crashing on
every report.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


try:
    import bidi.algorithm as _bidi_algorithm
    _BIDI_AVAILABLE = True
except ImportError:  # pragma: no cover - environment-specific
    log.warning("python-bidi not installed; RTL text will not be reordered")
    _BIDI_AVAILABLE = False
    _bidi_algorithm = None  # type: ignore[assignment]

try:
    import arabic_reshaper as _arabic_reshaper
    _RESHAPER_AVAILABLE = True
except ImportError:  # pragma: no cover - environment-specific
    log.warning(
        "arabic-reshaper not installed; Arabic letters will be disjointed",
    )
    _RESHAPER_AVAILABLE = False
    _arabic_reshaper = None  # type: ignore[assignment]

def bidi_shape(text: str) -> str:
    """Return ``text`` reshaped + visually reordered for RTL rendering.

    Safe to call on Latin text (just a no-op chain). Safe to call when
    the optional libraries are missing -- you get back the input string
    unchanged. Never raises.
    """
    if not text:
        return text

    out = text

    # Step 1 -- shape Arabic glyphs. Hebrew passes through unchanged.
    if _RESHAPER_AVAILABLE:
        try:
            out = _arabic_reshaper.reshape(out)
        except Exception as exc:  # noqa: BLE001 - shaper may raise on odd input
            log.debug("arabic_reshaper failed for %r: %s", text, exc)

    # Step 2 -- reverse to visual order.
    if _BIDI_AVAILABLE:
        try:
            return _bidi_algorithm.get_display(out)
        except Exception as exc:  # noqa: BLE001 - same defensive stance
            log.debug("bidi.get_display failed for %r: %s", text, exc)

    return out


def maybe_bidi(text: str, is_rtl: bool) -> str:
    """Apply :func:`bidi_shape` only when ``is_rtl`` is true.

    Saves a one-line ``if`` at every callsite that mixes LTR and RTL
    output (the inventory / loans report headers, for example).
    """
    return bidi_shape(text) if is_rtl else text
