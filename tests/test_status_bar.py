"""Tests for the unread-error byte counter used by the status bar (Phase 5)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# The status_bar module imports tkinter at module load. CI runners
# have it, but minimal local sandboxes might not -- skip cleanly.
pytest.importorskip("tkinter")

from medicalloan.ui.status_bar import unread_error_bytes  # noqa: E402


def test_returns_zero_when_log_missing(tmp_path: Path):
    missing = tmp_path / "nope.log"
    assert unread_error_bytes(str(missing), 0) == 0


def test_returns_full_size_when_offset_is_zero(tmp_path: Path):
    log = tmp_path / "app_errors.log"
    log.write_text("ERROR x\nERROR y\n")
    assert unread_error_bytes(str(log), 0) == os.path.getsize(log)


def test_returns_delta_after_marking_read(tmp_path: Path):
    log = tmp_path / "app_errors.log"
    log.write_text("ERROR a\n")
    seen = os.path.getsize(log)

    # Append a new error -- the unread count should be only the new bytes.
    with open(log, "a", encoding="utf-8") as fh:
        fh.write("ERROR b\n")

    assert unread_error_bytes(str(log), seen) == len("ERROR b\n")


def test_returns_zero_after_log_rotation(tmp_path: Path):
    """If the log was rotated (new file is smaller), treat as caught up."""
    log = tmp_path / "app_errors.log"
    log.write_text("short\n")
    # Operator's recorded offset is from a much larger pre-rotation log.
    huge_offset = 10_000_000
    assert unread_error_bytes(str(log), huge_offset) == 0
