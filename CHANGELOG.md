# Changelog

## v2.18.0 (2026-11-07) — health & fitness skills

**4 new keyless skills** (102 total) in `skills/health.py`:

- `calorie` — calories burned for an activity from a standard MET
  value, by minutes and body weight, metric or imperial
  (`calorie run 30 80kg`, `calorie walk 45 175lb`)
- `heartrate` — estimated max heart rate (220 minus age) and the five
  training zones, plus Karvonen moderate/vigorous targets when a
  resting rate is given (`heartrate 40`, `heartrate 40 60`)
- `steps` — step count to distance and rough calories, stride from
  height when given, otherwise a default 0.76 m stride
  (`steps 10000`, `steps 10000 180cm`, `steps 8000 5.9ft`)
- `workout` — total volume lifted from sets x reps x weight, metric
  with imperial in brackets (`workout 3x10 50kg bench`,
  `workout 5x5 225lb squat`)

Plain arithmetic only, labelled as such — MET values are published
averages, 220 minus age is a rough estimate (usually within 10-12
bpm), stride and per-step calories are averages, and volume is a
workload figure, not a training plan. Estimates, not medical advice.
No new dependencies. Also fixes the README test count, which still
said 297 after v2.17.0 took the total to 336.

**Tests**: 336 → 350, all passing (`tests/test_health.py` covers every
new skill, including edge cases and bad input, plus a regression
check that `bmi` keeps its trigger).

## v2.17.0 (2026-11-06) — cooking skills

**4 new keyless skills** (98 total) in `skills/cook.py`:

- `recipe` — scale a recipe amount between serving counts, same unit
  (`recipe 4 8 200g flour`, `recipe 4 6 1.5cups rice`)
- `bake` — oven temperature between Celsius, Fahrenheit, and gas mark,
  with the nearest gas mark shown (`bake 180C`, `bake 350F`,
  `bake gas 4`)
- `roast` — roast time by meat and weight (beef, lamb, pork, chicken,
  turkey) at a standard oven temperature, plus rest time and a
  thermometer target (`roast beef 1.5kg`, `roast chicken 4lb`,
  `roast lamb 2kg medium`)
- `serving` — food amounts per person for a main-course dish, metric
  with imperial in brackets (`serving 6 pasta`, `serving 4 rice`)

Plain arithmetic only, labelled as such — scaling changes amounts,
not bake time or temperature, gas marks are approximate, roast times
are estimates to confirm with a meat thermometer, and serving amounts
are main-course figures that vary with appetite. No new dependencies.

**Tests**: 322 → 336, all passing (`tests/test_cook.py` covers every
new skill, including edge cases and bad input, plus a regression
check that `convert` keeps its trigger).

## v2.16.0 (2026-11-05) — garden skills

**4 new keyless skills** (94 total) in `skills/garden.py`:

- `soil` — topsoil volume for a bed, in m³ (or cu yd) with 40 L
  (1.5 cu ft) bag counts, waste defaulting to 10% for settling
  (`soil 4x2m 15cm`, `soil 12x6ft 6in`)
- `seed` — grass seed for an area at 35 g/m² (7 lb per 1,000 sq ft),
  rate overridable (`seed 100sqm`, `seed 5000sqft`)
- `planter` — soil volume for a rectangular or round planter, in
  litres (or cu ft and US gallons) with bag counts
  (`planter 60x30x30cm`, `planter round 30cm 25cm`)
- `spacing` — plants in a bed on a grid at a given spacing, edge
  plants included (`spacing 4x2m 30cm`, `spacing 12x6ft 12in`)

Plain arithmetic only, labelled as such — seed rates vary by grass
species and new lawn versus overseeding, soil settles after watering,
planter fill is the ideal volume before drainage space and the rim
gap, and spacing is a grid count, not a planting plan. No new
dependencies. Also fixes the README skill count, which still said
86 after v2.15.0 took the total to 90.

**Tests**: 309 → 322, all passing (`tests/test_garden.py` covers
every new skill, including edge cases and bad input, plus a
regression check that `mulch` and `gravel` keep their triggers).

