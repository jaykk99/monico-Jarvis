"""DIY home-project estimators: concrete, mulch, wallpaper, and sod.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only, following the paint/tiles pattern: volumes are
rounded up to whole buyable units (bags, rolls, pallets), a waste
allowance covers cuts, spillage, and breakage, and every figure is an
estimate — measure twice, and confirm bag yields against the product
you actually buy, since brands differ.

Conventions:
- Concrete: an 80 lb bag yields about 0.6 cu ft (0.017 m³).
- Mulch: sold by the cubic yard or in 2 cu ft bags.
- Wallpaper: a standard roll is 0.53 m wide × 10.05 m long; the
  pattern repeat lengthens every drop, so fewer drops fit per roll.
- Sod: a standard roll is 2 ft × 5 ft (10 sq ft); a pallet holds
  about 50 rolls (500 sq ft).
"""
from __future__ import annotations

import math
import re

from .base import Skill, SkillRegistry

# One 80 lb bag of concrete mix yields ~0.6 cu ft.
_BAG_CUFT = 0.6
_BAG_M3 = _BAG_CUFT * 0.0283168  # ≈ 0.017 m³
_CUFT_PER_M3 = 35.3147
_M3_PER_CUYD = 0.764555


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


_ROOM_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)m$")
_ROOM_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)ft$")
_AREA_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqm$")
_AREA_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqft$")
_DEPTH_CM_RE = re.compile(r"^([0-9]*\.?[0-9]+)cm$")
_DEPTH_IN_RE = re.compile(r"^([0-9]*\.?[0-9]+)in$")


def _parse_area_and_depth(tokens: list[str]):
    """Shared area+depth parser for concrete and mulch.

    Returns (area, metric, depth, rest) where area is in m² (metric)
    or sq ft (imperial), depth in cm (metric) or in (imperial), and
    rest is the leftover tokens — or None when the shape is wrong.
    """
    if len(tokens) < 2:
        return None
    first, second = tokens[0], tokens[1]
    metric = None
    area = None
    m = _ROOM_M_RE.match(first) or _AREA_M_RE.match(first)
    if m:
        metric = True
        area = float(m.group(1)) * float(m.group(2)) if "x" in first else float(m.group(1))
    else:
        m = _ROOM_FT_RE.match(first) or _AREA_FT_RE.match(first)
        if m:
            metric = False
            area = float(m.group(1)) * float(m.group(2)) if "x" in first else float(m.group(1))
    if area is None:
        return None
    dm = _DEPTH_CM_RE.match(second) if metric else _DEPTH_IN_RE.match(second)
    if not dm:
        return None
    return area, metric, float(dm.group(1)), tokens[2:]


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


def _parse_area_only(tokens: list[str]):
    """Area-only parser for sod: returns (area, metric, rest) or None."""
    if not tokens:
        return None
    first = tokens[0]
    m = _ROOM_M_RE.match(first) or _AREA_M_RE.match(first)
    if m:
        area = float(m.group(1)) * float(m.group(2)) if "x" in first else float(m.group(1))
        return area, True, tokens[1:]
    m = _ROOM_FT_RE.match(first) or _AREA_FT_RE.match(first)
    if m:
        area = float(m.group(1)) * float(m.group(2)) if "x" in first else float(m.group(1))
        return area, False, tokens[1:]
    return None


# ---------------------------------------------------------------- concrete

_USAGE_CONCRETE = (
    "Usage: `concrete <length>x<width>m <depth>cm [waste%]` or "
    "`concrete <area>sqm <depth>cm [waste%]` — imperial: `ft` with `in` "
    "instead (`concrete 10x10ft 4in`). Waste defaults to 10%. "
    "Estimate only: an 80 lb bag yields about 0.6 cu ft."
)


