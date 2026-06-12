"""Helpers for the streaming protocol between the agent loop and the browser.

`sse` formats Server-Sent Events; `parse_tool_input` decodes the partial JSON
accumulated from a streamed tool_use block.
"""
import json


def sse(payload: dict) -> str:
    """Format a payload as a Server-Sent Event line."""
    return f"data: {json.dumps(payload)}\n\n"


def parse_tool_input(raw_json: str) -> dict:
    """Decode a tool's accumulated input JSON, tolerating empty/invalid input."""
    try:
        return json.loads(raw_json) if raw_json else {}
    except json.JSONDecodeError:
        return {}
