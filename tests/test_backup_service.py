"""
Tests for backup_service (B8): cadence + tiered retention.
"""

import os
from datetime import datetime, timedelta

from services import backup_service


def _touch_backup(backup_dir: str, when: datetime) -> str:
    os.makedirs(backup_dir, exist_ok=True)
    name = f"backup_{when.strftime('%Y%m%d_%H%M%S')}.db"
    path = os.path.join(backup_dir, name)
    with open(path, "wb") as f:
        f.write(b"")
    return path


def test_skips_backup_if_recent_enough(tmp_path):
    db_path = tmp_path / "x.db"
    db_path.write_bytes(b"db contents")
    backup_dir = os.path.join(os.path.dirname(str(db_path)), "backups")
    now = datetime(2026, 5, 16, 12, 0, 0)
    _touch_backup(backup_dir, now - timedelta(hours=1))

    result = backup_service.perform_backup(str(db_path), now=now)
    assert result is None
    # Only the original backup remains.
    assert len(os.listdir(backup_dir)) == 1


def test_creates_backup_when_old_enough(tmp_path):
    db_path = tmp_path / "x.db"
    db_path.write_bytes(b"db contents")
    backup_dir = os.path.join(os.path.dirname(str(db_path)), "backups")
    now = datetime(2026, 5, 16, 12, 0, 0)
    _touch_backup(backup_dir, now - timedelta(hours=24))

    result = backup_service.perform_backup(str(db_path), now=now)
    assert result is not None
    assert os.path.exists(result)


def test_retention_keeps_recent_then_daily_then_weekly(tmp_path):
    backup_dir = str(tmp_path / "backups")
    os.makedirs(backup_dir, exist_ok=True)
    now = datetime(2026, 5, 16, 12, 0, 0)

    # 3 backups within the recent window -> all kept
    for h in (1, 12, 36):
        _touch_backup(backup_dir, now - timedelta(hours=h))
    # 5 backups across 3 days within the daily window -> 3 kept (one per day)
    for delta in (
        timedelta(days=3, hours=1),
        timedelta(days=3, hours=10),
        timedelta(days=4, hours=2),
        timedelta(days=4, hours=14),
        timedelta(days=5, hours=8),
    ):
        _touch_backup(backup_dir, now - delta)
    # 4 backups in the same ISO-week within the weekly window -> 1 kept
    base_week = now - timedelta(weeks=4)
    for hours in (0, 5, 30, 50):
        _touch_backup(backup_dir, base_week - timedelta(hours=hours))
    # 1 ancient backup, beyond the weekly window -> dropped
    _touch_backup(backup_dir, now - timedelta(weeks=20))

    backup_service.prune_backups(backup_dir, now=now)

    survivors = sorted(os.listdir(backup_dir))
    # 3 (recent) + 3 (daily, one per day) + 1 (weekly) = 7
    assert len(survivors) == 7


def test_perform_backup_handles_missing_db(tmp_path):
    """Calling perform_backup before the DB has been created shouldn't crash."""
    result = backup_service.perform_backup(str(tmp_path / "missing.db"))
    assert result is None
