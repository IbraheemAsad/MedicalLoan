"""Tests for ``services.backup_service.list_backups`` and ``restore_backup``."""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path

import pytest

from services.backup_service import list_backups, perform_backup, restore_backup


def _seed_backup(backup_dir: Path, when: datetime, content: bytes = b"DB") -> Path:
    name = f"backup_{when.strftime('%Y%m%d_%H%M%S')}.db"
    path = backup_dir / name
    path.write_bytes(content)
    return path


def test_list_backups_returns_newest_first(tmp_path: Path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    older = _seed_backup(backup_dir, datetime(2026, 5, 14, 8, 0, 0))
    newest = _seed_backup(backup_dir, datetime(2026, 5, 16, 12, 30, 0))
    middle = _seed_backup(backup_dir, datetime(2026, 5, 15, 9, 0, 0))

    pairs = list_backups(str(backup_dir))
    paths = [p for _ts, p in pairs]
    assert paths == [str(newest), str(middle), str(older)]


def test_list_backups_ignores_non_matching_filenames(tmp_path: Path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    _seed_backup(backup_dir, datetime(2026, 5, 16, 12, 0, 0))
    # Random files in the backups dir shouldn't trip up the listing.
    (backup_dir / "README.txt").write_text("notes")
    (backup_dir / "pre_restore_20260101_120000.db").write_bytes(b"x")
    (backup_dir / "backup_BAD.db").write_bytes(b"x")  # malformed timestamp

    pairs = list_backups(str(backup_dir))
    assert len(pairs) == 1


def test_restore_backup_writes_safety_copy(tmp_path: Path):
    db = tmp_path / "medical_equipment.db"
    db.write_bytes(b"LIVE DB STATE")

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    backup = _seed_backup(
        backup_dir, datetime(2026, 5, 14, 8, 0, 0), content=b"RESTORED",
    )

    safety_path = restore_backup(str(backup), str(db))

    assert db.read_bytes() == b"RESTORED"
    assert os.path.exists(safety_path)
    assert Path(safety_path).read_bytes() == b"LIVE DB STATE"
    assert os.path.basename(safety_path).startswith("pre_restore_")


def test_restore_backup_raises_for_missing_source(tmp_path: Path):
    db = tmp_path / "medical_equipment.db"
    db.write_bytes(b"x")
    with pytest.raises(FileNotFoundError):
        restore_backup(str(tmp_path / "ghost.db"), str(db))


def test_restore_backup_when_db_doesnt_exist_yet(tmp_path: Path):
    """Restoring into an empty data dir should succeed without a safety copy."""
    db = tmp_path / "medical_equipment.db"  # not created yet
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    backup = _seed_backup(backup_dir, datetime(2026, 5, 14, 8, 0, 0), b"R")

    safety = restore_backup(str(backup), str(db))

    assert db.read_bytes() == b"R"
    # Safety path is *named* but won't exist on disk because there
    # was nothing to copy. The function still returns the path so a
    # caller can include it in a status message.
    assert not os.path.exists(safety)


def test_perform_backup_then_list_round_trip(tmp_path: Path):
    """Smoke test: ``perform_backup`` writes a file ``list_backups`` finds."""
    db = tmp_path / "medical_equipment.db"
    db.write_bytes(b"x")
    perform_backup(str(db))

    backups = list_backups(str(tmp_path / "backups"))
    assert len(backups) == 1
