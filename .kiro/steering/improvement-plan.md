# MedicalLoan — Improvement Plan
# MedicalLoan — Improvement Plan

This is the canonical reference for the ongoing refactor and bug-fix effort.
Treat the bug IDs (B1–B18) and phase numbers as stable identifiers — reference
them in commits, PRs, and issues (e.g. `fix(B2): parameterize import_loan_record`).

## Status

- **Phase 1 — Quick wins**: ✅ Done
- **Phase 2 — Database hardening**: ✅ Done
- **Phase 3 — Decompose `main.py` into views**: ✅ Done
- **Phase 4 — Reports refactor**: ✅ Done
- **Phase 5 — Polish**: ⏳ Not started

When working on this repo, prefer the phase order below. Cross-phase work is
fine when cheap, but don't start Phase 3's big restructure before Phase 2's
DB hardening is in.

---

## 1. Snapshot (baseline)

| File              | Lines  | Role                              | Health                          |
|-------------------|--------|-----------------------------------|---------------------------------|
| `main.py`         | 2,931  | UI + i18n dictionary + app logic  | Monolith, hard to navigate      |
| `database.py`     | 506    | SQLite layer                      | OK; missing FK pragma + ctx mgr |
| `reports.py`      | 669    | PDF generator + i18n strings      | OK; bare `except:` everywhere   |
| `config.ini`      | tiny   | PDF terms + institution name      | Underused                       |
| `requirements.txt`| 6 deps | Lower-bound only                  | No pinning                      |
| `.gitignore`      | clean  | —                                 | Good                            |

---

## 2. Bugs / correctness issues

| ID  | Bug                                                          | Where                                 | Impact                                                              | Fix                                                                 |
|-----|--------------------------------------------------------------|---------------------------------------|---------------------------------------------------------------------|---------------------------------------------------------------------|
| B1  | Dashboard buttons created twice                              | `show_dashboard()` — duplicate loop   | Stacked widgets at every grid cell                                  | Delete the second loop                                              |
| B2  | SQL injection in `import_loan_record`                        | `database.py` (f-string INSERT)       | Crafted Excel column header can inject SQL                          | Whitelist columns; use a fixed parameterized statement              |
| B3  | FOREIGN KEYs declared but not enforced                       | `database.py`                         | Orphan loan rows possible                                           | `PRAGMA foreign_keys=ON` per connect; add `ON DELETE CASCADE`       |
| B4  | "Lost" status is lossy                                       | `forfeit_deposit`                     | Equipment permanently excluded from inventory/available             | Make Lost a flag on the **loan**, not the equipment; add Restore   |
| B5  | Equipment auto-flips to In-Stock on return regardless of state| `process_return`                      | Blindly resurrects items previously marked Lost/etc.                | Only set In-Stock when current status is On-Loan                    |
| B6  | `resource_path('icons')` lowercase but folder is `Icons`     | `main.py` icon loading                | Crashes on case-sensitive filesystems (Linux)                       | Normalize at load time; defer folder rename to Phase 3              |
| B7  | Hardcoded English error string in HE/AR flow                 | `confirm_loan_logic`, `add_borrower_action` | Untranslated UX                                                | Move to `I18N_STRINGS`                                              |
| B8  | `perform_backup` runs every launch                           | startup                               | Disk fills up; "keep last 5" pointless on every restart             | Skip if last backup < N hours; also add daily/weekly retention      |
| B9  | `app_errors.log` written to CWD                              | `logging.basicConfig`                 | Unpredictable when packaged or run from elsewhere                   | Put log next to `db_path` (same dir as backups)                     |
| B10 | Bare `except:` everywhere                                    | `reports.py`, `auto_size_treeview_columns`, `_bidi` | Hides real errors (incl. `KeyboardInterrupt`)            | Catch `Exception` or specific types; log the swallowed error        |
| B11 | `setup_dialog_window` centering on multi-monitor             | `winfo_screenwidth()` (primary only)  | Dialogs spawn on the wrong monitor                                  | Center relative to `self.root` (its current monitor)                |
| B12 | `auto_size_treeview_columns` uses `tree.cget("font")`        | `main.py`                             | Returns style name, not a font; bare-except fallback runs every time| Use `style.lookup('Treeview', 'font')`                              |
| B13 | Default deposit silently becomes 0                           | `confirm_loan_logic`                  | Operator skips required deposit → accounting hole                   | Validate non-empty; show specific error                             |
| B14 | Duplicate i18n comment + dead font-probe branches            | `reports.py`                          | Noise; fragile font selection on Linux                              | Bundle TTFs from `fonts/`; stop probing system Arial                |
| B15 | `Database.close()` is never called                           | app exit                              | Non-deterministic WAL checkpoints                                   | Bind close to `root.protocol("WM_DELETE_WINDOW", ...)`              |
| B16 | Excel import has no schema validation                        | import path                           | Half-imported state on bad files                                    | Single transaction; validate columns; rollback on error             |
| B17 | `status_values['Active']` = `'OnLoan'` vs canonical `'On-Loan'`| i18n dict                            | Inconsistent display                                                | Pick one; permanent fix is `EquipmentStatus` enum in Phase 2        |
| B18 | `Database.connect()` not idempotent                          | reconnect path                        | Leaks previous connection                                           | Close existing first                                                |

