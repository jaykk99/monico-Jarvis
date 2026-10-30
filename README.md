# monico-Jarvis

Cloud-hosted Jarvis-like personal AI agent — FastAPI + a Jarvis-style console UI.
**No API keys required**: every skill runs locally on the box.

## Status

Working app (v2.10.0), **deploy-ready**: boots, serves a console UI, and routes
chat commands through a real plugin-style skill registry (70 skills).
Honest about what it can't do — see `GET /capabilities`.
Blocked only on Jay's hosting decision — see [docs/DEPLOY.md](docs/DEPLOY.md)
for the one-tap checklist (Fly.io config already in repo).

## What's here

| Path | Purpose |
| ---- | ------- |
| `main.py` | FastAPI app: console UI at `/`, JSON API (`/health`, `/ready`, `/skills`, `/capabilities`, `POST /chat`); request-id + security headers, per-IP rate limiting on `/chat` |
| `config.py` | Env-driven settings with safe defaults (see `.env.example`) |
| `agent.py` | `MonicoAgent`: command router over the skill registry, optional skill disabling |
| `skills/` | Plugin-style skills: `base.py` (Skill/registry), `builtin.py` (core), `texttools.py` (text utils), `productivity.py` (tools), `utilities.py` (color, age, lorem, slug), `moretools.py` (morse, roman, loan, system, epoch, tz, shuffle, countdown, prime), `everyday.py` (tip, discount, bmi, base, weekday, moon), `finance.py` (paycheck, compound, budget, savings), `household.py` (unitprice, pace, sleep, grade), `life.py` (split, fuel, readtime, water), `practical.py` (percent, paint, tiles, commute), `diy.py` (concrete, mulch, wallpaper, sod), `yard.py` (fence, gravel, firewood, deck) |
| `static/` | Jarvis console UI (dark/light theme, voice-wave canvas, mic input via Web Speech API, TTS voice picker, command history, chat export, skill search) |
| `api/index.py` | Vercel serverless entrypoint (re-exports the app; note: stateful skills need a real server, not serverless) |
| `Dockerfile` | Production image: non-root user, `HEALTHCHECK` on `/ready`, `/app/data` volume, `uvicorn main:app` on port 8000 |
| `docker-compose.yml` | Local staging: `docker compose up --build` |
| `fly.toml` | Fly.io deploy config (Dockerfile build, `/ready` health check, auto stop/start) |
| `vercel.json` | Vercel config — modern `rewrites` format (the old deprecated `builds` syntax was removed) |
| `docs/DEPLOY.md` | Hosting decision guide: Fly vs Railway vs Render vs VPS vs Vercel, exact deploy steps |
| `tests/` | 239 pytest tests: endpoints, every skill, config fallbacks, `/ready` 200/503, security headers, rate limiting, validation, structured errors |

## Skills (all local, keyless)

Core:

- `time [utc]` / `date` — current time/date
- `calc <expr>` — safe arithmetic (AST-based, no `eval`; e.g. `calc (12+8)*3`)
- `echo <text>` — repeat back
- `note <text>` / `notes` / `note clear` — quick notes persisted to `data/` (override with `MONICO_DATA_DIR`)
- `timer <5m|30s|1h> [label]` / `timers` / `timer clear` — countdown timers, checked with `timers`
- `dice [sides]` / `dice 2d6` — roll dice
- `coin` — flip a coin
- `password [length]` — secure random password (never saved)
- `convert <value> <from> to <to>` — length (mm/cm/m/km/in/ft/yd/mi), weight (g/kg/oz/lb), speed (ms/kmh/mph/knot), volume (ml/l/floz/cup/pt/qt/gal), area (sqm/sqft/acre/ha), data (b/kb/mb/gb/tb + kib/mib/gib/tib), temp (c/f/k)
- `todo <text>` / `todos` / `todo done <n>` / `todo del <n>` / `todo clear` — todo list persisted to `data/`
- `weather` — honest: needs a weather API key, not available in keyless mode
- `status` — uptime + skill count
- `help` — list commands

Text tools:

- `hash <algo> <text>` — md5, sha1, sha256, sha512, blake2b (`md5 hello` works too)
- `uuid [n]` — random UUIDs, up to 20 at once
- `words <text>` — word/character/line counts
- `case <upper|lower|title|capitalize|swap|camel|snake> <text>` — change text case
- `b64 <encode|decode> <text>` — base64, locally
- `url <encode|decode> <text>` — URL percent-encoding, locally
- `json <text>` — validate JSON (with error position) and pretty-print it
- `pick <a>, <b>, ...` — pick one option at random

Productivity:

