"""PDF report generation package.

Phase 4 of the improvement plan split the old ~670-line ``reports.py``
monolith into focused modules:

* :mod:`medicalloan.reports.strings`   -- per-language UI strings
* :mod:`medicalloan.reports.fonts`     -- TTF registration + LANG_FONT map
* :mod:`medicalloan.reports.rtl`       -- bidi shaping helpers
* :mod:`medicalloan.reports.builder`   -- PdfBuilder + table styling
* :mod:`medicalloan.reports.agreement` -- per-loan agreement renderer
* :mod:`medicalloan.reports.inventory` -- full-inventory renderer
* :mod:`medicalloan.reports.loans`     -- active-loans renderer
* :mod:`medicalloan.reports.generator` -- :class:`ReportGenerator`

The legacy ``reports.py`` at the repo root is now a thin shim that
re-exports :class:`ReportGenerator` and :data:`REPORT_STRINGS` from
this package, so external consumers keep working unchanged.
"""

from medicalloan.reports.generator import ReportGenerator
from medicalloan.reports.strings import REPORT_STRINGS

__all__ = ["ReportGenerator", "REPORT_STRINGS"]
