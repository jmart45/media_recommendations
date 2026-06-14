"""Queries for media types (the top-level categories: Movies, Games, ...)."""
import sqlite3

from .connection import get_conn
from .results import ok, err


def db_add_media_type(name: str) -> dict:
    with get_conn() as conn:
        try:
            conn.execute("INSERT INTO media_types (name) VALUES (?)", (name,))
            return ok(f"Added media type '{name}'.")
        except sqlite3.IntegrityError:
            existing = conn.execute(
                "SELECT name FROM media_types WHERE name = ? COLLATE NOCASE", (name,)
            ).fetchone()
            canonical = existing["name"] if existing else name
            return err(f"Media type '{canonical}' already exists.")


def db_remove_media_type(name: str) -> dict:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM media_types WHERE name = ? COLLATE NOCASE", (name,))
        if cur.rowcount == 0:
            return err(f"Media type '{name}' not found.")
        return ok(f"Removed media type '{name}' and all its items.")


def db_list_media_types() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name FROM media_types ORDER BY name").fetchall()
        return [dict(r) for r in rows]
