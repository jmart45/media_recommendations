"""Shared result-shape helpers.

Every db_* function returns a plain dict with a "success" boolean. These
constructors keep that shape defined in one place rather than hand-built at
each return site. The shape is consumed in three ways — as a DB return value,
as an HTTP response body, and as an LLM tool result — so keeping it consistent
matters.
"""
from typing import Optional


def ok(message: Optional[str] = None, **fields) -> dict:
    """A success result. Pass a human-readable `message` and/or extra payload
    fields (e.g. data=..., added=..., media_type=...)."""
    result = {"success": True}
    if message is not None:
        result["message"] = message
    result.update(fields)
    return result


def err(message: str) -> dict:
    """A failure result with an explanatory message."""
    return {"success": False, "message": message}
