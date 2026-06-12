import sqlite3
from contextlib import contextmanager
from typing import Optional

DB_PATH = "media.db"


def init_db():
    with get_conn() as conn:
        conn.executescript("""
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

            CREATE TRIGGER IF NOT EXISTS update_media_items_updated_at
            AFTER UPDATE ON media_items
            BEGIN
                UPDATE media_items SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        """)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
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


# --- Media Types ---

def db_add_media_type(name: str) -> dict:
    with get_conn() as conn:
        try:
            conn.execute("INSERT INTO media_types (name) VALUES (?)", (name,))
            return {"success": True, "message": f"Added media type '{name}'."}
        except sqlite3.IntegrityError:
            return {"success": False, "message": f"Media type '{name}' already exists."}


def db_remove_media_type(name: str) -> dict:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM media_types WHERE name = ? COLLATE NOCASE", (name,))
        if cur.rowcount == 0:
            return {"success": False, "message": f"Media type '{name}' not found."}
        return {"success": True, "message": f"Removed media type '{name}' and all its items."}


def db_list_media_types() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name FROM media_types ORDER BY name").fetchall()
        return [dict(r) for r in rows]


# --- Media Items ---

def db_add_media_item(media_type: str, title: str, genre: Optional[str], rating: Optional[float], notes: Optional[str]) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM media_types WHERE name = ? COLLATE NOCASE", (media_type,)).fetchone()
        if not row:
            return {"success": False, "message": f"Media type '{media_type}' not found. Add it first."}
        type_id = row["id"]
        # Check for duplicate title within this type
        existing = conn.execute(
            "SELECT id FROM media_items WHERE media_type_id = ? AND title = ? COLLATE NOCASE",
            (type_id, title)
        ).fetchone()
        if existing:
            return {"success": False, "message": f"'{title}' already exists in {media_type}."}
        conn.execute(
            "INSERT INTO media_items (media_type_id, title, genre, rating, notes) VALUES (?, ?, ?, ?, ?)",
            (type_id, title, genre, rating, notes)
        )
        rating_str = str(rating) if rating is not None else "not yet seen/played"
        return {"success": True, "message": f"Added '{title}' to {media_type} (rating: {rating_str})."}


def db_update_media_rating(title: str, media_type: str, rating: Optional[float]) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM media_types WHERE name = ? COLLATE NOCASE", (media_type,)).fetchone()
        if not row:
            return {"success": False, "message": f"Media type '{media_type}' not found."}
        cur = conn.execute(
            "UPDATE media_items SET rating = ? WHERE title = ? COLLATE NOCASE AND media_type_id = ?",
            (rating, title, row["id"])
        )
        if cur.rowcount == 0:
            return {"success": False, "message": f"'{title}' not found in {media_type}."}
        rating_str = str(rating) if rating is not None else "not yet seen/played"
        return {"success": True, "message": f"Updated '{title}' rating to {rating_str}."}


def db_remove_media_item(title: str, media_type: str) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM media_types WHERE name = ? COLLATE NOCASE", (media_type,)).fetchone()
        if not row:
            return {"success": False, "message": f"Media type '{media_type}' not found."}
        cur = conn.execute(
            "DELETE FROM media_items WHERE title = ? COLLATE NOCASE AND media_type_id = ?",
            (title, row["id"])
        )
        if cur.rowcount == 0:
            return {"success": False, "message": f"'{title}' not found in {media_type}."}
        return {"success": True, "message": f"Removed '{title}' from {media_type}."}


def db_list_media(media_type: Optional[str] = None) -> dict:
    with get_conn() as conn:
        if media_type:
            row = conn.execute("SELECT id, name FROM media_types WHERE name = ? COLLATE NOCASE", (media_type,)).fetchone()
            if not row:
                return {"success": False, "message": f"Media type '{media_type}' not found."}
            types = [dict(row)]
        else:
            types = [dict(r) for r in conn.execute("SELECT id, name FROM media_types ORDER BY name").fetchall()]

        result = {}
        for t in types:
            items = conn.execute(
                """SELECT title, genre, rating, notes FROM media_items
                   WHERE media_type_id = ? ORDER BY title""",
                (t["id"],)
            ).fetchall()
            result[t["name"]] = [dict(i) for i in items]

        return {"success": True, "data": result}


def db_get_rated_media(media_type: str, genre: Optional[str] = None) -> dict:
    """Return rated items for a given media type, optionally filtered by genre, for use in recommendations."""
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM media_types WHERE name = ? COLLATE NOCASE", (media_type,)).fetchone()
        if not row:
            return {"success": False, "message": f"Media type '{media_type}' not found."}

        query = """SELECT title, genre, rating, notes FROM media_items
                   WHERE media_type_id = ? AND rating IS NOT NULL"""
        params: list = [row["id"]]

        if genre:
            query += " AND genre LIKE ? COLLATE NOCASE"
            params.append(f"%{genre}%")

        query += " ORDER BY rating DESC"
        items = conn.execute(query, params).fetchall()
        return {"success": True, "data": [dict(i) for i in items], "media_type": media_type, "genre_filter": genre}
