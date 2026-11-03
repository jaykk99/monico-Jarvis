"""Plumbing estimators: pipe, drain slope, tank volume, fill time.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only, following the build pattern: counts are rounded
up to whole buyable units, a waste allowance covers cuts and offcuts,
and every figure is an estimate — confirm product sizes against what
you actually buy, since brands and suppliers differ.

Conventions:
- Pipe: lengths for a straight run — lengths 3 m (10 ft) long unless
  you give the length. Waste defaults to 10%. Fittings (elbows,
  couplings, valves) are not counted, so add those separately.
- Slope: drop for a drain run — grade defaults to 2% metric
  (1/4 in per ft imperial), the usual minimum for a drain that
  actually clears. This is fall only; venting and trap rules are
  a code question, not an arithmetic one.
- Tank: volume of a rectangular tank — litres and US gallons.
  Round tanks need a different formula, so they are not covered.
- Fill: time to fill a volume at a flow rate — litres with L/min,
  or US gallons with gpm; the two must match.
"""
from __future__ import annotations

import math
import re

from .base import Skill, SkillRegistry


def _num(token: str) -> float | None:
    """Parse a number, tolerating a leading $ and thousands commas."""
    token = token.lstrip("$").replace(",", "")
    try:
        return float(token)
    except ValueError:
        return None


def _fmt_num(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}".rstrip("0").rstrip(".")


_LENGTH_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)m$")
_LENGTH_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)ft$")
_DIMS_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)m$")
_DIMS_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)ft$")
_VOL_L_RE = re.compile(r"^([0-9]*\.?[0-9]+)l$")
_VOL_GAL_RE = re.compile(r"^([0-9]*\.?[0-9]+)gal$")
_RATE_L_RE = re.compile(r"^([0-9]*\.?[0-9]+)l/min$")
_RATE_GPM_RE = re.compile(r"^([0-9]*\.?[0-9]+)gpm$")
_GRADE_IN_RE = re.compile(r"^([0-9]*\.?[0-9]+)in$")


def _parse_waste(rest: list[str], default: float) -> float | None:
    """Optional trailing waste percent (``15%`` or bare ``15``)."""
    if not rest:
        return default
    if len(rest) > 1:
        return None
    waste = _num(rest[0].rstrip("%"))
    if waste is None or waste < 0:
        return None
    return waste


# ---------------------------------------------------------------- pipe

_USAGE_PIPE = (
    "Usage: `pipe <length>m [piece-m] [waste%]` | "
    "`pipe <length>ft [piece-ft] [waste%]` — e.g. "
    "`pipe 30m`, `pipe 100ft 20ft`."
)

_PIPE_M = 3.0
_PIPE_FT = 10.0


