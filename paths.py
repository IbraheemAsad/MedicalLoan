"""
Path helpers shared between Database, logging, and backups.

Centralizing these so the database file, the backups directory, and the
error log all live in the same place — next to the executable when frozen,
next to the script when running from source.
"""

import os
import sys


def application_data_dir() -> str:
    """Return the directory where persistent app data should live.

    - Frozen (PyInstaller .exe): directory containing the executable.
    - Source: directory containing this module.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def default_db_path() -> str:
    return os.path.join(application_data_dir(), 'medical_equipment.db')


def backups_dir(db_path: str) -> str:
    return os.path.join(os.path.dirname(db_path), 'backups')


def log_file_path(db_path: str) -> str:
    """Error log lives next to the DB so users find it where they expect."""
    return os.path.join(os.path.dirname(db_path), 'app_errors.log')
