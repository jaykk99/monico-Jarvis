"""Build-out estimators: insulation, drywall, gutter, and roof bundles.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only, following the diy/yard pattern: counts are
rounded up to whole buyable units, a waste allowance covers cuts and
offcuts, and every figure is an estimate — confirm product sizes
against what you actually buy, since brands and suppliers differ.

Conventions:
- Insulation: rolls cover an area; a default roll covers 10 m²
  (100 sq ft) unless you give its coverage. Waste defaults to 10%.
- Drywall: wall area is the room perimeter times the height, covered
  by standard sheets — 1.2 × 2.4 m (2.88 m²) metric, 4 × 8 ft
  (32 sq ft) imperial. Waste defaults to 10%; ceilings, doors,
  and windows are ignored.
- Gutter: sections come in 3 m (10 ft) lengths; downspouts sit one
  spacing apart (defaults 10 m / 30 ft), hangers every 0.6 m (2 ft),
  plus 2 end caps per run. Section counts are rounded up, which
  already covers cutting, so there is no separate waste allowance.
- Roof: one square is 100 sq ft (9.29 m²) and takes 3 bundles.
  A pitch given as rise/run (e.g. 6/12) multiplies the footprint by
  sqrt(1 + (rise/run)²); no pitch means a flat roof. Waste defaults
  to 10%.
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
_AREA_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqm$")
_AREA_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqft$")
_COVER_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)(?:m2|sqm)$")
_COVER_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqft$")
_LENGTH_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)m$")
_LENGTH_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)ft$")
_SPACING_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)m$")
_SPACING_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)ft$")
_HEIGHT_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)m$")
_HEIGHT_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)ft$")
_PITCH_RE = re.compile(r"^([0-9]*\.?[0-9]+)/([0-9]*\.?[0-9]+)$")


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


# ---------------------------------------------------------------- insulation

_USAGE_INSULATION = (
    "Usage: `insulation <area>sqm [roll-m2] [waste%]` | "
    "`insulation <area>sqft [roll-sqft] [waste%]` — e.g. "
    "`insulation 50sqm`, `insulation 1000sqft 75sqft`."
)

_INSUL_ROLL_M = 10.0
_INSUL_ROLL_FT = 100.0


def _run_insulation(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    parsed = _parse_area(tokens)
    if parsed is None:
        return _USAGE_INSULATION
    area, metric, rest = parsed
    cover = _INSUL_ROLL_M if metric else _INSUL_ROLL_FT
    if rest:
        cm = (_COVER_M_RE if metric else _COVER_FT_RE).match(rest[0])
        if cm:
            cover = float(cm.group(1))
            rest = rest[1:]
    # A leftover token that is not a number (e.g. a wrong-unit
    # coverage like `10cm`) is a usage error, not a waste value.
    if rest and _num(rest[0].rstrip("%")) is None:
        return _USAGE_INSULATION
    waste = _parse_waste(rest, 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if area <= 0:
        return "Area must be greater than 0."
    if cover <= 0:
        return "Roll coverage must be greater than 0."
    need = area * (1 + waste / 100)
    rolls = math.ceil(round(need / cover, 9))
    unit = "m²" if metric else "sq ft"
    return (f"{_fmt_num(area)} {unit} to cover, plus {_fmt_num(waste)}% waste = "
            f"{_fmt_num(need)} {unit} — buy {rolls} rolls "
            f"({_fmt_num(cover)} {unit} each).")


# ---------------------------------------------------------------- drywall

_USAGE_DRYWALL = (
    "Usage: `drywall <l>x<w>m <height>m [waste%]` | "
    "`drywall <l>x<w>ft <height>ft [waste%]` — e.g. `drywall 4x5m 2.4m`, "
    "`drywall 12x16ft 8ft`."
)

_SHEET_M = 2.88
_SHEET_FT = 32.0


def _run_drywall(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) < 2:
        return _USAGE_DRYWALL
    m = _RUN_M_RE.match(tokens[0])
    metric = True
    if m:
        room_l, room_w = float(m.group(1)), float(m.group(2))
        hm = _HEIGHT_M_RE.match(tokens[1])
        if not hm:
            return _USAGE_DRYWALL
        height = float(hm.group(1))
    else:
        m = _RUN_FT_RE.match(tokens[0])
        if not m:
            return _USAGE_DRYWALL
        metric = False
        room_l, room_w = float(m.group(1)), float(m.group(2))
        hm = _HEIGHT_FT_RE.match(tokens[1])
        if not hm:
            return _USAGE_DRYWALL
        height = float(hm.group(1))
    waste = _parse_waste(tokens[2:], 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if room_l <= 0 or room_w <= 0:
        return "Room size must be greater than 0."
    if height <= 0:
        return "Height must be greater than 0."
    area = 2 * (room_l + room_w) * height
    sheet = _SHEET_M if metric else _SHEET_FT
    sheets = math.ceil(round(area / sheet * (1 + waste / 100), 9))
    unit = "m²" if metric else "sq ft"
    return (f"{_fmt_num(area)} {unit} of walls, plus {_fmt_num(waste)}% waste — "
            f"buy {sheets} sheets ({_fmt_num(sheet)} {unit} each, "
            f"standard {'1.2 × 2.4 m' if metric else '4 × 8 ft'}).")


# ---------------------------------------------------------------- gutter

_USAGE_GUTTER = (
    "Usage: `gutter <length>m [downspout-spacing-m]` | "
    "`gutter <length>ft [downspout-spacing-ft]` — e.g. `gutter 30m`, "
    "`gutter 100ft 30ft`."
)

_SECTION_M = 3.0
_SECTION_FT = 10.0
_SPACING_DEFAULT_M = 10.0
_SPACING_DEFAULT_FT = 30.0
_HANGER_M = 0.6
_HANGER_FT = 2.0


def _run_gutter(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens or len(tokens) > 2:
        return _USAGE_GUTTER
    m = _LENGTH_M_RE.match(tokens[0])
    metric = True
    if m:
        length = float(m.group(1))
    else:
        m = _LENGTH_FT_RE.match(tokens[0])
        if not m:
            return _USAGE_GUTTER
        metric = False
        length = float(m.group(1))
    spacing = _SPACING_DEFAULT_M if metric else _SPACING_DEFAULT_FT
    if len(tokens) == 2:
        sm = (_SPACING_M_RE if metric else _SPACING_FT_RE).match(tokens[1])
        if not sm:
            return _USAGE_GUTTER
        spacing = float(sm.group(1))
    if length <= 0:
        return "Length must be greater than 0."
    if spacing <= 0:
        return "Downspout spacing must be greater than 0."
    section = _SECTION_M if metric else _SECTION_FT
    hanger = _HANGER_M if metric else _HANGER_FT
    sections = math.ceil(round(length / section, 9))
    downspouts = math.ceil(round(length / spacing, 9))
    hangers = math.ceil(round(length / hanger, 9))
    unit = "m" if metric else "ft"
    return (f"{_fmt_num(length)} {unit} gutter run — buy {sections} sections "
            f"({_fmt_num(section)} {unit} each), {downspouts} downspouts "
            f"(one every {_fmt_num(spacing)} {unit}), {hangers} hangers "
            f"(every {_fmt_num(hanger)} {unit}), and 2 end caps.")


# ---------------------------------------------------------------- roof

_USAGE_ROOF = (
    "Usage: `roof <l>x<w>m [pitch]` | `roof <l>x<w>ft [pitch]` — e.g. "
    "`roof 10x8m`, `roof 30x40ft 6/12` (pitch is rise/run)."
)

_SQ_M = 9.29
_SQ_FT = 100.0
_BUNDLES_PER_SQUARE = 3


def _run_roof(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens:
        return _USAGE_ROOF
    m = _RUN_M_RE.match(tokens[0])
    metric = True
    if m:
        roof_l, roof_w = float(m.group(1)), float(m.group(2))
    else:
        m = _RUN_FT_RE.match(tokens[0])
        if not m:
            return _USAGE_ROOF
        metric = False
        roof_l, roof_w = float(m.group(1)), float(m.group(2))
    rest = tokens[1:]
    factor = 1.0
    pitch_given = False
    if rest:
        pm = _PITCH_RE.match(rest[0])
        if pm:
            rise, run = float(pm.group(1)), float(pm.group(2))
            if run <= 0:
                return _USAGE_ROOF
            factor = math.sqrt(1 + (rise / run) ** 2)
            pitch_given = True
            rest = rest[1:]
    # A leftover token that is not a number (e.g. `6` instead of
    # `6/12`) is a usage error, not a waste value. Before any pitch,
    # a bare number is not a waste value either — waste there must
    # carry its `%` sign, so `roof 10x8m 6` fails as a bad pitch.
    if rest and _num(rest[0].rstrip("%")) is None:
        return _USAGE_ROOF
    if rest and not pitch_given and not rest[0].endswith("%"):
        return _USAGE_ROOF
    waste = _parse_waste(rest, 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if roof_l <= 0 or roof_w <= 0:
        return "Roof size must be greater than 0."
    footprint = roof_l * roof_w
    area = footprint * factor
    square = _SQ_M if metric else _SQ_FT
    squares = area / square
    bundles = math.ceil(round(squares * _BUNDLES_PER_SQUARE * (1 + waste / 100), 9))
    unit = "m²" if metric else "sq ft"
    return (f"{_fmt_num(footprint)} {unit} footprint, pitch factor "
            f"{_fmt_num(factor)} = {_fmt_num(area)} {unit} of roof "
            f"({_fmt_num(squares)} squares), plus {_fmt_num(waste)}% waste — "
            f"buy {bundles} bundles (3 per square).")


# ---------------------------------------------------------------- registration

def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="insulation", description="Insulation rolls for an area, with a waste allowance.",
        usage="insulation <area>sqm [roll-m2] [waste%] | insulation <area>sqft [roll-sqft] [waste%]",
        triggers=["insulation", "insulate"],
        run=_run_insulation,
        examples=["insulation 50sqm", "insulation 1000sqft 75sqft"]))
    registry.register(Skill(
        name="drywall", description="Drywall sheets for a room's walls, with a waste allowance.",
        usage="drywall <l>x<w>m <height>m [waste%] | drywall <l>x<w>ft <height>ft [waste%]",
        triggers=["drywall"],
        run=_run_drywall,
        examples=["drywall 4x5m 2.4m", "drywall 12x16ft 8ft"]))
    registry.register(Skill(
        name="gutter", description="Gutter sections, downspouts, hangers, and end caps for a run.",
        usage="gutter <length>m [downspout-spacing-m] | gutter <length>ft [downspout-spacing-ft]",
        triggers=["gutter", "gutters", "eavestrough"],
        run=_run_gutter,
        examples=["gutter 30m", "gutter 100ft 30ft"]))
    registry.register(Skill(
        name="roof", description="Roofing bundles for a roof area, pitch-adjusted, with waste.",
        usage="roof <l>x<w>m [pitch] | roof <l>x<w>ft [pitch]",
        triggers=["roof", "shingles"],
        run=_run_roof,
        examples=["roof 10x8m", "roof 30x40ft 6/12"]))
