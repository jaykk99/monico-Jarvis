# monico-Jarvis

Cloud-hosted Jarvis-like personal AI agent — FastAPI skeleton. No API keys required.

## Status

Working skeleton: the app boots, serves a health endpoint and a stub chat
endpoint. The autonomous-agent capabilities described in older notes
(Ollama, Playwright, LangGraph) are **not implemented** — `main.py` is a
two-endpoint FastAPI app and `agent.py` is a placeholder entrypoint.

## What's here

| File | Purpose |
| ---- | ------- |
| `main.py` | FastAPI app: `GET /` (health), `POST /chat?query=...` (stub echo) |
| `agent.py` | Placeholder agent entrypoint |
| `Dockerfile` | Production image: `uvicorn main:app` on port 8000 |
| `fly.toml` | Fly.io deploy config (builds the Dockerfile) |
| `vercel.json` | Vercel config (legacy `builds` format — may need updating for current Vercel Python runtime) |

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://localhost:8000/ — you should see the "alive" message.

## Deploy

- **Fly.io:** `fly launch` / `fly deploy` (uses the Dockerfile; health check hits `/`)
- **Vercel:** `vercel.json` is present but uses the deprecated `builds` syntax;
  verify against the current Vercel Python runtime docs before deploying.

## Configuration

None — the app reads no environment variables and needs no secrets.
