"""Claude agent package.

Split into focused modules: streaming protocol helpers, the system prompt, the
tool registry, and the streaming loop. This __init__ re-exports the public
surface so callers and tests keep using `from agent import run_agent, sse,
parse_tool_input, execute_tool` exactly as before.
"""
from .streaming import sse, parse_tool_input
from .prompts import SYSTEM_PROMPT
from .tools import TOOLS, MUTATING_TOOLS, execute_tool
from .loop import MODEL, run_agent

__all__ = [
    "sse", "parse_tool_input",
    "SYSTEM_PROMPT",
    "TOOLS", "MUTATING_TOOLS", "execute_tool",
    "MODEL", "run_agent",
]