---

## 3. Target architecture

```
medicalloan/
├── README.md
├── pyproject.toml              # replaces requirements.txt; pinned versions; entry_points
├── .gitignore
├── .pre-commit-config.yaml     # ruff + black + mypy
├── .github/workflows/ci.yml    # lint + tests
├── medicalloan/
│   ├── __init__.py             # __version__
│   ├── __main__.py             # `python -m medicalloan`
│   ├── app.py                  # MedicalEquipmentApp orchestration only (~150 lines)
│   ├── config.py               # AppConfig dataclass; load/save .ini; paths
│   ├── constants.py            # Enums: EquipmentStatus, LoanStatus, DepositStatus, Language
│   ├── paths.py                # resource_path, user_data_dir, backups_dir, logs_dir
│   ├── i18n/
│   │   ├── __init__.py         # Translator class, t('key', **fmt), missing-key logger
│   │   ├── en.py
│   │   ├── he.py
│   │   └── ar.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── schema.sql          # DDL + indexes + triggers
│   │   ├── migrations/         # 0001_init.sql, 0002_add_indexes.sql, ...
│   │   ├── connection.py       # context manager; FK pragma; WAL; row_factory
│   │   ├── models.py           # @dataclass Equipment / Borrower / Loan
│   │   └── repositories/
│   │       ├── equipment.py
│   │       ├── borrower.py
│   │       └── loan.py
│   ├── services/               # business logic, no Tk/SQL imports
│   │   ├── loan_service.py     # create / return / forfeit
│   │   ├── inventory_service.py
│   │   └── backup_service.py
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── fonts.py            # one place that registers TTFs
│   │   ├── rtl.py              # _bidi helper
│   │   ├── agreement.py
│   │   ├── inventory.py
│   │   └── loans.py
│   ├── data_io/
│   │   ├── excel_export.py
│   │   └── excel_import.py     # transactional; validates columns
│   └── ui/
│       ├── __init__.py
│       ├── styles.py           # setup_styles, theme palette, apply_theme(name)
│       ├── widgets/            # SearchableTable, FormRow, RtlTreeView, ...
│       ├── dialogs/
│       └── views/              # one Frame subclass per screen
├── assets/
│   ├── icons/                  # rename from "Icons" to lowercase (Phase 3)
│   └── fonts/
├── tests/
│   ├── conftest.py             # in-memory sqlite fixture
│   ├── test_db_*.py
│   ├── test_loan_service.py
│   ├── test_excel_import.py
│   └── test_reports_smoke.py
└── scripts/
    └── build_exe.py            # PyInstaller config
```

**Why each piece:**
- **Views as `ttk.Frame` subclasses** — collapse the 200-line "search frame + tree + scrollbars" pattern into a `SearchableTable` widget.
- **Services layer** — `LoanService.create_loan(...)` does all checks + DB writes in one transaction. Today this logic is interleaved with Tk callbacks.
- **Repositories** — `database.py` is doing two jobs (connection + queries). Split: `connection.py` owns the connection; one repository per table holds queries.
- **Migrations** — tiny home-grown migrator (apply `*.sql` in order, track in `schema_version` table).
- **i18n with Translator** — replaces `self.i18n[self.lang]['key']` with `t('key')`, plus missing-key warnings.

---

## 4. Database & data-model improvements (Phase 2)

