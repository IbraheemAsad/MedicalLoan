"""Translator + canonical I18N_STRINGS map.

Phase 3 of the improvement plan extracts the per-language string tables
out of the old ``main.py`` monolith into one module per language
(``en.py``, ``he.py``, ``ar.py``) and puts a small :class:`Translator`
class in front of them.

Two access patterns are supported on purpose:

1. ``app.t('key', name='Walker')`` -- the new sugar. Missing keys are
   logged once each (deduplicated) at WARNING level and returned as
   the bare key so the UI never crashes.
2. ``app.i18n[lang]['key']`` -- the legacy dict-of-dicts lookup that
   the original ``main.py`` used in dozens of places. Views moved out
   of ``main.py`` continue to work without rewriting every callsite,
   and we can migrate them to ``app.t(...)`` opportunistically.
"""

from __future__ import annotations

import logging
from typing import Any

from medicalloan.i18n import ar as _ar
from medicalloan.i18n import en as _en
from medicalloan.i18n import he as _he

log = logging.getLogger(__name__)


# Canonical RTL language set. Anything else is treated as LTR.
_RTL_LANGS: frozenset[str] = frozenset({'he', 'ar'})


# Public dict-of-dicts: ``I18N_STRINGS[lang][key]`` -> str (or nested dict
# for ``status_values``). Mirrors the shape the original ``main.py`` used,
# so any view module that still does ``self.i18n[self.lang][key]`` keeps
# working unchanged.
I18N_STRINGS: dict[str, dict[str, Any]] = {
    'en': _en.STRINGS,
    'he': _he.STRINGS,
    'ar': _ar.STRINGS,
}


def is_rtl(lang: str) -> bool:
    """Return ``True`` if ``lang`` reads right-to-left."""
    return lang in _RTL_LANGS


class Translator:
    """Looks up UI strings for the current language with fallbacks.

    Parameters
    ----------
    default:
        Initial language code. Anything not in :data:`I18N_STRINGS`
        falls back to English at lookup time.

    The translator keeps a set of already-warned-about missing keys so
    we don't spam the log for every redraw.
    """

    def __init__(self, default: str = 'he') -> None:
        self.lang: str = default if default in I18N_STRINGS else 'en'
        self._missing_seen: set[tuple[str, str]] = set()

    # ----- core API -----------------------------------------------------
    @property
    def is_rtl(self) -> bool:
        return is_rtl(self.lang)

    def set_lang(self, new_lang: str) -> None:
        """Change the active language. Unknown codes silently keep the
        current language so we never end up with a broken UI."""
        if new_lang in I18N_STRINGS:
            self.lang = new_lang

    def t(self, key: str, **fmt: Any) -> str:
        """Return the localized string for ``key``.

        Resolution order:
        1. current language
        2. English (fallback)
        3. the key itself, with a one-shot WARNING in the log

        ``**fmt`` is passed to :py:meth:`str.format`. We swallow
        ``KeyError`` from format() so a stray ``{user}`` placeholder
        doesn't crash the app.
        """
        value = I18N_STRINGS.get(self.lang, {}).get(key)
        if value is None:
            value = I18N_STRINGS['en'].get(key)
            if value is None:
                self._warn_missing(key)
                return key
        if not isinstance(value, str):
            # ``status_values`` etc. are nested dicts; return as-is so the
            # caller can index into them.
            return value  # type: ignore[return-value]
        if not fmt:
            return value
        try:
            return value.format(**fmt)
        except (KeyError, IndexError):
            log.warning("i18n: bad format args for key %r: %r", key, fmt)
            return value

    # ----- legacy dict-style access -------------------------------------
    @property
    def i18n(self) -> dict[str, dict[str, Any]]:
        """Backwards-compat alias so callers can still write
        ``app.t.i18n[lang][key]`` if they need the raw table."""
        return I18N_STRINGS

    # ----- internals ----------------------------------------------------
    def _warn_missing(self, key: str) -> None:
        marker = (self.lang, key)
        if marker in self._missing_seen:
            return
        self._missing_seen.add(marker)
        log.warning("i18n: missing key %r in language %r", key, self.lang)
