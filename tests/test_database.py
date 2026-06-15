import pytest
import database
from database import (
    init_db,
    db_add_media_type, db_remove_media_type, db_list_media_types,
    db_add_media_item, db_add_media_items_bulk,
    db_update_media_item, db_update_media_rating, db_update_media_genre,
    db_remove_media_item,
    db_list_media, db_get_rated_media, db_get_media_item,
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


def test_update_media_genre(with_movies):
    db_add_media_item("Movies", "Dune", None, None, None)
    result = db_update_media_genre("Dune", "Movies", "Sci-Fi")
    assert result["success"] is True
    data = db_list_media("Movies")["data"]["Movies"]
    assert data[0]["genre"] == "Sci-Fi"


def test_update_media_genre_to_null(with_movies):
    db_add_media_item("Movies", "Dune", "Sci-Fi", None, None)
    result = db_update_media_genre("Dune", "Movies", None)
    assert result["success"] is True
    data = db_list_media("Movies")["data"]["Movies"]
    assert data[0]["genre"] is None


def test_update_genre_nonexistent_item_fails(with_movies):
    result = db_update_media_genre("Ghost", "Movies", "Horror")
    assert result["success"] is False


def test_update_genre_nonexistent_type_fails():
    result = db_update_media_genre("Dune", "Movies", "Sci-Fi")
    assert result["success"] is False


def test_update_media_item_single_field(with_movies):
    db_add_media_item("Movies", "Dune", None, None, None)
    result = db_update_media_item("Dune", "Movies", genre="Sci-Fi")
    assert result["success"] is True
    data = db_list_media("Movies")["data"]["Movies"]
    assert data[0]["genre"] == "Sci-Fi"


def test_update_media_item_multiple_fields(with_movies):
    db_add_media_item("Movies", "Dune", None, None, None)
    result = db_update_media_item("Dune", "Movies", genre="Sci-Fi", rating=4.5, notes="Epic")
    assert result["success"] is True
    item = db_get_media_item("Dune", "Movies")["data"]
    assert item["genre"] == "Sci-Fi"
    assert item["rating"] == 4.5
    assert item["notes"] == "Epic"


def test_update_media_item_to_null(with_movies):
    db_add_media_item("Movies", "Dune", "Sci-Fi", 4.5, "Epic")
    result = db_update_media_item("Dune", "Movies", genre=None, notes=None)
    assert result["success"] is True
    item = db_get_media_item("Dune", "Movies")["data"]
    assert item["genre"] is None
    assert item["notes"] is None


def test_update_media_item_no_fields_fails(with_movies):
    db_add_media_item("Movies", "Dune", None, None, None)
    result = db_update_media_item("Dune", "Movies")
    assert result["success"] is False


def test_update_media_item_rating_out_of_range_fails(with_movies):
    db_add_media_item("Movies", "Dune", None, None, None)
    result = db_update_media_item("Dune", "Movies", rating=10.0)
    assert result["success"] is False


def test_update_media_item_nonexistent_item_fails(with_movies):
    result = db_update_media_item("Ghost", "Movies", genre="Horror")
    assert result["success"] is False


def test_update_media_item_nonexistent_type_fails():
    result = db_update_media_item("Dune", "Movies", genre="Sci-Fi")
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


# ---- Bulk insert ----

def test_bulk_insert(with_movies):
    items = [
        {"title": "Dune", "genre": "Sci-Fi", "rating": 4.5},
        {"title": "Inception", "genre": "Thriller", "rating": 5.0},
        {"title": "The Shining", "genre": "Horror", "rating": None},
    ]
    result = db_add_media_items_bulk("Movies", items)
    assert result["success"] is True
    assert result["added"] == 3
    assert result["total"] == 3


def test_bulk_insert_unknown_type_fails():
    result = db_add_media_items_bulk("Movies", [{"title": "Dune"}])
    assert result["success"] is False


def test_bulk_insert_skips_duplicates(with_movies):
    db_add_media_item("Movies", "Dune", None, None, None)
    result = db_add_media_items_bulk("Movies", [
        {"title": "Dune"},
        {"title": "Inception"},
    ])
    assert result["success"] is True
    assert result["added"] == 1
    assert result["total"] == 2
    dupe = next(r for r in result["results"] if r["title"] == "Dune")
    assert dupe["success"] is False


def test_bulk_insert_skips_empty_titles(with_movies):
    result = db_add_media_items_bulk("Movies", [
        {"title": ""},
        {"title": "Inception"},
    ])
    assert result["added"] == 1


def test_bulk_insert_empty_list(with_movies):
    result = db_add_media_items_bulk("Movies", [])
    assert result["success"] is True
    assert result["added"] == 0


def test_bulk_insert_preserves_ratings(with_movies):
    items = [
        {"title": "Dune", "rating": 4.5},
        {"title": "Inception", "rating": None},
    ]
    db_add_media_items_bulk("Movies", items)
    data = db_list_media("Movies")["data"]["Movies"]
    by_title = {i["title"]: i for i in data}
    assert by_title["Dune"]["rating"] == 4.5
    assert by_title["Inception"]["rating"] is None


# ---- Get single item ----

def test_get_media_item_found(with_movies):
    db_add_media_item("Movies", "Dune", "Sci-Fi", 4.5, "Great film")
    result = db_get_media_item("Dune", "Movies")
    assert result["success"] is True
    assert result["data"]["title"] == "Dune"
    assert result["data"]["genre"] == "Sci-Fi"
    assert result["data"]["rating"] == 4.5


def test_get_media_item_not_found(with_movies):
    result = db_get_media_item("Ghost", "Movies")
    assert result["success"] is False


def test_get_media_item_unknown_type():
    result = db_get_media_item("Dune", "Movies")
    assert result["success"] is False


# ---- Rating validation ----

def test_add_media_item_rating_above_max_fails(with_movies):
    result = db_add_media_item("Movies", "Dune", None, 6.0, None)
    assert result["success"] is False


def test_add_media_item_rating_below_min_fails(with_movies):
    result = db_add_media_item("Movies", "Dune", None, -1.0, None)
    assert result["success"] is False


def test_add_media_item_rating_boundary_values(with_movies):
    assert db_add_media_item("Movies", "Zero", None, 0.0, None)["success"] is True
    assert db_add_media_item("Movies", "Five", None, 5.0, None)["success"] is True


def test_update_rating_out_of_range_fails(with_movies):
    db_add_media_item("Movies", "Dune", None, None, None)
    result = db_update_media_rating("Dune", "Movies", 10.0)
    assert result["success"] is False


# ---- Cascade delete ----

def test_remove_media_type_cascades_to_items(with_movies):
    db_add_media_item("Movies", "Dune", None, 4.5, None)
    db_remove_media_type("Movies")
    # Type is gone; re-adding it should show empty items
    db_add_media_type("Movies")
    assert db_list_media("Movies")["data"]["Movies"] == []