- `stopwatch start|stop|lap|status|reset` — persisted across restarts
- `remind <30m|2h|1d> <text>` / `reminders` / `remind clear` — honest: no background scheduler, so check with `reminders`; due items are flagged
- `stats <n1 n2 ...>` — count, min, max, mean, median, std dev
- `days <date1> to <date2>` — days between dates (`2026-10-20 to 2026-12-25`)
- `dateadd <date> <+|-><n>d` — add/subtract days (`dateadd today +30d`)
- `currency <value> <from> to <to>` — offline snapshot rates, labeled with the snapshot date; **not live, verify before any real money move**

Utilities:

- `color <#hex|rgb r g b|hsl h s l|name>` — hex ↔ RGB ↔ HSL conversions (`color #ff8800`, `color orange`)
- `age <birthdate>` — age in years/months/days, total days, next birthday (`age 1990-05-01`)
- `lorem [n] [paragraphs|sentences|words]` — lorem ipsum placeholder text (`lorem 2`, `lorem 50 words`)
- `slug <text>` — slugify for URLs/filenames (`slug Hello World!` → `hello-world`)

Everyday tools:

- `morse <text>` / `morse <code>` — encode/decode morse (auto-detects; `/` separates words)
- `roman <number|numeral>` — numbers ↔ roman numerals (`roman 2026`, `roman MMXXVI`)
- `loan <principal> <annual-rate-%> <years>` — monthly payment, total paid, total interest (`loan 250000 6.5 25`)
- `system` — local box stats: CPUs, load, memory, disk, uptime
- `epoch [seconds|ms|YYYY-MM-DD [HH:MM]]` — unix timestamp ↔ date/time (`epoch`, `epoch 1760000000`)
- `tz <Zone>` / `tz <HH:MM> <ZoneA> to <ZoneB>` — current time in a zone, or convert between zones (`tz America/Winnipeg`)
- `shuffle <a>, <b>, ...` — shuffle a list of items
- `countdown <YYYY-MM-DD [HH:MM]>` — time remaining until a date/time
- `prime <integer>` — primality test + factorization (deterministic Miller-Rabin, up to 10^18)

Everyday math + calendar:

- `tip <bill> [tip-%] [people]` — tip, total, and per-person split (`tip 80 20`, `tip 80 20% for 4`; tip percent defaults to 15%)
- `discount <price> <off-%> [tax-%]` — sale price and savings, with optional tax (`discount 80 25`, `discount 80 25 5`)
- `bmi <weight> <height>` — BMI + WHO category, metric or imperial (`bmi 80kg 180cm`, `bmi 176lb 70in`; a rough indicator, not a diagnosis)
- `base <value> <from> to <to>` — bin/oct/dec/hex conversion, all four shown (`base ff hex to dec`, `base 1010 bin to dec`)
- `weekday <YYYY-MM-DD>` / `weekday today|tomorrow|yesterday` — day of the week plus distance from today
- `moon [YYYY-MM-DD]` — moon phase + illumination % from the synodic cycle (`moon`, `moon 2026-12-25`)

Household math:

- `unitprice <price> <qty>[unit]` — price per unit, or compare two packs (`unitprice 5.99 12oz`, `unitprice 5.99 12oz vs 9.99 24oz`)
- `pace <distance><km|mi|m> <time>` — pace per km/mile plus speed (`pace 5km 25:00`, `pace 10mi 1:20:00`)
- `sleep <HH:MM>` — wake times in 90-minute cycles after ~15 min to fall asleep (`sleep 22:30`, `sleep 10:30pm`; rough estimates, not medical advice)
- `grade <score> <weight> ...` — weighted average + letter grade, weights as decimals or percents (`grade 90 0.3 80 0.7`)

Everyday life:

- `split <total> <people> [tip%]` — split a bill evenly with optional tip; leftover cents go to the first few people so it adds up exactly (`split 120 4`, `split 120 4 15%`)
- `fuel <distance><km|mi> <consumption> <price>` — trip fuel needed and cost; km mode uses L/100km and $/L, mi mode uses mpg and $/gal (`fuel 400km 8 1.50`, `fuel 300mi 30 4.00`)
- `readtime <words> [wpm]` — estimated reading time at a steady pace, default 200 wpm (`readtime 12000`, `readtime 12000 250`)
- `water <weight><kg|lb> [exercise-minutes]` — rough daily water-intake estimate, about 33 ml per kg plus 500 ml per hour of exercise (`water 70kg`; rough estimate, not medical advice)

Practical math:

