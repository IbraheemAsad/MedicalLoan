"""Translator + per-language string tables.

The actual ``Translator`` class and ``I18N_STRINGS`` dict live in
:mod:`medicalloan.i18n.translator` and :mod:`medicalloan.i18n.en/he/ar`.
"""

from medicalloan.i18n.translator import I18N_STRINGS, Translator, is_rtl

__all__ = ["I18N_STRINGS", "Translator", "is_rtl"]
