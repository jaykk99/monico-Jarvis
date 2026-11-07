"""Health and fitness estimators: calorie burn, heart-rate zones,
step distance, and workout volume.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only, following the cook/garden pattern: calories come
from standard MET values, heart-rate zones from the 220-minus-age
formula, step distance from stride length, and workout volume from
sets x reps x weight. Every figure is an estimate — not medical advice,
not a training plan, and not a substitute for a doctor, a coach, or a
scale that measures the real thing.

Conventions and explicit caveats:
- Calorie: MET values are published averages for each activity.
  Real burn varies with intensity, fitness, body composition, and
  terrain — treat the number as a rough guide, not a measured value.
- Heartrate: 220 minus age estimates maximum heart rate, typically
  within about 10-12 bpm of the true value. Zones are percentages of
  that estimate. Resting heart rate refines the targets (Karvonen),
  but a chest strap or lab test beats any formula.
- Steps: stride is estimated as 0.413 x height when height is given,
  otherwise a default 0.76 m (2.5 ft) stride. Calories use a rough
  0.04 kcal per step. Real stride varies with speed and leg length.
- Workout: volume is sets x reps x weight — a workload figure, not
  a program. Pick weights you can lift with good form; add weight
  gradually and rest between sessions.
"""
from __future__ import annotations

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


_KG_PER_LB = 0.45359237
_LB_PER_KG = 2.20462262
_KM_PER_MI = 1.609344
_M_PER_FT = 0.3048
_CM_PER_IN = 2.54
_DEFAULT_STRIDE_M = 0.762  # 2.5 ft, a typical adult walking stride
_STRIDE_FRACTION = 0.413  # stride is roughly 0.413 x height
_KCAL_PER_STEP = 0.04

_WEIGHT_RE = re.compile(r"^([0-9]*\.?[0-9]+)(kg|lb)$")
_HEIGHT_RE = re.compile(r"^([0-9]*\.?[0-9]+)(cm|m|ft|in)$")
_SETS_REPS_RE = re.compile(r"^([0-9]+)x([0-9]+)$")


def _weight_kg(token: str) -> tuple[float, str] | None:
    """Parse '80kg' / '175lb' into (kg, display string)."""
    m = _WEIGHT_RE.match(token.strip().lower())
    if not m:
        return None
    amount = float(m.group(1))
    if amount <= 0:
        return None
    if m.group(2) == "lb":
        return amount * _KG_PER_LB, f"{_fmt_num(amount)} lb"
    return amount, f"{_fmt_num(amount)} kg"


def _height_m(token: str) -> tuple[float, str] | None:
    """Parse '180cm' / '1.8m' / '5.9ft' / '70in' into (metres, display)."""
    m = _HEIGHT_RE.match(token.strip().lower())
    if not m:
        return None
    amount = float(m.group(1))
    if amount <= 0:
        return None
    unit = m.group(2)
    if unit == "cm":
        return amount / 100, f"{_fmt_num(amount)} cm"
    if unit == "m":
        return amount, f"{_fmt_num(amount)} m"
    if unit == "ft":
        return amount * _M_PER_FT, f"{_fmt_num(amount)} ft"
    return amount * _CM_PER_IN / 100, f"{_fmt_num(amount)} in"


# ---------------------------------------------------------------- calorie

# MET values: published averages (Compendium of Physical Activities).
_MET_TABLE = {
    "walk": (3.5, "walking"),
    "walking": (3.5, "walking"),
    "run": (9.8, "running"),
    "running": (9.8, "running"),
    "cycle": (7.5, "cycling"),
    "cycling": (7.5, "cycling"),
    "bike": (7.5, "cycling"),
    "swim": (8.0, "swimming"),
    "swimming": (8.0, "swimming"),
    "hike": (6.0, "hiking"),
    "hiking": (6.0, "hiking"),
    "yoga": (2.5, "yoga"),
    "weights": (6.0, "weight training"),
    "lift": (6.0, "weight training"),
    "dance": (5.5, "dancing"),
    "dancing": (5.5, "dancing"),
    "row": (7.0, "rowing"),
    "rowing": (7.0, "rowing"),
    "climb": (8.0, "climbing"),
    "climbing": (8.0, "climbing"),
}

