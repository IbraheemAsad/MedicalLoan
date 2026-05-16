"""
Shared pytest configuration.

Adds the project root to sys.path so test modules can `import database`
without us having to install the project as a package. Once Phase 3
introduces `pyproject.toml` and a real package layout this hack goes
away.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


import pytest

from database import Database


@pytest.fixture
def db(tmp_path):
    """Per-test on-disk SQLite DB.

    We use a real file rather than `:memory:` because the schema
    migrator distinguishes between a brand-new file and one with
    pre-existing tables — round-tripping through disk is a closer
    match to production.
    """
    path = tmp_path / "test.db"
    database = Database(str(path))
    yield database
    database.close()
