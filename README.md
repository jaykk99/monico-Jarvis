# monico-Jarvis

Cloud-hosted Jarvis-like personal AI agent — FastAPI + a Jarvis-style console UI.
**No API keys required**: every skill runs locally on the box.

## Status

Working app (v2.32.0), **deploy-ready**: boots, serves a console UI, and routes
chat commands through a real plugin-style skill registry (158 skills).
Honest about what it can't do — see `GET /capabilities`.
Blocked only on Jay's hosting decision — see [docs/DEPLOY.md](docs/DEPLOY.md)
for the one-tap checklist (Fly.io config already in repo).

## What's here

| Path | Purpose |
| ---- | ------- |
| `main.py` | FastAPI app: console UI at `/`, JSON API (`/health`, `/ready`, `/skills`, `/capabilities`, `POST /chat`); request-id + security headers, per-IP rate limiting on `/chat` |
| `config.py` | Env-driven settings with safe defaults (see `.env.example`) |
| `agent.py` | `MonicoAgent`: command router over the skill registry, optional skill disabling |
| `skills/` | Plugin-style skills: `base.py` (Skill/registry), `builtin.py` (core), `texttools.py` (text utils), `productivity.py` (tools), `utilities.py` (color, age, lorem, slug), `moretools.py` (morse, roman, loan, system, epoch, tz, shuffle, countdown, prime), `everyday.py` (tip, discount, bmi, base, weekday, moon), `finance.py` (paycheck, compound, budget, savings), `household.py` (unitprice, pace, sleep, grade), `life.py` (split, fuel, readtime, water), `practical.py` (percent, paint, tiles, commute), `diy.py` (concrete, mulch, wallpaper, sod), `yard.py` (fence, gravel, firewood, deck), `build.py` (insulation, drywall, gutter, roof), `interior.py` (siding, floor, studs, brick), `finish.py` (trim, caulk, grout, adhesive), `plumb.py` (pipe, slope, tank, fill), `electric.py` (watts, circuit, bulb, runtime), `garden.py` (soil, seed, planter, spacing), `cook.py` (recipe, bake, roast, serving), `health.py` (calorie, heartrate, steps, workout), `travel.py` (distance, pack, jetlag, luggage), `weather.py` (windchill, heatindex, dewpoint, humidex), `car.py` (brake, tire, oil, tow), `school.py` (final, gpa, study, exam), `sports.py` (batting, era, qbrating, handicap), `music.py` (chord, musicscale, tempo, transpose), `science.py` (ph, moles, energy, density), `physics.py` (force, speed, pressure, wave), `geometry.py` (circle, triangle, trig, coord), `probability.py` (percentile, prob, odds, regress), `algebra.py` (linear, quadratic, simul, line, ineq, seq, gcd, ratio, exponent, logarithm, scientific, factorquad), `statistics.py` (zscore, weighted, movavg, quartile) |
| `static/` | Jarvis console UI (dark/light theme, voice-wave canvas, mic input via Web Speech API, TTS voice picker, command history, chat export, skill search) |
| `api/index.py` | Vercel serverless entrypoint (re-exports the app; note: stateful skills need a real server, not serverless) |
| `Dockerfile` | Production image: non-root user, `HEALTHCHECK` on `/ready`, `/app/data` volume, `uvicorn main:app` on port 8000 |
| `docker-compose.yml` | Local staging: `docker compose up --build` |
| `fly.toml` | Fly.io deploy config (Dockerfile build, `/ready` health check, auto stop/start) |
| `vercel.json` | Vercel config — modern `rewrites` format (the old deprecated `builds` syntax was removed) |
| `docs/DEPLOY.md` | Hosting decision guide: Fly vs Railway vs Render vs VPS vs Vercel, exact deploy steps |
| `tests/` | 489 pytest tests: endpoints, every skill, config fallbacks, `/ready` 200/503, security headers, rate limiting, validation, structured errors |

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

Build-out:

- `insulation <area>sqm [roll-m2] [waste%]` — insulation rolls for an area, default roll covers 10 m², default 10% waste; imperial form takes `sqft` with a `sqft` roll cover (`insulation 1000sqft 75sqft`)
- `drywall <length>x<width>m <height>m [waste%]` — drywall sheets for a room's walls (perimeter × height), standard 1.2 × 2.4 m sheets, default 10% waste; imperial form takes `ft` with 4 × 8 ft sheets (`drywall 12x16ft 8ft`; ignores ceilings, doors, windows)
- `gutter <length>m [downspout-spacing-m]` — gutter sections (3 m each), downspouts, hangers, and end caps for a run, defaults one downspout every 10 m and hangers every 0.6 m; imperial form takes `ft` with 10 ft sections (`gutter 100ft 30ft`)
- `roof <length>x<width>m [pitch]` — roofing bundles for a roof area, one square is 9.29 m² at 3 bundles, pitch given as rise/run multiplies the footprint (e.g. 6/12 → ×1.12), default 10% waste; imperial form takes `ft` with 100 sq ft squares (`roof 30x40ft 6/12`)