_USAGE_CALORIE = (
    "Usage: `calorie <activity> <minutes> <weight>kg|lb` — e.g. "
    "`calorie run 30 80kg`, `calorie walk 45 175lb`. Activities: "
    + ", ".join(sorted({label for _, label in _MET_TABLE.values()})) + "."
)


def _run_calorie(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) != 3:
        return _USAGE_CALORIE
    entry = _MET_TABLE.get(tokens[0])
    if entry is None:
        return _USAGE_CALORIE
    met, label = entry
    minutes = _num(tokens[1])
    weight = _weight_kg(tokens[2])
    if minutes is None or weight is None:
        return _USAGE_CALORIE
    if minutes <= 0:
        return "Minutes must be greater than 0."
    weight_kg, weight_display = weight
    kcal = met * weight_kg * (minutes / 60)
    per_hour = met * weight_kg
    return (f"{_fmt_num(minutes)} min of {label} at {weight_display} burns "
            f"about {_fmt_num(round(kcal))} kcal "
            f"({_fmt_num(round(per_hour))} kcal per hour). "
            f"Estimate from a standard MET value ({met}) — real burn "
            f"varies with intensity and fitness; not a measured value.")


# ---------------------------------------------------------------- heartrate

_USAGE_HEARTRATE = (
    "Usage: `heartrate <age> [resting-bpm]` — e.g. `heartrate 40`, "
    "`heartrate 40 60`."
)

_ZONES = (
    ("Z1 very light", 0.50, 0.60),
    ("Z2 light", 0.60, 0.70),
    ("Z3 moderate", 0.70, 0.80),
    ("Z4 hard", 0.80, 0.90),
    ("Z5 maximum", 0.90, 1.00),
)


def _run_heartrate(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) not in (1, 2):
        return _USAGE_HEARTRATE
    age = _num(tokens[0])
    if age is None or age != int(age):
        return _USAGE_HEARTRATE
    age = int(age)
    if age < 5 or age > 110:
        return "Age must be between 5 and 110."
    resting = None
    if len(tokens) == 2:
        resting = _num(tokens[1])
        if resting is None or resting != int(resting):
            return _USAGE_HEARTRATE
        resting = int(resting)
        if resting < 30 or resting > 120:
            return "Resting heart rate must be between 30 and 120 bpm."
    max_hr = 220 - age
    zones = ", ".join(
        f"{name} {round(max_hr * lo)}-{round(max_hr * hi)} bpm"
        for name, lo, hi in _ZONES
    )
    out = (f"Age {age}: estimated max heart rate {max_hr} bpm. "
           f"Zones: {zones}. "
           f"220 minus age is a rough estimate (usually within 10-12 bpm) "
           f"— not medical advice; check with a doctor before training "
           f"at high intensity.")
    if resting is not None:
        hrr = max_hr - resting
        mod_lo = round(resting + 0.40 * hrr)
        mod_hi = round(resting + 0.59 * hrr)
        vig_lo = round(resting + 0.60 * hrr)
        vig_hi = round(resting + 0.89 * hrr)
        out += (f" With a resting rate of {resting} bpm, moderate work "
                f"is about {mod_lo}-{mod_hi} bpm and vigorous work about "
                f"{vig_lo}-{vig_hi} bpm (Karvonen).")
    return out


# ---------------------------------------------------------------- steps

_USAGE_STEPS = (
    "Usage: `steps <count> [height]cm|m|ft|in` — e.g. `steps 10000`, "
    "`steps 10000 180cm`, `steps 8000 5.9ft`."
)


