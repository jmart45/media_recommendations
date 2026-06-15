"""HTTP-layer tests for the JSON API contract.

These pin the contract the frontend (and a future typed client) depend on:
typed success bodies with HTTP 200, and HTTP 404 on missing types/items.
The /api/chat streaming endpoint is not covered here since it calls the model.
"""
import pytest
from fastapi.testclient import TestClient

import database
from database import init_db, db_add_media_type, db_add_media_item


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    init_db()
    from main import app
    with TestClient(app) as c:
        yield c


# ---- /api/media ----

def test_list_media_empty(client):
    res = client.get("/api/media")
    assert res.status_code == 200
    assert res.json() == {"data": {}}


def test_list_media_with_items(client):
    db_add_media_type("Movies")
    db_add_media_item("Movies", "Dune", "Sci-Fi", 4.5, None)
    res = client.get("/api/media")
    assert res.status_code == 200
    movies = res.json()["data"]["Movies"]
    assert movies[0]["title"] == "Dune"
    assert movies[0]["rating"] == 4.5


def test_list_media_unknown_type_404(client):
    res = client.get("/api/media", params={"media_type": "Nope"})
    assert res.status_code == 404
    assert "Nope" in res.json()["detail"]


# ---- /api/media-types ----

def test_list_media_types(client):
    db_add_media_type("Movies")
    res = client.get("/api/media-types")
    assert res.status_code == 200
    names = [t["name"] for t in res.json()["types"]]
    assert names == ["Movies"]


# ---- /api/item ----

def test_get_item_found(client):
    db_add_media_type("Movies")
    db_add_media_item("Movies", "Dune", "Sci-Fi", 4.5, "great")
    res = client.get("/api/item", params={"media_type": "Movies", "title": "Dune"})
    assert res.status_code == 200
    body = res.json()
    assert body["media_type"] == "Movies"
    assert body["data"]["title"] == "Dune"
    assert body["data"]["notes"] == "great"


def test_get_item_not_found_404(client):
    db_add_media_type("Movies")
    res = client.get("/api/item", params={"media_type": "Movies", "title": "Ghost"})
    assert res.status_code == 404


def test_get_item_unknown_type_404(client):
    res = client.get("/api/item", params={"media_type": "Movies", "title": "Dune"})
    assert res.status_code == 404


# ---- PATCH /api/item/rating ----

def test_update_rating_success(client):
    db_add_media_type("Movies")
    db_add_media_item("Movies", "Dune", None, None, None)
    res = client.patch("/api/item/rating", json={"media_type": "Movies", "title": "Dune", "rating": 5.0})
    assert res.status_code == 200
    assert "message" in res.json()


def test_update_rating_not_found_404(client):
    db_add_media_type("Movies")
    res = client.patch("/api/item/rating", json={"media_type": "Movies", "title": "Ghost", "rating": 5.0})
    assert res.status_code == 404


def test_update_rating_out_of_range_422(client):
    db_add_media_type("Movies")
    db_add_media_item("Movies", "Dune", None, None, None)
    res = client.patch("/api/item/rating", json={"media_type": "Movies", "title": "Dune", "rating": 99})
    assert res.status_code == 422


# ---- PATCH /api/item/genre ----

def test_update_genre_success(client):
    db_add_media_type("Movies")
    db_add_media_item("Movies", "Dune", None, None, None)
    res = client.patch("/api/item/genre", json={"media_type": "Movies", "title": "Dune", "genre": "Sci-Fi"})
    assert res.status_code == 200
    assert "message" in res.json()


def test_update_genre_to_null(client):
    db_add_media_type("Movies")
    db_add_media_item("Movies", "Dune", "Sci-Fi", None, None)
    res = client.patch("/api/item/genre", json={"media_type": "Movies", "title": "Dune", "genre": None})
    assert res.status_code == 200


def test_update_genre_not_found_404(client):
    db_add_media_type("Movies")
    res = client.patch("/api/item/genre", json={"media_type": "Movies", "title": "Ghost", "genre": "Horror"})
    assert res.status_code == 404


# ---- DELETE /api/item ----

def test_delete_item_success(client):
    db_add_media_type("Movies")
    db_add_media_item("Movies", "Dune", None, None, None)
    res = client.delete("/api/item", params={"media_type": "Movies", "title": "Dune"})
    assert res.status_code == 200


def test_delete_item_not_found_404(client):
    db_add_media_type("Movies")
    res = client.delete("/api/item", params={"media_type": "Movies", "title": "Ghost"})
    assert res.status_code == 404


# ---- /api/browse ----

def test_browse_unknown_type_404(client):
    res = client.get("/api/browse", params={"media_type": "Nope"})
    assert res.status_code == 404


def test_browse_supported_type_no_api_key(client, monkeypatch):
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    db_add_media_type("Movies")
    db_add_media_item("Movies", "Dune", "Sci-Fi", 4.5, None)
    res = client.get("/api/browse", params={"media_type": "Movies"})
    assert res.status_code == 200
    body = res.json()
    assert body["media_type"] == "Movies"
    assert body["tmdb_supported"] is True
    assert body["tmdb_configured"] is False
    assert body["data"][0]["tmdb"] is None


def test_browse_unsupported_type_no_tmdb(client):
    db_add_media_type("Games")
    db_add_media_item("Games", "Elden Ring", "RPG", 5.0, None)
    res = client.get("/api/browse", params={"media_type": "Games"})
    assert res.status_code == 200
    body = res.json()
    assert body["tmdb_supported"] is False
    assert body["data"][0]["tmdb"] is None
