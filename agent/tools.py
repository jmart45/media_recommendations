"""Tool registry for the agent.

Each tool is declared once, in TOOL_REGISTRY, bundling its API schema, its
handler, and whether it mutates the database (mutations trigger a UI refresh).
The structures the rest of the app consumes — TOOLS (schemas sent to the model),
MUTATING_TOOLS, and execute_tool — are all derived from that single source, so
adding a tool means adding one entry here.
"""
import json

from database import (
    db_add_media_type, db_remove_media_type,
    db_add_media_item, db_add_media_items_bulk, db_update_media_rating, db_remove_media_item,
    db_list_media, db_get_rated_media,
)


# --- Handlers: each maps a validated tool input dict to a db_* call. ---

def _add_media_type(i: dict) -> dict:
    return db_add_media_type(i["name"])


def _remove_media_type(i: dict) -> dict:
    return db_remove_media_type(i["name"])


def _add_media_item(i: dict) -> dict:
    return db_add_media_item(
        i["media_type"], i["title"], i.get("genre"), i.get("rating"), i.get("notes")
    )


def _update_media_rating(i: dict) -> dict:
    return db_update_media_rating(i["title"], i["media_type"], i["rating"])


def _remove_media_item(i: dict) -> dict:
    return db_remove_media_item(i["title"], i["media_type"])


def _add_media_items_bulk(i: dict) -> dict:
    return db_add_media_items_bulk(i["media_type"], i.get("items", []))


def _list_media(i: dict) -> dict:
    return db_list_media(i.get("media_type"))


def _get_rated_media(i: dict) -> dict:
    return db_get_rated_media(i["media_type"], i.get("genre"))


# --- Registry: schema + handler + mutating flag, one entry per tool. ---

TOOL_REGISTRY = [
    {
        "name": "add_media_type",
        "description": "Add a new media category (e.g. Movies, Games, Music, Books).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the media type to add."}
            },
            "required": ["name"]
        },
        "handler": _add_media_type,
        "mutating": True,
    },
    {
        "name": "remove_media_type",
        "description": "Remove a media type and all its items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the media type to remove."}
            },
            "required": ["name"]
        },
        "handler": _remove_media_type,
        "mutating": True,
    },
    {
        "name": "add_media_item",
        "description": "Add a media item to a media type. Set rating to null if not yet seen/played. Always populate genre from your own knowledge if the user did not specify one.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_type": {"type": "string", "description": "The media category (e.g. Movies)."},
                "title": {"type": "string", "description": "The title of the media item."},
                "genre": {"type": "string", "description": "The genre (e.g. Horror, Comedy, RPG). Optional."},
                "rating": {
                    "type": ["number", "null"],
                    "description": "Rating from 0 to 5, or null if not yet seen/played."
                },
                "notes": {"type": "string", "description": "Personal notes. Optional."}
            },
            "required": ["media_type", "title"]
        },
        "handler": _add_media_item,
        "mutating": True,
    },
    {
        "name": "update_media_rating",
        "description": "Update the rating for an existing media item. Set to null to mark as not yet seen/played.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The title of the media item."},
                "media_type": {"type": "string", "description": "The media category it belongs to."},
                "rating": {
                    "type": ["number", "null"],
                    "description": "New rating from 0 to 5, or null for not yet seen/played."
                }
            },
            "required": ["title", "media_type", "rating"]
        },
        "handler": _update_media_rating,
        "mutating": True,
    },
    {
        "name": "remove_media_item",
        "description": "Remove a specific media item from a media type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The title to remove."},
                "media_type": {"type": "string", "description": "The media category it belongs to."}
            },
            "required": ["title", "media_type"]
        },
        "handler": _remove_media_item,
        "mutating": True,
    },
    {
        "name": "list_media",
        "description": "List all tracked media, optionally filtered by media type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_type": {"type": "string", "description": "Filter by this media type. Omit for all types."}
            }
        },
        "handler": _list_media,
        "mutating": False,
    },
    {
        "name": "add_media_items_bulk",
        "description": "Add multiple media items to a type in one call. You MUST use this tool instead of add_media_item whenever the user provides more than 3 items — never loop add_media_item for a list. Always populate genre for each item from your own knowledge if the user did not specify one.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_type": {"type": "string", "description": "The media category (e.g. Movies)."},
                "items": {
                    "type": "array",
                    "description": "List of media items to add.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title":  {"type": "string"},
                            "genre":  {"type": "string"},
                            "rating": {"type": ["number", "null"], "description": "0–5 or null if not yet seen/played."},
                            "notes":  {"type": "string"}
                        },
                        "required": ["title"]
                    }
                }
            },
            "required": ["media_type", "items"]
        },
        "handler": _add_media_items_bulk,
        "mutating": True,
    },
    {
        "name": "get_rated_media",
        "description": "Get rated (seen/played) media for a type, optionally filtered by genre. Use this before generating recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_type": {"type": "string", "description": "The media category to fetch."},
                "genre": {"type": "string", "description": "Filter by genre (e.g. Horror, Comedy). Optional."}
            },
            "required": ["media_type"]
        },
        "handler": _get_rated_media,
        "mutating": False,
    },
]


# --- Derived views over the registry. ---

# Schemas passed to the model (handler/mutating stripped out).
TOOLS = [
    {k: tool[k] for k in ("name", "description", "input_schema")}
    for tool in TOOL_REGISTRY
]

# Tools that modify the database and should trigger a sidebar refresh in the UI.
MUTATING_TOOLS = {tool["name"] for tool in TOOL_REGISTRY if tool["mutating"]}

_HANDLERS = {tool["name"]: tool["handler"] for tool in TOOL_REGISTRY}


def execute_tool(name: str, inputs: dict) -> str:
    """Run a tool by name and return its result as a JSON string."""
    handler = _HANDLERS.get(name)
    if handler is None:
        return json.dumps({"success": False, "message": f"Unknown tool: {name}"})
    return json.dumps(handler(inputs))
