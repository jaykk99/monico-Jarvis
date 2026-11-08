"""Travel helpers: straight-line distance between cities, packing lists,
jet-lag recovery, and luggage weight checks.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic and lookup tables only, following the health/cook
pattern: distances come from the haversine formula over a built-in
table of city coordinates, packing lists are fixed checklists with
quantities scaled by trip length, jet-lag recovery uses the usual
one-day-per-hour-east rule of thumb, and luggage limits are the
standard economy figures (23 kg checked, 10 kg carry-on).

Conventions and explicit caveats:
- Distance: straight-line ("as the crow flies") distance between city
  centres, from coordinates rounded to one decimal. Road or rail
  distance is always longer; flight time is a cruise-speed estimate,
  not a schedule — real flights add taxi, boarding, and routing.
- Pack: a checklist, not a guarantee — check the weather at the
  destination and any airline or venue rules before you leave.
- Jetlag: a rule of thumb, not medical advice. Eastbound travel is
  harder to adjust to than westbound; light exposure and sleep
  timing help, but a doctor beats any formula for sleep problems.
- Luggage: limits are the common economy figures. Airlines differ —
  budget carriers are often stricter — so check your ticket before
  you pack.
"""
from __future__ import annotations

import math
import re

from .base import Skill, SkillRegistry


def _num(token: str) -> float | None:
    """Parse a number, tolerating a leading $ and thousands commas."""
    token = token.strip().replace(",", "").lstrip("$")
    if token.endswith("%"):
        token = token[:-1]
    try:
        return float(token)
    except ValueError:
        return None


