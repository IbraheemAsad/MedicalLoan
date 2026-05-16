# Changelog

All notable changes to this project will be documented here. Versions
follow the phases in `.kiro/steering/improvement-plan.md`.

## [Unreleased] — Phase 4: Reports refactor

### Added
- `medicalloan/reports/` subpackage replacing the 670-line monolithic
  `reports.py`:
  - `strings.py` — per-language UI strings (`REPORT_STRINGS`).
  - `fonts.py` — single `register_fonts()` (idempotent) plus
    `LANG_FONT` map and `font_for_lang(lang)` helper. Replaces the
    four `if is_rtl` branches that used to live in
    `_get_font_for_lang`.
  - `rtl.py` — `bidi_shape()` / `maybe_bidi()` helpers that reshape
    Arabic and reorder RTL text. Degrades gracefully when
    `python-bidi` or `arabic-reshaper` are missing.
  - `builder.py` — `PdfBuilder` flowable factory (`title`, `subtitle`,
    `heading`, `body`, `kv`, `hr`, `signature_line`) and
    `make_data_table` for the inventory / loans tables. Hides the
    `if is_rtl` branches at every callsite.
  - `agreement.py`, `inventory.py`, `loans.py` — one focused renderer
    each (used to be three sections of one file).
  - `generator.py` — `ReportGenerator` orchestrator. Same public API
    as the legacy class: `__init__(output_dir, config)`,
    `generate_loan_agreement`, `generate_inventory_report`,
    `generate_loans_report`, `open_pdf`.
- `FontsMissingError`: raised at app startup if the bundled
  `DavidLibre-Regular.ttf` / `NotoSansArabic-Regular.ttf` can't be
  located (B14 / plan §6 — fail loudly instead of silently falling
  back to Helvetica which renders Hebrew/Arabic as boxes).
- `tests/test_reports_smoke.py` — renders all three PDF types in all
  three languages into `tmp_path`, asserts non-empty `%PDF`-prefixed
  output. Gated on `importorskip("reportlab")` so lint-only CI
  matrix entries still pass.

### Changed
- `reports.py` at the repo root is now a thin re-export shim
  (`from medicalloan.reports import ReportGenerator, REPORT_STRINGS`)
  so `from reports import ReportGenerator` in `medicalloan/app.py`,
  the PyInstaller spec, and any external scripts keep working
  unchanged.
- The loan-agreement PDF is now rendered as a stack of `Paragraph`
  flowables instead of raw `canvas.drawString` / `drawRightString`
  calls (plan §6). Long Hebrew equipment names and Arabic addresses
  now wrap onto multiple lines instead of running off the page.
- CI `syntax` job now byte-compiles the entire `medicalloan/`
  package and `services/` in addition to the three legacy top-level
  modules, so a typo in any package module fails CI immediately
  rather than at runtime.

### Notes for operators
- Public API of `ReportGenerator` is unchanged. No callsites in
  `medicalloan/app.py`, `medicalloan/ui/views/reports.py`, or
  `medicalloan/ui/views/new_loan.py` needed updating.
- If the `fonts/` directory is ever stripped from a deployment, the
  app will now fail loudly at startup with a clear
  `FontsMissingError` instead of generating PDFs with empty boxes
  where Hebrew/Arabic should be.

## [Unreleased] — Phase 2: Database hardening

### Added
- `constants.py`: canonical `EquipmentStatus`, `LoanStatus`, `DepositStatus`
  values plus a column allowlist for the Excel-restore loan import.
- `paths.py`: shared helpers for the application data directory, default
  database path, backups directory, and error log path.
- `services/backup_service.py`: replaces the launch-every-time backup with
  a tiered retention policy (recent / daily / weekly) and a minimum
  interval between backups (B8).
- `Database.set_equipment_retired()` / `is_retired` column: "Lost"
  equipment is now a flag on the row, not an overloaded status (B4). The
  inventory UI synthesizes a "Lost" display status from the flag.
- `Database.transaction()` and `Database.import_from_excel_transaction()`:
  context managers for atomic multi-statement work; the Excel import
  rolls back on any error (B16).
- Schema migrator with a `schema_version` table; pre-Phase-2 databases
  are migrated forward in place on first open.
- Pytest suite under `tests/` covering pragmas, cascades, status
  semantics, the v1 → v2 migration, and the backup retention policy.

### Changed
- `database.py`: enables `PRAGMA foreign_keys = ON` and
  `PRAGMA journal_mode = WAL` on every connect (B3); applies CHECK
  constraints on status columns (B17, permanent fix); adds
  `ON DELETE CASCADE` to loan FKs; adds indexes on hot columns;
  parameterizes `import_loan_record` against an allowlist (B2);
  makes `connect()` idempotent so reconnects don't leak handles (B18).
- `Database.process_return()` only flips equipment back to `In-Stock`
  when the current status is `On-Loan` (B5).
- `Database.forfeit_deposit()` resets equipment status to `In-Stock` and
  sets `is_retired = 1` instead of writing `'Lost'` to the status column.
- `Database.close()` runs `PRAGMA wal_checkpoint(TRUNCATE)` before
  closing so `-wal` / `-shm` files don't grow across sessions.
- `main.py`:
  - `MedicalEquipmentApp` now closes the database via
    `WM_DELETE_WINDOW` (B15).
  - `app_errors.log` is written next to the database (B9).
  - Excel import is wrapped in `import_from_excel_transaction()` so a
    bad row rolls everything back (B16).
  - The hardcoded "ID Number must be exactly 9 digits..." string at
    two call sites is replaced with `err_id_format`, translated into
    EN/HE/AR (B7).
  - `status_values['Active']` in the EN dictionary now reads `'On-Loan'`
    instead of the typo `'OnLoan'` (B17, cosmetic; CHECK constraint is
    the permanent fix).

### Notes for operators
- On first launch after upgrading, the existing `medical_equipment.db`
  is migrated forward in place. A backup is created automatically as
  long as `services/backup_service` deems one due (i.e., none in the
  last 6 hours).
- Old `'Lost'` equipment rows are converted to
  `(status='In-Stock', is_retired=1)`. Inventory reports continue to
  show them under "Lost / Retired".
