"""Pydantic request and response models for the HTTP API.

These define the public API contract. Success responses carry a typed body and
HTTP 200; failures raise HTTPException with a 4xx status and a `{"detail": ...}`
body (FastAPI's default), so clients branch on the status code rather than a
`success` flag. This shape is what makes a generated TypeScript client possible.
"""
from typing import Optional

from pydantic import BaseModel, Field


# --- Building blocks ---

class MediaItem(BaseModel):
    title: str
    genre: Optional[str] = None
    rating: Optional[float] = None
    notes: Optional[str] = None


class ItemDetail(MediaItem):
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MediaTypeInfo(BaseModel):
    id: int
    name: str


class TmdbMeta(BaseModel):
    tmdb_id: Optional[int] = None
    title: Optional[str] = None
    overview: Optional[str] = None
    poster_url: Optional[str] = None
    year: Optional[int] = None
    tmdb_rating: Optional[float] = None


class EnrichedMediaItem(MediaItem):
    tmdb: Optional[TmdbMeta] = None


# --- Request models ---

class UpdateRatingRequest(BaseModel):
    media_type: str
    title: str
    rating: Optional[float] = Field(default=None, ge=0, le=5)


class UpdateGenreRequest(BaseModel):
    media_type: str
    title: str
    genre: Optional[str] = None


class ChatRequest(BaseModel):
    messages: list[dict]


# --- Response models ---

class MediaListResponse(BaseModel):
    # Keyed by media type name -> its items.
    data: dict[str, list[MediaItem]]


class MediaTypesResponse(BaseModel):
    types: list[MediaTypeInfo]


class BrowseResponse(BaseModel):
    media_type: str
    data: list[EnrichedMediaItem]
    tmdb_supported: bool
    tmdb_configured: bool


class ItemDetailResponse(BaseModel):
    media_type: str
    data: ItemDetail


class MessageResponse(BaseModel):
    message: str
