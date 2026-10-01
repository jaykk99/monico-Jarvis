# monico-Jarvis

Cloud-hosted Jarvis-like personal AI agent — FastAPI + a Jarvis-style console UI.
**No API keys required**: every skill runs locally on the box.

## Status

Working app (v2.0.0): boots, serves a console UI, and routes chat commands
through a real plugin-style skill registry. Honest about what it can't do —
see `GET /capabilities`.

## What's here

| Path | Purpose |
| ---- | ------- |
| `main.py` | FastAPI app: console UI at `/`, JSON API (`/health`, `/skills`, `/capabilities`, `POST /chat`) |
| `agent.py` | `MonicoAgent`: command router over the skill registry |
| `skills/` | Plugin-style skills: `base.py` (Skill/registry), `builtin.py` (time, date, calc, echo, notes, status, help) |
| `static/` | Jarvis console UI (dark futuristic theme, voice-wave canvas, mic input via Web Speech API, optional TTS) |
| `api/index.py` | Vercel serverless entrypoint (re-exports the app) |
| `Dockerfile` | Production image: `uvicorn main:app` on port 8000 |
| `fly.toml` | Fly.io deploy config (Dockerfile build, `/health` check) |
| `vercel.json` | Vercel config — modern `rewrites` format (the old deprecated `builds` syntax was removed) |
| `tests/` | 15 pytest tests: endpoints, every skill, validation, structured errors |

## Skills (all local, keyless)

- `time [utc]` / `date` — current time/date
- `calc <expr>` — safe arithmetic (AST-based, no `eval`; e.g. `calc (12+8)*3`)
- `echo <text>` — repeat back
- `note <text>` / `notes` / `note clear` — quick notes persisted to `data/` (override with `MONICO_DATA_DIR`)
- `status` — uptime + skill count
- `help` — list commands

Anything else gets an honest fallback: "I don't have a skill for that yet."

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://localhost:8000/ — the Jarvis console. API docs at `/docs`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -q
```

## Deploy

- **Fly.io:** `fly deploy` (uses the Dockerfile; health check hits `/health`)
- **Vercel:** `vercel.json` uses the current `rewrites` → `/api/index` pattern for
  the Python runtime; `api/index.py` re-exports the FastAPI app.

## Configuration

None required. Optional: `MONICO_DATA_DIR` to relocate note storage.
The app reads no secrets and makes no network calls.
