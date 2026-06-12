from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from agent import run_agent
from database import init_db, db_list_media, db_list_media_types


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatRequest(BaseModel):
    messages: list[dict]


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/api/media")
async def api_list_media(media_type: Optional[str] = None):
    return db_list_media(media_type)


@app.get("/api/media-types")
async def api_list_media_types():
    return {"types": db_list_media_types()}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(run_agent(request.messages), media_type="text/event-stream")