## v2.15.0 (2026-11-04) — electrical skills

**4 new keyless skills** (90 total) in `skills/electric.py`:

- `watts` — any two of volts, amps, watts gives the third
  (P = V x I) (`watts 120V 10A`, `watts 1200W 120V`,
  `watts 1200W 10A`)
- `circuit` — circuit load against breaker capacity and the 80%
  continuous guideline (`circuit 15A 120V 800 400`,
  `circuit 20A 120V 1500`)
- `bulb` — bulbs for a room area at 200 lumens per m² (20 per
  sq ft), 800 lumens per bulb unless you give its brightness
  (`bulb 20sqm`, `bulb 200sqft 1600`)
- `runtime` — battery runtime from amp-hours and volts, or
  watt-hours directly, with an optional efficiency derate
  (`runtime 100Ah 12V 50W`, `runtime 500Wh 50W 85%`)

Plain arithmetic only, labelled as such — the 80% circuit figure
is a planning guideline, not code advice, and mains work is a
licensed-electrician question; runtime defaults to the ideal
figure before inverter losses. No new dependencies.

**Tests**: 297 → 309, all passing (`tests/test_electric.py` covers
every new skill, including edge cases and bad input, plus a
regression check that `loan` and `grade` keep their triggers).

## v2.14.0 (2026-11-03) — plumbing skills

**4 new keyless skills** (86 total) in `skills/plumb.py`:

- `pipe` — pipe lengths for a straight run, lengths 3 m (10 ft)
  unless you give the length, waste defaulting to 10%
  (`pipe 30m`, `pipe 100ft 20ft`)
- `slope` — drain drop for a run at a grade, defaulting to 2%
  metric (1/4 in per ft imperial) (`slope 10m`, `slope 40ft 0.5in`)
- `tank` — volume of a rectangular tank, in litres and US gallons
  (`tank 2x1x1m`, `tank 4x3x2ft`)
- `fill` — time to fill a volume at a flow rate, litres with L/min
  or US gallons with gpm (`fill 1000L 50L/min`, `fill 100gal 5gpm`)

Plain arithmetic only, labelled as such — pipe lengths, grades, and
tank volumes vary by product and code, fittings are not counted in
pipe runs, and slope covers fall only, not venting or trap rules.
`grade` was deliberately not added as a slope alias: it already
belongs to the household grade skill. No new dependencies.

**Tests**: 284 → 297, all passing (`tests/test_plumb.py` covers
every new skill, including edge cases and bad input, plus a
regression check that `grade` still routes to the grade skill).

## v2.13.0 (2026-11-02) — finish skills

**4 new keyless skills** (82 total) in `skills/finish.py`:

- `trim` — trim/baseboard pieces for a room's perimeter (length ×
  width), pieces 2.4 m (8 ft) unless you give the piece length, waste
  defaulting to 10% (`trim 4x5m`, `trim 12x16ft 10ft`)
- `caulk` — caulk tubes for a bead run, one tube covering about 9 m
  (30 ft) of bead unless you give its coverage, waste defaulting to
  10% (`caulk 30m`, `caulk 100ft 40ft`)
- `grout` — grout bags for a tiled area, one bag covering 10 m²
  (100 sq ft) unless you give its coverage, waste defaulting to 10%
  (`grout 20sqm`, `grout 200sqft 50sqft`)
- `adhesive` — tile adhesive (thinset) bags for a tiled area, one bag
  covering 5 m² (50 sq ft) unless you give its coverage, waste
  defaulting to 10% (`adhesive 20sqm`, `adhesive 200sqft 25sqft`)

Plain arithmetic only, labelled as such — piece, tube, and bag
coverages vary by brand and product, trim counts ignore door and
archway openings, and caulk coverage depends heavily on bead size.
No new dependencies.

**Tests**: 270 → 284, all passing (`tests/test_finish.py` covers
every new skill, including edge cases and bad input).

