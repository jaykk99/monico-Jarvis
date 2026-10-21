# Changelog

## v2.1.0 (2026-10-20) — deploy-ready

**Deploy readiness** (the repo's standing blocker was "never deployed"):

- `config.py`: env-driven settings with safe defaults (host, port, data dir,
  CORS, rate limit, log level, disabled skills, currency snapshot date);
  `.env.example` template
- `main.py`: request-id + security headers middleware, per-IP sliding-window
  rate limiting on `POST /chat` (429), new `GET /ready` readiness probe
  (skills loaded + data dir writable) for Fly/Render/Railway health checks,
  `/health` gains uptime, structured logging, `python-dotenv`, `python main.py`
  entrypoint
- `agent.py`: `MONICO_DISABLED_SKILLS` support, import-time `print()` replaced
  with logging, capabilities report lists disabled skills and honest offline limits
- `Dockerfile`: non-root user, `HEALTHCHECK` on `/ready`, `.dockerignore`,
  `/app/data` volume; `docker-compose.yml` for local staging; `fly.toml`
  health check moved from `/health` to `/ready`
- `docs/DEPLOY.md`: hosting decision matrix, exact deploy steps per host,
  env table, persistence + rollback notes, Jay's one-tap checklist
- `.github/workflows/ci.yml`: pytest + live boot smoke test on every push

**13 new keyless skills** (27 total): `hash`, `uuid`, `words`, `case`, `b64`,
`url`, `json`, `pick`, `stopwatch`, `remind`/`reminders`, `stats`, `datemath`
(`days`, `dateadd`), `currency` (offline snapshot rates, honestly labeled).
Honesty rules baked in: reminders have no scheduler (manual `reminders`
check), currency rates are a labeled snapshot, not live.

**Console UI**: command history (up/down, persisted), dark/light theme toggle
(persisted), chat export to `.txt`, clear-chat button, TTS voice picker,
reply latency in message tags, live skill search filter, message timestamps
for export.

**Tests**: 15 → 63, all passing. Covers every new skill, config fallbacks,
`/ready` 200/503, security headers, rate-limit 429 + disable path.

Removed: unused `SkillResult` dataclass in `skills/base.py` (dead code).

## v2.0.0 — Jarvis console UI, real skill/command routing, modern deploy configs

## v1.x — initial cloud-ready pushes