Pragmas on every connect:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
```

- **Cascade deletes**: `loan(equipment_id) REFERENCES equipment(id) ON DELETE CASCADE`.
- **Indexes**: `loan(borrower_id)`, `loan(equipment_id)`, `loan(loan_status)`, `equipment(status)`, `borrower(id_number)` (already UNIQUE).
- **Status as enum** (`EquipmentStatus.IN_STOCK`, …) + `CHECK` constraints in DDL. This is the **permanent fix for B17**.
- **Add `equipment.is_retired BOOLEAN`** instead of overloading status. "Lost" becomes a flag on the loan (B4).
- **Surface `loan.expected_return_date`** in the UI (column already exists; nothing fills it).
- **Add a `users`/`staff` table** — even one row — so signature/audit fields can later be tracked.
- **Audit columns** `created_at` / `updated_at` via triggers, not Python `datetime.now()` strings.
- **ISO-8601 helpers** consistently — wrap parsing in one util.
- **Context manager for transactions** — `with conn:` already commits; wrap multi-step ops to keep them atomic.
- **WAL checkpoint on close**: `PRAGMA wal_checkpoint(TRUNCATE)` before `Database.close()` to keep the `-wal` file from growing across sessions.

---

## 5. UI / UX cleanup (Phase 3)

- Extract `SearchableTable(ttk.Frame)` — same ~120 lines repeats in inventory, new-loan-step1, returns, and borrowers.
- Extract `FormRow(parent, label_key, var, validator=None)` so dialogs become 5 calls, not 5×3 grid lines.
- Extract theme palette to `ui/styles.py`; switch via `apply_theme(name)`. Keep dark/light dicts.
- Persist language + theme + font size + window size in `config.ini` (currently hardcoded `self.lang = 'he'`).
- Replace duplicated dashboard loop with one loop using `enumerate` (B1).
- Treeview `<Double-1>` = "edit" (currently requires select-then-click).
- Status bar: current language, DB path, unread error count from log.
- Keyboard shortcuts: `Ctrl+N` new loan, `Ctrl+R` returns, `Esc` closes dialogs, `Enter` confirms.
- Replace `messagebox.showerror("Error", ...)` with localized titles (`self.t('error_title')`).

---

## 6. Reports module cleanup (Phase 4)

- Stop probing for system Arial. Ship the two TTFs already in `fonts/`; fail loudly if missing.
- One `register_fonts()` function, called once at module import; cached.
- Tiny `PdfBuilder` helper that hides `if is_rtl` branches: `pdf.line(left, right)`, `pdf.kv(label, value)`.
- Replace four `if is_rtl` branches in `_get_font_for_lang` with a `LANG_FONT = {'ar': 'NotoSansArabic-Regular', 'he': 'DavidLibre-Regular'}` map.
- Use `Paragraph` everywhere instead of mixing `canvas.drawString` + `Paragraph`. Free wrapping for Arabic addresses **and** long Hebrew equipment names in line items.
- Smoke test: render each PDF type with fixture data; assert file exists & non-empty.

---

## 7. Tooling, packaging, DX

| Area            | Today                           | Recommend                                                       |
|-----------------|---------------------------------|-----------------------------------------------------------------|
| Dependency mgmt | `requirements.txt` `>=` only    | `pyproject.toml` pinned + `requirements-lock.txt` via `uv`/`pip-tools` |
| Linter          | none                            | `ruff check` (replaces flake8 + isort + pyupgrade)              |
| Formatter       | none                            | `black`                                                         |
| Type checking   | none                            | `mypy --strict` on `db/`, `services/`, `i18n/`; relaxed on `ui/`|
| Pre-commit      | none                            | `pre-commit` (ruff, black, mypy, end-of-file-fixer)             |
| Tests           | none                            | `pytest`; headless on services/db                               |
| CI              | none                            | GitHub Actions: matrix py3.10–3.12, lint, test, build artifact  |
| Build           | implicit                        | `scripts/build_exe.py` with PyInstaller spec checked in         |
| Logging         | global `basicConfig`            | `logging.getLogger(__name__)` per module + rotating file handler|
| Versioning      | none                            | `__version__` in `__init__.py`, surfaced in title bar           |
| Changelog       | none                            | `CHANGELOG.md`, updated per PR                                  |

`pyproject.toml` skeleton:

```toml
[project]
name = "medicalloan"
version = "0.2.0"
requires-python = ">=3.10"
dependencies = [
  "reportlab==4.2.2",
  "Pillow==10.4.0",
  "pandas==2.2.2",
  "openpyxl==3.1.5",
  "python-bidi==0.6.0",
  "arabic-reshaper==3.0.0",
]
[project.scripts]
medicalloan = "medicalloan.app:main"
```

---

## 8. i18n cleanup

- Move each language to its own file (`i18n/en.py`, etc.).
- One `Translator` class:
  ```python
  t = Translator(default='en')
  t.set_lang('he')
  t('btn_new_loan')
  t('eq_label', name='Walker')   # supports format kwargs
  ```
- `Translator.missing()` hook: log first occurrence of each missing key to `app_errors.log` at WARNING, deduplicated.
- `tools/check_i18n.py`: errors if any key exists in `en` but is missing in `he`/`ar` (and vice-versa).
- Default language picked from `config.ini`, not hardcoded `'he'`.

---

## 9. Security & reliability

- Parameterize all SQL (B2). **Never** use f-strings to build SQL.
- If staff login is added later: `argon2-cffi`. Don't roll your own.
- Validate Israeli ID with checksum (Luhn-like) — currently any 9 digits pass.
- Phone validation — currently any digits, no length cap.
- Backups:
  - Keep last N **and** one per day for D days **and** one per week.
  - Add a "Restore from backup" UI under Data menu.
- Excel import wrapped in a single transaction; rollback on first error; report row & column.

---

## 10. Testing strategy

- **DB tests** with `:memory:` SQLite + `Database` class:
  - add equipment → search → update → delete cascades.
  - create loan → process_return restores availability.
  - forfeit_deposit changes statuses correctly.
- **Service tests** for invariants:
  - cannot loan an item already On-Loan.
  - cannot return a loan that's already Returned.
- **i18n tests**: each language has the same key set.
- **Report smoke tests**: PDFs render in `tmp_path` for en/he/ar.
- **No Tk in CI** — services don't import `tkinter`.
- Write DB and service tests **in Phase 2**, alongside the hardening work, so they protect Phase 3's big refactor.

---

## 11. Phased execution plan

### Phase 1 — Quick wins ✅ Done
- B1 duplicate loop, B6 `Icons` casing, B7 untranslated string, B11 dialog centering, B17 status mismatch (band-aid), B10 some bare-`except` swaps, B12 font lookup.
- `pyproject.toml` + pinned versions, `ruff` + `black`, `.pre-commit-config.yaml`, GitHub Actions lint job.
- `WM_DELETE_WINDOW` → `db.close()` (B15).

### Phase 2 — Database hardening
- `PRAGMA foreign_keys=ON`, WAL, `ON DELETE CASCADE`, indexes, schema migrator, `EquipmentStatus`/`LoanStatus` enums (permanent B17 fix).
- Fix B2 (SQL injection), B4/B5 (status semantics), B8 (backup cadence + retention tiers), B16 (transactional import), B18 (idempotent connect).
- `wal_checkpoint(TRUNCATE)` before close (extends B15).
- Move `app_errors.log` next to DB (B9).
- Write DB + service tests now.

### Phase 3 — Decompose `main.py` into views
- Move I18N to `i18n/` package; introduce `Translator` with missing-key logging.
- Extract `SearchableTable`, `FormRow`, `Dialog` helpers.
- Extract `ui/styles.py`.
- Move each screen to `ui/views/*.py`.
- Rename `Icons/` → `assets/icons/` (breaking change; do it here, not in Phase 1).

### Phase 4 — Reports refactor
- Split `reports.py` per report.
- One font registration; ship TTFs.
- `Paragraph`-everywhere renderer (handles long Hebrew + Arabic naturally).
- Smoke tests.

### Phase 5 — Polish
- Persist language/theme/window size in config.
- Keyboard shortcuts, double-click edit, status bar.
- Restore-from-backup UI.
- PyInstaller build script + GitHub Actions artifact upload.

---

## 12. Conventions

- Reference bug IDs in commits/PRs: `fix(B2): parameterize import_loan_record`.
- Reference phase in PR titles: `[Phase 2] DB hardening — pragmas + cascades`.
- Each phase = one or more small, independently-reviewable PRs. App must stay runnable on `main` after every PR.
- Update the **Status** section at the top of this file as phases complete.
- Keep `CHANGELOG.md` in sync per PR.
