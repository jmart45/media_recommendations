from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv(Path(__file__).parent / ".env", override=True)

from agent import run_agent
from database import (
    init_db, db_list_media, db_list_media_types,
    db_get_media_item, db_update_media_rating, db_update_media_genre, db_remove_media_item,
)
from tmdb import enrich_items, get_api_key, tmdb_kind_for
from schemas import (
    ChatRequest, UpdateRatingRequest, UpdateGenreRequest,
    MediaListResponse, MediaTypesResponse, BrowseResponse,
    ItemDetailResponse, MessageResponse,
)

DIST_DIR = Path(__file__).parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


def _unwrap_or_404(result: dict) -> dict:
    """Unwrap a db_* result dict, raising 404 on failure."""
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


# --- JSON API ---

@app.get("/api/media", response_model=MediaListResponse)
async def api_list_media(media_type: Optional[str] = None):
    result = _unwrap_or_404(db_list_media(media_type))
    return {"data": result["data"]}


@app.get("/api/browse", response_model=BrowseResponse)
async def api_browse(media_type: str):
    result = _unwrap_or_404(db_list_media(media_type))
    # db_list_media returns data keyed by the canonical type name
    type_name, items = next(iter(result["data"].items()))
    enriched = await enrich_items(type_name, items)
    return {
        "media_type": type_name,
        "data": enriched,
        "tmdb_supported": tmdb_kind_for(type_name) is not None,
        "tmdb_configured": get_api_key() is not None,
    }


@app.get("/api/media-types", response_model=MediaTypesResponse)
async def api_list_media_types():
    return {"types": db_list_media_types()}


@app.get("/api/item", response_model=ItemDetailResponse)
async def api_get_item(media_type: str, title: str):
    result = _unwrap_or_404(db_get_media_item(title, media_type))
    return {"media_type": result["media_type"], "data": result["data"]}


@app.patch("/api/item/rating", response_model=MessageResponse)
async def api_update_rating(request: UpdateRatingRequest):
    result = _unwrap_or_404(db_update_media_rating(request.title, request.media_type, request.rating))
    return {"message": result["message"]}


@app.patch("/api/item/genre", response_model=MessageResponse)
async def api_update_genre(request: UpdateGenreRequest):
    result = _unwrap_or_404(db_update_media_genre(request.title, request.media_type, request.genre))
    return {"message": result["message"]}


@app.delete("/api/item", response_model=MessageResponse)
async def api_delete_item(media_type: str, title: str):
    result = _unwrap_or_404(db_remove_media_item(title, media_type))
    return {"message": result["message"]}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(run_agent(request.messages), media_type="text/event-stream")


# --- Static SPA (production build) ---
# Served only when the frontend has been built (frontend/dist). In development,
# run the Vite dev server (`npm run dev` in frontend/), which serves the UI and
# proxies /api calls to this backend. Registered after the API routes so they
# take precedence; the catch-all returns index.html so client-side routes
# (e.g. /browse) resolve on refresh/deep-link.
if (DIST_DIR / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        return FileResponse(DIST_DIR / "index.html")
