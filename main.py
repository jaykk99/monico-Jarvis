"""Monico Jarvis — FastAPI voice/agent assistant.

Serves a Jarvis-style console UI at `/` plus a JSON API:
  GET  /health        liveness: process is up
  GET  /ready         readiness: skills loaded, data dir writable
  GET  /capabilities  honest capability report
  GET  /skills        registered skills
  POST /chat          {"query": "..."} -> routed skill reply (also accepts ?query=)

Keyless by design: no API keys, no network calls, no secrets. Configuration
is env-driven (see config.py and .env.example); everything has a safe default.
"""
from __future__ import annotations

import logging
import time as _time
import uuid
from collections import defaultdict, deque
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

from agent import VERSION, agent  # noqa: E402
from config import settings  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("monico-jarvis")

app = FastAPI(
    title="Monico Jarvis",
    version=VERSION,
    description="Keyless local voice/agent assistant: real command skills, no API keys.",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Attach a request id, add security headers, and log slow requests."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    started = _time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("unhandled error req=%s %s %s", request_id, request.method, request.url.path)
        raise
    elapsed_ms = int((_time.monotonic() - started) * 1000)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if elapsed_ms > 1000:
        log.warning("slow request req=%s %s %s %dms", request_id, request.method,
                    request.url.path, elapsed_ms)
    return response


# ---------------------------------------------------------------- rate limiting

# per-IP sliding window of request timestamps (in-memory; resets on restart)
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


def _check_rate_limit(request: Request) -> None:
    limit = settings.rate_limit_per_minute
    if limit <= 0:
        return
    ip = request.client.host if request.client else "unknown"
    now = _time.monotonic()
    bucket = _rate_buckets[ip]
    while bucket and bucket[0] <= now - 60:
        bucket.popleft()
    if len(bucket) >= limit:
        log.warning("rate limit hit for %s", ip)
        raise HTTPException(
            status_code=429,
            detail=f"too many requests: {limit}/minute per IP — slow down a little",
        )
    bucket.append(now)


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
    """Liveness probe: the process is up and serving."""
    return {
        "status": "ok",
        "service": "monico-jarvis",
        "version": VERSION,
        "uptime_seconds": int(_time.monotonic() - _BOOT_MONO),
    }


@app.get("/ready")
def ready():
    """Readiness probe: skills loaded AND the data dir is writable.

    Fly/Render/Railway hit this before routing traffic; a 503 here means
    "don't send me requests yet".
    """
    problems: list[str] = []
    skill_count = len(agent.list_skills())
    if skill_count == 0:
        problems.append("no skills registered")
    data_dir = settings.data_dir
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        probe = data_dir / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        problems.append(f"data dir not writable: {exc}")
    if problems:
        return JSONResponse(
            status_code=503,
            content={"status": "not-ready", "service": "monico-jarvis", "problems": problems},
        )
    return {
        "status": "ready",
        "service": "monico-jarvis",
        "version": VERSION,
        "skills": skill_count,
        "data_dir": str(data_dir),
    }


@app.get("/capabilities")
def capabilities():
    return agent.capabilities()


@app.get("/skills")
def skills():
    return {"skills": agent.list_skills()}


@app.post("/chat")
def chat(body: Optional[ChatRequest] = None, query: Optional[str] = None,
         request: Request = None):  # type: ignore[assignment]
    """Accept JSON {"query": ...}; ?query= still works for backward compatibility."""
    _check_rate_limit(request)
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


_BOOT_MONO = _time.monotonic()

log.info("monico-jarvis v%s booting: %s", VERSION, settings.masked())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port,
                log_level=settings.log_level.lower())
