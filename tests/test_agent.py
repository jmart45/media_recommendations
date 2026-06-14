import json
import pytest
import database
from database import init_db, db_add_media_type
from agent import run_agent
from agent.streaming import sse
from agent.tools import execute_tool


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    init_db()


# ---- sse() ----

def test_sse_format():
    result = sse({"type": "done"})
    assert result == 'data: {"type": "done"}\n\n'


def test_sse_preserves_payload():
    payload = {"type": "text", "content": "hello"}
    result = sse(payload)
    parsed = json.loads(result.removeprefix("data: ").strip())
    assert parsed == payload


# ---- execute_tool() ----

def test_execute_tool_add_media_type():
    result = json.loads(execute_tool("add_media_type", {"name": "Movies"}))
    assert result["success"] is True


def test_execute_tool_remove_media_type():
    execute_tool("add_media_type", {"name": "Movies"})
    result = json.loads(execute_tool("remove_media_type", {"name": "Movies"}))
    assert result["success"] is True


def test_execute_tool_add_media_item():
    execute_tool("add_media_type", {"name": "Movies"})
    result = json.loads(execute_tool("add_media_item", {
        "media_type": "Movies", "title": "Dune", "genre": "Sci-Fi", "rating": 4.5
    }))
    assert result["success"] is True


def test_execute_tool_update_media_rating():
    execute_tool("add_media_type", {"name": "Movies"})
    execute_tool("add_media_item", {"media_type": "Movies", "title": "Dune"})
    result = json.loads(execute_tool("update_media_rating", {
        "title": "Dune", "media_type": "Movies", "rating": 5.0
    }))
    assert result["success"] is True


def test_execute_tool_remove_media_item():
    execute_tool("add_media_type", {"name": "Movies"})
    execute_tool("add_media_item", {"media_type": "Movies", "title": "Dune"})
    result = json.loads(execute_tool("remove_media_item", {"title": "Dune", "media_type": "Movies"}))
    assert result["success"] is True


def test_execute_tool_list_media():
    execute_tool("add_media_type", {"name": "Movies"})
    result = json.loads(execute_tool("list_media", {}))
    assert result["success"] is True
    assert "Movies" in result["data"]


def test_execute_tool_list_media_filtered():
    execute_tool("add_media_type", {"name": "Movies"})
    result = json.loads(execute_tool("list_media", {"media_type": "Movies"}))
    assert result["success"] is True


def test_execute_tool_get_rated_media():
    execute_tool("add_media_type", {"name": "Movies"})
    execute_tool("add_media_item", {"media_type": "Movies", "title": "Dune", "rating": 4.5})
    result = json.loads(execute_tool("get_rated_media", {"media_type": "Movies"}))
    assert result["success"] is True
    assert result["data"][0]["title"] == "Dune"


def test_execute_tool_add_media_items_bulk():
    execute_tool("add_media_type", {"name": "Movies"})
    result = json.loads(execute_tool("add_media_items_bulk", {
        "media_type": "Movies",
        "items": [
            {"title": "Dune", "genre": "Sci-Fi", "rating": 4.5},
            {"title": "Inception", "genre": "Thriller", "rating": 5.0},
        ]
    }))
    assert result["success"] is True
    assert result["added"] == 2


def test_execute_tool_add_media_items_bulk_skips_duplicates():
    execute_tool("add_media_type", {"name": "Movies"})
    execute_tool("add_media_item", {"media_type": "Movies", "title": "Dune"})
    result = json.loads(execute_tool("add_media_items_bulk", {
        "media_type": "Movies",
        "items": [{"title": "Dune"}, {"title": "Inception"}]
    }))
    assert result["success"] is True
    assert result["added"] == 1



def test_execute_tool_unknown_tool():
    result = json.loads(execute_tool("nonexistent_tool", {}))
    assert result["success"] is False


@pytest.mark.anyio
async def test_run_agent_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    events = [e async for e in run_agent([{"role": "user", "content": "hi"}])]
    payloads = [json.loads(e.removeprefix("data: ").strip()) for e in events]
    types = [p["type"] for p in payloads]
    assert "text" in types
    assert types[-1] == "done"
    text = next(p["content"] for p in payloads if p["type"] == "text")
    assert "API key" in text
