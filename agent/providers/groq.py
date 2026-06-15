"""Groq (Llama 3.3 70B) agent loop."""
import json
import os
from typing import AsyncGenerator

import groq as groq_sdk

from ..streaming import sse
from ..prompts import SYSTEM_PROMPT
from ..tools import GROQ_TOOLS, MUTATING_TOOLS, execute_tool

MODEL = "llama-3.3-70b-versatile"
_FAILED_FUNCTION_CALL = "Failed to call a function"


def _to_history(messages: list[dict]) -> list[dict]:
    result: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in messages:
        content = msg["content"]
        if isinstance(content, str) and content:
            result.append({"role": msg["role"], "content": content})
    return result


async def _stream_request(client: groq_sdk.AsyncGroq, history: list[dict], use_tools: bool) -> AsyncGenerator:
    """Single streaming API call, with or without tools."""
    kwargs: dict = {"model": MODEL, "messages": history, "stream": True}
    if use_tools:
        kwargs["tools"] = GROQ_TOOLS
        kwargs["tool_choice"] = "auto"
    stream = await client.chat.completions.create(**kwargs)
    async for chunk in stream:
        yield chunk


async def run(messages: list[dict]) -> AsyncGenerator[str, None]:
    if not os.environ.get("GROQ_API_KEY"):
        yield sse({
            'type': 'text',
            'content': (
                "**API key not configured.**\n\n"
                "Add your Groq API key to `.env`:\n\n"
                "```\nGROQ_API_KEY=...\n```\n\n"
                "Get a free key at [console.groq.com](https://console.groq.com)."
            )
        })
        yield sse({'type': 'done'})
        return

    client = groq_sdk.AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
    history = _to_history(messages)

    try:
        tools_executed = False
        while True:
            text_chunks: list[str] = []
            tool_call_accum: dict[int, dict] = {}

            try:
                # After tools run, omit tools entirely so the model can't
                # attempt another (often malformed) function call.
                async for chunk in _stream_request(client, history, use_tools=not tools_executed):
                    delta = chunk.choices[0].delta

                    if delta.content:
                        text_chunks.append(delta.content)
                        yield sse({'type': 'text', 'content': delta.content})

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_call_accum:
                                tool_call_accum[idx] = {'id': '', 'name': '', 'arguments': ''}
                            if tc.id:
                                tool_call_accum[idx]['id'] = tc.id
                            if tc.function and tc.function.name:
                                tool_call_accum[idx]['name'] += tc.function.name
                            if tc.function and tc.function.arguments:
                                tool_call_accum[idx]['arguments'] += tc.function.arguments

            except groq_sdk.APIError as exc:
                if _FAILED_FUNCTION_CALL in str(exc) and not tools_executed:
                    # Model generated a malformed tool call — retry without tools
                    # so it responds in plain text instead.
                    async for chunk in _stream_request(client, history, use_tools=False):
                        content = chunk.choices[0].delta.content
                        if content:
                            yield sse({'type': 'text', 'content': content})
                    break
                raise

            function_calls = []
            for v in tool_call_accum.values():
                if not v['name']:
                    continue
                try:
                    args = json.loads(v['arguments'] or '{}')
                except json.JSONDecodeError:
                    continue
                function_calls.append({'id': v['id'], 'name': v['name'], 'args': args})

            assistant_msg: dict = {"role": "assistant", "content": "".join(text_chunks) or None}
            if function_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": fc["id"],
                        "type": "function",
                        "function": {"name": fc["name"], "arguments": json.dumps(fc["args"])},
                    }
                    for fc in function_calls
                ]
            history.append(assistant_msg)

            if not function_calls:
                break

            for fc in function_calls:
                yield sse({'type': 'tool_call', 'name': fc["name"], 'input': fc["args"]})
                try:
                    result_str = execute_tool(fc["name"], fc["args"])
                except Exception as exc:
                    result_str = json.dumps({"success": False, "message": str(exc)})
                history.append({
                    "role": "tool",
                    "tool_call_id": fc["id"],
                    "content": result_str,
                })
                if fc["name"] in MUTATING_TOOLS:
                    yield sse({'type': 'refresh_media'})
            tools_executed = True

    except groq_sdk.RateLimitError:
        yield sse({
            'type': 'text',
            'content': (
                "\n\n**Groq quota exhausted.** You've hit the free-tier rate limit. "
                "Try again in a minute, or switch providers by setting "
                "`LLM_PROVIDER=gemini` in `.env` (requires a `GEMINI_API_KEY`)."
            )
        })
    except groq_sdk.AuthenticationError:
        yield sse({'type': 'text', 'content': "\n\n**Groq authentication failed.** Check your `GROQ_API_KEY` in `.env`."})
    except groq_sdk.APIError as exc:
        if tools_executed:
            async for chunk in _stream_request(client, history, use_tools=False):
                content = chunk.choices[0].delta.content
                if content:
                    yield sse({'type': 'text', 'content': content})
        else:
            yield sse({'type': 'text', 'content': f"\n\n**Groq API error:** {exc}"})
    except Exception as exc:
        yield sse({'type': 'text', 'content': f"\n\n**Unexpected error:** {exc}"})

    yield sse({'type': 'done'})
