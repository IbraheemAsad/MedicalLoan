# Changelog

All notable changes to this project will be documented here. Versions
follow the phases in `.kiro/steering/improvement-plan.md`.

## [Unreleased] — Phase 5: Polish

### Added
- `medicalloan/preferences.py` -- frozen `Preferences` dataclass with
  `load(config)` / `save(config, prefs, path)` for the new
  `[Preferences]` section in `config.ini`. Stores `lang`, `theme`,
  `font_size`, and last window `geometry`. Out-of-range font sizes
  are clamped on load; unknown lang/theme values fall back to
  defaults rather than raising, so a hand-edited `.ini` can never
  crash startup.
- `MedicalEquipmentApp` now reads preferences in `__init__` (instead
  of the old hardcoded `lang='he'`, `theme='light'`, `font_size=14`)
  and calls `_save_preferences()` from `toggle_theme`, the
  language-flag buttons, the font +/- buttons, and `_on_close`.
- Global keyboard shortcuts (`Control-N` new loan, `Control-R`
  process return, `Control-I` inventory, `Control-B` borrowers,
  `Control-P` reports, `Control-H` dashboard) bound on the Tk root
  via `_bind_global_shortcuts`. Both lower- and upper-case
  variants are bound so Caps Lock doesn't surprise the operator.
- `medicalloan/ui/dialogs.py` got localized wrappers
  (`error`/`info`/`warn`/`askyesno`) that look the dialog title up
  in the active i18n table (`error_title`, `success_title`,
  `warning_title`, `confirm_title`) -- the legacy code passed
  literal `"Error"` / `"Success"` strings, which left the title bar
  English even in HE/AR. New `bind_dialog_keys(dialog, on_confirm=...)`
  wires `Esc` to close and (optionally) `Enter`/`KP_Enter` to
  confirm, so form dialogs feel keyboard-native.
- `medicalloan/ui/status_bar.py` -- thin status strip rendered along
  the bottom of every screen by `app.show_global_controls()`. Shows
  `Lang: <code>  |  DB: <basename>` plus a clickable
  unread-error-bytes button when `app_errors.log` has grown since
  the last "mark read" (offset stored in
  `[Preferences].errors_seen_offset`). The byte counter
  (`unread_error_bytes`) is module-level so tests can import it
  without touching Tk.
- Restore-from-backup UI: the Data Management popup now has a
  **♻ Restore from Backup** button. It lists timestamped
  `backup_*.db` files under `<db_dir>/backups/` (newest first),
  takes a `pre_restore_<timestamp>.db` safety copy of the live DB,
  copies the chosen backup over it, then exits the app so the
  operator relaunches on the restored file.
- `services/backup_service.py` got two new public functions:
  `list_backups(backup_dir)` (newest-first) and
  `restore_backup(backup_path, db_path)` (returns the safety-copy
  path it just wrote).
- Inventory view: `<Double-1>` on a row now opens the Edit
  Equipment dialog (was: select-then-press-Edit).
- Borrowers view: `<Double-1>` on a row now opens the Loan History
  popup (mirrors the inventory ergonomics).
- `scripts/build_exe.py` -- PyInstaller helper that bundles `fonts/`,
  `Icons/`, and `config.ini`, threads `arabic_reshaper` /
  `bidi.algorithm` / `PIL._tkinter_finder` etc. as
  `--hidden-import`s, and writes a single-file binary to `dist/`.
  Runs `--windowed` so Windows users don't get a stray console.
- New CI jobs: `test` runs `pytest -q` against the repo on every
  push, and `build` runs `scripts/build_exe.py` and uploads the
  resulting `dist/medicalloan*` as a `medicalloan-linux` artifact.
  The build job depends on the existing `syntax` job to avoid
  burning minutes on broken commits.
- `tests/test_preferences.py`, `tests/test_status_bar.py`, and
  `tests/test_backup_restore.py` -- round-trip tests for the new
  preferences module, the unread-error byte counter, and the new
  `list_backups` / `restore_backup` helpers (including the
  pre-restore safety copy).
- New i18n keys for every supported language (`en`, `he`, `ar`):
  `error_title`, `warning_title`, `confirm_title`,
  `data_management`, `data_management_subtitle`,
  `btn_export_excel`, `btn_import_excel`, `btn_restore_backup`,
  `restore_title`, `restore_select`, `restore_no_backups`,
  `restore_button`, `confirm_restore_msg`, `restore_success`,
  `restore_failed`, `status_lang`, `status_db`,
  `status_unread_errors`, `shortcuts_help`. Each language gets
  152 keys total (was 133).

### Changed
- `MedicalEquipmentApp.__init__` no longer hardcodes `'he'` /
  `'light'` / `14`; the previous defaults are now wherever
  `medicalloan.preferences` keeps them, so a future change to the
  shipped defaults touches one constant.
- `MedicalEquipmentApp._on_close` calls `_save_preferences()` before
  closing the database, so the next launch restores the last
  language / theme / font / window geometry.
- The "Excel Export / Import" dashboard button is now localised
  (uses `data_management`) instead of being an English literal that
  stuck out in HE/AR.
- Most view modules now use the localised `ui_dialogs.error/info/warn`
  helpers; `messagebox.askyesno` calls already had translated titles
  via `app.i18n[app.lang][...]` and were left as-is.

### Notes for operators
- After upgrading, the first time you change the language / theme /
  font size or close the window, a `[Preferences]` section is
  appended to `config.ini`. Hand-edits to that section are honoured
  on the next launch.
- The pre-restore safety copies (`pre_restore_*.db`) are *not*
  pruned by the backup retention policy. Clean them up manually
  after you've confirmed the restored DB is healthy.

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