def _run_pipe(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens:
        return _USAGE_PIPE
    m = _LENGTH_M_RE.match(tokens[0])
    metric = True
    if m:
        length = float(m.group(1))
        piece = _PIPE_M
        rest = tokens[1:]
        if rest:
            pm = _LENGTH_M_RE.match(rest[0])
            if pm:
                piece = float(pm.group(1))
                rest = rest[1:]
    else:
        m = _LENGTH_FT_RE.match(tokens[0])
        if not m:
            return _USAGE_PIPE
        metric = False
        length = float(m.group(1))
        piece = _PIPE_FT
        rest = tokens[1:]
        if rest:
            pm = _LENGTH_FT_RE.match(rest[0])
            if pm:
                piece = float(pm.group(1))
                rest = rest[1:]
    # A leftover token that is not a number is a usage error, not waste.
    if rest and _num(rest[0].rstrip("%")) is None:
        return _USAGE_PIPE
    waste = _parse_waste(rest, 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if length <= 0:
        return "Run length must be greater than 0."
    if piece <= 0:
        return "Pipe length must be greater than 0."
    need = length * (1 + waste / 100)
    pieces = math.ceil(round(need / piece, 9))
    unit = "m" if metric else "ft"
    return (f"{_fmt_num(length)} {unit} run, plus {_fmt_num(waste)}% waste = "
            f"{_fmt_num(need)} {unit} — buy {pieces} lengths "
            f"({_fmt_num(piece)} {unit} each, fittings not counted).")


# ---------------------------------------------------------------- slope

_USAGE_SLOPE = (
    "Usage: `slope <length>m [grade%]` | "
    "`slope <length>ft [grade-in-per-ft]` — e.g. "
    "`slope 10m`, `slope 40ft 0.5in`."
)

_GRADE_M = 2.0
_GRADE_FT = 0.25


def _run_slope(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens:
        return _USAGE_SLOPE
    m = _LENGTH_M_RE.match(tokens[0])
    metric = True
    if m:
        length = float(m.group(1))
        grade = _GRADE_M
        rest = tokens[1:]
        if rest:
            g = _num(rest[0].rstrip("%"))
            if g is None:
                return _USAGE_SLOPE
            grade = g
            rest = rest[1:]
    else:
        m = _LENGTH_FT_RE.match(tokens[0])
        if not m:
            return _USAGE_SLOPE
        metric = False
        length = float(m.group(1))
        grade = _GRADE_FT
        rest = tokens[1:]
        if rest:
            gm = _GRADE_IN_RE.match(rest[0])
            if gm:
                grade = float(gm.group(1))
            else:
                g = _num(rest[0])
                if g is None:
                    return _USAGE_SLOPE
                grade = g
            rest = rest[1:]
    if rest:
        return _USAGE_SLOPE
    if length <= 0:
        return "Run length must be greater than 0."
    if grade <= 0:
        return "Grade must be greater than 0."
    if metric:
        drop_cm = length * grade / 100 * 100
        return (f"{_fmt_num(length)} m run at {_fmt_num(grade)}% grade — "
                f"drop {_fmt_num(drop_cm)} cm "
                f"({_fmt_num(length * grade / 100)} m).")
    drop_in = length * grade
    return (f"{_fmt_num(length)} ft run at {_fmt_num(grade)} in per ft — "
            f"drop {_fmt_num(drop_in)} in "
            f"({_fmt_num(drop_in / 12)} ft).")


# ---------------------------------------------------------------- tank

_USAGE_TANK = (
    "Usage: `tank <length>x<width>x<height>m` | "
    "`tank <length>x<width>x<height>ft` — e.g. "
    "`tank 2x1x1m`, `tank 4x3x2ft`."
)

_L_PER_M3 = 1000.0
_GAL_PER_L = 0.264172
_GAL_PER_CUFT = 7.48052


def _run_tank(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) != 1:
        return _USAGE_TANK
    m = _DIMS_M_RE.match(tokens[0])
    if m:
        length, width, height = (float(g) for g in m.groups())
        if length <= 0 or width <= 0 or height <= 0:
            return "Tank dimensions must be greater than 0."
        volume_m3 = length * width * height
        litres = volume_m3 * _L_PER_M3
        gallons = litres * _GAL_PER_L
        return (f"{_fmt_num(length)} x {_fmt_num(width)} x {_fmt_num(height)} m tank — "
                f"{_fmt_num(volume_m3)} m³, {_fmt_num(litres)} litres "
                f"({_fmt_num(gallons)} US gallons).")
    m = _DIMS_FT_RE.match(tokens[0])
    if not m:
        return _USAGE_TANK
    length, width, height = (float(g) for g in m.groups())
    if length <= 0 or width <= 0 or height <= 0:
        return "Tank dimensions must be greater than 0."
    volume_ft3 = length * width * height
    gallons = volume_ft3 * _GAL_PER_CUFT
    return (f"{_fmt_num(length)} x {_fmt_num(width)} x {_fmt_num(height)} ft tank — "
            f"{_fmt_num(volume_ft3)} cu ft "
            f"({_fmt_num(gallons)} US gallons).")


# ---------------------------------------------------------------- fill

_USAGE_FILL = (
    "Usage: `fill <volume>L <rate>L/min` | "
    "`fill <volume>gal <rate>gpm` — e.g. "
    "`fill 1000L 50L/min`, `fill 100gal 5gpm`."
)


def _fmt_minutes(minutes: float) -> str:
    whole = int(round(minutes))
    if whole < 60:
        return f"{whole} minutes"
    hours, mins = divmod(whole, 60)
    if mins == 0:
        return f"{hours}h ({whole} minutes)"
    return f"{hours}h {mins}m ({whole} minutes)"


def _run_fill(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) != 2:
        return _USAGE_FILL
    vm = _VOL_L_RE.match(tokens[0])
    vg = _VOL_GAL_RE.match(tokens[0])
    if vm:
        volume = float(vm.group(1))
        metric = True
        rm = _RATE_L_RE.match(tokens[1])
        if not rm:
            return "Volume and rate units must match (both litres or both gallons)."
        rate = float(rm.group(1))
        vol_label = f"{_fmt_num(volume)} litres"
        rate_label = f"{_fmt_num(rate)} L/min"
    elif vg:
        volume = float(vg.group(1))
        metric = False
        rm = _RATE_GPM_RE.match(tokens[1])
        if not rm:
            return "Volume and rate units must match (both litres or both gallons)."
        rate = float(rm.group(1))
        vol_label = f"{_fmt_num(volume)} US gallons"
        rate_label = f"{_fmt_num(rate)} gpm"
    else:
        return _USAGE_FILL
    if volume <= 0:
        return "Volume must be greater than 0."
    if rate <= 0:
        return "Flow rate must be greater than 0."
    minutes = volume / rate
    return (f"{vol_label} at {rate_label} — "
            f"fills in {_fmt_minutes(minutes)}.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="pipe", description="Pipe lengths for a straight run, with a waste allowance.",
        usage="pipe <length>m [piece-m] [waste%] | pipe <length>ft [piece-ft] [waste%]",
        triggers=["pipe", "piping"],
        run=_run_pipe,
        examples=["pipe 30m", "pipe 100ft 20ft"]))
    registry.register(Skill(
        name="slope", description="Drain drop for a run at a grade (2% metric, 1/4 in per ft imperial).",
        usage="slope <length>m [grade%] | slope <length>ft [grade-in-per-ft]",
        triggers=["slope", "drain", "fall"],
        run=_run_slope,
        examples=["slope 10m", "slope 40ft 0.5in"]))
    registry.register(Skill(
        name="tank", description="Volume of a rectangular tank, in litres and US gallons.",
        usage="tank <length>x<width>x<height>m | tank <length>x<width>x<height>ft",
        triggers=["tank", "tankvolume"],
        run=_run_tank,
        examples=["tank 2x1x1m", "tank 4x3x2ft"]))
    registry.register(Skill(
        name="fill", description="Time to fill a volume at a flow rate.",
        usage="fill <volume>L <rate>L/min | fill <volume>gal <rate>gpm",
        triggers=["fill", "filltime"],
        run=_run_fill,
        examples=["fill 1000L 50L/min", "fill 100gal 5gpm"]))