Cooking & kitchen:

- `recipe <from-servings> <to-servings> <amount><unit> [ingredient]` — scale a recipe amount by the serving ratio, same unit (`recipe 4 8 200g flour`, `recipe 4 6 1.5cups rice`; scaling changes amounts, not bake time or temperature)
- `bake <temp>C` / `bake <temp>F` / `bake gas <1-9>` — oven temperature between Celsius, Fahrenheit, and gas mark, with the nearest gas mark shown (`bake 180C`, `bake 350F`, `bake gas 4`; gas marks are approximate, ovens vary)
- `roast <meat> <weight>kg|lb [doneness]` — roast time by meat and weight at a standard oven temperature, plus rest time and a thermometer target (`roast beef 1.5kg`, `roast chicken 4lb`, `roast lamb 2kg medium`; doneness only applies to beef and lamb)
- `serving <people> <dish>` — food amounts per person for a main-course dish, metric with imperial in brackets (`serving 6 pasta`, `serving 4 rice`; main-course amounts, scale down for a side dish)

Health & fitness:

- `calorie <activity> <minutes> <weight>kg|lb` — calories burned for an activity from a standard MET value (`calorie run 30 80kg`, `calorie walk 45 175lb`; an estimate, real burn varies with intensity and fitness)
- `heartrate <age> [resting-bpm]` — estimated max heart rate and training zones, with Karvonen targets when resting rate is given (`heartrate 40`, `heartrate 40 60`; 220 minus age is a rough estimate, not medical advice)
- `steps <count> [height]cm|m|ft|in` — step count to distance and rough calories, stride from height when given (`steps 10000`, `steps 10000 180cm`; stride and calories are averages)
- `workout <sets>x<reps> <weight>kg|lb [exercise]` — total volume lifted, sets x reps x weight (`workout 3x10 50kg bench`, `workout 5x5 225lb squat`; a workload figure, not a training plan)

Travel:

- `distance <city> to <city>` — straight-line distance between two cities from a built-in table of 30 cities, with a rough nonstop flight time (`distance winnipeg to toronto`, `distance toronto to london`; as the crow flies, road distance is longer)
- `pack <trip> [days]` — packing checklist for a trip type, quantities scaled by days, default 3 days (`pack beach 5`, `pack business 3`, `pack camping`; beach, business, camping, winter, city, roadtrip)
- `jetlag <hours> [east|west]` — jet-lag recovery time for crossing time zones, about 1 day per hour eastbound and half a day per hour westbound (`jetlag 8 east`, `jetlag 5 west`; a rule of thumb, not medical advice)
- `luggage <weight>kg|lb [checked|carryon]` — check a bag against standard economy limits, 23 kg checked and 10 kg carry-on (`luggage 25kg`, `luggage 18lb carryon`; limits vary by airline, check your ticket)

Weather math (formulas only — no lookup, that still needs an API key):

- `windchill <temp>C|F <wind>kmh|mph` — wind chill from air temperature and wind speed, with frostbite-time guidance (`windchill -15C 30kmh`, `windchill 5F 20mph`; only applies at or below 10 C with wind at or above 4.8 km/h)
- `heatindex <temp>C|F <humidity>%` — heat index from temperature and humidity, with danger bands (`heatindex 32C 70%`, `heatindex 90F 65%`; only applies at or above 27 C / 80 F with humidity at or above 40%)
- `dewpoint <temp>C|F <humidity>%` — dew point and humidity comfort from temperature and humidity, with a frost note when the dew point is at or below freezing (`dewpoint 25C 60%`, `dewpoint 77F 50%`)
- `humidex <temp>C|F <humidity>%` — Canadian humidex from temperature and humidity, with the dew point shown (`humidex 30C 60%`, `humidex 86F 50%`; a formula estimate, not medical advice)

Car math (formulas and rules of thumb only — no OBD, no telematics):

