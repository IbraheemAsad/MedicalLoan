"""Backwards-compat entry point for the Medical Equipment Loan app.

Phase 3 of the improvement plan moved every screen into the
``medicalloan`` package; this file is now a thin shim so existing
launch scripts, ``.spec`` files for PyInstaller, and people who type
``python main.py`` from the repo root keep working unchanged.

For new tooling prefer ``python -m medicalloan`` instead.
"""

from medicalloan.app import main

if __name__ == "__main__":
    main()
