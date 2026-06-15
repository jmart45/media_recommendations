"""Cache for external metadata (e.g. TMDB lookups), keyed by (title, kind)."""
import json
from typing import Optional

from .connection import get_conn


def db_get_metadata_cache(title: str, kind: str) -> Optional[dict]:
    """Return cached metadata for (title, kind), or None if not cached.
    A cached empty dict means a previous lookup found no match (negative cache)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT payload FROM metadata_cache WHERE title = ? COLLATE NOCASE AND kind = ?",
            (title, kind)
        ).fetchone()
        return json.loads(row["payload"]) if row else None


def db_set_metadata_cache(title: str, kind: str, payload: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO metadata_cache (title, kind, payload) VALUES (?, ?, ?)
               ON CONFLICT (title, kind) DO UPDATE SET payload = excluded.payload, fetched_at = CURRENT_TIMESTAMP""",
            (title, kind, json.dumps(payload))
        )
