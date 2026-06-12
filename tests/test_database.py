import pytest
import database
from database import (
    init_db,
    db_add_media_type, db_remove_media_type, db_list_media_types,
    db_add_media_item, db_update_media_rating, db_remove_media_item,
    db_list_media, db_get_rated_media,
)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    init_db()


# ---- Media Types ----

def test_add_media_type():
    result = db_add_media_type("Movies")
    assert result["success"] is True
    assert "Movies" in db_list_media_types()[0]["name"]


def test_add_duplicate_media_type_fails():
    db_add_media_type("Movies")
    result = db_add_media_type("Movies")
    assert result["success"] is False


def test_add_media_type_case_insensitive_duplicate():
    db_add_media_type("Movies")
    result = db_add_media_type("movies")
    assert result["success"] is False


def test_remove_media_type():
    db_add_media_type("Movies")
    result = db_remove_media_type("Movies")
    assert result["success"] is True
    assert db_list_media_types() == []


def test_remove_nonexistent_media_type_fails():
    result = db_remove_media_type("Movies")
    assert result["success"] is False


def test_list_media_types_sorted():
    db_add_media_type("Music")
    db_add_media_type("Books")
    db_add_media_type("Games")
    names = [t["name"] for t in db_list_media_types()]
    assert names == sorted(names)


# ---- Media Items ----

@pytest.fixture
def with_movies():
    db_add_media_type("Movies")


def test_add_media_item(with_movies):
    result = db_add_media_item("Movies", "Dune", "Sci-Fi", 4.5, None)
    assert result["success"] is True


def test_add_media_item_unrated(with_movies):
    result = db_add_media_item("Movies", "Dune", "Sci-Fi", None, None)
    assert result["success"] is True
    data = db_list_media("Movies")["data"]["Movies"]
    assert data[0]["rating"] is None


def test_add_media_item_unknown_type_fails():
    result = db_add_media_item("Movies", "Dune", None, None, None)
    assert result["success"] is False


def test_add_duplicate_media_item_fails(with_movies):
    db_add_media_item("Movies", "Dune", None, None, None)
    result = db_add_media_item("Movies", "Dune", None, None, None)
    assert result["success"] is False


def test_add_duplicate_media_item_case_insensitive_fails(with_movies):
    db_add_media_item("Movies", "Dune", None, None, None)
    result = db_add_media_item("Movies", "dune", None, None, None)
    assert result["success"] is False


def test_update_media_rating(with_movies):
    db_add_media_item("Movies", "Dune", None, None, None)
    result = db_update_media_rating("Dune", "Movies", 4.0)
    assert result["success"] is True
    data = db_list_media("Movies")["data"]["Movies"]
    assert data[0]["rating"] == 4.0


def test_update_media_rating_to_null(with_movies):
    db_add_media_item("Movies", "Dune", None, 4.0, None)
    result = db_update_media_rating("Dune", "Movies", None)
    assert result["success"] is True
    data = db_list_media("Movies")["data"]["Movies"]
    assert data[0]["rating"] is None


def test_update_rating_nonexistent_item_fails(with_movies):
    result = db_update_media_rating("Ghost", "Movies", 3.0)
    assert result["success"] is False


def test_update_rating_nonexistent_type_fails():
    result = db_update_media_rating("Dune", "Movies", 3.0)
    assert result["success"] is False


def test_remove_media_item(with_movies):
    db_add_media_item("Movies", "Dune", None, None, None)
    result = db_remove_media_item("Dune", "Movies")
    assert result["success"] is True
    assert db_list_media("Movies")["data"]["Movies"] == []


def test_remove_nonexistent_media_item_fails(with_movies):
    result = db_remove_media_item("Ghost", "Movies")
    assert result["success"] is False


# ---- List & Query ----

def test_list_media_all_types():
    db_add_media_type("Movies")
    db_add_media_type("Games")
    db_add_media_item("Movies", "Dune", None, 4.5, None)
    db_add_media_item("Games", "Elden Ring", None, None, None)
    result = db_list_media()
    assert result["success"] is True
    assert "Movies" in result["data"]
    assert "Games" in result["data"]


def test_list_media_filtered_by_type(with_movies):
    db_add_media_item("Movies", "Dune", None, 4.5, None)
    result = db_list_media("Movies")
    assert result["success"] is True
    assert list(result["data"].keys()) == ["Movies"]


def test_list_media_unknown_type_fails():
    result = db_list_media("Nonexistent")
    assert result["success"] is False


def test_get_rated_media_excludes_unrated(with_movies):
    db_add_media_item("Movies", "Dune", "Sci-Fi", 4.5, None)
    db_add_media_item("Movies", "Inception", "Thriller", None, None)
    result = db_get_rated_media("Movies")
    assert result["success"] is True
    titles = [i["title"] for i in result["data"]]
    assert "Dune" in titles
    assert "Inception" not in titles


def test_get_rated_media_sorted_by_rating_desc(with_movies):
    db_add_media_item("Movies", "Dune", "Sci-Fi", 3.0, None)
    db_add_media_item("Movies", "Inception", "Thriller", 5.0, None)
    result = db_get_rated_media("Movies")
    ratings = [i["rating"] for i in result["data"]]
    assert ratings == sorted(ratings, reverse=True)


def test_get_rated_media_genre_filter(with_movies):
    db_add_media_item("Movies", "Dune", "Sci-Fi", 4.5, None)
    db_add_media_item("Movies", "The Shining", "Horror", 4.0, None)
    result = db_get_rated_media("Movies", genre="Horror")
    titles = [i["title"] for i in result["data"]]
    assert "The Shining" in titles
    assert "Dune" not in titles


def test_get_rated_media_unknown_type_fails():
    result = db_get_rated_media("Nonexistent")
    assert result["success"] is False


# ---- Cascade delete ----

def test_remove_media_type_cascades_to_items(with_movies):
    db_add_media_item("Movies", "Dune", None, 4.5, None)
    db_remove_media_type("Movies")
    # Type is gone; re-adding it should show empty items
    db_add_media_type("Movies")
    assert db_list_media("Movies")["data"]["Movies"] == []