def _fmt_num(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _fmt_hours(hours: float) -> str:
    """Format a duration in hours as '1h 30m' / '45m' / '2h'."""
    total_min = int(round(hours * 60))
    h, m = divmod(total_min, 60)
    if h == 0:
        return f"{m}m"
    if m == 0:
        return f"{h}h"
    return f"{h}h {m}m"


# ---------------------------------------------------------------- distance

# City centres, (latitude, longitude), one decimal — good to ~10 km,
# plenty for a straight-line estimate. Aliases map common short names.
_CITIES = {
    "winnipeg": (49.9, -97.1),
    "toronto": (43.7, -79.4),
    "vancouver": (49.3, -123.1),
    "montreal": (45.5, -73.6),
    "calgary": (51.0, -114.1),
    "edmonton": (53.5, -113.5),
    "ottawa": (45.4, -75.7),
    "quebec city": (46.8, -71.2),
    "halifax": (44.6, -63.6),
    "victoria": (48.4, -123.4),
    "saskatoon": (52.1, -106.7),
    "regina": (50.4, -104.6),
    "new york": (40.7, -74.0),
    "los angeles": (34.1, -118.2),
    "chicago": (41.9, -87.6),
    "san francisco": (37.8, -122.4),
    "miami": (25.8, -80.2),
    "las vegas": (36.2, -115.1),
    "london": (51.5, -0.1),
    "paris": (48.9, 2.3),
    "rome": (41.9, 12.5),
    "berlin": (52.5, 13.4),
    "madrid": (40.4, -3.7),
    "amsterdam": (52.4, 4.9),
    "tokyo": (35.7, 139.7),
    "sydney": (-33.9, 151.2),
    "singapore": (1.4, 103.8),
    "dubai": (25.2, 55.3),
    "hong kong": (22.3, 114.2),
    "bangkok": (13.8, 100.5),
}

_CITY_ALIASES = {
    "nyc": "new york",
    "la": "los angeles",
    "sf": "san francisco",
    "vegas": "las vegas",
    "quebec": "quebec city",
    "mtl": "montreal",
    "yyz": "toronto",
    "yvr": "vancouver",
    "ywg": "winnipeg",
}

_EARTH_RADIUS_KM = 6371.0
_KM_PER_MI = 1.609344
_CRUISE_KMH = 850.0  # typical jet cruise speed
_FLIGHT_OVERHEAD_H = 0.5  # climb, descent, taxi

_USAGE_DISTANCE = (
    "Usage: `distance <city> to <city>` — e.g. "
    "`distance winnipeg to toronto`, `distance toronto to london`. "
    "Known cities: " + ", ".join(sorted(_CITIES)) + "."
)


def _city_key(name: str) -> str | None:
    key = " ".join(name.strip().lower().split())
    if key in _CITIES:
        return key
    return _CITY_ALIASES.get(key)


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = (math.sin(dlat / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def _run_distance(trigger: str, args: str) -> str:
    parts = re.split(r"\s+to\s+", (args or "").strip(), flags=re.IGNORECASE)
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        return _USAGE_DISTANCE
    from_key = _city_key(parts[0])
    to_key = _city_key(parts[1])
    if from_key is None or to_key is None:
        unknown = parts[0] if from_key is None else parts[1]
        return (f"Unknown city `{unknown.strip()}`. Known cities: "
                + ", ".join(sorted(_CITIES)) + ".")
    if from_key == to_key:
        return "Those are the same city — distance is 0."
    km = _haversine_km(_CITIES[from_key], _CITIES[to_key])
    mi = km / _KM_PER_MI
    flight_h = km / _CRUISE_KMH + _FLIGHT_OVERHEAD_H
    from_name = from_key.title()
    to_name = to_key.title()
    return (f"{from_name} to {to_name}: about {_fmt_num(round(km))} km "
            f"({_fmt_num(round(mi))} mi) as the crow flies. A nonstop "
            f"flight is roughly {_fmt_hours(flight_h)} at a typical "
            f"850 km/h cruise (plus climb and descent). Straight-line "
            f"distance — road distance is longer, and real flight times "
            f"vary with routing and winds.")


# ---------------------------------------------------------------- pack

# (fixed items, per-day items with a per-day multiplier)
_PACK_LISTS = {
    "beach": (
        ["swimsuit", "sunscreen", "sunglasses", "beach towel", "sandals",
         "water bottle", "sun hat", "waterproof phone pouch", "book"],
        [("underwear", 1), ("t-shirts", 1), ("shorts", 0.5)],
    ),
    "business": (
        ["suit or blazer", "dress shoes", "belt", "laptop + charger",
         "notebook", "toiletries", "presentation materials"],
        [("dress shirts", 1), ("underwear", 1), ("socks", 1),
         ("ties", 0.5)],
    ),
    "camping": (
        ["tent", "sleeping bag", "sleeping pad", "headlamp", "camp stove + fuel",
         "water filter or purification", "first-aid kit", "bug spray",
         "fire starter", "food + cooking pot"],
        [("underwear", 1), ("socks", 1), ("t-shirts", 1)],
    ),
    "winter": (
        ["heavy coat", "thermal base layers", "gloves", "toque", "scarf",
         "insulated boots", "hand warmers", "lip balm", "snow pants"],
        [("underwear", 1), ("socks", 1), ("sweaters", 0.5)],
    ),
    "city": (
        ["comfortable walking shoes", "day bag", "water bottle",
         "phone charger", "light jacket", "sunglasses", "snacks"],
        [("underwear", 1), ("socks", 1), ("t-shirts", 1)],
    ),
    "roadtrip": (
        ["snacks", "water", "playlist or podcasts", "phone charger",
         "cooler", "travel pillow", "sunglasses", "first-aid kit",
         "spare tyre check", "paper map"],
        [("underwear", 1), ("socks", 1), ("t-shirts", 1)],
    ),
}

_USAGE_PACK = (
    "Usage: `pack <trip> [days]` — e.g. `pack beach 5`, "
    "`pack business 3`, `pack camping`. Trip types: "
    + ", ".join(sorted(_PACK_LISTS)) + "."
)


def _run_pack(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) not in (1, 2):
        return _USAGE_PACK
    entry = _PACK_LISTS.get(tokens[0])
    if entry is None:
        return _USAGE_PACK
    days = 3
    if len(tokens) == 2:
        days_num = _num(tokens[1])
        if days_num is None or days_num != int(days_num):
            return _USAGE_PACK
        days = int(days_num)
        if days < 1 or days > 30:
            return "Days must be between 1 and 30."
    fixed, per_day = entry
    items = list(fixed)
    for name, per in per_day:
        count = math.ceil(days * per)
        items.append(f"{name} x {count}")
    day_word = "day" if days == 1 else "days"
    out = (f"Packing list for a {days}-{day_word} {tokens[0]} trip "
           f"({len(items)} items): " + "; ".join(items) + ".")
    if days > 7:
        out += (" For trips over a week, pack for 7 days and plan a "
                "laundry day mid-trip.")
    return out + " Check the weather at your destination before you go."


# ---------------------------------------------------------------- jetlag

_USAGE_JETLAG = (
    "Usage: `jetlag <hours> [east|west]` — e.g. `jetlag 8 east`, "
    "`jetlag 5 west`. Hours is how many time zones you crossed (1-12)."
)

_EAST_RATE = 1.0  # days to adjust per hour crossed, flying east
_WEST_RATE = 0.5  # days to adjust per hour crossed, flying west


def _run_jetlag(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) not in (1, 2):
        return _USAGE_JETLAG
    hours = _num(tokens[0])
    if hours is None or hours != int(hours):
        return _USAGE_JETLAG
    hours = int(hours)
    if hours < 1 or hours > 12:
        return "Hours crossed must be between 1 and 12."
    direction = "east"
    if len(tokens) == 2:
        if tokens[1] not in ("east", "west"):
            return _USAGE_JETLAG
        direction = tokens[1]
    rate = _EAST_RATE if direction == "east" else _WEST_RATE
    days = hours * rate
    days_text = _fmt_num(days)
    day_word = "day" if days == 1 else "days"
    hour_word = "time zone" if hours == 1 else "time zones"
    rate_word = "day" if rate == 1 else "days"
    if direction == "east":
        tips = ("seek bright light in the morning, avoid it late in the "
                "evening, and try to sleep on the destination schedule "
                "from the first night.")
    else:
        tips = ("seek bright light in the late afternoon and evening, "
                "and stay up until a normal local bedtime on arrival.")
    return (f"Crossing {hours} {hour_word} {direction} takes about "
            f"{days_text} {day_word} to adjust to (roughly "
            f"{_fmt_num(rate)} {rate_word} per hour crossed — eastbound "
            f"is harder than westbound). To adjust faster: {tips} "
            f"Rule of thumb, not medical advice.")


# ---------------------------------------------------------------- luggage

_WEIGHT_RE = re.compile(r"^([0-9]*\.?[0-9]+)(kg|lb)$")
_KG_PER_LB = 0.45359237
_LB_PER_KG = 2.20462262

# Common economy limits; airlines differ, budget carriers are stricter.
_LIMITS = {
    "checked": (23.0, "checked bag (23 kg / 50 lb)"),
    "carryon": (10.0, "carry-on (10 kg / 22 lb)"),
}

_USAGE_LUGGAGE = (
    "Usage: `luggage <weight>kg|lb [checked|carryon]` — e.g. "
    "`luggage 25kg`, `luggage 18lb carryon`, `luggage 20kg checked`. "
    "Defaults to checked."
)


def _run_luggage(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) not in (1, 2):
        return _USAGE_LUGGAGE
    m = _WEIGHT_RE.match(tokens[0])
    if not m:
        return _USAGE_LUGGAGE
    amount = float(m.group(1))
    if amount <= 0:
        return "Weight must be greater than 0."
    weight_kg = amount * _KG_PER_LB if m.group(2) == "lb" else amount
    weight_display = (f"{_fmt_num(amount)} lb"
                      if m.group(2) == "lb" else f"{_fmt_num(amount)} kg")
    kind = "checked"
    if len(tokens) == 2:
        if tokens[1] not in _LIMITS:
            return _USAGE_LUGGAGE
        kind = tokens[1]
    limit_kg, limit_label = _LIMITS[kind]
    diff_kg = weight_kg - limit_kg
    if diff_kg <= 0:
        headroom_kg = -diff_kg
        headroom_lb = headroom_kg * _LB_PER_KG
        return (f"{weight_display} fits the {limit_label} limit with "
                f"{_fmt_num(round(headroom_kg, 1))} kg "
                f"({_fmt_num(round(headroom_lb, 1))} lb) to spare. "
                f"Limits vary by airline — check your ticket.")
    over_lb = diff_kg * _LB_PER_KG
    return (f"{weight_display} is {_fmt_num(round(diff_kg, 1))} kg "
            f"({_fmt_num(round(over_lb, 1))} lb) over the {limit_label} "
            f"limit — move about {_fmt_num(round(diff_kg, 1))} kg to "
            f"another bag or leave it behind, or expect an overweight "
            f"fee. Limits vary by airline — check your ticket.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="distance", description="Straight-line distance between two cities, with a flight-time estimate.",
        usage="distance <city> to <city>",
        triggers=["distance", "dist", "howfar"],
        run=_run_distance,
        examples=["distance winnipeg to toronto", "distance toronto to london"]))
    registry.register(Skill(
        name="pack", description="Packing checklist for a trip type, scaled by days.",
        usage="pack <trip> [days]",
        triggers=["pack", "packing"],
        run=_run_pack,
        examples=["pack beach 5", "pack business 3", "pack camping"]))
    registry.register(Skill(
        name="jetlag", description="Jet-lag recovery time for crossing time zones.",
        usage="jetlag <hours> [east|west]",
        triggers=["jetlag", "jet-lag"],
        run=_run_jetlag,
        examples=["jetlag 8 east", "jetlag 5 west"]))
    registry.register(Skill(
        name="luggage", description="Check a bag weight against standard economy luggage limits.",
        usage="luggage <weight>kg|lb [checked|carryon]",
        triggers=["luggage", "bag", "bags"],
        run=_run_luggage,
        examples=["luggage 25kg", "luggage 18lb carryon", "luggage 20kg checked"]))
