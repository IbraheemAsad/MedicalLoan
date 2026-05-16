"""
Backup service for the SQLite database (B8).

Replaces the old "copy on every launch, keep last 5" behavior with a
tiered retention policy:

- Skip the launch backup entirely if the most recent one is younger than
  MIN_BACKUP_INTERVAL_HOURS. Saves disk on quick restarts and reduces the
  risk of a long error spree blowing away every good backup.
- Keep all backups from the last KEEP_RECENT_HOURS hours.
- After that window, keep one per day for KEEP_DAILY_DAYS days.
- After that window, keep one per ISO-week for KEEP_WEEKLY_WEEKS weeks.
- Anything older is removed.

Backup filenames follow `backup_YYYYMMDD_HHMMSS.db` so we can derive
their timestamps without stat() and avoid timezone surprises from
mtime across hosts.
"""

import glob
import logging
import os
import re
import shutil
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

MIN_BACKUP_INTERVAL_HOURS = 6
KEEP_RECENT_HOURS = 48
KEEP_DAILY_DAYS = 14
KEEP_WEEKLY_WEEKS = 12

_NAME_RE = re.compile(r'^backup_(\d{8})_(\d{6})\.db$')


def _parse_backup_time(filename: str) -> datetime | None:
    m = _NAME_RE.match(os.path.basename(filename))
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S')
    except ValueError:
        return None


def _list_backups(backup_dir: str) -> list[tuple[datetime, str]]:
    """Return [(timestamp, path), ...] sorted oldest-first."""
    pairs: list[tuple[datetime, str]] = []
    for path in glob.glob(os.path.join(backup_dir, 'backup_*.db')):
        ts = _parse_backup_time(path)
        if ts is not None:
            pairs.append((ts, path))
    pairs.sort()
    return pairs


def list_backups(backup_dir: str) -> list[tuple[datetime, str]]:
    """Public newest-first listing of backups under ``backup_dir``.

    Phase 5's restore-from-backup UI uses this to populate a chooser
    dialog. Returning newest-first matches what an operator wants to
    see (most recent backup at the top); the internal pruner still
    works oldest-first, which is why we keep both directions.
    """
    pairs = _list_backups(backup_dir)
    pairs.sort(key=lambda p: p[0], reverse=True)
    return pairs


def restore_backup(backup_path: str, db_path: str) -> str:
    """Replace ``db_path`` with ``backup_path`` after taking a safety copy.

    Returns the path to the safety copy of the *current* database that
    we make before overwriting it -- so a user who restored the wrong
    backup can recover. The safety copy lands next to the live DB
    with a ``pre_restore_<timestamp>.db`` filename so it's never
    confused with a regular tiered backup (which uses ``backup_*.db``).

    Raises
    ------
    FileNotFoundError
        If ``backup_path`` doesn't exist.
    """
    if not os.path.exists(backup_path):
        raise FileNotFoundError(backup_path)

    db_dir = os.path.dirname(db_path) or '.'
    os.makedirs(db_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safety_name = f"pre_restore_{timestamp}.db"
    safety_path = os.path.join(db_dir, safety_name)

    if os.path.exists(db_path):
        shutil.copy2(db_path, safety_path)
        log.info("Saved pre-restore safety copy to %s", safety_path)

    shutil.copy2(backup_path, db_path)
    log.info("Restored database from %s", backup_path)
    return safety_path


def perform_backup(db_path: str, *, now: datetime | None = None) -> str | None:
    """Create a timestamped backup if enough time has passed; prune old ones.

    Returns the new backup's path, or None if a backup was skipped because
    the most recent one is recent enough.
    """
    if not os.path.exists(db_path):
        return None
    now = now or datetime.now()

    backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    backups = _list_backups(backup_dir)
    if backups:
        latest_ts, _ = backups[-1]
        if now - latest_ts < timedelta(hours=MIN_BACKUP_INTERVAL_HOURS):
            log.debug("Skipping backup; latest is from %s", latest_ts)
            return None

    new_name = f"backup_{now.strftime('%Y%m%d_%H%M%S')}.db"
    new_path = os.path.join(backup_dir, new_name)
    shutil.copy2(db_path, new_path)
    log.info("Database backup created: %s", new_path)

    prune_backups(backup_dir, now=now)
    return new_path


def prune_backups(backup_dir: str, *, now: datetime | None = None) -> list[str]:
    """Apply the retention policy. Returns the list of removed paths.

    Policy walks newest -> oldest:
      - Within KEEP_RECENT_HOURS: keep everything.
      - Beyond that, until KEEP_DAILY_DAYS: keep at most one per calendar day.
      - Beyond that, until KEEP_WEEKLY_WEEKS: keep at most one per ISO-week.
      - Anything older: discard.
    """
    now = now or datetime.now()
    pairs = _list_backups(backup_dir)
    pairs.sort(key=lambda p: p[0], reverse=True)  # newest first

    recent_cutoff = now - timedelta(hours=KEEP_RECENT_HOURS)
    daily_cutoff = now - timedelta(days=KEEP_DAILY_DAYS)
    weekly_cutoff = now - timedelta(weeks=KEEP_WEEKLY_WEEKS)

    seen_days: set = set()
    seen_weeks: set = set()
    removed: list[str] = []

    for ts, path in pairs:
        keep = False
        if ts >= recent_cutoff:
            keep = True
        elif ts >= daily_cutoff:
            day_key = ts.date()
            if day_key not in seen_days:
                seen_days.add(day_key)
                keep = True
        elif ts >= weekly_cutoff:
            iso = ts.isocalendar()
            week_key = (iso[0], iso[1])
            if week_key not in seen_weeks:
                seen_weeks.add(week_key)
                keep = True
        # else: too old to keep at all.

        if not keep:
            try:
                os.remove(path)
                removed.append(path)
            except OSError as e:
                log.warning("Failed to remove old backup %s: %s", path, e)

    return removed
