# Changelog

All notable changes to this project will be documented here. Versions
follow the phases in `.kiro/steering/improvement-plan.md`.

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
