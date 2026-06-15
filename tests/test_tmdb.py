import pytest
import database
from database import init_db, db_get_metadata_cache, db_set_metadata_cache
from tmdb import tmdb_kind_for, parse_search_result, enrich_items


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    init_db()


# ---- tmdb_kind_for() ----

def test_kind_for_movies():
    assert tmdb_kind_for("Movies") == "movie"


def test_kind_for_tv_variants():
    assert tmdb_kind_for("TV Shows") == "tv"
    assert tmdb_kind_for("Anime") == "tv"


def test_kind_for_unsupported_type():
    assert tmdb_kind_for("Games") is None
    assert tmdb_kind_for("Books") is None


# ---- parse_search_result() ----

def test_parse_movie_result():
    raw = {
        "id": 27205, "title": "Inception", "overview": "A thief...",
        "poster_path": "/abc.jpg", "release_date": "2010-07-15", "vote_average": 8.37,
    }
    parsed = parse_search_result(raw, "movie")
    assert parsed["tmdb_id"] == 27205
    assert parsed["title"] == "Inception"
    assert parsed["poster_url"].endswith("/abc.jpg")
    assert parsed["year"] == 2010
    assert parsed["tmdb_rating"] == 8.4


def test_parse_tv_result_uses_name_and_first_air_date():
    raw = {"id": 1, "name": "Dark", "first_air_date": "2017-12-01", "vote_average": 8.0}
    parsed = parse_search_result(raw, "tv")
    assert parsed["title"] == "Dark"
    assert parsed["year"] == 2017


def test_parse_result_missing_fields():
    parsed = parse_search_result({"id": 2}, "movie")
    assert parsed["poster_url"] is None
    assert parsed["year"] is None
    assert parsed["tmdb_rating"] is None
    assert parsed["overview"] is None


# ---- metadata cache ----

def test_metadata_cache_roundtrip():
    db_set_metadata_cache("Dune", "movie", {"tmdb_id": 1, "year": 2021})
    assert db_get_metadata_cache("Dune", "movie") == {"tmdb_id": 1, "year": 2021}


def test_metadata_cache_miss_returns_none():
    assert db_get_metadata_cache("Unknown", "movie") is None


def test_metadata_cache_case_insensitive_title():
    db_set_metadata_cache("Dune", "movie", {"tmdb_id": 1})
    assert db_get_metadata_cache("DUNE", "movie") == {"tmdb_id": 1}


def test_metadata_cache_upsert_overwrites():
    db_set_metadata_cache("Dune", "movie", {"tmdb_id": 1})
    db_set_metadata_cache("Dune", "movie", {"tmdb_id": 2})
    assert db_get_metadata_cache("Dune", "movie") == {"tmdb_id": 2}


def test_metadata_cache_keyed_by_kind():
    db_set_metadata_cache("Dune", "movie", {"tmdb_id": 1})
    assert db_get_metadata_cache("Dune", "tv") is None


# ---- enrich_items() ----

@pytest.mark.anyio
async def test_enrich_unsupported_type_no_metadata():
    items = [{"title": "Elden Ring", "genre": "RPG", "rating": 5.0}]
    enriched = await enrich_items("Games", items)
    assert enriched[0]["tmdb"] is None
    assert enriched[0]["title"] == "Elden Ring"


@pytest.mark.anyio
async def test_enrich_without_api_key_no_metadata():
    items = [{"title": "Dune", "genre": "Sci-Fi", "rating": 4.5}]
    enriched = await enrich_items("Movies", items)
    assert enriched[0]["tmdb"] is None


@pytest.mark.anyio
async def test_enrich_uses_cache_without_api_key():
    db_set_metadata_cache("Dune", "movie", {"tmdb_id": 1, "year": 2021})
    items = [{"title": "Dune", "genre": "Sci-Fi", "rating": 4.5}]
    enriched = await enrich_items("Movies", items)
    assert enriched[0]["tmdb"] == {"tmdb_id": 1, "year": 2021}


@pytest.mark.anyio
async def test_enrich_negative_cache_returns_none():
    db_set_metadata_cache("Obscure Title", "movie", {})
    items = [{"title": "Obscure Title", "genre": None, "rating": None}]
    enriched = await enrich_items("Movies", items)
    assert enriched[0]["tmdb"] is None


@pytest.mark.anyio
async def test_enrich_does_not_mutate_input():
    items = [{"title": "Dune", "genre": "Sci-Fi", "rating": 4.5}]
    await enrich_items("Movies", items)
    assert "tmdb" not in items[0]
