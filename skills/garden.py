"""Garden estimators: topsoil, grass seed, planter fill, plant spacing.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only, following the yard/diy pattern: counts are
rounded up to whole buyable units, a waste allowance covers settling
and spillage, and every figure is an estimate — confirm product sizes
against what you actually buy, since brands and bag sizes differ.

Conventions and explicit caveats:
- Soil: bag size is 40 L metric (1.5 cu ft imperial), a common retail
  bag. Waste defaults to 10% because loose soil settles and compacts
  after watering; a bed filled level today sits lower in a week, so
  the extra is not padding, it is the settling allowance.
- Seed: the default is a general new-lawn rate, 35 g/m2 (7 lb per
  1,000 sq ft). Rates vary a lot by grass species and by new lawn
  versus overseeding, so check the bag: this is a planning figure,
  not a seeding prescription.
- Planter: volume is the ideal fill of the box or pot. Real fill is
  less — pots need drainage space at the bottom and a gap below the
  rim — so buy the rounded-up bag count and expect leftover soil.
- Spacing: a grid count, edge plants included (one plant at each
  end of every row). Staggered rows, mature plant size, and the
  seed packet's own spacing all change the real count.
"""
from __future__ import annotations

import math
import re

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


_RUN_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)m$")
_RUN_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)ft$")
_RUN3_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)cm$")
_RUN3_IN_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)in$")
_AREA_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqm$")
_AREA_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqft$")
_DEPTH_CM_RE = re.compile(r"^([0-9]*\.?[0-9]+)cm$")
_DEPTH_IN_RE = re.compile(r"^([0-9]*\.?[0-9]+)in$")
_LENGTH_CM_RE = re.compile(r"^([0-9]*\.?[0-9]+)cm$")
_LENGTH_IN_RE = re.compile(r"^([0-9]*\.?[0-9]+)in$")


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


def _parse_area_and_depth(tokens: list[str]):
    """Shared area+depth parser (same shape as yard.py).

    Returns (area, metric, depth, rest) where area is in m2 (metric)
    or sq ft (imperial), depth in cm (metric) or in (imperial), and
    rest is the leftover tokens — or None when the shape is wrong.
    """
    if len(tokens) < 2:
        return None
    first, second = tokens[0], tokens[1]
    metric = None
    area = None
    m = _RUN_M_RE.match(first) or _AREA_M_RE.match(first)
    if m:
        metric = True
        area = float(m.group(1)) * float(m.group(2)) if "x" in first else float(m.group(1))
    else:
        m = _RUN_FT_RE.match(first) or _AREA_FT_RE.match(first)
        if m:
            metric = False
            area = float(m.group(1)) * float(m.group(2)) if "x" in first else float(m.group(1))
    if area is None:
        return None
    dm = _DEPTH_CM_RE.match(second) if metric else _DEPTH_IN_RE.match(second)
    if not dm:
        return None
    return area, metric, float(dm.group(1)), tokens[2:]


# ---------------------------------------------------------------- soil

_USAGE_SOIL = (
    "Usage: `soil <l>x<w>m <depth>cm [waste%]` | "
    "`soil <l>x<w>ft <depth>in [waste%]` — e.g. `soil 4x2m 15cm`, "
    "`soil 12x6ft 6in`."
)

_SOIL_BAG_L = 40.0
_SOIL_BAG_CUFT = 1.5
_CUFT_PER_CUYD = 27


