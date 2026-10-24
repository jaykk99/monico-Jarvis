"""Everyday math + calendar tools: tip, discount, BMI, number-base
conversion, weekday lookup, moon phase.

All local, keyless, no network — same contract as the rest of skills/.
Money values are plain arithmetic, not financial advice; BMI uses the
standard WHO category cutoffs and is a rough indicator, not a diagnosis.
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime, timedelta, timezone

from .base import Skill, SkillRegistry

# ---------------------------------------------------------------- helpers


def _num(token: str) -> float | None:
    """Parse a number, tolerating $ , and a trailing % sign."""
    token = token.replace("$", "").replace(",", "").strip()
    if token.endswith("%"):
        token = token[:-1]
    try:
        return float(token)
    except ValueError:
        return None


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _parse_date(text: str) -> date | None:
    text = text.strip().lower()
    today = date.today()
    if text in ("today", "now"):
        return today
    if text == "tomorrow":
        return today + timedelta(days=1)
    if text == "yesterday":
        return today - timedelta(days=1)
    match = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


# ---------------------------------------------------------------- tip


def _run_tip(trigger: str, args: str) -> str:
    tokens = (args or "").strip().split()
    if not tokens:
        return ("Usage: `tip <bill> [tip-%] [people]` — e.g. `tip 80 20` or "
                "`tip 80 20% for 4`. Tip percent defaults to 15%.")
    bill = _num(tokens[0])
    if bill is None or bill <= 0:
        return f"Couldn't read a bill amount from `{tokens[0]}`."
    pct = 15.0
    people = 1
    rest = tokens[1:]
    # tolerate "for 4" / "split 4" phrasing for the people count
    if len(rest) >= 2 and rest[-2] in ("for", "split", "between"):
        count = _num(rest[-1])
        if count is not None and float(count).is_integer() and count >= 1:
            people = int(count)
            rest = rest[:-2]
    if rest:
        value = _num(rest[0])
        if value is None or value < 0 or value > 100:
            return f"Tip percent must be 0–100, got `{rest[0]}`."
        pct = value
        rest = rest[1:]
    if rest:
        count = _num(rest[0])
        if count is None or not float(count).is_integer() or count < 1:
            return f"People count must be a whole number >= 1, got `{rest[0]}`."
        people = int(count)
    tip = bill * pct / 100
    total = bill + tip
    out = f"Tip ({pct:g}%): {_money(tip)} — Total: {_money(total)}"
    if people > 1:
        out += f" — {_money(total / people)} each ({people} people)"
    return out


# ---------------------------------------------------------------- discount


def _run_discount(trigger: str, args: str) -> str:
    tokens = (args or "").strip().split()
    if len(tokens) < 2:
        return ("Usage: `discount <price> <off-%> [tax-%]` — e.g. "
                "`discount 80 25` or `discount 80 25 5` (5% tax).")
    price = _num(tokens[0])
    pct = _num(tokens[1])
    if price is None or price <= 0:
        return f"Couldn't read a price from `{tokens[0]}`."
    if pct is None or pct < 0 or pct > 100:
        return f"Discount percent must be 0–100, got `{tokens[1]}`."
    tax = 0.0
    if len(tokens) > 2:
        tax = _num(tokens[2])
        if tax is None or tax < 0:
            return f"Tax percent must be >= 0, got `{tokens[2]}`."
    sale = price * (1 - pct / 100)
    out = (f"Was {_money(price)}, {pct:g}% off → {_money(sale)} "
           f"(you save {_money(price - sale)})")
    if tax:
        out += f". With {tax:g}% tax: {_money(sale * (1 + tax / 100))}"
    return out


# ---------------------------------------------------------------- bmi


def _parse_weight(token: str) -> float | None:
    match = re.fullmatch(r"([\d.]+)\s*(kg|kgs|lb|lbs|pounds?)?", token.lower())
    if not match:
        return None
    value = float(match.group(1))
    if match.group(2) in ("lb", "lbs", "pound", "pounds"):
        value *= 0.45359237
    return value


def _parse_height(token: str) -> float | None:
    """Return height in metres. Bare numbers <= 3 are metres, else cm."""
    match = re.fullmatch(r"([\d.]+)\s*(m|cm|in|inch|inches|ft|feet)?", token.lower())
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2)
    if unit in ("cm",):
        value /= 100
    elif unit in ("in", "inch", "inches"):
        value *= 0.0254
    elif unit in ("ft", "feet"):
        value *= 0.3048
    elif unit is None and value > 3:
        value /= 100
    return value


def _run_bmi(trigger: str, args: str) -> str:
    tokens = (args or "").strip().split()
    if len(tokens) < 2:
        return ("Usage: `bmi <weight> <height>` — e.g. `bmi 80kg 180cm`, "
                "`bmi 80 1.8`, `bmi 176lb 70in`.")
    weight = _parse_weight(tokens[0])
    height = _parse_height(tokens[1])
    if weight is None or weight <= 0:
        return f"Couldn't read a weight from `{tokens[0]}`."
    if height is None or height <= 0 or height > 3:
        return f"Couldn't read a height from `{tokens[1]}`."
    bmi = weight / (height * height)
    if bmi < 18.5:
        category = "underweight"
    elif bmi < 25:
        category = "healthy weight"
    elif bmi < 30:
        category = "overweight"
    else:
        category = "obese"
    return (f"BMI {bmi:.1f} ({category}) — {weight:.1f} kg, {height:.2f} m. "
            "A rough indicator, not a diagnosis.")


# ---------------------------------------------------------------- base


_BASES = {"bin": 2, "binary": 2, "2": 2, "oct": 8, "octal": 8, "8": 8,
          "dec": 10, "decimal": 10, "10": 10, "hex": 16, "hexadecimal": 16,
          "16": 16}
_PREFIX = {"0b": 2, "0o": 8, "0x": 16}


def _parse_based_value(token: str, base: int) -> int | None:
    text = token.lower()
    negative = text.startswith("-")
    if negative:
        text = text[1:]
    for prefix, prefix_base in _PREFIX.items():
        if text.startswith(prefix) and prefix_base == base:
            text = text[len(prefix):]
            break
    if not text:
        return None
    digits = "0123456789abcdef"
    if any(c not in digits[:base] for c in text):
        return None
    try:
        value = int(text, base)
    except ValueError:
        return None
    return -value if negative else value


def _run_base(trigger: str, args: str) -> str:
    match = re.fullmatch(r"(\S+)\s+(\S+)\s+to\s+(\S+)", (args or "").strip().lower())
    if not match:
        return ("Usage: `base <value> <from> to <to>` — bases bin, oct, dec, "
                "hex (or 2, 8, 10, 16). E.g. `base ff hex to dec`, "
                "`base 1010 bin to dec`.")
    value_token, from_name, to_name = match.groups()
    from_base = _BASES.get(from_name)
    to_base = _BASES.get(to_name)
    if from_base is None or to_base is None:
        return "Bases must be bin, oct, dec, or hex (or 2, 8, 10, 16)."
    value = _parse_based_value(value_token, from_base)
    if value is None:
        return f"`{value_token}` isn't valid base-{from_base}."
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    rendered = {
        2: f"0b{bin(magnitude)[2:]}",
        8: f"0o{oct(magnitude)[2:]}",
        10: str(magnitude),
        16: f"0x{hex(magnitude)[2:].upper()}",
    }
    names = {2: "bin", 8: "oct", 10: "dec", 16: "hex"}
    return " = ".join(
        f"{sign}{rendered[b]} ({names[b]})" for b in (10, 2, 8, 16))


# ---------------------------------------------------------------- weekday


def _run_weekday(trigger: str, args: str) -> str:
    target = _parse_date(args or "")
    if target is None:
        return ("Usage: `weekday <YYYY-MM-DD>` or `weekday today|tomorrow|"
                "yesterday` — e.g. `weekday 2026-12-25`.")
    today = date.today()
    delta = (target - today).days
    label = target.strftime("%A")
    if delta == 0:
        when = "today"
    elif delta == 1:
        when = "tomorrow"
    elif delta == -1:
        when = "yesterday"
    elif delta > 1:
        when = f"{delta} days from now"
    else:
        when = f"{-delta} days ago"
    return f"{target.isoformat()} is a {label} ({when})."


# ---------------------------------------------------------------- moon


_SYNODIC = 29.530588853
_NEW_MOON_REF = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
_PHASES = [
    (1.84566, "New Moon"),
    (5.53699, "Waxing Crescent"),
    (9.22831, "First Quarter"),
    (12.91963, "Waxing Gibbous"),
    (16.61096, "Full Moon"),
    (20.30228, "Waning Gibbous"),
    (23.99361, "Last Quarter"),
    (27.68493, "Waning Crescent"),
]


def _moon_age(day: date) -> float:
    moment = datetime(day.year, day.month, day.day, 12, tzinfo=timezone.utc)
    return (moment - _NEW_MOON_REF).total_seconds() / 86400 % _SYNODIC


def _run_moon(trigger: str, args: str) -> str:
    text = (args or "").strip()
    target = _parse_date(text) if text else date.today()
    if target is None:
        return "Usage: `moon [YYYY-MM-DD]` — e.g. `moon 2026-12-25`."
    age = _moon_age(target)
    phase = "New Moon"
    for boundary, name in _PHASES:
        if age < boundary:
            phase = name
            break
    illumination = (1 - math.cos(2 * math.pi * age / _SYNODIC)) / 2 * 100
    return (f"{target.isoformat()}: {phase} — illumination "
            f"{illumination:.0f}%, moon age {age:.1f} days.")


# ---------------------------------------------------------------- registry


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="tip", description="Tip + bill split calculator.",
        usage="tip <bill> [tip-%] [people]",
        triggers=["tip"],
        run=_run_tip,
        examples=["tip 80 20", "tip 80 20% for 4", "tip 45"]))
    registry.register(Skill(
        name="discount", description="Sale price + savings, optional tax.",
        usage="discount <price> <off-%> [tax-%]",
        triggers=["discount", "sale"],
        run=_run_discount,
        examples=["discount 80 25", "discount 80 25 5"]))
    registry.register(Skill(
        name="bmi", description="Body mass index + WHO category.",
        usage="bmi <weight> <height>",
        triggers=["bmi"],
        run=_run_bmi,
        examples=["bmi 80kg 180cm", "bmi 80 1.8", "bmi 176lb 70in"]))
    registry.register(Skill(
        name="base", description="Number-base conversion (bin/oct/dec/hex).",
        usage="base <value> <from> to <to>",
        triggers=["base", "hex2dec", "bin2dec"],
        run=_run_base,
        examples=["base ff hex to dec", "base 1010 bin to dec"]))
    registry.register(Skill(
        name="weekday", description="Day of the week for a date.",
        usage="weekday <YYYY-MM-DD> | today|tomorrow|yesterday",
        triggers=["weekday", "dayofweek"],
        run=_run_weekday,
        examples=["weekday 2026-12-25", "weekday today"]))
    registry.register(Skill(
        name="moon", description="Moon phase + illumination for a date.",
        usage="moon [YYYY-MM-DD]",
        triggers=["moon", "moonphase"],
        run=_run_moon,
        examples=["moon", "moon 2026-12-25"]))
