"""Provider selector: reads LLM_PROVIDER from env and delegates to the matching provider."""
import os


def run_agent(messages: list[dict]):
    """Return an async generator that streams SSE events for the given messages."""
    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()
    if provider == "groq":
        from .providers.groq import run
    else:
        from .providers.gemini import run
    return run(messages)
