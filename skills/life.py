"""Everyday life math: bill splitting, trip fuel cost, reading time,
and a daily water-intake estimate.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only: the water figure is a rough rule-of-thumb
estimate (about 33 ml per kg of body weight), not medical advice, and
reading time assumes a steady pace with no breaks.
"""
from __future__ import annotations

import re

from .base import Skill, SkillRegistry


def _num(token: str) -> float | None:
    """Parse a number, tolerating a leading $ and thousands commas."""
    token = token.strip().lstrip("$").replace(",", "")
    if token.endswith("%"):
        token = token[:-1]
    try:
        return float(token)
    except ValueError:
        return None


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _money_cents(cents: int) -> str:
    return f"${cents // 100:,}.{cents % 100:02d}"


# ---------------------------------------------------------------- split


def _run_split(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) not in (2, 3):
        return ("Usage: `split <total> <people> [tip%]` — e.g. `split 120 4` "
                "or `split 120 4 15%`. Any leftover cents go to the first "
                "few people so the total adds up exactly.")
    total = _num(tokens[0])
    people = _num(tokens[1])
    tip = _num(tokens[2]) if len(tokens) == 3 else 0.0
    if total is None or people is None or tip is None:
        return "Couldn't read the total, people, or tip."
    if total < 0:
        return "Total must be >= 0."
    if people != int(people) or people <= 0:
        return "People must be a whole number greater than 0."
    if tip < 0:
        return "Tip must be >= 0."
    people = int(people)
    bill_cents = int(round(total * 100))
    tip_cents = int(round(bill_cents * tip / 100))
    grand_cents = bill_cents + tip_cents
    base, extra = divmod(grand_cents, people)
    tip_part = f" (bill {_money_cents(bill_cents)} + {tip:g}% tip {_money_cents(tip_cents)})" if tip else ""
    if extra == 0:
        return (f"Split {_money_cents(grand_cents)}{tip_part} between "
                f"{people}: {_money_cents(base)} each.")
    return (f"Split {_money_cents(grand_cents)}{tip_part} between "
            f"{people}: first {extra} pay {_money_cents(base + 1)} each, "
            f"remaining {people - extra} pay {_money_cents(base)} each.")


# ---------------------------------------------------------------- fuel


_DIST_RE = re.compile(r"^([0-9]*\.?[0-9]+)(km|mi)$")


def _run_fuel(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) != 3:
        return ("Usage: `fuel <distance><km|mi> <consumption> <price>` — "
                "for km, consumption is L/100km and price is $/L; for mi, "
                "consumption is mpg and price is $/gal. E.g. "
                "`fuel 400km 8 1.50` or `fuel 300mi 30 4.00`.")
    m = _DIST_RE.match(tokens[0])
    consumption = _num(tokens[1])
    price = _num(tokens[2])
    if not m or consumption is None or price is None:
        return "Couldn't read the distance, consumption, or price."
    dist = float(m.group(1))
    if dist <= 0 or consumption <= 0 or price < 0:
        return "Distance and consumption must be > 0, price must be >= 0."
    if m.group(2) == "km":
        litres = dist * consumption / 100
        cost = litres * price
        return (f"{dist:g}km at {consumption:g} L/100km needs {litres:.2f} L "
                f"— {_money(cost)} at {_money(price)}/L "
                f"({_money(cost / dist)} per km).")
    gallons = dist / consumption
    cost = gallons * price
    return (f"{dist:g}mi at {consumption:g} mpg needs {gallons:.2f} gal "
            f"— {_money(cost)} at {_money(price)}/gal "
            f"({_money(cost / dist)} per mile).")


# ---------------------------------------------------------------- readtime


def _run_readtime(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) not in (1, 2):
        return ("Usage: `readtime <words> [wpm]` — e.g. `readtime 12000` "
                "or `readtime 12000 250`. Default pace is 200 words per "
                "minute, a rough average; your pace will vary.")
    words = _num(tokens[0])
    wpm = _num(tokens[1]) if len(tokens) == 2 else 200.0
    if words is None or wpm is None:
        return "Couldn't read the word count or pace."
    if words != int(words) or words <= 0:
        return "Word count must be a whole number greater than 0."
    if wpm <= 0:
        return "Reading pace must be > 0 words per minute."
    seconds = int(round(words / wpm * 60))
    if seconds < 60:
        span = f"about {seconds} seconds"
    elif seconds < 3600:
        span = f"about {seconds // 60} minutes"
    else:
        hours, rem = divmod(seconds, 3600)
        span = f"about {hours}h {rem // 60}m"
    return (f"{int(words):,} words at {wpm:g} wpm: {span}. "
            "Rough estimate at a steady pace, no breaks.")


# ---------------------------------------------------------------- water


_WEIGHT_RE = re.compile(r"^([0-9]*\.?[0-9]+)(kg|lb)$")


def _run_water(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) not in (1, 2):
        return ("Usage: `water <weight><kg|lb> [exercise-minutes]` — e.g. "
                "`water 70kg` or `water 154lb 60`. Rough rule of thumb: "
                "about 33 ml per kg of body weight, plus about 500 ml "
                "per hour of exercise.")
    m = _WEIGHT_RE.match(tokens[0])
    exercise = _num(tokens[1]) if len(tokens) == 2 else 0.0
    if not m or exercise is None:
        return "Couldn't read the weight or exercise minutes."
    weight = float(m.group(1))
    kg = weight if m.group(2) == "kg" else weight / 2.20462
    if kg <= 0 or exercise < 0:
        return "Weight must be > 0 and exercise minutes must be >= 0."
    litres = kg * 0.033 + exercise * 0.5 / 60
    glasses = litres * 1000 / 250
    return (f"About {litres:.2f} L ({litres * 33.814:.1f} fl oz, "
            f"about {glasses:.0f} glasses of 250 ml) per day. "
            "Rough estimate, not medical advice — needs vary with heat, "
            "activity, and health.")


# ---------------------------------------------------------------- registry


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="split", description="Split a bill evenly, with optional tip.",
        usage="split <total> <people> [tip%]",
        triggers=["split", "splitbill"],
        run=_run_split,
        examples=["split 120 4", "split 120 4 15%"]))
    registry.register(Skill(
        name="fuel", description="Trip fuel needed and fuel cost.",
        usage="fuel <distance><km|mi> <consumption> <price>",
        triggers=["fuel", "gas"],
        run=_run_fuel,
        examples=["fuel 400km 8 1.50", "fuel 300mi 30 4.00"]))
    registry.register(Skill(
        name="readtime", description="Estimated reading time for a word count.",
        usage="readtime <words> [wpm]",
        triggers=["readtime", "readingtime"],
        run=_run_readtime,
        examples=["readtime 12000", "readtime 12000 250"]))
    registry.register(Skill(
        name="water", description="Rough daily water-intake estimate.",
        usage="water <weight><kg|lb> [exercise-minutes]",
        triggers=["water", "hydration"],
        run=_run_water,
        examples=["water 70kg", "water 154lb 60"]))
