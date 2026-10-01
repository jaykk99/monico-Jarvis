"""Monico Jarvis — FastAPI voice/agent assistant.

Serves a Jarvis-style console UI at `/` plus a JSON API:
  GET  /health        service health
  GET  /capabilities  honest capability report
  GET  /skills        registered skills
  POST /chat          {"query": "..."} -> routed skill reply (also accepts ?query=)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent import VERSION, agent

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Monico Jarvis",
    version=VERSION,
    description="Keyless local voice/agent assistant: real command skills, no API keys.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


def _error(status: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": status, "message": message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "request failed"
    return _error(exc.status_code, detail)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return _error(500, "internal error")


@app.get("/", include_in_schema=False)
def console():
    return FileResponse(BASE_DIR / "static" / "index.html", media_type="text/html")


@app.get("/health")
def health():
    return {"status": "ok", "service": "monico-jarvis", "version": VERSION}


@app.get("/capabilities")
def capabilities():
    return agent.capabilities()


@app.get("/skills")
def skills():
    return {"skills": agent.list_skills()}


@app.post("/chat")
def chat(body: Optional[ChatRequest] = None, query: Optional[str] = None):
    """Accept JSON {"query": ...}; ?query= still works for backward compatibility."""
    text = (body.query if body is not None else None) or query
    if text is None or not text.strip():
        raise HTTPException(
            status_code=400,
            detail='query is required: POST JSON {"query": "..."} or ?query=...',
        )
    return agent.respond(text.strip()[:2000])


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
def not_found(path: str):
    # Registered last so real routes win; funnels every miss through the
    # structured error handler instead of Starlette's plain {"detail": ...}.
    raise HTTPException(status_code=404, detail=f"no route for /{path}")
