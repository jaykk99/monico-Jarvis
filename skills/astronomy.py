"""Astronomy helpers: planet facts, Kepler orbits, light travel time,
nearest stars, surface gravity / weight on other worlds, telescope
magnification, and approximate equinox / solstice dates.

All local, keyless, no network — same contract as the rest of skills/.
Plain textbook astronomy for everyday questions: how far away a
planet is, how long its year lasts, how long light takes to get
there, how heavy you would feel standing on it, what a telescope
can usefully show, and roughly when the seasons turn.

Rules and data used:
- Planets: mean distance from the Sun in AU, orbital period in
  Earth days, diameter in km, known moons, mean surface temperature
  in Celsius, and rotation period in hours. Moon counts are the
  confirmed counts as of 2024 (Saturn 146, Jupiter 95); new moons
  keep being confirmed, so the answer says the count is a snapshot.
  Venus and Uranus rotate backwards (retrograde), which the answer
  notes instead of hiding behind a bare negative number.
- Kepler's third law, in Earth units: P^2 = a^3, so a period in
  Earth years is a^(3/2) for a semi-major axis in AU, and the axis
  is P^(2/3) for a period in Earth years. This holds for anything
  orbiting the Sun; for other stars it is only an approximation.
- Light travel: c = 299,792.458 km/s, 1 AU = 149,597,870.7 km
  (about 8.32 light-minutes), 1 light-year = 9.4607 x 10^12 km.
- Nearest stars: distances in light-years for the ten nearest
  known star systems; 1 parsec = 3.26156 light-years. Proxima
  Centauri is the nearest star after the Sun.
- Surface gravity: weight on a world is your weight times its
  surface-gravity factor relative to Earth (Mercury 0.38, Venus
  0.91, Moon 0.17, Mars 0.38, Jupiter 2.53, Saturn 1.07, Uranus
  0.89, Neptune 1.14, Pluto 0.06). Gas giants have no solid
  surface, so the factor is for the 1-bar level, and the answer
  says so.
- Telescope: magnification = telescope focal length / eyepiece
  focal length. The maximum useful magnification is about 2x the
  aperture in mm (50x per inch); past it the image only gets
  bigger and dimmer, never sharper. Exit pupil = aperture /
  magnification; much above 7 mm the eye cannot use the light.
- Seasons: equinoxes and solstices are found from the Sun's
  apparent longitude using the low-precision Meeus formulae
  (mean longitude and anomaly, equation of centre). The dates are
  approximate, within about a day, and the answer says so — exact
  times need a full ephemeris.

Conventions and explicit caveats:
- Planet and star data are rounded textbook values, not live
  ephemeris positions; `planet mars` tells you about Mars in
  general, not where it is in tonight's sky.
- `orbit` assumes an orbit around the Sun. A moon or an exoplanet
  around another star follows the same law with that star's mass
  folded in, which this skill does not do.
- `lighttime` for a planet uses its mean distance; real travel
  time varies as planets move around their orbits, and the answer
  says the figure is for the mean distance.
- Season dates are approximate (within about a day). The southern
  hemisphere has the seasons reversed, and the answer notes that.
- Huge values refuse to print rather than dumping a wall of digits.
"""
from __future__ import annotations

import math
import re
from datetime import date

from .base import Skill, SkillRegistry

_C_KM_S = 299792.458
_AU_KM = 149597870.7
_LY_KM = 9460730472580.8
_LY_PER_PC = 3.26156

# name -> (mean distance AU, orbital period days, diameter km,
#          known moons, mean temp C, rotation hours, retrograde?)
PLANETS: dict[str, tuple[float, float, int, int, int, float, bool]] = {
    "mercury": (0.387, 88, 4879, 0, 167, 4222.6, False),
    "venus": (0.723, 224.7, 12104, 0, 464, 2802, True),
    "earth": (1.0, 365.25, 12742, 1, 15, 24, False),
    "mars": (1.524, 687, 6779, 2, -65, 24.6, False),
    "jupiter": (5.203, 4331, 139820, 95, -110, 9.9, False),
    "saturn": (9.537, 10747, 116460, 146, -140, 10.7, False),
    "uranus": (19.19, 30589, 50724, 28, -195, 17.2, True),
    "neptune": (30.07, 59800, 49244, 16, -200, 16.1, False),
}

