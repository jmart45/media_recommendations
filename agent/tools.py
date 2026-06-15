"""Tool registry for the agent.

Each tool is declared once in TOOL_REGISTRY, bundling its schema, handler, and
whether it mutates the database. GEMINI_TOOLS, MUTATING_TOOLS, and execute_tool
are all derived from that single source — adding a tool means one entry here.
"""
import json

from database import (
    db_add_media_type, db_remove_media_type,
    db_add_media_item, db_add_media_items_bulk, db_update_media_item, db_remove_media_item,
    db_list_media, db_get_rated_media,
)


# --- Handlers: each maps a validated tool input dict to a db_* call. ---

def _add_media_type(args: dict) -> dict:
    return db_add_media_type(args["name"])


def _remove_media_type(args: dict) -> dict:
    return db_remove_media_type(args["name"])


def _add_media_item(args: dict) -> dict:
    return db_add_media_item(
        args["media_type"], args["title"], args.get("genre"), args.get("rating"), args.get("notes")
    )


def _update_media_item(args: dict) -> dict:
    kwargs = {}
    if "genre" in args:
        kwargs["genre"] = args["genre"]
    if "rating" in args:
        kwargs["rating"] = args["rating"]
    if "notes" in args:
        kwargs["notes"] = args["notes"]
    return db_update_media_item(args["title"], args["media_type"], **kwargs)


def _remove_media_item(args: dict) -> dict:
    return db_remove_media_item(args["title"], args["media_type"])


def _add_media_items_bulk(args: dict) -> dict:
    return db_add_media_items_bulk(args["media_type"], args.get("items", []))


def _list_media(args: dict) -> dict:
    return db_list_media(args.get("media_type"))


def _get_rated_media(args: dict) -> dict:
    return db_get_rated_media(args["media_type"], args.get("genre"))


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
        "description": "Add a media item to a media type. Set rating to null if not yet seen/played. REQUIRED: Always populate genre from your own knowledge — never omit it unless the title is completely unknown to you.",
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
        "name": "update_media_item",
        "description": "Update any fields of an existing media item. Provide only the fields you want to change — genre, rating, and/or notes. To clear a field, pass null.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The title of the media item to update."},
                "media_type": {"type": "string", "description": "The media category it belongs to."},
                "genre": {
                    "type": ["string", "null"],
                    "description": "New genre, or null to clear it. Omit to leave unchanged."
                },
                "rating": {
                    "type": ["number", "null"],
                    "description": "New rating from 0 to 5, or null to mark as not yet seen/played. Omit to leave unchanged."
                },
                "notes": {
                    "type": ["string", "null"],
                    "description": "New personal notes, or null to clear them. Omit to leave unchanged."
                },
            },
            "required": ["title", "media_type"]
        },
        "handler": _update_media_item,
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
        "description": "Add multiple media items to a type in one call. You MUST use this tool instead of add_media_item whenever the user provides more than 3 items — never loop add_media_item for a list. REQUIRED: Always populate genre for every item from your own knowledge — never omit it unless the title is completely unknown to you.",
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

MUTATING_TOOLS = {tool["name"] for tool in TOOL_REGISTRY if tool["mutating"]}

_HANDLERS = {tool["name"]: tool["handler"] for tool in TOOL_REGISTRY}


def execute_tool(name: str, inputs: dict) -> str:
    """Run a tool by name and return its result as a JSON string."""
    handler = _HANDLERS.get(name)
    if handler is None:
        return json.dumps({"success": False, "message": f"Unknown tool: {name}"})
    return json.dumps(handler(inputs))


# --- Gemini tool format conversion. ---

def _convert_schema(schema: dict) -> dict:
    """Convert Anthropic-style JSON schema to Gemini-compatible schema."""
    result = {}
    type_val = schema.get("type")
    if isinstance(type_val, list):
        # e.g. ["number", "null"] -> type: "number", nullable: True
        non_null = [t for t in type_val if t != "null"]
        result["type"] = non_null[0] if non_null else "string"
        if "null" in type_val:
            result["nullable"] = True
    elif type_val:
        result["type"] = type_val
    for key in ("description", "enum", "required"):
        if key in schema:
            result[key] = schema[key]
    if "properties" in schema:
        result["properties"] = {k: _convert_schema(v) for k, v in schema["properties"].items()}
    if "items" in schema:
        result["items"] = _convert_schema(schema["items"])
    return result


GEMINI_TOOLS = [
    {
        "name": tool["name"],
        "description": tool["description"],
        "parameters": _convert_schema(tool["input_schema"]),
    }
    for tool in TOOL_REGISTRY
]


# --- Groq / OpenAI tool format conversion. ---

def _to_openai_schema(schema: dict) -> dict:
    """Convert to OpenAI-compatible JSON Schema (anyOf for nullable types)."""
    result = {}
    type_val = schema.get("type")
    if isinstance(type_val, list):
        non_null = [t for t in type_val if t != "null"]
        result["anyOf"] = [{"type": t} for t in non_null]
        if "null" in type_val:
            result["anyOf"].append({"type": "null"})
    elif type_val:
        result["type"] = type_val
    for key in ("description", "enum", "required"):
        if key in schema:
            result[key] = schema[key]
    if "properties" in schema:
        result["properties"] = {k: _to_openai_schema(v) for k, v in schema["properties"].items()}
    if "items" in schema:
        result["items"] = _to_openai_schema(schema["items"])
    return result


GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": _to_openai_schema(tool["input_schema"]),
        },
    }
    for tool in TOOL_REGISTRY
]