def _run_concrete(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    parsed = _parse_area_and_depth(tokens)
    if parsed is None:
        return _USAGE_CONCRETE
    area, metric, depth, rest = parsed
    waste = _parse_waste(rest, 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if area <= 0 or depth <= 0:
        return "Area and depth must be greater than 0."
    if metric:
        vol = area * depth / 100  # m³
        vol_waste = vol * (1 + waste / 100)
        bags = math.ceil(vol_waste / _BAG_M3)
        return (f"{_fmt_num(area)} m² at {_fmt_num(depth)} cm deep = "
                f"{_fmt_num(vol)} m³, plus {_fmt_num(waste)}% waste = "
                f"{_fmt_num(vol_waste)} m³ — buy {bags} × 80 lb bags.")
    vol_ft = area * depth / 12  # cu ft
    vol_waste = vol_ft * (1 + waste / 100)
    bags = math.ceil(vol_waste / _BAG_CUFT)
    return (f"{_fmt_num(area)} sq ft at {_fmt_num(depth)} in deep = "
            f"{_fmt_num(vol_ft)} cu ft ({_fmt_num(vol_ft / 27)} cu yd), "
            f"plus {_fmt_num(waste)}% waste = {_fmt_num(vol_waste)} cu ft "
            f"— buy {bags} × 80 lb bags.")


# ---------------------------------------------------------------- mulch

_USAGE_MULCH = (
    "Usage: `mulch <length>x<width>m <depth>cm [waste%]` or "
    "`mulch <area>sqm <depth>cm [waste%]` — imperial: `ft` with `in` "
    "instead (`mulch 10x20ft 3in`). Waste defaults to 5%. "
    "Estimate only: mulch settles after spreading, so a little extra is normal."
)


def _run_mulch(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    parsed = _parse_area_and_depth(tokens)
    if parsed is None:
        return _USAGE_MULCH
    area, metric, depth, rest = parsed
    waste = _parse_waste(rest, 5.0)
    if waste is None:
        return "Waste must be 0% or more."
    if area <= 0 or depth <= 0:
        return "Area and depth must be greater than 0."
    if metric:
        vol = area * depth / 100  # m³
        vol_waste = vol * (1 + waste / 100)
        bags = math.ceil(vol_waste * _CUFT_PER_M3 / 2)
        return (f"{_fmt_num(area)} m² at {_fmt_num(depth)} cm deep = "
                f"{_fmt_num(vol)} m³, plus {_fmt_num(waste)}% waste = "
                f"{_fmt_num(vol_waste)} m³ ({_fmt_num(vol_waste / _M3_PER_CUYD)} cu yd) "
                f"— buy {bags} × 2 cu ft bags.")
    vol_ft = area * depth / 12  # cu ft
    vol_waste = vol_ft * (1 + waste / 100)
    bags = math.ceil(vol_waste / 2)
    return (f"{_fmt_num(area)} sq ft at {_fmt_num(depth)} in deep = "
            f"{_fmt_num(vol_ft)} cu ft, plus {_fmt_num(waste)}% waste = "
            f"{_fmt_num(vol_waste)} cu ft ({_fmt_num(vol_waste / 27)} cu yd) "
            f"— buy {bags} × 2 cu ft bags.")


# ---------------------------------------------------------------- wallpaper

_USAGE_WALLPAPER = (
    "Usage: `wallpaper <length>x<width> <height> [pattern-repeat-cm]` — "
    "all in metres, e.g. `wallpaper 4x5 2.4`, `wallpaper 4x5 2.4 32`. "
    "Standard roll: 0.53 m wide × 10.05 m long. Estimate only: it "
    "covers all walls and ignores doors/windows."
)

_WALL_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)$")
_ROLL_WIDTH_M = 0.53
_ROLL_LENGTH_M = 10.05


def _run_wallpaper(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) not in (2, 3):
        return _USAGE_WALLPAPER
    m = _WALL_RE.match(tokens[0])
    height = _num(tokens[1])
    if not m or height is None:
        return _USAGE_WALLPAPER
    length, width = float(m.group(1)), float(m.group(2))
    repeat_m = 0.0
    if len(tokens) == 3:
        repeat = _num(tokens[2].removesuffix("cm"))
        if repeat is None or repeat < 0:
            return "Pattern repeat must be 0 cm or more."
        repeat_m = repeat / 100
    if length <= 0 or width <= 0 or height <= 0:
        return "Room size and wall height must be greater than 0."
    drop_len = height + repeat_m
    if drop_len > _ROLL_LENGTH_M:
        return ("Wall height plus pattern repeat exceeds one roll length "
                f"({_fmt_num(_ROLL_LENGTH_M)} m) — this roll size can't do it.")
    perimeter = 2 * (length + width)
    drops = math.ceil(perimeter / _ROLL_WIDTH_M)
    drops_per_roll = int(_ROLL_LENGTH_M // drop_len)
    rolls = math.ceil(drops / drops_per_roll)
    repeat_note = (f" with a {_fmt_num(repeat_m * 100)} cm repeat"
                   if repeat_m else "")
    return (f"Walls {_fmt_num(perimeter)} m around, "
            f"{_fmt_num(height)} m high{repeat_note}: {drops} drops "
            f"({drops_per_roll} per roll) — buy {rolls} rolls "
            f"(0.53 m × 10.05 m).")


# ---------------------------------------------------------------- sod

_USAGE_SOD = (
    "Usage: `sod <area>sqm [waste%]` or `sod <length>x<width>m [waste%]` — "
    "imperial: `sqft` / `ft` instead (`sod 1000sqft`). Waste defaults "
    "to 5% for cuts and odd shapes. Standard roll: 2 ft × 5 ft; "
    "a pallet holds about 50 rolls."
)

_ROLL_M2 = 10 * 0.092903  # 10 sq ft in m²
_ROLLS_PER_PALLET = 50


def _run_sod(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    parsed = _parse_area_only(tokens)
    if parsed is None:
        return _USAGE_SOD
    area, metric, rest = parsed
    waste = _parse_waste(rest, 5.0)
    if waste is None:
        return "Waste must be 0% or more."
    if area <= 0:
        return "Area must be greater than 0."
    if metric:
        area_waste = area * (1 + waste / 100)
        rolls = math.ceil(area_waste / _ROLL_M2)
        pallets = math.ceil(rolls / _ROLLS_PER_PALLET)
        return (f"{_fmt_num(area)} m², plus {_fmt_num(waste)}% waste = "
                f"{_fmt_num(area_waste)} m² — buy {rolls} rolls "
                f"(2 ft × 5 ft), about {pallets} pallet"
                f"{'s' if pallets != 1 else ''}.")
    area_waste = area * (1 + waste / 100)
    rolls = math.ceil(area_waste / 10)
    pallets = math.ceil(rolls / _ROLLS_PER_PALLET)
    return (f"{_fmt_num(area)} sq ft, plus {_fmt_num(waste)}% waste = "
            f"{_fmt_num(area_waste)} sq ft — buy {rolls} rolls "
            f"(2 ft × 5 ft), about {pallets} pallet"
            f"{'s' if pallets != 1 else ''}.")


# ---------------------------------------------------------------- registration

def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="concrete", description="Concrete volume and 80 lb bags for a slab.",
        usage="concrete <l>x<w>m <depth>cm [waste%] | concrete <l>x<w>ft <depth>in [waste%]",
        triggers=["concrete", "cement"],
        run=_run_concrete,
        examples=["concrete 4x5m 10cm", "concrete 10x10ft 4in"]))
    registry.register(Skill(
        name="mulch", description="Mulch volume in m³/cu yd and 2 cu ft bags for a bed.",
        usage="mulch <l>x<w>m <depth>cm [waste%] | mulch <l>x<w>ft <depth>in [waste%]",
        triggers=["mulch"],
        run=_run_mulch,
        examples=["mulch 10sqm 8cm", "mulch 10x20ft 3in"]))
    registry.register(Skill(
        name="wallpaper", description="Wallpaper rolls for a room, with pattern-repeat waste.",
        usage="wallpaper <length>x<width> <height> [pattern-repeat-cm]",
        triggers=["wallpaper"],
        run=_run_wallpaper,
        examples=["wallpaper 4x5 2.4", "wallpaper 4x5 2.4 32"]))
    registry.register(Skill(
        name="sod", description="Sod rolls and pallets for a lawn area.",
        usage="sod <area>sqm [waste%] | sod <area>sqft [waste%]",
        triggers=["sod", "turf"],
        run=_run_sod,
        examples=["sod 50sqm", "sod 1000sqft"]))
