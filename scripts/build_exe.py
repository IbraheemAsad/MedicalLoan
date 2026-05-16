"""Build a single-file frozen executable with PyInstaller.

Phase 5 of the improvement plan checked this script in so the
build is reproducible from source instead of relying on whatever
``.spec`` an individual developer happened to have on disk.

What it bundles
---------------
* ``main.py`` -- the legacy entry point that dispatches to
  ``medicalloan.app.main``.
* ``fonts/`` -- Hebrew + Arabic TTFs (``register_fonts`` raises
  ``FontsMissingError`` if these aren't available at runtime).
* ``Icons/`` -- dashboard / flag PNGs + ``app_icon.ico``.
* ``config.ini`` -- shipped as a default; the running app rewrites
  the user's copy in ``application_data_dir()``.

Usage
-----
::

    python scripts/build_exe.py [--debug] [--no-clean]

The script writes to ``dist/`` (the binary) and ``build/`` (PyInstaller
intermediate output). Both are in ``.gitignore``.

The CI workflow in ``.github/workflows/ci.yml`` runs this on every push
and uploads ``dist/medicalloan*`` as an artifact so reviewers can grab
a build without setting up PyInstaller themselves.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist"
BUILD_DIR = REPO_ROOT / "build"

ENTRY_POINT = REPO_ROOT / "main.py"

# (source_path, dest_inside_bundle). PyInstaller's --add-data uses
# ``src{os.pathsep}dest`` so we keep the tuples here and stitch them
# together below; that way the list reads cleanly even with relative
# paths.
DATA_FILES: list[tuple[Path, str]] = [
    (REPO_ROOT / "fonts", "fonts"),
    (REPO_ROOT / "Icons", "Icons"),
    (REPO_ROOT / "config.ini", "."),
]

# PyInstaller doesn't always discover these via static import
# analysis (e.g. arabic_reshaper has dynamic submodule loads).
HIDDEN_IMPORTS = [
    "arabic_reshaper",
    "bidi",
    "bidi.algorithm",
    "PIL",
    "PIL._tkinter_finder",
    "openpyxl",
    "pandas",
    "reportlab",
]


def _ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "PyInstaller is not installed. Install it with "
            "`pip install pyinstaller`.",
        ) from exc


def _validate_data_files() -> None:
    for src, _dest in DATA_FILES:
        if not src.exists():
            raise SystemExit(
                f"Required data path missing: {src} -- run from repo root"
                " or restore the file before building.",
            )


def _build_command(args: argparse.Namespace) -> list[str]:
    cmd: list[str] = [
        sys.executable, "-m", "PyInstaller",
        "--name", "medicalloan",
        "--onefile",
        "--noconfirm",
        # Tk apps need windowed mode on Windows so a console doesn't
        # pop up. On Linux/macOS it's a no-op for the executable but
        # still suppresses the redundant terminal window.
        "--windowed",
        "--workpath", str(BUILD_DIR),
        "--distpath", str(DIST_DIR),
        "--specpath", str(BUILD_DIR),
        str(ENTRY_POINT),
    ]

    icon_ico = REPO_ROOT / "Icons" / "app_icon.ico"
    if icon_ico.exists():
        cmd.extend(["--icon", str(icon_ico)])

    for src, dest in DATA_FILES:
        cmd.extend(["--add-data", f"{src}{os.pathsep}{dest}"])

    for hidden in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", hidden])

    if args.debug:
        cmd.append("--debug=imports")

    return cmd


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--debug", action="store_true",
        help="Pass --debug=imports to PyInstaller (very verbose).",
    )
    parser.add_argument(
        "--no-clean", action="store_true",
        help="Skip removing build/ and dist/ before invoking PyInstaller.",
    )
    args = parser.parse_args(argv)

    _ensure_pyinstaller()
    _validate_data_files()

    if not args.no_clean:
        for d in (BUILD_DIR, DIST_DIR):
            if d.exists():
                shutil.rmtree(d)

    cmd = _build_command(args)
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(REPO_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