# name -> surface gravity relative to Earth (1-bar level for gas giants).
GRAVITY: dict[str, float] = {
    "mercury": 0.38, "venus": 0.91, "earth": 1.0, "moon": 0.17,
    "mars": 0.38, "jupiter": 2.53, "saturn": 1.07, "uranus": 0.89,
    "neptune": 1.14, "pluto": 0.06,
}

# name -> distance in light-years (ten nearest known star systems).
STARS: dict[str, float] = {
    "proxima centauri": 4.246, "alpha centauri": 4.37,
    "barnard's star": 5.96, "wolf 359": 7.86,
    "lalande 21185": 8.31, "sirius": 8.60,
    "luyten 726-8": 8.73, "ross 154": 9.68,
    "ross 248": 10.32, "epsilon eridani": 10.48,
}


def _fmt(x: float) -> str:
    """Short human number: integers plain, else up to 4 significant digits."""
    if x == int(x) and abs(x) < 1e15:
        return f"{int(x):,}"
    return f"{x:.4g}"


def _num(token: str) -> float | None:
    try:
        value = float(token.replace(",", ""))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return value


def _parse_weight(text: str) -> tuple[float, str] | None:
    """Parse '80', '80kg', '176lb' -> (value, 'kg'|'lb')."""
    match = re.fullmatch(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(kg|lb|lbs)?", text.strip(), re.IGNORECASE)
    if not match:
        return None
    value = _num(match.group(1))
    if value is None or value <= 0:
        return None
    return value, (match.group(2) or "kg").lower().rstrip("s") if match.group(2) else "kg"


def _fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{_fmt(seconds)} seconds"
    minutes = seconds / 60
    if minutes < 60:
        return f"{_fmt(minutes)} minutes"
    hours = minutes / 60
    if hours < 48:
        return f"{_fmt(hours)} hours"
    days = hours / 24
    if days < 730:
        return f"{_fmt(days)} days"
    return f"{_fmt(days / 365.25)} years"


# ---------------------------------------------------------------- planet

def _run_planet(trigger: str, args: str) -> str:
    name = (args or "").strip().lower()
    if not name:
        lines = ["Planets (mean distance from the Sun, orbital period):"]
        for key, (au, period, _d, _m, _t, _r, _retro) in PLANETS.items():
            lines.append(f"  {key.title()}: {_fmt(au)} AU, {_fmt(period)} days")
        lines.append("Ask `planet <name>` for the full facts on one planet.")
        return "\n".join(lines)
    if name not in PLANETS:
        known = ", ".join(k.title() for k in PLANETS)
        return f"I don't know a planet called {args.strip()!r}. Known planets: {known}."
    au, period, diameter, moons, temp, rotation, retro = PLANETS[name]
    day = f"{_fmt(rotation)} hours"
    if retro:
        day += " (retrograde — spins backwards)"
    return (f"{name.title()}: {_fmt(au)} AU from the Sun, one year is "
            f"{_fmt(period)} Earth days, diameter {_fmt(diameter)} km, "
            f"{moons} known moon{'s' if moons != 1 else ''}, mean temperature "
            f"{temp} C, one day is {day}. Moon counts are the confirmed "
            f"counts as of 2024; distances and periods are mean values, "
            f"not tonight's sky position.")


# ---------------------------------------------------------------- orbit

def _run_orbit(trigger: str, args: str) -> str:
    text = (args or "").strip()
    match = re.fullmatch(r"a\s+([0-9.]+)", text, re.IGNORECASE)
    if match:
        axis = _num(match.group(1))
        if axis is None or axis <= 0:
            return "Usage: `orbit a <AU>` or `orbit p <years>` — e.g. `orbit a 1.524`."
        period_years = axis ** 1.5
        return (f"An orbit {_fmt(axis)} AU from the Sun takes "
                f"{_fmt(period_years)} Earth years ({_fmt(period_years * 365.25)} days). "
                f"Kepler's third law: period^2 = distance^3 in Earth units.")
    match = re.fullmatch(r"p\s+([0-9.]+)", text, re.IGNORECASE)
    if match:
        period = _num(match.group(1))
        if period is None or period <= 0:
            return "Usage: `orbit a <AU>` or `orbit p <years>` — e.g. `orbit p 1.88`."
        axis = period ** (2 / 3)
        return (f"An orbit with a {_fmt(period)} Earth-year period sits "
                f"{_fmt(axis)} AU from the Sun. Kepler's third law: "
                f"period^2 = distance^3 in Earth units.")
    return ("Usage: `orbit a <AU>` for the period of an orbit, or "
            "`orbit p <years>` for its distance — e.g. `orbit a 1.524` "
            "(Mars: 1.88 years), `orbit p 11.86` (Jupiter: 5.2 AU).")


# ---------------------------------------------------------------- lighttime

def _run_lighttime(trigger: str, args: str) -> str:
    text = (args or "").strip()
    if not text:
        return ("Usage: `lighttime <planet>` or `lighttime <number> <au|ly|km>` "
                "or `lighttime <number> <min|h>` — e.g. `lighttime mars`, "
                "`lighttime 1 au`, `lighttime 8 min`.")
    planet = text.lower()
    if planet in PLANETS:
        au = PLANETS[planet][0]
        seconds = au * _AU_KM / _C_KM_S
        return (f"Light from the Sun takes {_fmt_duration(seconds)} to reach "
                f"{planet.title()} at its mean distance of {_fmt(au)} AU. "
                f"The real time varies as the planets move around their orbits.")
    match = re.fullmatch(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(au|ly|km|m)", text, re.IGNORECASE)
    if match:
        value = _num(match.group(1))
        unit = match.group(2).lower()
        if value is None or value <= 0:
            return "That distance needs to be a positive number."
        km = {"au": _AU_KM, "ly": _LY_KM, "km": 1, "m": 0.001}[unit]
        seconds = value * km / _C_KM_S
        return (f"Light takes {_fmt_duration(seconds)} to travel "
                f"{_fmt(value)} {unit}.")
    match = re.fullmatch(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(min|h|hr|hrs|hour|hours|s|sec|secs|second|seconds)", text, re.IGNORECASE)
    if match:
        value = _num(match.group(1))
        unit = match.group(2).lower()
        if value is None or value <= 0:
            return "That time needs to be a positive number."
        seconds = value * {"s": 1, "sec": 1, "secs": 1, "second": 1,
                           "seconds": 1, "min": 60, "h": 3600, "hr": 3600,
                           "hrs": 3600, "hour": 3600, "hours": 3600}[unit]
        km = seconds * _C_KM_S
        if km >= _LY_KM:
            dist = f"{_fmt(km / _LY_KM)} light-years"
        elif km >= _AU_KM:
            dist = f"{_fmt(km / _AU_KM)} AU"
        else:
            dist = f"{km:,.0f} km"
        return (f"In {_fmt(value)} {unit}, light travels {dist}.")
    return ("Usage: `lighttime <planet>` or `lighttime <number> <au|ly|km>` "
            "or `lighttime <number> <min|h>` — e.g. `lighttime mars`, "
            "`lighttime 1 au`, `lighttime 8 min`.")


# ---------------------------------------------------------------- star

def _run_star(trigger: str, args: str) -> str:
    name = (args or "").strip().lower()
    if not name:
        lines = ["Nearest stars (light-years away):"]
        for key, ly in STARS.items():
            lines.append(f"  {key.title()}: {_fmt(ly)} ly")
        lines.append("Ask `star <name>` for parsecs and light travel time.")
        return "\n".join(lines)
    if name not in STARS:
        known = ", ".join(k.title() for k in STARS)
        return f"I don't know a star called {args.strip()!r}. Nearest known: {known}."
    ly = STARS[name]
    pc = ly / _LY_PER_PC
    return (f"{name.title()} is {_fmt(ly)} light-years away "
            f"({_fmt(pc)} parsecs) — light from it takes {_fmt(ly)} years "
            f"to reach us. Distances are the nearest known star systems, "
            f"excluding the Sun.")


# ---------------------------------------------------------------- gravity

def _run_gravity(trigger: str, args: str) -> str:
    text = (args or "").strip()
    if not text:
        lines = ["Surface gravity relative to Earth:"]
        for key, factor in GRAVITY.items():
            lines.append(f"  {key.title()}: {_fmt(factor)}x")
        lines.append("Ask `gravity <weight> <world>` — e.g. `gravity 80kg mars`.")
        return "\n".join(lines)
    parts = text.lower().split()
    if len(parts) == 1 and parts[0] in GRAVITY:
        factor = GRAVITY[parts[0]]
        note = ""
        if parts[0] in ("jupiter", "saturn", "uranus", "neptune"):
            note = " (at the 1-bar level — gas giants have no solid surface to stand on)"
        return (f"Surface gravity on {parts[0].title()} is {_fmt(factor)}x "
                f"Earth's — you would weigh {_fmt(factor * 100)}% of your "
                f"Earth weight there{note}.")
    if len(parts) >= 2:
        parsed = _parse_weight(parts[0])
        world = " ".join(parts[1:])
        if parsed is not None and world in GRAVITY:
            value, unit = parsed
            factor = GRAVITY[world]
            there = value * factor
            note = ""
            if world in ("jupiter", "saturn", "uranus", "neptune"):
                note = " (at the 1-bar level — gas giants have no solid surface to stand on)"
            return (f"{_fmt(value)} {unit} on Earth weighs {_fmt(there)} {unit} "
                    f"on {world.title()}{note}.")
    known = ", ".join(k.title() for k in GRAVITY)
    return (f"Usage: `gravity <weight> <world>` — e.g. `gravity 80kg mars`, "
            f"`gravity 176lb moon`. Known worlds: {known}.")


# ---------------------------------------------------------------- scope

def _run_scope(trigger: str, args: str) -> str:
    text = (args or "").strip()
    parts = text.split()
    if len(parts) not in (2, 3):
        return ("Usage: `scope <telescope focal length mm> <eyepiece mm> "
                "[aperture mm]` — e.g. `scope 1200 25`, `scope 1200 25 150`.")
    focal = _num(parts[0])
    eyepiece = _num(parts[1])
    if focal is None or eyepiece is None or focal <= 0 or eyepiece <= 0:
        return "Focal length and eyepiece both need to be positive numbers in mm."
    mag = focal / eyepiece
    out = (f"A {_fmt(focal)} mm telescope with a {_fmt(eyepiece)} mm eyepiece "
           f"gives {_fmt(mag)}x magnification.")
    if len(parts) == 3:
        aperture = _num(parts[2])
        if aperture is None or aperture <= 0:
            return "Aperture needs to be a positive number in mm."
        max_useful = 2 * aperture
        exit_pupil = aperture / mag
        out += (f" With a {_fmt(aperture)} mm aperture, the maximum useful "
                f"magnification is about {_fmt(max_useful)}x, and the exit "
                f"pupil is {_fmt(exit_pupil)} mm.")
        if mag > max_useful:
            out += (f" At {_fmt(mag)}x you are past the useful limit — the "
                    f"image only gets bigger and dimmer, never sharper.")
        if exit_pupil > 7:
            out += (" The exit pupil is wider than a dark-adapted eye "
                    "(~7 mm), so some light is wasted.")
    return out


# ---------------------------------------------------------------- season

def _sun_longitude(day: date) -> float:
    """Sun's apparent ecliptic longitude, low-precision Meeus formulae."""
    # Evaluate at noon so the crossing day is the event day, not the day after.
    j = day.toordinal() - date(2000, 1, 1).toordinal() + 2451545.0
    n = j - 2451545.0
    mean_long = (280.460 + 0.9856474 * n) % 360
    anomaly = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = (mean_long + 1.915 * math.sin(anomaly)
           + 0.020 * math.sin(2 * anomaly)) % 360
    return lam


def _season_date(year: int, target: float) -> date:
    """First day of `year` whose noon Sun longitude passes `target`."""
    day = date(year, 1, 1)
    prev = _sun_longitude(day)
    while True:
        day = date.fromordinal(day.toordinal() + 1)
        if day.year != year:
            return date(year, 12, 31)
        lam = _sun_longitude(day)
        crossed = (prev < target <= lam) or (prev > 270 and lam < 90 and target == 0)
        if crossed:
            return day
        prev = lam


def _run_season(trigger: str, args: str) -> str:
    text = (args or "").strip()
    year = date.today().year
    if text:
        try:
            year = int(text)
        except ValueError:
            return "Usage: `season [year]` — e.g. `season 2026`."
        if not 1900 <= year <= 2200:
            return "Give a year between 1900 and 2200."
    spring = _season_date(year, 0)
    summer = _season_date(year, 90)
    autumn = _season_date(year, 180)
    winter = _season_date(year, 270)
    return (f"{year} seasons (northern hemisphere, approximate — within "
            f"about a day): spring equinox {spring.isoformat()}, summer "
            f"solstice {summer.isoformat()}, autumn equinox "
            f"{autumn.isoformat()}, winter solstice {winter.isoformat()}. "
            f"The southern hemisphere has the seasons reversed.")


# ---------------------------------------------------------------- registry

def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="planet", description="Planet facts: distance, year length, size, moons, temperature, day length.",
        usage="planet [name]",
        triggers=["planet", "planets"],
        run=_run_planet,
        examples=["planet", "planet mars", "planet saturn"]))
    registry.register(Skill(
        name="orbit", description="Kepler's third law: orbital period from distance, or distance from period.",
        usage="orbit a <AU> | orbit p <years>",
        triggers=["orbit", "kepler"],
        run=_run_orbit,
        examples=["orbit a 1.524", "orbit p 11.86", "orbit a 30.07"]))
    registry.register(Skill(
        name="lighttime", description="How long light takes to travel a distance, or how far it goes in a time.",
        usage="lighttime <planet> | lighttime <number> <au|ly|km> | lighttime <number> <min|h>",
        triggers=["lighttime"],
        run=_run_lighttime,
        examples=["lighttime mars", "lighttime 1 au", "lighttime 8 min"]))
    registry.register(Skill(
        name="star", description="Nearest stars: distance in light-years and parsecs.",
        usage="star [name]",
        triggers=["star", "stars"],
        run=_run_star,
        examples=["star", "star sirius", "star proxima centauri"]))
    registry.register(Skill(
        name="gravity", description="Your weight on another world: surface gravity relative to Earth.",
        usage="gravity <weight> <world> | gravity <world>",
        triggers=["gravity"],
        run=_run_gravity,
        examples=["gravity 80kg mars", "gravity 176lb moon", "gravity jupiter"]))
    registry.register(Skill(
        name="scope", description="Telescope magnification, maximum useful magnification, and exit pupil.",
        usage="scope <focal mm> <eyepiece mm> [aperture mm]",
        triggers=["scope", "telescope"],
        run=_run_scope,
        examples=["scope 1200 25", "scope 1200 25 150", "scope 900 10 114"]))
    registry.register(Skill(
        name="season", description="Approximate equinox and solstice dates for a year.",
        usage="season [year]",
        triggers=["season", "seasons", "equinox", "solstice"],
        run=_run_season,
        examples=["season", "season 2026", "season 2030"]))
