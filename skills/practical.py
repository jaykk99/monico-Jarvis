"""Practical everyday math: percentages, paint coverage, tile counts,
and commute times.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only: paint and tile figures are estimates (paint
ignores doors/windows unless you subtract them yourself; tiles round
up and include a waste allowance), and commute times assume a steady
speed with no traffic or stops.
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timedelta

from .base import Skill, SkillRegistry


def _num(token: str) -> float | None:
    """Parse a number, tolerating a leading $ and thousands commas."""
    token = (token or "").strip().replace(",", "").lstrip("$")
    try:
        return float(token)
    except ValueError:
        return None


def _fmt_num(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _fmt_minutes(total_minutes: float) -> str:
    total = int(round(total_minutes))
    hours, minutes = divmod(total, 60)
    if hours == 0:
        return f"{minutes} min"
    if minutes == 0:
        return f"{hours}h"
    return f"{hours}h {minutes:02d}m"


# ---------------------------------------------------------------- percent

_USAGE_PERCENT = (
    "Usage: `percent <n>% of <total>` | `percent <part> of <total>` | "
    "`percent <old> to <new>` | `percent <value> +<n>%` | "
    "`percent <value> -<n>%` — e.g. `percent 20% of 80`, "
    "`percent 20 of 80`, `percent 80 to 100`, `percent 80 +20%`."
)


def _run_percent(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens:
        return _USAGE_PERCENT
    # Form: <n>% of <total>  ->  the value that percent represents
    # Form: <part> of <total>  ->  what percent part is of total
    if len(tokens) == 3 and tokens[1] == "of":
        first, total = _num(tokens[0].rstrip("%")), _num(tokens[2])
        if first is None or total is None:
            return "Couldn't read those numbers."
        if tokens[0].endswith("%"):
            if total == 0:
                return "Total must not be 0."
            return f"{_fmt_num(first)}% of {_fmt_num(total)} = {_fmt_num(first * total / 100)}."
        if total == 0:
            return "Total must not be 0."
        return f"{_fmt_num(first)} is {_fmt_num(first / total * 100)}% of {_fmt_num(total)}."
    # Form: <old> to <new>  ->  percent change
    if len(tokens) == 3 and tokens[1] == "to":
        old, new = _num(tokens[0]), _num(tokens[2])
        if old is None or new is None:
            return "Couldn't read those numbers."
        if old == 0:
            return "Can't compute a percent change from 0."
        change = (new - old) / old * 100
        direction = "increase" if change > 0 else "decrease" if change < 0 else "change"
        return (f"{_fmt_num(old)} to {_fmt_num(new)} is a "
                f"{_fmt_num(abs(change))}% {direction}.")
    # Form: <value> +<n>% / -<n>%  ->  value after applying the percent
    if len(tokens) == 2 and re.fullmatch(r"[+-][0-9]*\.?[0-9]+%?", tokens[1]):
        value = _num(tokens[0])
        pct = _num(tokens[1].rstrip("%"))
        if value is None or pct is None:
            return "Couldn't read those numbers."
        result = value * (1 + pct / 100)
        verb = "up" if pct >= 0 else "down"
        return (f"{_fmt_num(value)} {verb} {_fmt_num(abs(pct))}% = "
                f"{_fmt_num(result)}.")
    return _USAGE_PERCENT


# ---------------------------------------------------------------- paint

_USAGE_PAINT = (
    "Usage: `paint <length>x<width> <height> [coats] [coverage-m2-per-L]` "
    "or `paint <area>sqm [coats] [coverage-m2-per-L]` — e.g. "
    "`paint 4x5 2.4`, `paint 43sqm 2`. Coverage defaults to 10 m²/L. "
    "Estimate only: it covers all walls and ignores doors/windows — "
    "subtract about 2 m² per door and 1.5 m² per window if you want it exact."
)

_ROOM_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)$")
_AREA_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqm$")


def _run_paint(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens:
        return _USAGE_PAINT
    m = _ROOM_RE.match(tokens[0])
    area_m = None
    rest = tokens[1:]
    if m:
        if not rest:
            return _USAGE_PAINT
        length, width = float(m.group(1)), float(m.group(2))
        height = _num(rest[0])
        if height is None:
            return "Couldn't read the wall height."
        area_m = 2 * (length + width) * height
        rest = rest[1:]
    else:
        m = _AREA_RE.match(tokens[0])
        if not m:
            return _USAGE_PAINT
        area_m = float(m.group(1))
    coats = 1
    coverage = 10.0
    if len(rest) >= 1:
        coats_f = _num(rest[0])
        if coats_f is None or coats_f != int(coats_f) or coats_f < 1:
            return "Coats must be a whole number of 1 or more."
        coats = int(coats_f)
    if len(rest) >= 2:
        coverage = _num(rest[1])
        if coverage is None or coverage <= 0:
            return "Coverage must be a positive number of m² per litre."
    if len(rest) > 2:
        return _USAGE_PAINT
    if area_m <= 0:
        return "Area must be greater than 0."
    litres_exact = area_m * coats / coverage
    litres = math.ceil(litres_exact)
    return (f"Walls {_fmt_num(area_m)} m² × {coats} coat{'s' if coats != 1 else ''} "
            f"at {_fmt_num(coverage)} m²/L = {_fmt_num(litres_exact)} L — "
            f"buy {litres} L (rounded up; paint is sold by the litre).")


# ---------------------------------------------------------------- tiles

_USAGE_TILES = (
    "Usage: `tiles <area>sqm <tile-width>x<tile-height>cm [waste%]` or "
    "`tiles <length>x<width>m <tile-width>x<tile-height>cm [waste%]` — "
    "e.g. `tiles 12sqm 30x30cm`, `tiles 4x5m 60x60cm 15%`. Waste "
    "defaults to 10% for cuts and breakage."
)

_TILE_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)cm$")


def _run_tiles(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) not in (2, 3):
        return _USAGE_TILES
    m = _AREA_RE.match(tokens[0])
    area_m = None
    if m:
        area_m = float(m.group(1))
    else:
        m = _ROOM_RE.match(tokens[0].removesuffix("m")) if tokens[0].endswith("m") else None
        if m:
            area_m = float(m.group(1)) * float(m.group(2))
    if area_m is None:
        return _USAGE_TILES
    m = _TILE_RE.match(tokens[1])
    if not m:
        return _USAGE_TILES
    tile_w, tile_h = float(m.group(1)), float(m.group(2))
    waste = 10.0
    if len(tokens) == 3:
        waste = _num(tokens[2].rstrip("%"))
        if waste is None or waste < 0:
            return "Waste must be 0% or more."
    if area_m <= 0 or tile_w <= 0 or tile_h <= 0:
        return "Area and tile size must be greater than 0."
    tile_area = (tile_w / 100) * (tile_h / 100)
    exact = area_m / tile_area
    base = math.ceil(exact)
    total = math.ceil(base * (1 + waste / 100))
    return (f"{_fmt_num(area_m)} m² with {_fmt_num(tile_w)}×{_fmt_num(tile_h)} cm tiles "
            f"= {base} tiles, plus {_fmt_num(waste)}% waste = {total} tiles "
            f"(buy {total}).")


# ---------------------------------------------------------------- commute

_USAGE_COMMUTE = (
    "Usage: `commute <distance><km|mi> <speed>` — speed in km/h for km, "
    "mph for mi — with an optional depart time `HH:MM` for an arrival "
    "time. E.g. `commute 25km 50`, `commute 30mi 60 08:30`. "
    "Estimate only: assumes a steady speed, no traffic or stops."
)

_DIST_RE = re.compile(r"^([0-9]*\.?[0-9]+)(km|mi)$")
_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def _run_commute(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) not in (2, 3):
        return _USAGE_COMMUTE
    m = _DIST_RE.match(tokens[0])
    speed = _num(tokens[1])
    if not m or speed is None:
        return _USAGE_COMMUTE
    distance, unit = float(m.group(1)), m.group(2)
    if distance <= 0 or speed <= 0:
        return "Distance and speed must be greater than 0."
    speed_unit = "km/h" if unit == "km" else "mph"
    hours = distance / speed
    travel = _fmt_minutes(hours * 60)
    depart = None
    if len(tokens) == 3:
        tm = _TIME_RE.match(tokens[2])
        if not tm:
            return "Depart time must be HH:MM (24-hour)."
        now = datetime.now()
        depart = now.replace(hour=int(tm.group(1)), minute=int(tm.group(2)),
                             second=0, microsecond=0)
        arrival = depart + timedelta(hours=hours)
        return (f"{_fmt_num(distance)} {unit} at {_fmt_num(speed)} {speed_unit} "
                f"takes {travel}. Depart {depart.strftime('%H:%M')} → "
                f"arrive {arrival.strftime('%H:%M')}.")
    arrival = datetime.now() + timedelta(hours=hours)
    return (f"{_fmt_num(distance)} {unit} at {_fmt_num(speed)} {speed_unit} "
            f"takes {travel} (arrive about {arrival.strftime('%H:%M')} "
            f"if you leave now).")


# ---------------------------------------------------------------- registration

def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="percent", description="Percentage math: % of a total, share of a total, change, up/down.",
        usage="percent <n>% of <total> | <part> of <total> | <old> to <new> | <value> +<n>%",
        triggers=["percent", "percentage", "%"],
        run=_run_percent,
        examples=["percent 20% of 80", "percent 20 of 80",
                  "percent 80 to 100", "percent 80 +20%"]))
    registry.register(Skill(
        name="paint", description="Paint needed for walls or a wall area, in litres.",
        usage="paint <length>x<width> <height> [coats] [coverage] | paint <area>sqm [coats] [coverage]",
        triggers=["paint"],
        run=_run_paint,
        examples=["paint 4x5 2.4", "paint 43sqm 2"]))
    registry.register(Skill(
        name="tiles", description="Floor tiles needed for an area, with a waste allowance.",
        usage="tiles <area>sqm <w>x<h>cm [waste%] | tiles <l>x<w>m <w>x<h>cm [waste%]",
        triggers=["tiles", "tile"],
        run=_run_tiles,
        examples=["tiles 12sqm 30x30cm", "tiles 4x5m 60x60cm 15%"]))
    registry.register(Skill(
        name="commute", description="Travel time and arrival time for a distance at a steady speed.",
        usage="commute <distance><km|mi> <speed> [HH:MM]",
        triggers=["commute", "travel"],
        run=_run_commute,
        examples=["commute 25km 50", "commute 30mi 60 08:30"]))