def _run_steps(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) not in (1, 2):
        return _USAGE_STEPS
    steps = _num(tokens[0])
    if steps is None or steps != int(steps):
        return _USAGE_STEPS
    steps = int(steps)
    if steps <= 0:
        return "Steps must be greater than 0."
    if len(tokens) == 2:
        height = _height_m(tokens[1])
        if height is None:
            return _USAGE_STEPS
        stride_m, height_display = height
        stride_m = _STRIDE_FRACTION * stride_m
        stride_note = f"stride about {_fmt_num(round(stride_m, 2))} m from {height_display}"
    else:
        stride_m = _DEFAULT_STRIDE_M
        stride_note = "default stride 0.76 m (2.5 ft)"
    distance_m = steps * stride_m
    distance_km = distance_m / 1000
    distance_mi = distance_km / _KM_PER_MI
    kcal = steps * _KCAL_PER_STEP
    return (f"{steps:,} steps ({stride_note}) is about "
            f"{_fmt_num(round(distance_km, 2))} km "
            f"({_fmt_num(round(distance_mi, 2))} mi), roughly "
            f"{_fmt_num(round(kcal))} kcal. Stride and calories are "
            f"averages — real distance varies with speed and leg length.")


# ---------------------------------------------------------------- workout

_USAGE_WORKOUT = (
    "Usage: `workout <sets>x<reps> <weight>kg|lb [exercise]` — e.g. "
    "`workout 3x10 50kg bench`, `workout 5x5 225lb squat`."
)


def _run_workout(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) not in (2, 3):
        return _USAGE_WORKOUT
    m = _SETS_REPS_RE.match(tokens[0])
    if not m:
        return _USAGE_WORKOUT
    sets, reps = int(m.group(1)), int(m.group(2))
    if sets <= 0 or reps <= 0:
        return "Sets and reps must be greater than 0."
    weight = _weight_kg(tokens[1])
    if weight is None:
        return _USAGE_WORKOUT
    weight_kg, weight_display = weight
    exercise = tokens[2] if len(tokens) == 3 else None
    total_reps = sets * reps
    volume_kg = total_reps * weight_kg
    per_set_kg = reps * weight_kg
    if weight_display.endswith("lb"):
        volume_lb = total_reps * (weight_kg * _LB_PER_KG)
        per_set_lb = reps * (weight_kg * _LB_PER_KG)
        volume = (f"{_fmt_num(round(volume_kg))} kg "
                  f"({_fmt_num(round(volume_lb))} lb)")
        per_set = (f"{_fmt_num(round(per_set_kg))} kg "
                   f"({_fmt_num(round(per_set_lb))} lb)")
    else:
        volume = f"{_fmt_num(round(volume_kg))} kg"
        per_set = f"{_fmt_num(round(per_set_kg))} kg"
    label = f" {exercise}" if exercise else ""
    return (f"{sets} sets x {reps} reps x {weight_display}{label} = "
            f"{total_reps} reps, {volume} total volume "
            f"({per_set} per set). Volume is a workload figure, not a "
            f"training plan — lift weights you can control with good form.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="calorie", description="Calories burned for an activity, by time and body weight.",
        usage="calorie <activity> <minutes> <weight>kg|lb",
        triggers=["calorie", "calories", "burn"],
        run=_run_calorie,
        examples=["calorie run 30 80kg", "calorie walk 45 175lb"]))
    registry.register(Skill(
        name="heartrate", description="Max heart rate and training zones by age.",
        usage="heartrate <age> [resting-bpm]",
        triggers=["heartrate", "hr", "pulse"],
        run=_run_heartrate,
        examples=["heartrate 40", "heartrate 40 60"]))
    registry.register(Skill(
        name="steps", description="Step count to distance and rough calories.",
        usage="steps <count> [height]cm|m|ft|in",
        triggers=["steps", "stepcount"],
        run=_run_steps,
        examples=["steps 10000", "steps 10000 180cm"]))
    registry.register(Skill(
        name="workout", description="Total volume lifted from sets, reps, and weight.",
        usage="workout <sets>x<reps> <weight>kg|lb [exercise]",
        triggers=["workout", "volume", "lift"],
        run=_run_workout,
        examples=["workout 3x10 50kg bench", "workout 5x5 225lb squat"]))
