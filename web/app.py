import os
import sys
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from main import DigitalTwin

app = FastAPI(title="Life Legacy - Digital Twin")
twin = DigitalTwin()

STATIC_DIR = BASE_DIR / "web" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(STATIC_DIR / "index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/status")
async def status():
    return twin.get_status()


@app.get("/api/chat/stream")
async def chat_stream(message: str = Query(...), interactor: Optional[str] = Query(None)):
    return EventSourceResponse(twin.chat_stream(message, interactor))
