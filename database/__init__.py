"""SQLite persistence layer.

Split into focused modules by responsibility (connection/schema, media types,
media items, metadata cache). This __init__ re-exports the public surface so
callers and tests keep using `from database import db_add_media_item, ...`
and `database.DB_PATH` exactly as before.
"""
from .connection import DB_PATH, SCHEMA, get_conn, init_db
from .results import ok, err
from .media_types import (
    db_add_media_type,
    db_remove_media_type,
    db_list_media_types,
)
from .media_items import (
    db_add_media_item,
    db_update_media_rating,
    db_remove_media_item,
    db_list_media,
    db_get_media_item,
    db_add_media_items_bulk,
    db_get_rated_media,
)
from .metadata_cache import (
    db_get_metadata_cache,
    db_set_metadata_cache,
)

__all__ = [
    "DB_PATH", "SCHEMA", "get_conn", "init_db",
    "ok", "err",
    "db_add_media_type", "db_remove_media_type", "db_list_media_types",
    "db_add_media_item", "db_update_media_rating", "db_remove_media_item",
    "db_list_media", "db_get_media_item", "db_add_media_items_bulk", "db_get_rated_media",
    "db_get_metadata_cache", "db_set_metadata_cache",
]