def _run_soil(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    parsed = _parse_area_and_depth(tokens)
    if parsed is None:
        return _USAGE_SOIL
    area, metric, depth, rest = parsed
    waste = _parse_waste(rest, 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if area <= 0:
        return "Area must be greater than 0."
    if depth <= 0:
        return "Depth must be greater than 0."
    if metric:
        volume = area * depth / 100
        volume_waste = volume * (1 + waste / 100)
        litres = volume_waste * 1000
        bags = math.ceil(round(litres / _SOIL_BAG_L, 9))
        return (f"{_fmt_num(area)} m² at {_fmt_num(depth)} cm deep = "
                f"{_fmt_num(volume)} m³, plus {_fmt_num(waste)}% waste = "
                f"{_fmt_num(volume_waste)} m³ ({_fmt_num(litres)} L) — "
                f"buy {bags} bags ({_fmt_num(_SOIL_BAG_L)} L each).")
    volume_ft = area * depth / 12
    volume_yd = volume_ft / _CUFT_PER_CUYD
    volume_yd_waste = volume_yd * (1 + waste / 100)
    volume_ft_waste = volume_yd_waste * _CUFT_PER_CUYD
    bags = math.ceil(round(volume_ft_waste / _SOIL_BAG_CUFT, 9))
    return (f"{_fmt_num(area)} sq ft at {_fmt_num(depth)} in deep = "
            f"{_fmt_num(volume_ft)} cu ft ({_fmt_num(volume_yd)} cu yd), "
            f"plus {_fmt_num(waste)}% waste = {_fmt_num(volume_yd_waste)} cu yd "
            f"— buy {bags} bags ({_fmt_num(_SOIL_BAG_CUFT)} cu ft each).")


# ---------------------------------------------------------------- seed

_USAGE_SEED = (
    "Usage: `seed <area>sqm [rate-g/m2]` | "
    "`seed <area>sqft [rate-lb-per-1000sqft]` — e.g. `seed 100sqm`, "
    "`seed 5000sqft`."
)

_SEED_G_PER_M2 = 35.0
_SEED_LB_PER_1000FT2 = 7.0


def _run_seed(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens or len(tokens) > 2:
        return _USAGE_SEED
    mm = _AREA_M_RE.match(tokens[0])
    mf = _AREA_FT_RE.match(tokens[0])
    if mm:
        area = float(mm.group(1))
        metric = True
    elif mf:
        area = float(mf.group(1))
        metric = False
    else:
        return _USAGE_SEED
    rate = _SEED_G_PER_M2 if metric else _SEED_LB_PER_1000FT2
    if len(tokens) == 2:
        given = _num(tokens[1])
        if given is None:
            return _USAGE_SEED
        rate = given
    if area <= 0:
        return "Area must be greater than 0."
    if rate <= 0:
        return "Seed rate must be greater than 0."
    if metric:
        grams = area * rate
        kilos = grams / 1000
        return (f"{_fmt_num(area)} m² at {_fmt_num(rate)} g/m² — "
                f"buy {_fmt_num(grams)} g ({_fmt_num(kilos)} kg) of seed "
                f"(general new-lawn rate; check the bag for your grass).")
    pounds = area / 1000 * rate
    return (f"{_fmt_num(area)} sq ft at {_fmt_num(rate)} lb per 1,000 sq ft — "
            f"buy {_fmt_num(pounds)} lb of seed "
            f"(general new-lawn rate; check the bag for your grass).")


# ---------------------------------------------------------------- planter

_USAGE_PLANTER = (
    "Usage: `planter <l>x<w>x<h>cm` | `planter <l>x<w>x<h>in` | "
    "`planter round <diameter>cm <depth>cm` | "
    "`planter round <diameter>in <depth>in` — e.g. "
    "`planter 60x30x30cm`, `planter round 30cm 25cm`."
)

_LITRES_PER_CUFT = 28.3168


def _run_planter(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens:
        return _USAGE_PLANTER
    metric = None
    litres = None
    if tokens[0] == "round":
        if len(tokens) != 3:
            return _USAGE_PLANTER
        dm = _LENGTH_CM_RE.match(tokens[1])
        hm = _LENGTH_CM_RE.match(tokens[2])
        if dm and hm:
            metric = True
            diameter, depth = float(dm.group(1)), float(hm.group(1))
        else:
            di = _LENGTH_IN_RE.match(tokens[1])
            hi = _LENGTH_IN_RE.match(tokens[2])
            if not di or not hi:
                return _USAGE_PLANTER
            metric = False
            diameter, depth = float(di.group(1)), float(hi.group(1))
        if diameter <= 0 or depth <= 0:
            return "Diameter and depth must be greater than 0."
        if metric:
            litres = math.pi * (diameter / 2) ** 2 * depth / 1000
        else:
            cubic_in = math.pi * (diameter / 2) ** 2 * depth
            litres = cubic_in / 61.0237
    else:
        if len(tokens) != 1:
            return _USAGE_PLANTER
        m = _RUN3_M_RE.match(tokens[0])
        if m:
            metric = True
            dims = [float(m.group(i)) for i in (1, 2, 3)]
        else:
            m = _RUN3_IN_RE.match(tokens[0])
            if not m:
                return _USAGE_PLANTER
            metric = False
            dims = [float(m.group(i)) for i in (1, 2, 3)]
        if any(d <= 0 for d in dims):
            return "Planter size must be greater than 0."
        if metric:
            litres = dims[0] * dims[1] * dims[2] / 1000
        else:
            litres = dims[0] * dims[1] * dims[2] / 61.0237
    if metric:
        bags = math.ceil(round(litres / _SOIL_BAG_L, 9))
        shape = (f"round planter {_fmt_num(diameter)} cm across, "
                 f"{_fmt_num(depth)} cm deep" if tokens[0] == "round" else
                 f"{_fmt_num(dims[0])} × {_fmt_num(dims[1])} × {_fmt_num(dims[2])} cm planter")
        return (f"{shape} holds about {_fmt_num(litres)} L of soil — "
                f"buy {bags} bag{'s' if bags != 1 else ''} "
                f"({_fmt_num(_SOIL_BAG_L)} L each).")
    cuft = litres / _LITRES_PER_CUFT
    gallons = litres * 0.264172
    bags = math.ceil(round(cuft / _SOIL_BAG_CUFT, 9))
    shape = (f"round planter {_fmt_num(diameter)} in across, "
             f"{_fmt_num(depth)} in deep" if tokens[0] == "round" else
             f"{_fmt_num(dims[0])} × {_fmt_num(dims[1])} × {_fmt_num(dims[2])} in planter")
    return (f"{shape} holds about {_fmt_num(cuft)} cu ft "
            f"({_fmt_num(gallons)} US gallons) of soil — "
            f"buy {bags} bag{'s' if bags != 1 else ''} "
            f"({_fmt_num(_SOIL_BAG_CUFT)} cu ft each).")


# ---------------------------------------------------------------- spacing

_USAGE_SPACING = (
    "Usage: `spacing <l>x<w>m <spacing>cm` | "
    "`spacing <l>x<w>ft <spacing>in` — e.g. `spacing 4x2m 30cm`, "
    "`spacing 12x6ft 12in`."
)


def _run_spacing(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) != 2:
        return _USAGE_SPACING
    m = _RUN_M_RE.match(tokens[0])
    metric = True
    if m:
        bed_l, bed_w = float(m.group(1)), float(m.group(2))
        sm = _DEPTH_CM_RE.match(tokens[1])
        if not sm:
            return _USAGE_SPACING
        spacing = float(sm.group(1))
    else:
        m = _RUN_FT_RE.match(tokens[0])
        if not m:
            return _USAGE_SPACING
        metric = False
        bed_l, bed_w = float(m.group(1)), float(m.group(2))
        sm = _DEPTH_IN_RE.match(tokens[1])
        if not sm:
            return _USAGE_SPACING
        spacing = float(sm.group(1))
    if bed_l <= 0 or bed_w <= 0:
        return "Bed size must be greater than 0."
    if spacing <= 0:
        return "Spacing must be greater than 0."
    if metric:
        along_l = math.floor(round(bed_l * 100 / spacing, 9)) + 1
        along_w = math.floor(round(bed_w * 100 / spacing, 9)) + 1
        unit = "cm"
        bed_unit = "m"
    else:
        along_l = math.floor(round(bed_l * 12 / spacing, 9)) + 1
        along_w = math.floor(round(bed_w * 12 / spacing, 9)) + 1
        unit = "in"
        bed_unit = "ft"
    plants = along_l * along_w
    return (f"{_fmt_num(bed_l)} × {_fmt_num(bed_w)} {bed_unit} bed at "
            f"{_fmt_num(spacing)} {unit} spacing — {along_l} along the length "
            f"x {along_w} across = {plants} plants "
            f"(grid count, edge plants included).")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="soil", description="Topsoil volume in m³ (or cu yd) and 40 L (1.5 cu ft) bags for a bed.",
        usage="soil <l>x<w>m <depth>cm [waste%] | soil <l>x<w>ft <depth>in [waste%]",
        triggers=["soil", "topsoil"],
        run=_run_soil,
        examples=["soil 4x2m 15cm", "soil 12x6ft 6in"]))
    registry.register(Skill(
        name="seed", description="Grass seed for an area at 35 g/m² (7 lb per 1,000 sq ft).",
        usage="seed <area>sqm [rate-g/m2] | seed <area>sqft [rate-lb-per-1000sqft]",
        triggers=["seed", "grass"],
        run=_run_seed,
        examples=["seed 100sqm", "seed 5000sqft"]))
    registry.register(Skill(
        name="planter", description="Soil volume for a rectangular or round planter, in litres or gallons.",
        usage="planter <l>x<w>x<h>cm | planter <l>x<w>x<h>in | planter round <diameter>cm <depth>cm | planter round <diameter>in <depth>in",
        triggers=["planter", "pot"],
        run=_run_planter,
        examples=["planter 60x30x30cm", "planter round 30cm 25cm"]))
    registry.register(Skill(
        name="spacing", description="Plants in a bed on a grid at a given spacing.",
        usage="spacing <l>x<w>m <spacing>cm | spacing <l>x<w>ft <spacing>in",
        triggers=["spacing", "plants"],
        run=_run_spacing,
        examples=["spacing 4x2m 30cm", "spacing 12x6ft 12in"]))