- `brake <speed>kmh|mph [dry|wet|snow|ice]` — stopping distance from speed and road condition: reaction distance (1.5 s) plus braking distance, with car-length equivalents (`brake 100kmh dry`, `brake 60mph snow`; assumes good tires and brakes on a flat road)
- `tire <pressure>psi|kpa|bar <from-temp>C|F <to-temp>C|F` — what a tire set at one temperature reads at another, via the ideal gas law, with the ~1 psi per 10 F rule of thumb as a cross-check (`tire 32psi -20C 20C`, `tire 220kpa -30C 20C`; set pressures cold, never let air out of a hot tire)
- `oil <km-since>km <interval>km [months-since]mo [months-interval]mo` — oil-change due check by km and months, whichever limit hits first (`oil 8000km 10000km`, `oil 8000km 10000km 5mo 6mo`; use the interval in your owner's manual)
- `tow <trailer-weight>kg|lb <tow-rating>kg|lb [tongue-%]` — towing check: trailer weight against the tow rating, with tongue weight at 10-15% of the trailer (`tow 1500kg 2000kg`, `tow 5000lb 7000lb 12`; the hitch rating can be lower than the vehicle's — the lower one wins)

School math (formulas only — no gradebook lookup, grades come from you):

- `final <current>% <final-weight> <target>%` — the score needed on the final exam to finish at a target average (`final 80 40% 85`, `final 80 0.4 85`; weight as a percent or a fraction; says so when the target is out of reach, with the best average a perfect final gives, and when it's already locked in)
- `gpa <grade> <grade> ...` — GPA on the common 4.0 scale from letter grades or percents, with an optional `x<credits>` weight per course (`gpa A B+ C`, `gpa 92 88 76`, `gpa 92x3 88x1`; your school may use a different scale, so treat it as an estimate)
- `study <hours>h <days>d` or `study <hours>h before <YYYY-MM-DD>` — splits study hours across the days left, flagging a heavy daily load over about 6 hours a day (`study 20h 5d`, `study 12h before 2026-11-30`)
- `exam <questions>q <minutes>min` — pace per question with quarter-way checkpoints and a 10% time buffer target (`exam 60q 90min`, `exam 40q 120m`)

Sports stats (formulas only — no box-score lookup, the numbers come from you):

- `batting <hits> <at-bats> [target]` — batting average to three decimals, with an optional target average and the consecutive hits needed to reach it (`batting 100 300`, `batting 80 300 .300`; a rate, not a prediction — the next at-bat is still a coin flip weighted by the hitter)
- `era <earned-runs> <innings>` — earned run average, 9 x earned runs / innings, with baseball innings notation where .1 is one out and .2 is two outs (`era 18 60`, `era 10 6.1`; earned runs only — errors and passed balls don't count)
- `qbrating <completions> <attempts> <yards> <touchdowns> <interceptions>` — NFL passer rating, max 158.3 (`qbrating 20 30 250 2 1`; the NFL formula, not ESPN's QBR and not college passer efficiency)
- `handicap <score> <course-rating> <slope>` / `handicap diffs <d1> <d2> ...` — one round's differential, or a WHS handicap index from 3-20 differentials using the best few per the WHS table, averaged and times 0.96 (`handicap 85 72.1 128`, `handicap diffs 10.2 12.5 8.9`; an official index comes from your golf association, course rating/slope from the scorecard)

Music theory (pitch arithmetic only — notes come from you, no song lookup):

- `chord <root><type>` / `chord <root> <type>` — the notes in a chord: major, minor, dim, aug, sus2, sus4, 7, maj7, m7, m7b5, dim7, 6, m6, 9, m9, add9 (`chord C`, `chord Am`, `chord G7`, `chord C major`; pitch names only — the spelling on sheet music follows the key, and D# reads as Eb)
- `musicscale <root> [type]` — the notes in a scale: major, minor, harmonic minor, melodic minor, dorian, mixolydian, pentatonic, minor pentatonic, blues (`musicscale C`, `musicscale A minor`, `musicscale D blues`; plain `scale` is still the recipe scaler)
- `tempo <bpm> [beats-per-bar|duration]` / `tempo <ms>ms` — beat and bar lengths at a tempo, beats in a duration, or BPM from a beat length (`tempo 120`, `tempo 120 3`, `tempo 120 90s`, `tempo 500ms`; assumes a steady beat)
- `transpose <note> <note> ... <shift>` — move notes up or down by semitones or an interval (`transpose C E G +2`, `transpose A C# E +P5`; shift -12 to 12, or m2, M2, m3, M3, P4, TT, P5, m6, M6, m7, M7, octave)

Science (formulas only — concentrations and masses come from you, no lab lookup):

- `ph <concentration>` / `ph oh <concentration>` / `ph value <pH>` — pH, pOH, [H+] and [OH-] for a dilute water solution at 25 C, with an acid/neutral/base label (`ph 0.01`, `ph oh 0.001`, `ph value 3`; weak acids need their dissociation constant for a real pH)
- `moles <mass>g <molar-mass>` / `moles <n>mol <molar-mass>` / `moles molarity ...` — moles from mass and molar mass (with molecule count via Avogadro's number), mass from moles, or molarity from moles or mass and volume (`moles 36g 18`, `moles 2mol 18`, `moles molarity 2mol 0.5L`, `moles molarity 36g 18 2L`)
- `energy <value> <unit> to <unit>` / `energy ke <mass>kg <speed>` / `energy pe <mass>kg <height>m` — energy unit conversions (J, kJ, MJ, cal, kcal, eV, kWh, BTU), kinetic energy KE = 1/2 m v^2, gravitational potential PE = m g h (`energy 1 kWh to J`, `energy ke 80kg 10`, `energy pe 10kg 5m`; textbook formulas, no friction or air resistance)
- `density <mass> <volume>` / `density <value> <unit> to <unit>` — density in g/cm3 and kg/m3 with a floats-or-sinks verdict against water, or a density unit conversion (`density 100g 50ml`, `density 500g 1L`, `density 2.7 g/cm3 to kg/m3`; shape still matters — a steel boat floats because of its shape)

Physics (textbook formulas only — steady speeds, even force spread, no friction):

- `force <mass> <acceleration>` / `force weight <mass>` / `force accel <force> <mass>` / `force mass <force> <acceleration>` — force from F = m a, weight W = m g, or the rearranged forms (`force 10kg 5`, `force weight 80kg`, `force accel 100N 20kg`, `force mass 50N 5`; g is the standard 9.81 m/s^2, no friction included)
- `speed <distance> <time>` / `speed dist <speed> <time>` / `speed time <distance> <speed>` — speed from v = d / t, or distance/time from speed (`speed 100km 2h`, `speed dist 60kmh 2h`, `speed time 120km 60kmh`; steady speed assumed, no stops)
- `pressure <force> <area>` / `pressure <value> <unit> to <unit>` — pressure P = F / A, or a pressure unit conversion in Pa, kPa, MPa, bar, atm, psi, mmHg (`pressure 100N 2m2`, `pressure 1 atm to psi`, `pressure 100 kPa to Pa`; force spread evenly, gauge vs absolute not distinguished)
- `wave <frequency> <speed>` / `wave freq <wavelength> <speed>` / `wave period <frequency>` / `wave light <wavelength>` — wavelength from v = f x lambda, frequency, period T = 1 / f, or light frequency from a wavelength (`wave 440Hz 343`, `wave freq 2m 343`, `wave period 440Hz`, `wave light 500nm`; sound speed is 343 m/s at 20 C, light in vacuum)

Geometry (textbook formulas only — lengths in whatever unit you give, angles in degrees):

- `circle r<radius>` / `circle d<diameter>` / `circle c<circumference>` / `circle a<area>` — radius, diameter, circumference, and area from any one measurement (`circle r5`, `circle d10`, `circle c31.42`, `circle a78.54`; C = 2 pi r, A = pi r^2)
- `triangle <leg> <leg>` / `triangle <side> <side> <side>` — right-triangle hypotenuse and area from two legs, or perimeter, Heron area, right-angled check, and type from three sides (`triangle 3 4`, `triangle 3 4 5`, `triangle 5 5 6`; two sides are read as the legs of a right triangle)
- `trig <sin|cos|tan> <degrees>` / `trig <asin|acos|atan> <ratio>` — sine, cosine, tangent of an angle in degrees, or the inverse trig of a ratio in degrees (`trig sin 30`, `trig tan 45`, `trig asin 0.5`; asin/acos only take -1 to 1)
- `coord <x1> <y1> <x2> <y2>` — distance, midpoint, and slope between two points (`coord 0 0 3 4`, `coord 1 2 1 5`; a vertical line has no slope)

Probability & statistics (textbook formulas only — independent tries, same p every try; a percentile describes the list you give, not the wider population):

- `percentile <p> <numbers...>` / `percentile rank <value> in <numbers...>` — the value at the pth percentile (linear interpolation), or the percentile rank of a value in the list (`percentile 90 10 20 30 40 50`, `percentile rank 30 in 10 20 30 40 50`; p = 0 is the minimum, p = 100 the maximum)
- `prob <trials> <successes> <p>` / `prob atleast|atmost <trials> <successes> <p>` — binomial chance of exactly, at least, or at most k successes in n tries (`prob 10 3 0.5`, `prob atleast 10 9 0.5`, `prob atmost 10 1 0.5`; tries are independent with the same p)
- `odds <decimal>` / `odds <american>` / `odds <fraction>` — convert between decimal, fractional, and American odds, with the implied probability (`odds 2.5`, `odds +150`, `odds -200`, `odds 3/2`; arithmetic only — the implied probability is not a prediction, and no real money is involved)
- `regress <x1,y1> <x2,y2> ... [predict <x>]` — least-squares line, correlation r, and r^2 for a set of points, with an optional prediction (`regress 1,2 2,4 3,5 4,4 5,5`, `regress 1,2 2,4 3,5 4,4 5,5 predict 6`; association is not cause, and predicting far outside the x range is a guess)

Algebra (textbook formulas only — real roots only where stated; a vertical line has no slope):

- `linear <a> <b>` / `linear <equation>` — solve a x + b = 0 for x, or an equation written out (`linear 2 3`, `linear 2x+3=7`; a = 0 means every x works or none does)
- `quadratic <a> <b> <c>` — roots, discriminant, and vertex of a x^2 + b x + c = 0 (`quadratic 1 -3 2`, `quadratic 1 2 1`; a negative discriminant means no real roots, only a complex pair)
- `simul <a1> <b1> <c1> <a2> <b2> <c2>` — solve two linear equations in x and y by Cramer's rule (`simul 1 1 5 2 -1 1`; a zero determinant means parallel lines: same line or no solution)
- `line <x1> <y1> <x2> <y2>` — slope-intercept equation of the line through two points (`line 0 0 3 4`; a vertical line has no slope)
- `ineq <inequality>` — which x values satisfy a one-variable linear inequality (`ineq 2x+3>7` = x > 2; dividing by a negative flips the sign, `ineq -2x+4<10` = x > -3)
- `seq arith <first> <difference> <n>` / `seq geo <first> <ratio> <n>` — nth term and sum of an arithmetic or geometric sequence (`seq arith 3 5 10` = term 48, sum 255; `seq geo 2 3 5` = term 162, sum 242)
- `gcd <a> <b>` — greatest common divisor and least common multiple of two whole numbers (`gcd 12 18` = GCD 6, LCM 36; coprime numbers give GCD 1)
- `ratio <a> <b>` / `ratio <a> <b> <c>` — simplify a ratio to lowest terms (`ratio 12 18` = 2:3) or solve a proportion (`ratio 3 4 12` = 12:16)
- `exponent <base> <power>` — powers, including negative and fractional ones (`exponent 2 10` = 1,024; `exponent 9 0.5` = 3), plus same-base rules (`exponent 2 3 * 4` = 2^7 = 128)
- `log <value>` / `log <value> <base>` / `log ln <value>` — logarithms, base 10 by default (`log 100` = 2; `log 8 2` = 3; `log ln 10` = 2.303)
- `sci <number>` / `sci <mantissa> <exponent>` — scientific notation both ways (`sci 1234567` = 1.235 x 10^6; `sci 1.5 6` = 1,500,000)
- `factorquad <a> <b> <c>` — factor a quadratic over the integers when it factors (`factorquad 1 -3 2` = (x - 2)(x - 1); unfactorable ones say so with the discriminant)

Statistics II (textbook formulas only — builds on `stats` and `percentile`; a z-score or quartile describes the list you give, not the wider population):

- `zscore <value> in <numbers...>` / `zscore <value> <mean> <sd>` — how many standard deviations a value sits from the mean (`zscore 50 in 10 20 30 40 50`, `zscore 50 30 15.81`; sample sd, the same one `stats` reports)
- `weighted <value>x<weight> ...` — weighted average of value-weight pairs (`weighted 90x3 80x2 70x1`; weights must be positive)
- `movavg <window> <numbers...>` — moving average with a sliding window (`movavg 3 1 2 3 4 5`; the window must be at least 2 and no bigger than the list)
- `quartile <numbers...>` — five-number summary, IQR, and Tukey outlier fences (`quartile 1 2 3 4 5 6 7 8 9 10`; quartiles use the same linear interpolation as `percentile`)

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
pytest tests/ -q   # 489 tests
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