- `percent <n>% of <total>` / `<part> of <total>` / `<old> to <new>` / `<value> +<n>%` — percentage math: share of a total, percent change, value after a percent up/down (`percent 20% of 80`, `percent 20 of 80`, `percent 80 to 100`, `percent 80 +20%`)
- `paint <length>x<width> <height> [coats] [coverage]` or `paint <area>sqm [coats] [coverage]` — paint in litres for walls, rounded up to whole litres, default 10 m²/L (`paint 4x5 2.4`, `paint 43sqm 2`; estimate only, ignores doors/windows)
- `tiles <area>sqm <w>x<h>cm [waste%]` or `tiles <length>x<width>m <w>x<h>cm [waste%]` — floor tiles needed, default 10% waste for cuts/breakage (`tiles 12sqm 30x30cm`, `tiles 4x5m 60x60cm 15%`)
- `commute <distance><km|mi> <speed> [HH:MM]` — travel time and arrival time at a steady speed, optional depart time (`commute 25km 50`, `commute 30mi 60 08:30`; estimate only, no traffic/stops)

DIY home projects:

- `concrete <length>x<width>m <depth>cm [waste%]` — slab volume in m³ and 80 lb bags needed, default 10% waste; imperial form takes `ft` with `in` (`concrete 10x10ft 4in`; an 80 lb bag yields about 0.6 cu ft)
- `mulch <length>x<width>m <depth>cm [waste%]` — mulch volume in m³/cu yd and 2 cu ft bags needed, default 5% waste; imperial form takes `ft` with `in` (`mulch 10x20ft 3in`)
- `wallpaper <length>x<width> <height> [pattern-repeat-cm]` — wallpaper rolls for a room's walls from a standard 0.53 m × 10.05 m roll, with the repeat lengthening every drop (`wallpaper 4x5 2.4`, `wallpaper 4x5 2.4 32`; ignores doors/windows)
- `sod <area>sqm [waste%]` — sod rolls (2 ft × 5 ft) and pallets for a lawn area, default 5% waste (`sod 50sqm`, `sod 1000sqft`)

Yard & outdoor:

- `fence <length>m [board-cm] [spacing-m] [waste%]` — picket boards, posts, and rails for a fence run, defaults 15 cm boards, 2.4 m post spacing, 10% waste; imperial form takes `ft` with `in` (`fence 100ft 6in 8ft`)
- `gravel <length>x<width>m <depth>cm [waste%]` — gravel volume in m³ and weight in tonnes for a bed or drive, default 5% waste; imperial form takes `ft` with `in` (`gravel 10x20ft 4in`; about 1.5 t/m³, 1.4 short tons/cu yd)
- `firewood <length>x<height>ft <log>in` — firewood in full cords (128 cu ft) and face cords for a stack; metric form takes `m` with `cm` (`firewood 2.4x1.2m 40cm`)
- `deck <length>x<width>m <board>cm [waste%]` — deck boards for a deck area, boards run along the length, default 10% waste; imperial form takes `ft` with `in` (`deck 12x16ft 5.5in`)

Anything else gets an honest fallback: "I don't have a skill for that yet."

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: every setting has a safe default
python main.py         # or: uvicorn main:app --reload
```

Then open http://localhost:8000/ — the Jarvis console. API docs at `/docs`.

## Run in Termux (Android)

Paste this whole block into Termux:

```bash
pkg update -y && pkg install -y git curl
git clone https://github.com/jaykk99/monico-Jarvis.git ~/monico-Jarvis
cd ~/monico-Jarvis
bash termux_install.sh
python main.py
```

Then open **http://127.0.0.1:8000** in your Android browser.

One-liner version (the installer clones the repo for you):

```bash
curl -sL https://raw.githubusercontent.com/jaykk99/monico-Jarvis/main/termux_install.sh -o ~/termux_install.sh && bash ~/termux_install.sh
cd ~/monico-Jarvis && python main.py
```

Do NOT just run `pip install -r requirements.txt` in Termux: fastapi
pulls in pydantic v2, and pydantic-core (a Rust extension) has no
precompiled Termux wheel on PyPI, so pip tries to compile Rust on the
phone and fails. `termux_install.sh` uses the Termux User Repository
index for a prebuilt wheel, with a Rust source build only as fallback.
No API keys needed — every skill runs locally on the phone.

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -q   # 63 tests
```

## Deploy

**See [docs/DEPLOY.md](docs/DEPLOY.md)** — hosting comparison, exact steps,
env table, health checks, and Jay's one-tap checklist. Short version:

- **Fly.io:** `fly deploy` (uses the Dockerfile; `/ready` health check)
- **Railway/Render:** new project from GitHub, Dockerfile auto-detected, health check path `/ready`
- **Vercel:** works via `vercel.json` + `api/index.py`, but stateful skills (notes/todos/timers) won't persist on serverless — use a real server for the full app

## Configuration

Optional, all via env (see `.env.example`): `MONICO_HOST`, `MONICO_PORT`,
`MONICO_DATA_DIR`, `MONICO_CORS_ORIGINS`, `MONICO_RATE_LIMIT_PER_MIN`,
`MONICO_LOG_LEVEL`, `MONICO_DISABLED_SKILLS`, `MONICO_CURRENCY_RATES_DATE`.
The app reads no secrets and makes no network calls.
