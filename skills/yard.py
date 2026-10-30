"""Yard and outdoor estimators: fence, gravel, firewood, and deck boards.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only, following the paint/tiles/diy pattern: counts are
rounded up to whole buyable units, a waste allowance covers cuts and
breakage, and every figure is an estimate — confirm product sizes
against what you actually buy, since brands and lumber yards differ.

Conventions:
- Fence: vertical picket boards cover the run; posts sit one spacing
  apart plus one end post; two horizontal rails per span between posts.
  Defaults: 15 cm (6 in) boards, 2.4 m (8 ft) post spacing, 10% waste.
- Gravel: compacted density about 1.5 tonnes/m³ (≈ 1.4 short tons per
  cubic yard); waste defaults to 5% for spreading and settling.
- Firewood: a full cord is 128 cu ft (4 × 4 × 8 ft) ≈ 3.62 m³; a face
  cord is one 4 ft × 8 ft row at the log length, so it is a fraction
  of a full cord, not a cord on its own.
- Deck: boards run along the deck length; the count covers the deck
  width, board edge to board edge; waste defaults to 10% for cuts.
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


_LENGTH_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)m$")
_LENGTH_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)ft$")
_RUN_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)m$")
_RUN_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)ft$")
_AREA_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqm$")
_AREA_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqft$")
_DEPTH_CM_RE = re.compile(r"^([0-9]*\.?[0-9]+)cm$")
_DEPTH_IN_RE = re.compile(r"^([0-9]*\.?[0-9]+)in$")
_BOARD_CM_RE = re.compile(r"^([0-9]*\.?[0-9]+)cm$")
_BOARD_IN_RE = re.compile(r"^([0-9]*\.?[0-9]+)in$")
_SPACING_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)m$")
_SPACING_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)ft$")


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
    """Shared area+depth parser for gravel (same shape as diy.py).

    Returns (area, metric, depth, rest) where area is in m² (metric)
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


# ---------------------------------------------------------------- fence

_USAGE_FENCE = (
    "Usage: `fence <length>m [board-cm] [spacing-m] [waste%]` | "
    "`fence <length>ft [board-in] [spacing-ft] [waste%]` — e.g. "
    "`fence 30m`, `fence 100ft 6in 8ft`."
)

# Default picket width and post spacing, metric then imperial.
# Board defaults are in the input units: cm for metric, in for imperial.
_FENCE_BOARD_M = 15.0
_FENCE_SPACING_M = 2.4
_FENCE_BOARD_IN = 6.0
_FENCE_SPACING_FT = 8.0


