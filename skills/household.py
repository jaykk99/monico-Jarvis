"""Household everyday math: unit pricing, running pace, sleep-cycle wake
times, and weighted grades.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only: sleep times are rough 90-minute-cycle estimates,
not medical advice, and the grade scale is the common US letter scale —
your class or school may use a different one.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

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


_QTY_RE = re.compile(r"^([0-9]*\.?[0-9]+)([a-z]*)$")


def _qty(token: str) -> tuple[float, str] | None:
    """Parse a quantity like '12', '12oz', '1.5kg' into (amount, unit)."""
    m = _QTY_RE.match(token.strip().lower())
    if not m:
        return None
    amount = float(m.group(1))
    if amount <= 0:
        return None
    return amount, m.group(2)


# ---------------------------------------------------------------- unitprice


def _run_unitprice(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if "vs" in tokens:
        idx = tokens.index("vs")
        left, right = tokens[:idx], tokens[idx + 1:]
        if len(left) != 2 or len(right) != 2:
            return ("Usage: `unitprice <price> <qty>[unit]` or "
                    "`unitprice <price> <qty> vs <price> <qty>` — e.g. "
                    "`unitprice 5.99 12oz` or `unitprice 5.99 12oz vs 9.99 24oz`.")
        price_a, qty_a = _num(left[0]), _qty(left[1])
        price_b, qty_b = _num(right[0]), _qty(right[1])
        if price_a is None or qty_a is None or price_b is None or qty_b is None:
            return "Couldn't read one of the prices or quantities."
        if qty_a[1] != qty_b[1]:
            return (f"Units don't match ({qty_a[1] or 'none'} vs "
                    f"{qty_b[1] or 'none'}) — compare like with like.")
        per_a = price_a / qty_a[0]
        per_b = price_b / qty_b[0]
        unit = qty_a[1]
        if per_a == per_b:
            verdict = "Both cost the same per unit."
        elif per_a < per_b:
            verdict = f"First pack is cheaper ({_money(per_b - per_a)} less per {unit or 'unit'})."
        else:
            verdict = f"Second pack is cheaper ({_money(per_a - per_b)} less per {unit or 'unit'})."
        return (f"First: {_money(per_a)} per {unit or 'unit'} — "
                f"Second: {_money(per_b)} per {unit or 'unit'}. {verdict}")
    if len(tokens) != 2:
        return ("Usage: `unitprice <price> <qty>[unit]` or "
                "`unitprice <price> <qty> vs <price> <qty>` — e.g. "
                "`unitprice 5.99 12oz`.")
    price, qty = _num(tokens[0]), _qty(tokens[1])
    if price is None or qty is None:
        return "Couldn't read the price or quantity."
    return f"{_money(price)} for {qty[0]:g}{qty[1]} = {_money(price / qty[0])} per {qty[1] or 'unit'}."


# ---------------------------------------------------------------- pace


_TIME_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{2})$")
_DIST_RE = re.compile(r"^([0-9]*\.?[0-9]+)(km|mi|m)$")


def _seconds(text: str) -> int | None:
    """Parse MM:SS or H:MM:SS into total seconds."""
    m = _TIME_RE.match(text.strip())
    if not m:
        return None
    hours = int(m.group(1)) if m.group(1) else 0
    minutes, seconds = int(m.group(2)), int(m.group(3))
    if minutes >= 60 and not m.group(1):
        return None
    if seconds >= 60:
        return None
    return hours * 3600 + minutes * 60 + seconds


def _pace_str(seconds_per_km: float) -> str:
    total = int(round(seconds_per_km))
    minutes, seconds = divmod(total, 60)
    return f"{minutes}:{seconds:02d}"


def _run_pace(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) != 2:
        return ("Usage: `pace <distance><km|mi|m> <time>` — e.g. "
                "`pace 5km 25:00` or `pace 10mi 1:20:00`.")
    m = _DIST_RE.match(tokens[0])
    total = _seconds(tokens[1])
    if not m or total is None or total <= 0:
        return "Couldn't read the distance or time."
    dist = float(m.group(1))
    unit = m.group(2)
    if dist <= 0:
        return "Distance must be > 0."
    km = dist if unit == "km" else dist * 1.60934 if unit == "mi" else dist / 1000
    if km <= 0:
        return "Distance must be > 0."
    per_km = total / km
    per_mi = per_km * 1.60934
    kmh = 3600 / per_km
    mph = kmh / 1.60934
    return (f"{tokens[0]} in {tokens[1]}: {_pace_str(per_km)}/km — "
            f"{_pace_str(per_mi)}/mi — {kmh:.1f} km/h — {mph:.1f} mph.")


# ---------------------------------------------------------------- sleep


_BEDTIME_RE = re.compile(r"^(\d{1,2}):(\d{2})\s*([ap]m)?$")


def _run_sleep(trigger: str, args: str) -> str:
    text = (args or "").strip().lower()
    m = _BEDTIME_RE.match(text)
    if not m:
        return ("Usage: `sleep <HH:MM>` (24-hour, or with am/pm) — e.g. "
                "`sleep 22:30` or `sleep 10:30pm`. Wake times follow "
                "90-minute cycles after ~15 minutes to fall asleep.")
    hour, minute = int(m.group(1)), int(m.group(2))
    suffix = m.group(3)
    if suffix:
        if hour < 1 or hour > 12:
            return "With am/pm, the hour must be 1–12."
        if suffix == "pm" and hour != 12:
            hour += 12
        if suffix == "am" and hour == 12:
            hour = 0
    if hour > 23 or minute > 59:
        return "Time must be a valid HH:MM."
    bedtime = datetime(2000, 1, 1, hour, minute) + timedelta(minutes=15)
    wakes = []
    for cycles in (4, 5, 6):
        wake = bedtime + timedelta(minutes=90 * cycles)
        wakes.append(f"{cycles} cycles ({cycles * 1.5:.1f}h): {wake.strftime('%-I:%M %p')}")
    return ("Asleep around " + bedtime.strftime("%-I:%M %p") +
            " — wake at " + "; ".join(wakes) +
            ". Rough 90-minute-cycle estimates, not medical advice.")


# ---------------------------------------------------------------- grade


def _letter(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _run_grade(trigger: str, args: str) -> str:
    tokens = (args or "").strip().split()
    if len(tokens) < 4 or len(tokens) % 2 != 0:
        return ("Usage: `grade <score> <weight> ...` in pairs — e.g. "
                "`grade 90 0.3 80 0.7` or `grade 90 30% 80 70%`. "
                "Weights may be decimals or percents; they are scaled "
                "to add up to 100%.")
    pairs = []
    for i in range(0, len(tokens), 2):
        score = _num(tokens[i])
        weight = _num(tokens[i + 1])
        if score is None or weight is None:
            return f"Couldn't read score/weight pair `{tokens[i]} {tokens[i + 1]}`."
        if not 0 <= score <= 100:
            return f"Scores must be 0–100, got `{tokens[i]}`."
        if weight < 0:
            return f"Weights must be >= 0, got `{tokens[i + 1]}`."
        pairs.append((score, weight))
    total_weight = sum(w for _, w in pairs)
    if total_weight <= 0:
        return "Weights must add up to more than 0."
    weighted = sum(s * w for s, w in pairs) / total_weight
    return (f"Weighted average: {weighted:.1f} ({_letter(weighted)}) — "
            f"common US letter scale; your class may use a different one.")


# ---------------------------------------------------------------- registry


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="unitprice", description="Price per unit, or compare two packs.",
        usage="unitprice <price> <qty>[unit] | unitprice <price> <qty> vs <price> <qty>",
        triggers=["unitprice", "unit-price", "perunit"],
        run=_run_unitprice,
        examples=["unitprice 5.99 12oz",
                  "unitprice 5.99 12oz vs 9.99 24oz"]))
    registry.register(Skill(
        name="pace", description="Running pace per km/mile and speed.",
        usage="pace <distance><km|mi|m> <time>",
        triggers=["pace"],
        run=_run_pace,
        examples=["pace 5km 25:00", "pace 10mi 1:20:00"]))
    registry.register(Skill(
        name="sleep", description="Wake times from a bedtime in 90-min cycles.",
        usage="sleep <HH:MM>",
        triggers=["sleep", "wakeup"],
        run=_run_sleep,
        examples=["sleep 22:30", "sleep 10:30pm"]))
    registry.register(Skill(
        name="grade", description="Weighted grade average + letter grade.",
        usage="grade <score> <weight> ...",
        triggers=["grade", "grades"],
        run=_run_grade,
        examples=["grade 90 0.3 80 0.7", "grade 90 30% 80 70%"]))
