"""FastAPI application — Agent Builder & Testing Playground."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.playground.api.routes import router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


app = FastAPI(
    title="AgentLangGraph Playground",
    description="Build, test, and iterate on LangGraph agents interactively.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")

# Serve frontend
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))


@app.get("/")
async def index():
    from fastapi.responses import HTMLResponse

    html = (FRONTEND_DIR / "templates" / "index.html").read_text()
    return HTMLResponse(html)