## v2.12.0 (2026-11-01) — interior build-out skills

**4 new keyless skills** (78 total) in `skills/interior.py`:

- `siding` — siding squares for a wall area, one square is 100 sq ft
  (9.29 m²), waste defaulting to 10% (`siding 50sqm`,
  `siding 1000sqft 15%`)
- `floor` — flooring boxes for a floor area, a box covers 2 m²
  (20 sq ft) unless you give its coverage, waste defaulting to 10%
  (`floor 20sqm`, `floor 400sqft 24sqft`)
- `studs` — wall studs for a wall run, one spacing apart (0.4 m /
  16 in on centre by default) plus one end stud
  (`studs 10m`, `studs 12ft 24in`)
- `brick` — bricks for a wall area, about 60 bricks per m²
  (7 per sq ft) with mortar joints, waste defaulting to 10%
  (`brick 20sqm`, `brick 200sqft 15%`)

Plain arithmetic only, labelled as such — square, box, and brick
counts vary by brand and product, stud counts ignore openings and
headers, and brick counts exclude mortar, ties, and lintels. No new
dependencies.

**Tests**: 255 → 270, all passing (`tests/test_interior.py` covers
every new skill, including edge cases and bad input).

## v2.11.0 (2026-10-31) — build-out skills

**4 new keyless skills** (74 total) in `skills/build.py`:

- `insulation` — insulation rolls for an area, metric or imperial,
  with roll coverage (default 10 m² / 100 sq ft) and a waste allowance
  defaulting to 10% (`insulation 50sqm`, `insulation 1000sqft 75sqft`)
- `drywall` — drywall sheets for a room's walls from perimeter ×
  height, standard 1.2 × 2.4 m sheets (4 × 8 ft imperial), waste
  defaulting to 10% (`drywall 4x5m 2.4m`, `drywall 12x16ft 8ft`)
- `gutter` — gutter sections (3 m / 10 ft each), downspouts, hangers,
  and end caps for a run, with downspout spacing defaulting to 10 m /
  30 ft and hangers every 0.6 m / 2 ft (`gutter 30m`,
  `gutter 100ft 30ft`)
- `roof` — roofing bundles for a roof area, one square is 100 sq ft
  (9.29 m²) at 3 bundles, pitch given as rise/run multiplies the
  footprint by sqrt(1 + (rise/run)²), waste defaulting to 10%
  (`roof 10x8m`, `roof 30x40ft 6/12`)

Plain arithmetic only, labelled as such — roll and sheet sizes vary by
brand, drywall ignores ceilings/doors/windows, and roof counts ignore
valleys, hips, and flashing. No new dependencies.

**Tests**: 239 → 255, all passing (`tests/test_build.py` covers every
new skill, including edge cases and bad input).

## v2.10.0 (2026-10-30) — yard & outdoor skills

**4 new keyless skills** (70 total) in `skills/yard.py`:

- `fence` — picket boards, posts, and rails for a fence run, metric or
  imperial, with board width, post spacing, and a waste allowance
  defaulting to 10% (`fence 30m`, `fence 100ft 6in 8ft`)
- `gravel` — gravel volume in m³/cu yd and weight in tonnes/short tons
  for a bed or drive, metric or imperial, waste defaulting to 5%
  (`gravel 10sqm 10cm`, `gravel 10x20ft 4in`)
- `firewood` — firewood for a stack in full cords (128 cu ft) and face
  cords, metric or imperial (`firewood 4x8ft 16in`,
  `firewood 2.4x1.2m 40cm`)
- `deck` — deck boards for a deck area, boards run along the length,
  metric or imperial, waste defaulting to 10% (`deck 4x5m 14cm`,
  `deck 12x16ft 5.5in`)

Plain arithmetic only, labelled as such — board and post sizes, gravel
density, and cord volumes vary by supplier, and fence/deck counts ignore
gates and obstacles. No new dependencies.

**Tests**: 225 → 239, all passing (`tests/test_yard.py` covers every
new skill, including edge cases and bad input).

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
