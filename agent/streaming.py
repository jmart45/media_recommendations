import json


def sse(payload: dict) -> str:
    """Format a payload as a Server-Sent Event line."""
    return f"data: {json.dumps(payload)}\n\n"
