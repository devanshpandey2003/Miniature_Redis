"""
Dependency-injection providers. Routes ask for these via `Depends(...)`
instead of importing globals directly -- this is what makes routes easy to
unit-test later (you can swap in a fake store in tests without touching
route code).
"""
from app.core.store import store as _store
from app.core.persistence import AOFLogger
from app.config import settings

# One process-wide AOF logger instance, built from config.
aof_logger = AOFLogger(settings.aof_path)


def get_store():
    """Hand every route the same shared KVStore instance."""
    return _store


def get_aof_logger():
    """Hand every route the same shared AOFLogger instance."""
    return aof_logger
