"""The Claude agent loop: streams model output, executes tool calls, and feeds
results back into the conversation, yielding SSE events to the browser."""
import os
from typing import Optional, AsyncGenerator

import anthropic

from .streaming import sse, parse_tool_input
from .prompts import SYSTEM_PROMPT
from .tools import TOOLS, MUTATING_TOOLS, execute_tool

MODEL = "claude-opus-4-8"


async def run_agent(messages: list[dict]) -> AsyncGenerator[str, None]:
    """Run the Claude agent loop, yielding SSE-formatted strings."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        yield sse({
            'type': 'text',
            'content': (
                "**API key not configured.**\n\n"
                "Add your Anthropic API key to `.env`:\n\n"
                "```\nANTHROPIC_API_KEY=sk-ant-...\n```\n\n"
                "Get a key at [console.anthropic.com](https://console.anthropic.com/settings/keys)."
            )
        })
        yield sse({'type': 'done'})
        return

    client = anthropic.Anthropic()

    while True:
        text_chunks = []
        tool_uses = []
        stop_reason = None

        with client.messages.stream(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            thinking={"type": "adaptive"},
            messages=messages,
        ) as stream:
            current_tool: Optional[dict] = None

            for event in stream:
                if event.type == "content_block_start":
                    block = event.content_block
                    if block.type == "tool_use":
                        current_tool = {"id": block.id, "name": block.name, "input_json": ""}
                    elif block.type == "text":
                        current_tool = None

                elif event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        text_chunks.append(delta.text)
                        yield sse({'type': 'text', 'content': delta.text})
                    elif delta.type == "input_json_delta" and current_tool is not None:
                        current_tool["input_json"] += delta.partial_json

                elif event.type == "content_block_stop":
                    if current_tool is not None:
                        tool_uses.append(current_tool)
                        current_tool = None

                elif event.type == "message_delta":
                    stop_reason = event.delta.stop_reason

        # Build assistant message for conversation history
        assistant_content = []
        if text_chunks:
            assistant_content.append({"type": "text", "text": "".join(text_chunks)})
        for tu in tool_uses:
            assistant_content.append({
                "type": "tool_use",
                "id": tu["id"],
                "name": tu["name"],
                "input": parse_tool_input(tu["input_json"])
            })

        messages = messages + [{"role": "assistant", "content": assistant_content}]

        if stop_reason == "max_tokens":
            yield sse({'type': 'max_tokens_warning'})
            break

        if stop_reason != "tool_use" or not tool_uses:
            break

        # Execute tools and feed results back into the conversation
        tool_results = []
        for tu in tool_uses:
            parsed_input = parse_tool_input(tu["input_json"])
            tool_name = tu["name"]

            yield sse({'type': 'tool_call', 'name': tool_name, 'input': parsed_input})

            result_str = execute_tool(tool_name, parsed_input)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu["id"],
                "content": result_str
            })

            if tool_name in MUTATING_TOOLS:
                yield sse({'type': 'refresh_media'})

        messages = messages + [{"role": "user", "content": tool_results}]

    yield sse({'type': 'done'})
