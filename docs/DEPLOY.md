# Deploying monico-Jarvis

The app is **deploy-ready**. Everything below is verified locally except the
final `fly deploy` / dashboard click, which needs Jay's hosting account.
No code changes are required to ship — only a hosting decision.

## What was verified (2026-10-20)

- `pytest tests/ -q` — 63/63 pass (endpoints, all 27 skills, config, hardening)
- Live boot: `uvicorn main:app` serves `/` (200), `/ready` (200, 27 skills),
  `/health` (200), `POST /chat` end-to-end, security headers present
- Dockerfile reviewed line-by-line (no docker daemon on this box, so the
  image build itself is the one unverified step — it uses only
  `python:3.12-slim` + `pip install -r requirements.txt`, both pinned)

## Pick a host

| Host | Cost | Sleep | Best for |
| ---- | ---- | ----- | -------- |
| Fly.io (`fly.toml` in repo) | free tier | auto-stop/start, wakes on request | cheapest always-ready-ish; config already written |
| Railway | free tier | no sleep on some plans | simplest dashboard deploy from GitHub |
| Render | free tier spins down | 50s+ cold start | only if you accept the spin-down |
| VPS + Docker (`Dockerfile`, `docker-compose.yml`) | you own the box | never | full control, persistent `/app/data` volume |
| Vercel (`vercel.json`, `api/index.py`) | free | serverless | works, but notes/timers/todos won't persist between invocations (no filesystem) — the stateful skills need a real server |

Recommendation: **Fly.io** — the `fly.toml` is already tuned (Dockerfile
build, `/ready` health check, auto stop/start, `ord` region). One command
and it's live. If you'd rather click through a dashboard, Railway is the
zero-config fallback (point it at this repo, it finds the Dockerfile).

## Fly.io — one command

```bash
fly launch        # accept the detected Dockerfile build (or skip: fly.toml exists)
fly deploy        # builds the image, runs the /ready check, routes traffic
fly open          # opens the live console
```

`fly.toml` already sets: app name `monico-jarvis`, `ord` region,
`internal_port 8000`, HTTPS forced, machines auto-stop when idle and
auto-start on request, health check `GET /ready` every 30s.

Useful after deploy:

```bash
fly logs          # tail logs
fly status        # machine state
fly scale count 1 # keep one machine (or 0 to fully stop)
```

## Railway / Render (dashboard)

1. New project → deploy from GitHub → pick `jaykk99/monico-Jarvis`.
2. It detects the Dockerfile automatically. Start command is in the image.
3. Health check path: `/ready`. Port: `8000`.
4. Add a persistent disk mounted at `/app/data` if you want notes, todos,
   timers, and reminders to survive restarts (Railway volumes / Render disks).
5. No env vars required. Optional: `MONICO_LOG_LEVEL`, `MONICO_RATE_LIMIT_PER_MIN`
   (see `.env.example`).

## Environment variables (all optional)

| Variable | Default | What it does |
| -------- | ------- | ------------ |
| `MONICO_HOST` | `0.0.0.0` | bind address (`python main.py` uses this) |
| `MONICO_PORT` | `8000` | bind port |
| `MONICO_DATA_DIR` | `./data` | where notes/todos/timers/reminders persist |
| `MONICO_CORS_ORIGINS` | `*` | comma-separated allowed origins |
| `MONICO_RATE_LIMIT_PER_MIN` | `60` | `/chat` requests per minute per IP (`0` = off) |
| `MONICO_LOG_LEVEL` | `info` | `debug`, `info`, `warning`, `error` |
| `MONICO_DISABLED_SKILLS` | _(empty)_ | comma-separated skill names to turn off |
| `MONICO_CURRENCY_RATES_DATE` | `2026-10-20` | date label on the offline currency snapshot |

Copy `.env.example` to `.env` for local tweaks. The app reads no secrets
and makes no network calls — there is nothing sensitive to configure.

## Health checks

- `GET /health` — liveness: process is up (returns uptime + version).
- `GET /ready` — readiness: 27 skills loaded AND the data dir is writable.
  Orchestrators should probe this one; a 503 means "don't route here yet".

## Data persistence

Stateful skills (`note`, `todo`, `timer`, `remind`, `stopwatch`) store JSON
in `MONICO_DATA_DIR`. On Fly, attach a volume at `/app/data` (the Dockerfile
already declares it as a `VOLUME`). Without a volume, a redeploy wipes the
lists — the app keeps working, just with empty lists.

## Rollback

Every push to `main` is a normal commit (no history rewrites, ever).
To roll back: `fly deploy --image <previous-image>` or redeploy the
previous commit from the Railway/Render dashboard.

## Jay's one-tap checklist

- [ ] Pick Fly.io or Railway (Fly recommended — config is already in repo)
- [ ] Run `fly deploy` (needs your Fly login) or click Deploy in the dashboard
- [ ] Open the live URL, type `help`, confirm 27 skills
- [ ] Optional: attach a volume at `/app/data` for persistent notes/todos
- [ ] Optional: point your domain at it

That's it. No keys, no env secrets, no build config left to write.
