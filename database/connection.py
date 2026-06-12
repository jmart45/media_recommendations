"""Database connection management and schema definition.

This is the leaf module of the `database` package: it imports nothing else
from the package, so the entity modules (media_types, media_items,
metadata_cache) can all depend on `get_conn` without import cycles.
"""
import sqlite3
from contextlib import contextmanager

DB_PATH = "media.db"

SCHEMA = """
    -- future: add a `users` table and a user_id FK on media_types/media_items
    -- when the app goes multi-tenant. Type names are unique globally today;
    -- that becomes UNIQUE(user_id, name) at that point.
    CREATE TABLE IF NOT EXISTS media_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE COLLATE NOCASE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS media_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        media_type_id INTEGER NOT NULL REFERENCES media_types(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        genre TEXT,
        rating REAL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_media_items_type ON media_items(media_type_id);

    CREATE TRIGGER IF NOT EXISTS update_media_items_updated_at
    AFTER UPDATE ON media_items
    BEGIN
        UPDATE media_items SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

    CREATE TABLE IF NOT EXISTS metadata_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL COLLATE NOCASE,
        kind TEXT NOT NULL,
        payload TEXT NOT NULL,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (title, kind)
    );
"""


def _resolve_db_path() -> str:
    """Resolve the DB path at call time.

    Tests monkeypatch `database.DB_PATH` (the name re-exported from the package
    __init__), so we read it through the package here rather than binding the
    module-level constant, ensuring the override is honored.
    """
    import database
    return getattr(database, "DB_PATH", DB_PATH)


@contextmanager
def get_conn():
    conn = sqlite3.connect(_resolve_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
