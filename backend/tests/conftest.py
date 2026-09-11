"""Test bootstrap: set a hermetic SQLite DATABASE_URL before any app import.

Runs before any test module import, so app.core.config.Settings() is always
constructed with a valid database URL regardless of collection order or of a
missing .env file.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_saksham.db")
os.environ.setdefault("SEED_ON_STARTUP", "1")