def _run_fence(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens:
        return _USAGE_FENCE
    m = _LENGTH_M_RE.match(tokens[0])
    metric = True
    if m:
        length = float(m.group(1))
    else:
        m = _LENGTH_FT_RE.match(tokens[0])
        if not m:
            return _USAGE_FENCE
        metric = False
        length = float(m.group(1))
    rest = tokens[1:]
    board = _FENCE_BOARD_M if metric else _FENCE_BOARD_IN
    spacing = _FENCE_SPACING_M if metric else _FENCE_SPACING_FT
    # Optional board width, then optional post spacing, then waste.
    if rest:
        bm = (_BOARD_CM_RE if metric else _BOARD_IN_RE).match(rest[0])
        if bm:
            board = float(bm.group(1))
            rest = rest[1:]
    if rest:
        sm = (_SPACING_M_RE if metric else _SPACING_FT_RE).match(rest[0])
        if sm:
            spacing = float(sm.group(1))
            rest = rest[1:]
    # A leftover token that is not a number (e.g. a wrong-unit board
    # like `15in` on a metric run) is a usage error, not a waste value.
    if rest and _num(rest[0].rstrip("%")) is None:
        return _USAGE_FENCE
    waste = _parse_waste(rest, 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if length <= 0:
        return "Length must be greater than 0."
    if board <= 0:
        return "Board width must be greater than 0."
    if spacing <= 0:
        return "Post spacing must be greater than 0."
    if metric:
        run_m = length
        board_m = board / 100
        # Round before ceil: float noise (e.g. 200 x 1.1 -> 220.000...03)
        # must not push an exact count one board over.
        boards = math.ceil(round(run_m / board_m * (1 + waste / 100), 9))
        posts = math.floor(run_m / spacing) + 1
        unit = "m"
    else:
        run_in = length * 12
        boards = math.ceil(round(run_in / board * (1 + waste / 100), 9))
        posts = math.floor(length / spacing) + 1
        unit = "ft"
    rails = 2 * (posts - 1)
    return (f"{_fmt_num(length)} {unit} fence, plus {_fmt_num(waste)}% waste — "
            f"buy {boards} picket boards, {posts} posts, and {rails} rails "
            f"(2 per span).")


# ---------------------------------------------------------------- gravel

_USAGE_GRAVEL = (
    "Usage: `gravel <l>x<w>m <depth>cm [waste%]` | "
    "`gravel <l>x<w>ft <depth>in [waste%]` — e.g. `gravel 10sqm 10cm`, "
    "`gravel 10x20ft 4in`."
)

_TONNES_PER_M3 = 1.5
_TONS_PER_CUYD = 1.4
_CUFT_PER_CUYD = 27


def _run_gravel(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    parsed = _parse_area_and_depth(tokens)
    if parsed is None:
        return _USAGE_GRAVEL
    area, metric, depth, rest = parsed
    waste = _parse_waste(rest, 5.0)
    if waste is None:
        return "Waste must be 0% or more."
    if area <= 0:
        return "Area must be greater than 0."
    if depth <= 0:
        return "Depth must be greater than 0."
    if metric:
        volume = area * depth / 100
        volume_waste = volume * (1 + waste / 100)
        tonnes = volume_waste * _TONNES_PER_M3
        return (f"{_fmt_num(area)} m² at {_fmt_num(depth)} cm deep = "
                f"{_fmt_num(volume)} m³, plus {_fmt_num(waste)}% waste = "
                f"{_fmt_num(volume_waste)} m³ — about {_fmt_num(tonnes)} tonnes.")
    volume_ft = area * depth / 12
    volume_yd = volume_ft / _CUFT_PER_CUYD
    volume_yd_waste = volume_yd * (1 + waste / 100)
    tons = volume_yd_waste * _TONS_PER_CUYD
    return (f"{_fmt_num(area)} sq ft at {_fmt_num(depth)} in deep = "
            f"{_fmt_num(volume_ft)} cu ft ({_fmt_num(volume_yd)} cu yd), "
            f"plus {_fmt_num(waste)}% waste = {_fmt_num(volume_yd_waste)} cu yd "
            f"— about {_fmt_num(tons)} short tons.")


# ---------------------------------------------------------------- firewood

_USAGE_FIREWOOD = (
    "Usage: `firewood <l>x<h>ft <log-length>in` | "
    "`firewood <l>x<h>m <log-length>cm` — e.g. `firewood 4x8ft 16in`, "
    "`firewood 2.4x1.2m 40cm`."
)

_CUFT_PER_CORD = 128
_M3_PER_CORD = 3.6246


def _run_firewood(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) != 2:
        return _USAGE_FIREWOOD
    m = _RUN_FT_RE.match(tokens[0])
    metric = False
    if m:
        length, height = float(m.group(1)), float(m.group(2))
        lm = _DEPTH_IN_RE.match(tokens[1])
        if not lm:
            return _USAGE_FIREWOOD
        log_ft = float(lm.group(1)) / 12
    else:
        m = _RUN_M_RE.match(tokens[0])
        if not m:
            return _USAGE_FIREWOOD
        metric = True
        length, height = float(m.group(1)), float(m.group(2))
        lm = _DEPTH_CM_RE.match(tokens[1])
        if not lm:
            return _USAGE_FIREWOOD
        log_m = float(lm.group(1)) / 100
    if length <= 0 or height <= 0:
        return "Stack size must be greater than 0."
    if metric:
        if log_m <= 0:
            return "Log length must be greater than 0."
        volume = length * height * log_m
        cords = volume / _M3_PER_CORD
        return (f"{_fmt_num(length)} × {_fmt_num(height)} m stack, "
                f"{_fmt_num(log_m * 100)} cm logs = {_fmt_num(volume)} m³ — "
                f"about {_fmt_num(cords)} full cords (128 cu ft each).")
    if log_ft <= 0:
        return "Log length must be greater than 0."
    volume = length * height * log_ft
    cords = volume / _CUFT_PER_CORD
    face = volume / (32 * log_ft)
    return (f"{_fmt_num(length)} × {_fmt_num(height)} ft stack, "
            f"{_fmt_num(log_ft * 12)} in logs = {_fmt_num(volume)} cu ft — "
            f"about {_fmt_num(cords)} full cords, or {_fmt_num(face)} face "
            f"cord{'s' if face != 1 else ''}.")


# ---------------------------------------------------------------- deck

_USAGE_DECK = (
    "Usage: `deck <l>x<w>m <board>cm [waste%]` | "
    "`deck <l>x<w>ft <board>in [waste%]` — e.g. `deck 4x5m 14cm`, "
    "`deck 12x16ft 5.5in`."
)


def _run_deck(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) < 2:
        return _USAGE_DECK
    m = _RUN_M_RE.match(tokens[0])
    metric = True
    if m:
        deck_len, deck_w = float(m.group(1)), float(m.group(2))
        bm = _BOARD_CM_RE.match(tokens[1])
        if not bm:
            return _USAGE_DECK
        board = float(bm.group(1))
    else:
        m = _RUN_FT_RE.match(tokens[0])
        if not m:
            return _USAGE_DECK
        metric = False
        deck_len, deck_w = float(m.group(1)), float(m.group(2))
        bm = _BOARD_IN_RE.match(tokens[1])
        if not bm:
            return _USAGE_DECK
        board = float(bm.group(1))
    waste = _parse_waste(tokens[2:], 10.0)
    if waste is None:
        return "Waste must be 0% or more."
    if deck_len <= 0 or deck_w <= 0:
        return "Deck size must be greater than 0."
    if board <= 0:
        return "Board width must be greater than 0."
    if metric:
        boards = math.ceil(round(deck_w / (board / 100) * (1 + waste / 100), 9))
        total = boards * deck_len
        return (f"{_fmt_num(deck_len)} × {_fmt_num(deck_w)} m deck, "
                f"{_fmt_num(board)} cm boards, plus {_fmt_num(waste)}% waste — "
                f"buy {boards} boards ({_fmt_num(deck_len)} m each, "
                f"{_fmt_num(total)} m total).")
    boards = math.ceil(round(deck_w * 12 / board * (1 + waste / 100), 9))
    total = boards * deck_len
    return (f"{_fmt_num(deck_len)} × {_fmt_num(deck_w)} ft deck, "
            f"{_fmt_num(board)} in boards, plus {_fmt_num(waste)}% waste — "
            f"buy {boards} boards ({_fmt_num(deck_len)} ft each, "
            f"{_fmt_num(total)} ft total).")


# ---------------------------------------------------------------- registration

def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="fence", description="Fence picket boards, posts, and rails for a run.",
        usage="fence <length>m [board-cm] [spacing-m] [waste%] | fence <length>ft [board-in] [spacing-ft] [waste%]",
        triggers=["fence"],
        run=_run_fence,
        examples=["fence 30m", "fence 100ft 6in 8ft"]))
    registry.register(Skill(
        name="gravel", description="Gravel volume in m³/cu yd and weight for a bed or drive.",
        usage="gravel <l>x<w>m <depth>cm [waste%] | gravel <l>x<w>ft <depth>in [waste%]",
        triggers=["gravel"],
        run=_run_gravel,
        examples=["gravel 10sqm 10cm", "gravel 10x20ft 4in"]))
    registry.register(Skill(
        name="firewood", description="Firewood cords and face cords for a stack.",
        usage="firewood <l>x<h>ft <log>in | firewood <l>x<h>m <log>cm",
        triggers=["firewood", "wood"],
        run=_run_firewood,
        examples=["firewood 4x8ft 16in", "firewood 2.4x1.2m 40cm"]))
    registry.register(Skill(
        name="deck", description="Deck boards for a deck area, with a waste allowance.",
        usage="deck <l>x<w>m <board>cm [waste%] | deck <l>x<w>ft <board>in [waste%]",
        triggers=["deck"],
        run=_run_deck,
        examples=["deck 4x5m 14cm", "deck 12x16ft 5.5in"]))
