"""Queries for individual media items, plus the recommendation read paths
(get_rated_media) and bulk insert."""
import sqlite3
from typing import Optional

from .connection import get_conn
from .results import ok, err


def _resolve_type_id(conn: sqlite3.Connection, media_type: str) -> Optional[int]:
    """Return the id of a media type by name (case-insensitive), or None."""
    row = conn.execute(
        "SELECT id FROM media_types WHERE name = ? COLLATE NOCASE", (media_type,)
    ).fetchone()
    return row["id"] if row else None


def _validate_rating(rating: Optional[float]) -> Optional[str]:
    if rating is not None and not (0 <= rating <= 5):
        return f"Rating must be between 0 and 5, got {rating}."
    return None


def db_add_media_item(media_type: str, title: str, genre: Optional[str],
                      rating: Optional[float], notes: Optional[str]) -> dict:
    if (msg := _validate_rating(rating)):
        return err(msg)
    with get_conn() as conn:
        type_id = _resolve_type_id(conn, media_type)
        if type_id is None:
            return err(f"Media type '{media_type}' not found. Add it first.")
        existing = conn.execute(
            "SELECT id FROM media_items WHERE media_type_id = ? AND title = ? COLLATE NOCASE",
            (type_id, title)
        ).fetchone()
        if existing:
            return err(f"'{title}' already exists in {media_type}.")
        conn.execute(
            "INSERT INTO media_items (media_type_id, title, genre, rating, notes) VALUES (?, ?, ?, ?, ?)",
            (type_id, title, genre, rating, notes)
        )
        rating_str = str(rating) if rating is not None else "not yet seen/played"
        return ok(f"Added '{title}' to {media_type} (rating: {rating_str}).")


def db_update_media_rating(title: str, media_type: str, rating: Optional[float]) -> dict:
    if (msg := _validate_rating(rating)):
        return err(msg)
    with get_conn() as conn:
        type_id = _resolve_type_id(conn, media_type)
        if type_id is None:
            return err(f"Media type '{media_type}' not found.")
        cur = conn.execute(
            "UPDATE media_items SET rating = ? WHERE title = ? COLLATE NOCASE AND media_type_id = ?",
            (rating, title, type_id)
        )
        if cur.rowcount == 0:
            return err(f"'{title}' not found in {media_type}.")
        rating_str = str(rating) if rating is not None else "not yet seen/played"
        return ok(f"Updated '{title}' rating to {rating_str}.")


def db_remove_media_item(title: str, media_type: str) -> dict:
    with get_conn() as conn:
        type_id = _resolve_type_id(conn, media_type)
        if type_id is None:
            return err(f"Media type '{media_type}' not found.")
        cur = conn.execute(
            "DELETE FROM media_items WHERE title = ? COLLATE NOCASE AND media_type_id = ?",
            (title, type_id)
        )
        if cur.rowcount == 0:
            return err(f"'{title}' not found in {media_type}.")
        return ok(f"Removed '{title}' from {media_type}.")


def db_list_media(media_type: Optional[str] = None) -> dict:
    with get_conn() as conn:
        if media_type:
            row = conn.execute(
                "SELECT id, name FROM media_types WHERE name = ? COLLATE NOCASE", (media_type,)
            ).fetchone()
            if not row:
                return err(f"Media type '{media_type}' not found.")
            types = [dict(row)]
        else:
            types = [dict(r) for r in conn.execute(
                "SELECT id, name FROM media_types ORDER BY name").fetchall()]

        result = {}
        for t in types:
            items = conn.execute(
                """SELECT title, genre, rating, notes FROM media_items
                   WHERE media_type_id = ? ORDER BY title""",
                (t["id"],)
            ).fetchall()
            result[t["name"]] = [dict(i) for i in items]

        return ok(data=result)


def db_get_media_item(title: str, media_type: str) -> dict:
    with get_conn() as conn:
        type_id = _resolve_type_id(conn, media_type)
        if type_id is None:
            return err(f"Media type '{media_type}' not found.")
        item = conn.execute(
            """SELECT title, genre, rating, notes, created_at, updated_at
               FROM media_items WHERE media_type_id = ? AND title = ? COLLATE NOCASE""",
            (type_id, title)
        ).fetchone()
        if not item:
            return err(f"'{title}' not found in {media_type}.")
        return ok(data=dict(item), media_type=media_type)


def db_add_media_items_bulk(media_type: str, items: list[dict]) -> dict:
    """Insert multiple media items for a given type. Returns per-item success/failure."""
    with get_conn() as conn:
        type_id = _resolve_type_id(conn, media_type)
        if type_id is None:
            return err(f"Media type '{media_type}' not found. Add it first.")
        results = []
        for item in items:
            title = item.get("title", "").strip()
            if not title:
                results.append({"title": title, "success": False, "message": "Title is empty."})
                continue
            existing = conn.execute(
                "SELECT id FROM media_items WHERE media_type_id = ? AND title = ? COLLATE NOCASE",
                (type_id, title)
            ).fetchone()
            if existing:
                results.append({"title": title, "success": False, "message": "Already exists."})
                continue
            conn.execute(
                "INSERT INTO media_items (media_type_id, title, genre, rating, notes) VALUES (?, ?, ?, ?, ?)",
                (type_id, title, item.get("genre"), item.get("rating"), item.get("notes"))
            )
            results.append({"title": title, "success": True})
        added = sum(1 for r in results if r["success"])
        return ok(added=added, total=len(items), results=results)


def db_get_rated_media(media_type: str, genre: Optional[str] = None) -> dict:
    """Return rated items for a given media type, optionally filtered by genre,
    for use in recommendations."""
    with get_conn() as conn:
        type_id = _resolve_type_id(conn, media_type)
        if type_id is None:
            return err(f"Media type '{media_type}' not found.")

        query = """SELECT title, genre, rating, notes FROM media_items
                   WHERE media_type_id = ? AND rating IS NOT NULL"""
        params: list = [type_id]

        if genre:
            query += " AND genre LIKE ? ESCAPE '\\' COLLATE NOCASE"
            escaped = genre.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            params.append(f"%{escaped}%")

        query += " ORDER BY rating DESC"
        items = conn.execute(query, params).fetchall()
        return ok(data=[dict(i) for i in items], media_type=media_type, genre_filter=genre)
