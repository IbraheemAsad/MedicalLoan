"""Medical Equipment Loan Management System.

This package was introduced in Phase 3 of the improvement plan
(see .kiro/steering/improvement-plan.md) to decompose the original
2,956-line ``main.py`` monolith into focused modules:

* ``medicalloan.i18n``  -- Translator + per-language string tables
* ``medicalloan.ui.styles``       -- ttk theme palette + ``apply_theme``
* ``medicalloan.ui.widgets``      -- reusable widgets (SearchFrame, ...)
* ``medicalloan.ui.views``        -- one module per screen
* ``medicalloan.app``             -- ``MedicalEquipmentApp`` orchestrator

The legacy ``main.py`` at the repo root is now a thin shim that
delegates to :func:`medicalloan.app.main`, so packaged builds and
existing launch scripts keep working unchanged.
"""

__version__ = "0.3.0"
