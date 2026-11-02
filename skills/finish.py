"""Finishing estimators: trim, caulk, grout, tile adhesive.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only, following the build pattern: counts are rounded
up to whole buyable units, a waste allowance covers cuts and offcuts,
and every figure is an estimate — confirm product sizes against what
you actually buy, since brands and suppliers differ.

Conventions:
- Trim: baseboard/skirting for a room's perimeter — perimeter from
  length x width, pieces 2.4 m (8 ft) long unless you give the piece
  length. Waste defaults to 10%. Openings (doors, archways) are not
  subtracted, so the count runs slightly high.
- Caulk: tubes for a bead run — one tube covers about 9 m (30 ft) of
  bead unless you give its coverage. Waste defaults to 10%; bead size
  changes coverage a lot, so measure against the tube you buy.
- Grout: bags for a tiled area — one bag covers 10 m² (100 sq ft)
  unless you give its coverage. Waste defaults to 10%.
- Adhesive: tile adhesive (thinset) bags for a tiled area — one bag
  covers 5 m² (50 sq ft) unless you give its coverage. Waste defaults
  to 10%. Trowel size changes coverage, so confirm against the bag.
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


_DIMS_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)m$")
_DIMS_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)ft$")
_AREA_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqm$")
_AREA_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqft$")
_LENGTH_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)m$")
_LENGTH_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)ft$")
_COVER_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)(?:m2|sqm)$")
_COVER_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqft$")


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
    m = _DIMS_M_RE.match(first) or _AREA_M_RE.match(first)
    if m:
        area = float(m.group(1)) * float(m.group(2)) if "x" in first else float(m.group(1))
        return area, True, tokens[1:]
    m = _DIMS_FT_RE.match(first) or _AREA_FT_RE.match(first)
    if m:
        area = float(m.group(1)) * float(m.group(2)) if "x" in first else float(m.group(1))
        return area, False, tokens[1:]
    return None


def _parse_area_skill(tokens, usage, cover_m, cover_ft):
    """Shared area + optional coverage + optional waste parse.

    Returns (area, metric, cover, waste, error) — error is a reply
    string when the input is unusable, else None.
    """
    parsed = _parse_area(tokens)
    if parsed is None:
        return None, None, None, None, usage
    area, metric, rest = parsed
    cover = cover_m if metric else cover_ft
    if rest:
        cm = (_COVER_M_RE if metric else _COVER_FT_RE).match(rest[0])
        if cm:
            cover = float(cm.group(1))
            rest = rest[1:]
    # A leftover token that is not a number is a usage error, not waste.
    if rest and _num(rest[0].rstrip("%")) is None:
        return None, None, None, None, usage
    waste = _parse_waste(rest, 10.0)
    if waste is None:
        return None, None, None, None, "Waste must be 0% or more."
    if area <= 0:
        return None, None, None, None, "Area must be greater than 0."
    if cover <= 0:
        return None, None, None, None, "Bag coverage must be greater than 0."
    return area, metric, cover, waste, None


# ---------------------------------------------------------------- trim

_USAGE_TRIM = (
    "Usage: `trim <length>x<width>m [piece-m] [waste%]` | "
    "`trim <length>x<width>ft [piece-ft] [waste%]` — e.g. "
    "`trim 4x5m`, `trim 12x16ft 10ft`."
)

_PIECE_M = 2.4
_PIECE_FT = 8.0


def _run_trim(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens:
        return _USAGE_TRIM
    m = _DIMS_M_RE.match(tokens[0])
    metric = True
    if m:
        length, width = float(m.group(1)), float(m.group(2))
        piece = _PIECE_M
        rest = tokens[1:]
        if rest:
            pm = _LENGTH_M_RE.match(rest[0])
            if pm:
                piece = float(pm.group(1))
                rest = rest[1:]
    else:
        m = _DIMS_FT_RE.match(tokens[0])
        if not m:
            return _USAGE_TRIM
        metric = False
        length, width = float(m.group(1)), float(m.group(2))
        piece = _PIECE_FT
        rest = tokens[1:]
        if rest:
            pm = _LENGTH_FT_RE.match(rest[0])
            if pm:
                piece = float(pm.group(1))
                rest = rest[1:]
    # A leftover token that is not a number is a usage error, not waste.
    if rest and _num(rest[0].rstrip("%")) is None:
        return _USAGE_TRIM
    waste = _parse_waste(rest, 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if length <= 0 or width <= 0:
        return "Room dimensions must be greater than 0."
    if piece <= 0:
        return "Piece length must be greater than 0."
    perimeter = 2 * (length + width)
    need = perimeter * (1 + waste / 100)
    pieces = math.ceil(round(need / piece, 9))
    unit = "m" if metric else "ft"
    return (f"{_fmt_num(length)} x {_fmt_num(width)} {unit} room, "
            f"{_fmt_num(perimeter)} {unit} of trim, plus {_fmt_num(waste)}% waste = "
            f"{_fmt_num(need)} {unit} — buy {pieces} pieces "
            f"({_fmt_num(piece)} {unit} each, openings not subtracted).")


# ---------------------------------------------------------------- caulk

_USAGE_CAULK = (
    "Usage: `caulk <length>m [tube-m] [waste%]` | "
    "`caulk <length>ft [tube-ft] [waste%]` — e.g. "
    "`caulk 30m`, `caulk 100ft 40ft`."
)

_TUBE_M = 9.0
_TUBE_FT = 30.0


def _run_caulk(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens:
        return _USAGE_CAULK
    m = _LENGTH_M_RE.match(tokens[0])
    metric = True
    if m:
        length = float(m.group(1))
        cover = _TUBE_M
        rest = tokens[1:]
        if rest:
            cm = _LENGTH_M_RE.match(rest[0])
            if cm:
                cover = float(cm.group(1))
                rest = rest[1:]
    else:
        m = _LENGTH_FT_RE.match(tokens[0])
        if not m:
            return _USAGE_CAULK
        metric = False
        length = float(m.group(1))
        cover = _TUBE_FT
        rest = tokens[1:]
        if rest:
            cm = _LENGTH_FT_RE.match(rest[0])
            if cm:
                cover = float(cm.group(1))
                rest = rest[1:]
    # A leftover token that is not a number is a usage error, not waste.
    if rest and _num(rest[0].rstrip("%")) is None:
        return _USAGE_CAULK
    waste = _parse_waste(rest, 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if length <= 0:
        return "Bead length must be greater than 0."
    if cover <= 0:
        return "Tube coverage must be greater than 0."
    need = length * (1 + waste / 100)
    tubes = math.ceil(round(need / cover, 9))
    unit = "m" if metric else "ft"
    return (f"{_fmt_num(length)} {unit} of bead, plus {_fmt_num(waste)}% waste = "
            f"{_fmt_num(need)} {unit} — buy {tubes} tubes "
            f"({_fmt_num(cover)} {unit} of bead each).")


# ---------------------------------------------------------------- grout

_USAGE_GROUT = (
    "Usage: `grout <area>sqm [bag-m2] [waste%]` | "
    "`grout <area>sqft [bag-sqft] [waste%]` — e.g. "
    "`grout 20sqm`, `grout 200sqft 50sqft`."
)

_GROUT_M = 10.0
_GROUT_FT = 100.0


def _run_grout(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    area, metric, cover, waste, err = _parse_area_skill(
        tokens, _USAGE_GROUT, _GROUT_M, _GROUT_FT)
    if err is not None:
        return err
    need = area * (1 + waste / 100)
    bags = math.ceil(round(need / cover, 9))
    unit = "m²" if metric else "sq ft"
    return (f"{_fmt_num(area)} {unit} to grout, plus {_fmt_num(waste)}% waste = "
            f"{_fmt_num(need)} {unit} — buy {bags} bags "
            f"({_fmt_num(cover)} {unit} each).")


# ---------------------------------------------------------------- adhesive

_USAGE_ADHESIVE = (
    "Usage: `adhesive <area>sqm [bag-m2] [waste%]` | "
    "`adhesive <area>sqft [bag-sqft] [waste%]` — e.g. "
    "`adhesive 20sqm`, `adhesive 200sqft 25sqft`."
)

_ADHESIVE_M = 5.0
_ADHESIVE_FT = 50.0


def _run_adhesive(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    area, metric, cover, waste, err = _parse_area_skill(
        tokens, _USAGE_ADHESIVE, _ADHESIVE_M, _ADHESIVE_FT)
    if err is not None:
        return err
    need = area * (1 + waste / 100)
    bags = math.ceil(round(need / cover, 9))
    unit = "m²" if metric else "sq ft"
    return (f"{_fmt_num(area)} {unit} to tile, plus {_fmt_num(waste)}% waste = "
            f"{_fmt_num(need)} {unit} — buy {bags} bags of adhesive "
            f"({_fmt_num(cover)} {unit} each).")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="trim", description="Trim/baseboard pieces for a room's perimeter, with a waste allowance.",
        usage="trim <length>x<width>m [piece-m] [waste%] | trim <length>x<width>ft [piece-ft] [waste%]",
        triggers=["trim", "baseboard", "skirting"],
        run=_run_trim,
        examples=["trim 4x5m", "trim 12x16ft 10ft"]))
    registry.register(Skill(
        name="caulk", description="Caulk tubes for a bead run, with a waste allowance.",
        usage="caulk <length>m [tube-m] [waste%] | caulk <length>ft [tube-ft] [waste%]",
        triggers=["caulk", "caulking", "sealant"],
        run=_run_caulk,
        examples=["caulk 30m", "caulk 100ft 40ft"]))
    registry.register(Skill(
        name="grout", description="Grout bags for a tiled area, with a waste allowance.",
        usage="grout <area>sqm [bag-m2] [waste%] | grout <area>sqft [bag-sqft] [waste%]",
        triggers=["grout", "grouting"],
        run=_run_grout,
        examples=["grout 20sqm", "grout 200sqft 50sqft"]))
    registry.register(Skill(
        name="adhesive", description="Tile adhesive bags for a tiled area, with a waste allowance.",
        usage="adhesive <area>sqm [bag-m2] [waste%] | adhesive <area>sqft [bag-sqft] [waste%]",
        triggers=["adhesive", "thinset"],
        run=_run_adhesive,
        examples=["adhesive 20sqm", "adhesive 200sqft 25sqft"]))
