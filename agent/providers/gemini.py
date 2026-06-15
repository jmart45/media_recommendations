"""Gemini 2.0 Flash agent loop."""
import json
import os
from typing import AsyncGenerator

from google import genai
from google.genai.errors import ClientError

from ..streaming import sse
from ..prompts import SYSTEM_PROMPT
from ..tools import GEMINI_TOOLS, MUTATING_TOOLS, execute_tool

MODEL = "gemini-2.0-flash"


def _to_history(messages: list[dict]) -> list[dict]:
    result = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else msg["role"]
        content = msg["content"]
        if not isinstance(content, str):
            continue
        if not result and role != "user":
            continue
        result.append({"role": role, "parts": [{"text": content}]})
    return result


async def run(messages: list[dict]) -> AsyncGenerator[str, None]:
    if not os.environ.get("GEMINI_API_KEY"):
        yield sse({
            'type': 'text',
            'content': (
                "**API key not configured.**\n\n"
                "Add your Gemini API key to `.env`:\n\n"
                "```\nGEMINI_API_KEY=...\n```\n\n"
                "Get a free key at [aistudio.google.com](https://aistudio.google.com/apikey)."
            )
        })
        yield sse({'type': 'done'})
        return

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    history = _to_history(messages)

    try:
        while True:
            text_chunks: list[str] = []
            function_calls: list[dict] = []

            stream = await client.aio.models.generate_content_stream(
                model=MODEL,
                contents=history,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "tools": [{"function_declarations": GEMINI_TOOLS}],
                },
            )

            async for chunk in stream:
                if not chunk.candidates:
                    continue
                candidate = chunk.candidates[0]
                if not candidate.content or not candidate.content.parts:
                    continue
                for part in candidate.content.parts:
                    if part.text:
                        text_chunks.append(part.text)
                        yield sse({'type': 'text', 'content': part.text})
                    elif part.function_call and part.function_call.name:
                        fc = part.function_call
                        function_calls.append({"name": fc.name, "args": dict(fc.args)})

            model_parts = []
            if text_chunks:
                model_parts.append({"text": "".join(text_chunks)})
            for fc in function_calls:
                model_parts.append({"function_call": {"name": fc["name"], "args": fc["args"]}})
            if model_parts:
                history.append({"role": "model", "parts": model_parts})

            if not function_calls:
                break

            result_parts = []
            for fc in function_calls:
                yield sse({'type': 'tool_call', 'name': fc["name"], 'input': fc["args"]})
                try:
                    result = json.loads(execute_tool(fc["name"], fc["args"]))
                except Exception as exc:
                    result = {"success": False, "message": str(exc)}
                result_parts.append({
                    "function_response": {
                        "name": fc["name"],
                        "response": result,
                    }
                })
                if fc["name"] in MUTATING_TOOLS:
                    yield sse({'type': 'refresh_media'})

            history.append({"role": "user", "parts": result_parts})

    except ClientError as exc:
        code = exc.args[0] if exc.args else 0
        if code == 429:
            yield sse({
                'type': 'text',
                'content': (
                    "\n\n**Gemini quota exhausted.** You've hit the free-tier rate limit. "
                    "Try again in a few minutes, or switch providers by setting "
                    "`LLM_PROVIDER=groq` in `.env` (requires a `GROQ_API_KEY`)."
                )
            })
        else:
            yield sse({'type': 'text', 'content': f"\n\n**Gemini API error ({code}):** {exc}"})

    yield sse({'type': 'done'})
