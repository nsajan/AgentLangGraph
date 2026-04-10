"""FastAPI application — Agent Builder & Testing Playground."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.playground.api.routes import router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="AgentLangGraph Playground",
    description="Pattern-based Agent Builder & Testing Playground powered by LangGraph.",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")


@app.get("/")
async def index():
    html = (FRONTEND_DIR / "templates" / "index.html").read_text()
    return HTMLResponse(html)
