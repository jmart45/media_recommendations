"""TMDB (The Movie Database) metadata enrichment.

Looks up posters, descriptions, and ratings for movie/TV titles via the TMDB
search API, caching results (including misses) in the local metadata_cache
table so each title is only fetched once.

Requires a TMDB_API_KEY in the environment (.env). Works without one — items
are simply returned without metadata.
"""
import asyncio
import os
from typing import Optional

import httpx

from database import db_get_metadata_cache, db_set_metadata_cache

TMDB_API_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"

# Maps lowercase media type names to a TMDB search endpoint kind.
# Types not listed here (games, music, books, ...) have no TMDB coverage.
TMDB_KIND = {
    "movies": "movie", "movie": "movie", "films": "movie", "film": "movie",
    "tv": "tv", "tv shows": "tv", "tv show": "tv", "shows": "tv", "show": "tv",
    "series": "tv", "anime": "tv",
}

MAX_CONCURRENT_REQUESTS = 8


def tmdb_kind_for(media_type: str) -> Optional[str]:
    return TMDB_KIND.get(media_type.lower())


def get_api_key() -> Optional[str]:
    return os.environ.get("TMDB_API_KEY") or None


def parse_search_result(result: dict, kind: str) -> dict:
    """Convert a raw TMDB search result into the metadata shape the UI uses."""
    title = result.get("title") if kind == "movie" else result.get("name")
    date = result.get("release_date") or result.get("first_air_date") or ""
    poster = result.get("poster_path")
    vote = result.get("vote_average")
    return {
        "tmdb_id": result.get("id"),
        "title": title,
        "overview": result.get("overview") or None,
        "poster_url": TMDB_IMAGE_BASE + poster if poster else None,
        "year": int(date[:4]) if date[:4].isdigit() else None,
        "tmdb_rating": round(vote, 1) if vote else None,
    }


def _request_args(api_key: str, query: str) -> dict:
    """TMDB accepts either a v3 key (query param) or a v4 read token (Bearer).
    v4 tokens are JWTs starting with 'eyJ'."""
    params = {"query": query, "include_adult": "false"}
    headers = {}
    if api_key.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {api_key}"
    else:
        params["api_key"] = api_key
    return {"params": params, "headers": headers}


async def fetch_metadata(client: httpx.AsyncClient, title: str, kind: str, api_key: str) -> Optional[dict]:
    """Search TMDB for a title. Returns parsed metadata for the top result,
    {} if the search found nothing (cacheable miss), or None if the request
    failed (transient — should not be cached)."""
    try:
        res = await client.get(f"{TMDB_API_BASE}/search/{kind}", **_request_args(api_key, title))
        res.raise_for_status()
        results = res.json().get("results", [])
        if not results:
            return {}
        return parse_search_result(results[0], kind)
    except (httpx.HTTPError, ValueError, KeyError):
        return None


async def enrich_items(media_type: str, items: list[dict]) -> list[dict]:
    """Attach a 'tmdb' metadata dict (or None) to each item.

    Cached results are used when available; uncached titles are fetched
    concurrently and cached, including misses, so they aren't re-fetched.
    """
    kind = tmdb_kind_for(media_type)
    api_key = get_api_key()
    out = [dict(item) for item in items]

    if not kind:
        for item in out:
            item["tmdb"] = None
        return out

    to_fetch = []
    for item in out:
        cached = db_get_metadata_cache(item["title"], kind)
        if cached is not None:
            item["tmdb"] = cached or None
        elif api_key:
            to_fetch.append(item)
        else:
            item["tmdb"] = None

    if to_fetch:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        async with httpx.AsyncClient(timeout=10) as client:
            async def fetch_one(item: dict):
                async with semaphore:
                    meta = await fetch_metadata(client, item["title"], kind, api_key)
                item["tmdb"] = meta or None
                if meta is not None:
                    db_set_metadata_cache(item["title"], kind, meta)
            await asyncio.gather(*(fetch_one(i) for i in to_fetch))

    return out
