# Changelog

## v2.4.0 (2026-10-24) — everyday math + calendar skills

**6 new keyless skills** (46 total) in `skills/everyday.py`:

- `tip` — tip, total, and per-person split (`tip 80 20`, `tip 80 20% for 4`)
- `discount` — sale price + savings, optional tax (`discount 80 25 5`)
- `bmi` — BMI + WHO category, metric or imperial (`bmi 80kg 180cm`)
- `base` — bin/oct/dec/hex conversion, all four bases shown (`base ff hex to dec`)
- `weekday` — day of the week for a date, plus distance from today
- `moon` — moon phase + illumination % from the synodic cycle

**Tests**: 144 → 162, all passing (`tests/test_everyday.py` covers every
new skill, including edge cases and bad input).

## v2.2.0 (2026-10-22) — utility skills + convert extensions

**4 new keyless skills** (31 total) in `skills/utilities.py`:

- `color` — hex ↔ RGB ↔ HSL conversions plus a curated named-color lookup
  (`color #ff8800`, `color rgb 255 136 0`, `color hsl 32 100 50`, `color orange`)
- `age` — age calculator: years/months/days, total days alive, next birthday
  countdown; Feb 29 birthdays handled (`age 1990-05-01`)
- `lorem` — lorem ipsum placeholder generator by paragraphs/sentences/words
  (`lorem 2`, `lorem 3 sentences`, `lorem 50 words`)
- `slug` — slugify text for URLs/filenames, accent-stripping
  (`slug Hello World!` → `hello-world`)

**Tests**: 63 → 89, all passing (`tests/test_utilities.py` covers every
new skill).

**`convert` extended** — 4 new categories: speed (ms, kmh, mph, knot),
volume (ml, l, floz, cup, pt, qt, gal), area (sqm, sqft, acre, ha),
data (b, kb, mb, gb, tb + binary kib/mib/gib/tib), with natural-language
aliases (`cups`, `hectare`, `kilometersperhour`…). Suite now 102 tests,
all green.

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
