"""Interior build-out estimators: siding, flooring, wall studs, bricks.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only, following the build pattern: counts are rounded
up to whole buyable units, a waste allowance covers cuts and offcuts,
and every figure is an estimate — confirm product sizes against what
you actually buy, since brands and suppliers differ.

Conventions:
- Siding: sold by the square — 100 sq ft (9.29 m²) per square.
  Waste defaults to 10%.
- Floor: flooring sold by the box — a box covers 2 m² (20 sq ft)
  unless you give its coverage. Waste defaults to 10%.
- Studs: wall studs one spacing apart — 0.4 m (16 in) on centre by
  default, plus one end stud. No waste allowance: a stud count is
  exact for the run, and offcuts are reused as blocking.
- Brick: standard brick face with mortar joints — about 60 bricks
  per m² (7 per sq ft). Waste defaults to 10%; mortar, ties, and
  lintels are not counted.
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


_RUN_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)m$")
_RUN_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)ft$")
_AREA_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqm$")
_AREA_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqft$")
_COVER_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)(?:m2|sqm)$")
_COVER_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqft$")
_LENGTH_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)m$")
_LENGTH_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)ft$")
_SPACING_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)m$")
_SPACING_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)ft$")
_SPACING_IN_RE = re.compile(r"^([0-9]*\.?[0-9]+)in$")


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


def _parse_area(tokens: list[str]):
    """Area token: ``<l>x<w>m``, ``<l>x<w>ft``, ``<n>sqm``, ``<n>sqft``.

    Returns (area, metric, rest) or None when the shape is wrong.
    """
    if not tokens:
        return None
    first = tokens[0]
    m = _RUN_M_RE.match(first) or _AREA_M_RE.match(first)
    if m:
        area = float(m.group(1)) * float(m.group(2)) if "x" in first else float(m.group(1))
        return area, True, tokens[1:]
    m = _RUN_FT_RE.match(first) or _AREA_FT_RE.match(first)
    if m:
        area = float(m.group(1)) * float(m.group(2)) if "x" in first else float(m.group(1))
        return area, False, tokens[1:]
    return None


# ---------------------------------------------------------------- siding

_USAGE_SIDING = (
    "Usage: `siding <area>sqm [waste%]` | "
    "`siding <area>sqft [waste%]` — e.g. "
    "`siding 50sqm`, `siding 1000sqft 15%`."
)

_SQUARE_M = 9.29
_SQUARE_FT = 100.0


def _run_siding(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    parsed = _parse_area(tokens)
    if parsed is None:
        return _USAGE_SIDING
    area, metric, rest = parsed
    # A leftover token that is not a number is a usage error, not waste.
    if rest and _num(rest[0].rstrip("%")) is None:
        return _USAGE_SIDING
    waste = _parse_waste(rest, 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if area <= 0:
        return "Area must be greater than 0."
    square = _SQUARE_M if metric else _SQUARE_FT
    need = area * (1 + waste / 100)
    squares = math.ceil(round(need / square, 9))
    unit = "m²" if metric else "sq ft"
    return (f"{_fmt_num(area)} {unit} to cover, plus {_fmt_num(waste)}% waste = "
            f"{_fmt_num(need)} {unit} — buy {squares} squares "
            f"({_fmt_num(square)} {unit} each).")


# ---------------------------------------------------------------- floor

_USAGE_FLOOR = (
    "Usage: `floor <area>sqm [box-m2] [waste%]` | "
    "`floor <area>sqft [box-sqft] [waste%]` — e.g. "
    "`floor 20sqm`, `floor 400sqft 24sqft`."
)

_BOX_M = 2.0
_BOX_FT = 20.0


def _run_floor(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    parsed = _parse_area(tokens)
    if parsed is None:
        return _USAGE_FLOOR
    area, metric, rest = parsed
    cover = _BOX_M if metric else _BOX_FT
    if rest:
        cm = (_COVER_M_RE if metric else _COVER_FT_RE).match(rest[0])
        if cm:
            cover = float(cm.group(1))
            rest = rest[1:]
    # A leftover token that is not a number (e.g. a wrong-unit
    # coverage like `10cm`) is a usage error, not a waste value.
    if rest and _num(rest[0].rstrip("%")) is None:
        return _USAGE_FLOOR
    waste = _parse_waste(rest, 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if area <= 0:
        return "Area must be greater than 0."
    if cover <= 0:
        return "Box coverage must be greater than 0."
    need = area * (1 + waste / 100)
    boxes = math.ceil(round(need / cover, 9))
    unit = "m²" if metric else "sq ft"
    return (f"{_fmt_num(area)} {unit} to cover, plus {_fmt_num(waste)}% waste = "
            f"{_fmt_num(need)} {unit} — buy {boxes} boxes "
            f"({_fmt_num(cover)} {unit} each).")


# ---------------------------------------------------------------- studs

_USAGE_STUDS = (
    "Usage: `studs <length>m [spacing-m]` | "
    "`studs <length>ft [spacing-in]` — e.g. "
    "`studs 10m`, `studs 12ft 24in`."
)

_SPACING_DEFAULT_M = 0.4
_SPACING_DEFAULT_IN = 16.0


def _run_studs(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens:
        return _USAGE_STUDS
    m = _LENGTH_M_RE.match(tokens[0])
    metric = True
    if m:
        length = float(m.group(1))
        spacing = _SPACING_DEFAULT_M
        if len(tokens) > 1:
            sm = _SPACING_M_RE.match(tokens[1])
            if not sm:
                return _USAGE_STUDS
            spacing = float(sm.group(1))
        rest = tokens[2:]
    else:
        m = _LENGTH_FT_RE.match(tokens[0])
        if not m:
            return _USAGE_STUDS
        metric = False
        length = float(m.group(1))
        spacing = _SPACING_DEFAULT_IN
        if len(tokens) > 1:
            sm = _SPACING_IN_RE.match(tokens[1])
            if not sm:
                return _USAGE_STUDS
            spacing = float(sm.group(1))
        rest = tokens[2:]
    if rest:
        return _USAGE_STUDS
    if length <= 0:
        return "Wall length must be greater than 0."
    if spacing <= 0:
        return "Stud spacing must be greater than 0."
    if metric:
        bays = math.ceil(round(length / spacing, 9))
        studs = bays + 1
        return (f"{_fmt_num(length)} m wall, studs every "
                f"{_fmt_num(spacing)} m — buy {studs} studs "
                f"({bays} bays plus one end stud).")
    length_in = length * 12
    bays = math.ceil(round(length_in / spacing, 9))
    studs = bays + 1
    return (f"{_fmt_num(length)} ft wall, studs every "
            f"{_fmt_num(spacing)} in — buy {studs} studs "
            f"({bays} bays plus one end stud).")


# ---------------------------------------------------------------- brick

_USAGE_BRICK = (
    "Usage: `brick <area>sqm [waste%]` | "
    "`brick <area>sqft [waste%]` — e.g. "
    "`brick 20sqm`, `brick 200sqft 15%`."
)

_BRICKS_PER_M2 = 60.0
_BRICKS_PER_SQFT = 7.0


def _run_brick(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    parsed = _parse_area(tokens)
    if parsed is None:
        return _USAGE_BRICK
    area, metric, rest = parsed
    # A leftover token that is not a number is a usage error, not waste.
    if rest and _num(rest[0].rstrip("%")) is None:
        return _USAGE_BRICK
    waste = _parse_waste(rest, 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if area <= 0:
        return "Area must be greater than 0."
    rate = _BRICKS_PER_M2 if metric else _BRICKS_PER_SQFT
    bricks = math.ceil(round(area * rate * (1 + waste / 100), 9))
    unit = "m²" if metric else "sq ft"
    return (f"{_fmt_num(area)} {unit} of wall at {_fmt_num(rate)} bricks per "
            f"{unit}, plus {_fmt_num(waste)}% waste — buy {_fmt_num(bricks)} bricks "
            f"(mortar, ties, and lintels not counted).")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="siding", description="Siding squares for a wall area, with a waste allowance.",
        usage="siding <area>sqm [waste%] | siding <area>sqft [waste%]",
        triggers=["siding", "cladding"],
        run=_run_siding,
        examples=["siding 50sqm", "siding 1000sqft 15%"]))
    registry.register(Skill(
        name="floor", description="Flooring boxes for a floor area, with a waste allowance.",
        usage="floor <area>sqm [box-m2] [waste%] | floor <area>sqft [box-sqft] [waste%]",
        triggers=["floor", "flooring"],
        run=_run_floor,
        examples=["floor 20sqm", "floor 400sqft 24sqft"]))
    registry.register(Skill(
        name="studs", description="Wall studs for a wall run at a given on-centre spacing.",
        usage="studs <length>m [spacing-m] | studs <length>ft [spacing-in]",
        triggers=["studs", "framing"],
        run=_run_studs,
        examples=["studs 10m", "studs 12ft 24in"]))
    registry.register(Skill(
        name="brick", description="Bricks for a wall area, with a waste allowance.",
        usage="brick <area>sqm [waste%] | brick <area>sqft [waste%]",
        triggers=["brick", "bricks"],
        run=_run_brick,
        examples=["brick 20sqm", "brick 200sqft 15%"]))
