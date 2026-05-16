# Medical Equipment Loan Management System

A desktop application for managing medical equipment loans, built with Python and Tkinter. Designed for healthcare institutions that lend out medical devices (wheelchairs, crutches, hospital beds, etc.) to patients and need to track inventory, borrowers, deposits, and returns.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![CI](https://img.shields.io/github/actions/workflow/status/IbraheemAsad/MedicalLoan/ci.yml?label=CI)

---

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Installation](#installation)
  - [From Source (Development)](#from-source-development)
  - [Pre-built Executable](#pre-built-executable)
- [Usage](#usage)
  - [Running the Application](#running-the-application)
  - [Dashboard](#dashboard)
  - [New Loan (Check-Out)](#new-loan-check-out)
  - [Process Return (Check-In)](#process-return-check-in)
  - [Search Inventory](#search-inventory)
  - [Manage Borrowers](#manage-borrowers)
  - [Generate Reports (PDF)](#generate-reports-pdf)
  - [Data Management (Excel Import/Export)](#data-management-excel-importexport)
  - [Backup & Restore](#backup--restore)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Configuration](#configuration)
  - [config.ini](#configini)
  - [Preferences](#preferences)
- [Internationalization (i18n)](#internationalization-i18n)
- [Database](#database)
  - [Schema](#schema)
  - [Migrations](#migrations)
  - [WAL Mode & Safety](#wal-mode--safety)
- [Project Structure](#project-structure)
- [Development](#development)
  - [Setting Up for Development](#setting-up-for-development)
  - [Running Tests](#running-tests)
  - [Linting & Formatting](#linting--formatting)
  - [Pre-commit Hooks](#pre-commit-hooks)
- [Building a Standalone Executable](#building-a-standalone-executable)
- [CI/CD](#cicd)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Category | Details |
|----------|---------|
| **Inventory Management** | Add, edit, search, and delete medical equipment items. View summary of stock vs. on-loan counts. Double-click a row to edit. |
| **Loan Workflow** | Two-step check-out wizard (select equipment then borrower/deposit). Supports deposit tracking and optional donations. |
| **Return Processing** | Search active loans, process returns (deposit refund), or mark as non-returned (forfeit deposit and retire equipment). |
| **Borrower Management** | Add/edit/search borrowers. View full loan history per borrower. Double-click a row for history. |
| **PDF Reports** | Generate loan agreements, full inventory reports, and on-loan reports. Full RTL support for Hebrew and Arabic (BiDi + reshaping). |
| **Excel Import/Export** | Bulk export all tables to Excel. Import from Excel with atomic transactions (rollback on error). |
| **Backup & Restore** | Automatic tiered backup on launch (recent/daily/weekly retention). Manual restore from backup with safety copy. |
| **Multi-language UI** | English, Hebrew (RTL), and Arabic (RTL). Switch instantly via flag buttons. |
| **Themes** | Light and Dark mode with one-click toggle. Icons auto-invert in dark mode. |
| **Font Scaling** | Increase/decrease font size (9pt -- 24pt) from the toolbar. |
| **Preferences Persistence** | Language, theme, font size, and window geometry saved to `config.ini` and restored on next launch. |
| **Error Logging** | Uncaught exceptions logged to `app_errors.log`. Status bar shows unread error count. |
| **Single-file Executable** | Build with PyInstaller (bundles fonts, icons, config). CI produces a Linux artifact automatically. |

---

## Requirements

- **Python** 3.10, 3.11, or 3.12
- **Tkinter** (usually ships with Python; on some Linux distros install `python3-tk`)
- **Operating System**: Windows, macOS, or Linux

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| reportlab | >= 4.0.0 | PDF generation |
| Pillow | >= 9.0.0 | Icon loading & resizing |
| pandas | >= 2.0.0 | Excel import/export |
| openpyxl | >= 3.1.0 | Excel file format (.xlsx) |
| python-bidi | >= 0.4.2 | Right-to-left text rendering |
| arabic-reshaper | >= 3.0.0 | Arabic character reshaping |

---

## Installation

### From Source (Development)

```bash
# 1. Clone the repository
git clone https://github.com/IbraheemAsad/MedicalLoan.git
cd MedicalLoan

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# 3. Install in editable mode with all dependencies
pip install -e ".[dev]"

# 4. (Linux only) Ensure Tkinter is installed
# Ubuntu/Debian:
sudo apt-get install python3-tk
# Fedora:
sudo dnf install python3-tkinter
```

### Quick Install (no dev tools)

```bash
pip install -e .
```

Or simply install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Pre-built Executable

Download the latest `medicalloan-linux` artifact from the [GitHub Actions CI workflow](https://github.com/IbraheemAsad/MedicalLoan/actions). The artifact is a single-file executable that requires no Python installation:

```bash
chmod +x medicalloan
./medicalloan
```

---

## Usage

### Running the Application

```bash
# Option 1: Package entry point (after pip install)
medicalloan

# Option 2: Module invocation
python -m medicalloan

# Option 3: Direct script (legacy)
python main.py
```

On first launch the application:
1. Creates `medical_equipment.db` (SQLite) in the application data directory
2. Seeds a default `config.ini` if one doesn't exist
3. Runs a backup (if enough time has passed since the last one)
4. Opens the Dashboard

### Dashboard

The main screen provides navigation buttons to all features:

- **New Loan (Check-Out)** -- Start the loan wizard
- **Process Return (Check-In)** -- Return equipment and refund deposits
- **Search Inventory** -- Browse/search/edit equipment
- **Manage Borrowers** -- Browse/search/edit borrowers
- **Generate Reports** -- Create PDF reports
- **Data Management** -- Excel export/import + restore from backup

The top toolbar provides:
- **Language flags** (EN / HE / AR) -- switch UI language instantly
- **Font size +/-** -- scale the UI
- **Theme toggle** -- switch between Light and Dark mode

The bottom status bar shows:
- Current language
- Database file path
- Unread error count (clickable)

### New Loan (Check-Out)

A two-step wizard:

1. **Step 1 -- Select Equipment**: Search or browse available (in-stock, non-retired) equipment. Select a row and click "Loan This Item".
2. **Step 2 -- Borrower & Deposit**: Search for an existing borrower by ID/phone, or enter new borrower details. Enter deposit paid and optional donation. Click "Confirm & Print Agreement" to create the loan and generate a PDF agreement.

### Process Return (Check-In)

- Search active loans by borrower name, ID, or equipment name/serial
- Select a loan and choose:
  - **Process Return** -- marks loan returned, refunds deposit, sets equipment back to In-Stock
  - **Mark as Non-Returned (Forfeit Deposit)** -- forfeits the deposit, marks equipment as retired

### Search Inventory

- Full-text search across equipment name and serial number
- Add new equipment (name, description, serial number, deposit amount)
- Edit equipment (double-click or select + "Edit Selected")
- Delete equipment (cascades to loan history)
- View Summary -- aggregated counts per equipment type

### Manage Borrowers

- Search by name, ID number, or phone
- Add new borrowers
- Edit borrower details
- View loan history per borrower (double-click a row)

### Generate Reports (PDF)

Three report types:

| Report | Contents |
|--------|----------|
| **Loan Agreement** | Auto-generated during check-out. Includes borrower details, equipment info, terms from `config.ini`, signature lines. |
| **Full Inventory Report** | All equipment with status, deposit amounts, retirement flag. |
| **Equipment on Loan Report** | Active loans with borrower contact, loan dates, deposit info. |

All reports support RTL (Hebrew/Arabic) with proper BiDi reordering and Arabic reshaping. PDFs are generated using ReportLab and use bundled fonts (`DavidLibre-Regular.ttf` for Hebrew, `NotoSansArabic-Regular.ttf` for Arabic).

### Data Management (Excel Import/Export)

- **Export**: Dumps all three tables (equipment, borrower, loan) into an Excel workbook (.xlsx)
- **Import**: Reads an Excel workbook and upserts records. The entire import is wrapped in a single transaction -- if any row fails, the entire import rolls back (no partial data)

### Backup & Restore

**Automatic backups** run on each launch with a tiered retention policy:

| Tier | Retention |
|------|-----------|
| Recent (< 48h) | Keep all |
| Daily (2-14 days) | Keep one per day |
| Weekly (2-12 weeks) | Keep one per week |
| Older | Removed |

Backups are skipped if the most recent one is less than 6 hours old.

**Manual restore** (from Data Management screen):
1. Lists available backups (newest first)
2. Takes a safety copy of the current DB (`pre_restore_<timestamp>.db`)
3. Restores the selected backup
4. Closes the application (relaunch to use the restored DB)

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New Loan |
| `Ctrl+R` | Process Return |
| `Ctrl+I` | Search Inventory |
| `Ctrl+B` | Manage Borrowers |
| `Ctrl+P` | Generate Reports |
| `Ctrl+H` | Dashboard (Home) |
| `Escape` | Close current dialog |
| `Enter` | Confirm current dialog |

Shortcuts work regardless of Caps Lock state (both lower and upper case are bound).

---

## Configuration

### config.ini

Located next to the database file. Contains two default sections:

```ini
[General]
institution_name = Medical Loan Center

[PDF_Terms]
term1 = 1. The borrower agrees to return the equipment in good condition.
term2 = 2. The deposit will be refunded upon return.
term3 = 3. The borrower is responsible for damages.
term4 = 4. Equipment must be returned on time.
```

- **`[General]`** -- Institution name shown on PDF reports
- **`[PDF_Terms]`** -- Terms printed on loan agreement PDFs. Add/remove/edit terms freely.

### Preferences

A `[Preferences]` section is auto-appended on first setting change:

```ini
[Preferences]
lang = he
theme = light
font_size = 14
geometry = 1200x700+100+50
```

| Key | Values | Default |
|-----|--------|---------|
| `lang` | `en`, `he`, `ar` | `he` |
| `theme` | `light`, `dark` | `light` |
| `font_size` | 9 -- 24 | 14 |
| `geometry` | Tk geometry string | `1200x700` |

Invalid values are silently replaced with defaults on next launch (never crashes).

---

## Internationalization (i18n)

The UI supports three languages with full translations (152 keys each):

| Code | Language | Direction | Font |
|------|----------|-----------|------|
| `en` | English | LTR | Helvetica (system) |
| `he` | Hebrew | RTL | DavidLibre-Regular.ttf |
| `ar` | Arabic | RTL | NotoSansArabic-Regular.ttf |

Switch languages at any time using the flag buttons in the toolbar. The entire UI rebuilds instantly.

Translation dictionaries live in:
- `medicalloan/i18n/en.py`
- `medicalloan/i18n/he.py`
- `medicalloan/i18n/ar.py`

To add a new language: create a new `<code>.py` in `medicalloan/i18n/`, add the code to `VALID_LANGS` in `medicalloan/preferences.py`, and register it in `medicalloan/i18n/__init__.py`.

---

## Database

### Schema

The application uses SQLite with three main tables:

```
equipment
├── id (PK, autoincrement)
├── item_name (TEXT, NOT NULL)
├── description (TEXT)
├── serial_number (TEXT, UNIQUE, NOT NULL)
├── status (TEXT: 'In-Stock' | 'On-Loan')
├── deposit_amount (REAL, NOT NULL)
├── is_retired (INTEGER: 0 | 1)
└── created_date (TEXT)

borrower
├── id (PK, autoincrement)
├── full_name (TEXT, NOT NULL)
├── id_number (TEXT, UNIQUE, NOT NULL)
├── primary_phone (TEXT, NOT NULL)
├── secondary_phone (TEXT)
├── address (TEXT)
└── created_date (TEXT)

loan
├── id (PK, autoincrement)
├── borrower_id (FK -> borrower, CASCADE)
├── equipment_id (FK -> equipment, CASCADE)
├── loan_date (TEXT, NOT NULL)
├── deposit_paid (REAL, NOT NULL)
├── deposit_status (TEXT: 'Held' | 'Returned' | 'Forfeited')
├── expected_return_date (TEXT)
├── actual_return_date (TEXT)
├── donation_amount (REAL, default 0)
├── loan_status (TEXT: 'Active' | 'Returned' | 'Not Returned')
└── notes (TEXT)
```

### Migrations

Schema versioning is tracked in a `schema_version` table. On first open after upgrade, legacy databases are migrated in-place:
- `status = 'Lost'` equipment rows are converted to `(status='In-Stock', is_retired=1)`
- CHECK constraints and ON DELETE CASCADE are applied
- Indexes are created on hot columns

### WAL Mode & Safety

- **Write-Ahead Logging (WAL)** is enabled for concurrent read performance
- **Foreign keys** are enforced (`PRAGMA foreign_keys = ON`)
- **WAL checkpoint** runs on clean shutdown to prevent unbounded `-wal` file growth
- **Atomic transactions** wrap multi-statement operations (loan creation, returns, imports)

---

## Project Structure

```
MedicalLoan/
├── main.py                     # Legacy entry point (shim -> medicalloan.app.main)
├── database.py                 # SQLite database layer
├── constants.py                # Status enums & column allowlists
├── paths.py                    # Application data/log/backup path helpers
├── reports.py                  # Thin re-export shim for backward compat
├── config.ini                  # Default configuration (terms, institution)
├── pyproject.toml              # Build config, deps, tooling
├── requirements.txt            # Minimal pip dependencies
│
├── medicalloan/                # Main application package
│   ├── __init__.py
│   ├── __main__.py             # `python -m medicalloan` entry point
│   ├── app.py                  # MedicalEquipmentApp orchestrator + main()
│   ├── preferences.py          # Preferences dataclass + load/save
│   │
│   ├── i18n/                   # Internationalization
│   │   ├── __init__.py         # I18N_STRINGS aggregator
│   │   ├── translator.py       # Translation helper
│   │   ├── en.py               # English strings (152 keys)
│   │   ├── he.py               # Hebrew strings
│   │   └── ar.py               # Arabic strings
│   │
│   ├── reports/                # PDF report generators
│   │   ├── __init__.py
│   │   ├── generator.py        # ReportGenerator orchestrator
│   │   ├── builder.py          # PdfBuilder flowable factory
│   │   ├── agreement.py        # Loan agreement renderer
│   │   ├── inventory.py        # Inventory report renderer
│   │   ├── loans.py            # On-loan report renderer
│   │   ├── fonts.py            # Font registration + helpers
│   │   ├── rtl.py              # BiDi + Arabic reshaping utilities
│   │   └── strings.py          # Per-language report strings
│   │
│   └── ui/                     # Tkinter UI layer
│       ├── __init__.py
│       ├── dialogs.py          # Localized message dialogs + key bindings
│       ├── status_bar.py       # Bottom status strip
│       ├── styles.py           # ttk theme/style configuration
│       ├── treeview.py         # Treeview helpers
│       ├── validators.py       # Input validation (numbers, ID format)
│       │
│       ├── views/              # Individual screens
│       │   ├── dashboard.py
│       │   ├── new_loan.py
│       │   ├── process_return.py
│       │   ├── inventory.py
│       │   ├── borrowers.py
│       │   ├── reports.py
│       │   └── data_io.py      # Excel + restore UI
│       │
│       └── widgets/            # Reusable widget components
│           ├── form_row.py
│           └── search_frame.py
│
├── services/
│   └── backup_service.py       # Tiered backup + restore logic
│
├── scripts/
│   └── build_exe.py            # PyInstaller build script
│
├── fonts/
│   ├── DavidLibre-Regular.ttf  # Hebrew font
│   └── NotoSansArabic-Regular.ttf  # Arabic font
│
├── Icons/                      # Dashboard + flag icons
│   ├── app_icon.ico
│   ├── app_icon.png
│   ├── NewLoan.png
│   ├── ReturnProcess.png
│   ├── SearchInventory.png
│   ├── ManageBorrowers.png
│   ├── GenerateReports.png
│   ├── flag_en.png
│   ├── flag_he.png
│   └── flag_ar.png
│
├── tests/                      # Pytest test suite
│   ├── conftest.py
│   ├── test_database.py
│   ├── test_migration.py
│   ├── test_preferences.py
│   ├── test_status_bar.py
│   ├── test_backup_service.py
│   ├── test_backup_restore.py
│   ├── test_reports_smoke.py
│   └── test_phase3_decomposition.py
│
├── .github/workflows/ci.yml   # GitHub Actions (lint, test, build)
├── .pre-commit-config.yaml    # Pre-commit hooks
├── .gitignore
└── CHANGELOG.md               # Detailed changelog by phase
```

---

## Development

### Setting Up for Development

```bash
# Install with dev dependencies (ruff, black, pytest, pre-commit)
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_database.py

# Run tests matching a pattern
pytest -k "backup"
```

> **Note**: Tests requiring Tkinter (GUI) are automatically skipped on headless CI environments.

### Linting & Formatting

```bash
# Lint with ruff
ruff check .

# Auto-fix lint issues
ruff check --fix .

# Format with black (not enforced in CI yet)
black .

# Check formatting without modifying
black --check .
```

### Pre-commit Hooks

The repository includes a `.pre-commit-config.yaml`. After installing hooks (`pre-commit install`), every commit is automatically checked for lint errors before it lands.

---

## Building a Standalone Executable

The application can be packaged as a single-file executable using PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller==6.10.0

# Build the executable
python scripts/build_exe.py

# The binary will be in dist/medicalloan
./dist/medicalloan
```

### Build Options

```bash
# Debug mode (verbose import tracing)
python scripts/build_exe.py --debug

# Skip cleaning build/dist directories
python scripts/build_exe.py --no-clean
```

The build bundles:
- `fonts/` (Hebrew + Arabic TTFs)
- `Icons/` (all PNG/ICO icons)
- `config.ini` (default configuration)
- Hidden imports for arabic_reshaper, bidi, PIL, openpyxl, pandas, reportlab

---

## CI/CD

GitHub Actions runs on every push and PR to `main`:

| Job | What it does |
|-----|--------------|
| **lint** | Runs `ruff check .` across Python 3.10, 3.11, 3.12 |
| **syntax** | Byte-compiles all source files |
| **test** | Runs `pytest -q` (Python 3.12) |
| **build** | Builds single-file executable with PyInstaller, uploads as artifact |

The `build` job depends on `syntax` passing first.

---

## Troubleshooting

### "FontsMissingError" on startup

The bundled fonts (`fonts/DavidLibre-Regular.ttf` and `fonts/NotoSansArabic-Regular.ttf`) are required for PDF generation. Ensure the `fonts/` directory is present next to `main.py` (or bundled in the executable).

### Tkinter not found (Linux)

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora/RHEL
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

### Database locked / WAL errors

The application uses WAL mode. If you see "database is locked" errors:
1. Ensure no other process has the database open
2. Check for stale `-wal` and `-shm` files (the app cleans these on normal exit)
3. If the app crashed, the next normal startup will recover automatically

### Icons not displaying

- Ensure `Pillow` is installed (`pip install Pillow`)
- Check that the `Icons/` directory is present next to `main.py`
- Without Pillow, basic Tk PhotoImage loading is used (limited format support)

### Preferences reset on every launch

Check that `config.ini` is writable. The application writes the `[Preferences]` section on theme/language/font changes and on close. If the file is read-only, preferences won't persist (but the app won't crash either).

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Install dev dependencies (`pip install -e ".[dev]"`)
4. Install pre-commit hooks (`pre-commit install`)
5. Make your changes
6. Run tests (`pytest`)
7. Run linter (`ruff check .`)
8. Commit and push
9. Open a Pull Request

### Code Style

- Line length: 100 characters (configured in `pyproject.toml`)
- Formatter: Black (not yet enforced in CI)
- Linter: Ruff (E, F, W, I, B, UP rules)
- Type hints: Used throughout (Python 3.10+ syntax)

---

## License

This project is licensed under the **MIT License**. See `pyproject.toml` for details.

---

## Author

**Ibraheem Asad** -- [GitHub](https://github.com/IbraheemAsad)
