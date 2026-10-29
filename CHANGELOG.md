# Changelog

## v2.9.0 (2026-10-29) — DIY home-project skills

**4 new keyless skills** (66 total) in `skills/diy.py`:

- `concrete` — slab volume and 80 lb bags needed, metric or imperial,
  with a waste allowance defaulting to 10% (`concrete 4x5m 10cm`,
  `concrete 10x10ft 4in`; an 80 lb bag yields about 0.6 cu ft)
- `mulch` — mulch volume in m³/cu yd and 2 cu ft bags for a bed,
  metric or imperial, waste defaulting to 5% (`mulch 10sqm 8cm`,
  `mulch 10x20ft 3in`)
- `wallpaper` — wallpaper rolls for a room's walls from a standard
  0.53 m × 10.05 m roll, with an optional pattern repeat that
  lengthens every drop (`wallpaper 4x5 2.4`, `wallpaper 4x5 2.4 32`)
- `sod` — sod rolls (2 ft × 5 ft) and pallets for a lawn area, waste
  defaulting to 5% (`sod 50sqm`, `sod 1000sqft`)

Plain arithmetic only, labelled as such — bag and roll yields vary by
brand, wallpaper ignores doors/windows, and mulch settles after
spreading. No new dependencies.

**Tests**: 210 → 225, all passing (`tests/test_diy.py` covers every
new skill, including edge cases and bad input).

## v2.8.0 (2026-10-28) — practical math skills

**4 new keyless skills** (62 total) in `skills/practical.py`:

- `percent` — percentage math in four forms: share of a total
  (`percent 20% of 80`), what percent one number is of another
  (`percent 20 of 80`), percent change (`percent 80 to 100`), and a
  value after a percent up/down (`percent 80 +20%`)
- `paint` — paint needed for a room's walls or a wall area, in litres
  rounded up, with coats and coverage rate (`paint 4x5 2.4`,
  `paint 43sqm 2`, default 10 m²/L)
- `tiles` — floor tiles needed for an area, with a waste allowance
  for cuts and breakage, default 10% (`tiles 12sqm 30x30cm`,
  `tiles 4x5m 60x60cm 15%`)
- `commute` — travel time and arrival time for a distance at a steady
  speed, km or mi, with an optional depart time (`commute 25km 50`,
  `commute 30mi 60 08:30`)

Plain arithmetic only, labelled as such — paint ignores doors/windows
unless subtracted, and commute times assume a steady speed with no
traffic or stops. No new dependencies.

**Tests**: 195 → 210, all passing (`tests/test_practical.py` covers every
new skill, including edge cases and bad input).

## v2.7.0 (2026-10-27) — everyday life skills

**4 new keyless skills** (58 total) in `skills/life.py`:

- `split` — split a bill evenly between people, with an optional tip
  percent; leftover cents go to the first few people so the total adds
  up exactly (`split 120 4`, `split 120 4 15%`)
- `fuel` — trip fuel needed and fuel cost; km mode takes L/100km and
  $/L, mi mode takes mpg and $/gal (`fuel 400km 8 1.50`,
  `fuel 300mi 30 4.00`)
- `readtime` — estimated reading time for a word count at a steady
  pace, default 200 wpm (`readtime 12000`, `readtime 12000 250`)
- `water` — rough daily water-intake estimate, about 33 ml per kg of
  body weight plus about 500 ml per hour of exercise
  (`water 70kg`, `water 154lb 60`)

Plain arithmetic only, labelled as such — the water figure is a rough
rule-of-thumb estimate, not medical advice, and reading time assumes a
steady pace with no breaks. No new dependencies.

**Tests**: 184 → 195, all passing (`tests/test_life.py` covers every
new skill, including edge cases and bad input).

## v2.6.0 (2026-10-26) — household math skills

**4 new keyless skills** (54 total) in `skills/household.py`:

- `unitprice` — price per unit, or compare two packs side by side
  (`unitprice 5.99 12oz`, `unitprice 5.99 12oz vs 9.99 24oz`)
- `pace` — running pace per km/mile plus km/h and mph
  (`pace 5km 25:00`, `pace 10mi 1:20:00`)
- `sleep` — wake times from a bedtime in 90-minute cycles, after ~15
  minutes to fall asleep (`sleep 22:30`, `sleep 10:30pm`)
- `grade` — weighted grade average + letter grade, weights as decimals
  or percents, scaled to 100% (`grade 90 0.3 80 0.7`)

Plain arithmetic only, labelled as such — sleep times are rough
cycle estimates, not medical advice, and the letter scale is the common
US scale. No new dependencies.

**Tests**: 172 → 184, all passing (`tests/test_household.py` covers every
new skill, including edge cases and bad input).

## v2.5.0 (2026-10-25) — personal-finance skills

**4 new keyless skills** (50 total) in `skills/finance.py`:

- `paycheck` — hourly/weekly/monthly/yearly pay conversion, optional
  hours-per-week (`paycheck 25 hourly`, `paycheck 60000 yearly`,
  `paycheck 25 hourly 35`)
- `compound` — compound growth of savings + monthly contributions, fixed
  nominal rate, monthly compounding (`compound 1000 5 10 100`)
- `budget` — monthly budget breakdown vs income, per-category share and
  savings rate (`budget 3000 rent 1200 food 400 transport 200`)
- `savings` — months until a savings goal is reached, with an
  approximate finish month (`savings 5000 200 1000`)

Plain arithmetic only, labelled as such — no tax, fees, or inflation
modelled, not financial advice. No new dependencies (month math is
hand-rolled, not dateutil).

**Tests**: 162 → 172, all passing (`tests/test_finance.py` covers every
new skill, including edge cases and bad input).

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
