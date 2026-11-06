"""Cooking estimators: recipe scaling, oven temperatures, roast times,
per-person serving amounts.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only, following the garden/diy pattern: amounts scale
by a simple ratio, times come from standard per-weight rates, and
every figure is an estimate — check the recipe, the packet, and a
thermometer, since ovens, joints, and appetites all vary.

Conventions and explicit caveats:
- Recipe: scaling changes amounts, not bake time or oven temperature.
  Leavening, yeast, and seasoning do not scale perfectly — taste and
  check, especially when doubling or tripling.
- Bake: gas marks are approximate; the table values are the standard
  chart figures. Ovens run hot or cold, so an oven thermometer beats
  the dial.
- Roast: times are per 500 g at the stated oven temperature, plus the
  extra minutes for poultry. Always confirm with a meat thermometer
  (beef 63 C medium-rare, pork 71 C, poultry 74 C) and rest the meat
  before carving — a thick joint or a cold oven changes the time.
- Serving: main-course amounts per person. Scale down for a side
  dish, up for big appetites; children eat less than adults.
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


_AMOUNT_RE = re.compile(
    r"^([0-9]*\.?[0-9]+)(g|kg|ml|l|oz|lb|cups?|tbsp|tsp)$")
_WEIGHT_RE = re.compile(r"^([0-9]*\.?[0-9]+)(kg|lb)$")
_TEMP_C_RE = re.compile(r"^([0-9]*\.?[0-9]+)c$")
_TEMP_F_RE = re.compile(r"^([0-9]*\.?[0-9]+)f$")
_GAS_RE = re.compile(r"^gas([1-9])$")


def _fmt_minutes(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} min"
    hours, rest = divmod(minutes, 60)
    if rest == 0:
        return f"{hours} h"
    return f"{hours} h {rest} min"


# ---------------------------------------------------------------- recipe

_USAGE_RECIPE = (
    "Usage: `recipe <from-servings> <to-servings> <amount><unit> [ingredient]` — "
    "e.g. `recipe 4 8 200g flour`, `recipe 4 6 1.5cups rice`."
)

_RECIPE_UNITS = ("g", "kg", "ml", "l", "oz", "lb", "cup", "cups",
                 "tbsp", "tsp")


def _run_recipe(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) < 3:
        return _USAGE_RECIPE
    from_servings = _num(tokens[0])
    to_servings = _num(tokens[1])
    if from_servings is None or to_servings is None:
        return _USAGE_RECIPE
    m = _AMOUNT_RE.match(tokens[2])
    if not m:
        return _USAGE_RECIPE
    amount = float(m.group(1))
    unit = m.group(2)
    if unit not in _RECIPE_UNITS:
        return _USAGE_RECIPE
    if from_servings <= 0 or to_servings <= 0:
        return "Servings must be greater than 0."
    if amount <= 0:
        return "Amount must be greater than 0."
    ingredient = " ".join(tokens[3:])
    factor = to_servings / from_servings
    scaled = amount * factor
    what = f"{_fmt_num(amount)} {unit}"
    if ingredient:
        what += f" {ingredient}"
    scaled_what = f"{_fmt_num(scaled)} {unit}"
    if ingredient:
        scaled_what += f" {ingredient}"
    return (f"{_fmt_num(from_servings)} servings → {_fmt_num(to_servings)} "
            f"servings (×{_fmt_num(factor)}): {what} becomes {scaled_what}. "
            f"Scaling changes amounts, not bake time or oven temperature — "
            f"seasoning and leavening do not scale perfectly, so taste and check.")


# ---------------------------------------------------------------- bake

_USAGE_BAKE = (
    "Usage: `bake <temp>C` | `bake <temp>F` | `bake gas <1-9>` — "
    "e.g. `bake 180C`, `bake 350F`, `bake gas 4`."
)

# Standard gas-mark chart: (mark, celsius, fahrenheit).
_GAS_MARKS = (
    (1, 140, 275),
    (2, 150, 300),
    (3, 160, 325),
    (4, 180, 350),
    (5, 190, 375),
    (6, 200, 400),
    (7, 220, 425),
    (8, 230, 450),
    (9, 240, 475),
)


def _nearest_gas_mark(celsius: float, fahrenheit: float):
    return min(_GAS_MARKS, key=lambda row: abs(row[1] - celsius))


def _run_bake(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens or len(tokens) > 2:
        return _USAGE_BAKE
    mark = None
    if tokens[0] == "gas":
        if len(tokens) != 2:
            return _USAGE_BAKE
        try:
            mark = int(tokens[1])
        except ValueError:
            return _USAGE_BAKE
        row = next((r for r in _GAS_MARKS if r[0] == mark), None)
        if row is None:
            return "Gas mark must be 1 to 9."
        return (f"Gas mark {row[0]} = {row[1]}°C / {row[2]}°F. "
                f"Gas marks are approximate and ovens run hot or cold — "
                f"an oven thermometer beats the dial.")
    if len(tokens) != 1:
        return _USAGE_BAKE
    gm = _GAS_RE.match(tokens[0])
    if gm:
        mark = int(gm.group(1))
        row = next((r for r in _GAS_MARKS if r[0] == mark), None)
        return (f"Gas mark {row[0]} = {row[1]}°C / {row[2]}°F. "
                f"Gas marks are approximate and ovens run hot or cold — "
                f"an oven thermometer beats the dial.")
    mc = _TEMP_C_RE.match(tokens[0])
    mf = _TEMP_F_RE.match(tokens[0])
    if mc:
        celsius = float(mc.group(1))
        if celsius <= 0:
            return "Temperature must be greater than 0."
        fahrenheit = celsius * 9 / 5 + 32
        row = _nearest_gas_mark(celsius, fahrenheit)
        return (f"{_fmt_num(celsius)}°C = {_fmt_num(round(fahrenheit))}°F — "
                f"nearest gas mark {row[0]} ({row[1]}°C / {row[2]}°F). "
                f"Ovens run hot or cold — an oven thermometer beats the dial.")
    if mf:
        fahrenheit = float(mf.group(1))
        if fahrenheit <= 0:
            return "Temperature must be greater than 0."
        celsius = (fahrenheit - 32) * 5 / 9
        row = _nearest_gas_mark(celsius, fahrenheit)
        return (f"{_fmt_num(fahrenheit)}°F = {_fmt_num(round(celsius))}°C — "
                f"nearest gas mark {row[0]} ({row[1]}°C / {row[2]}°F). "
                f"Ovens run hot or cold — an oven thermometer beats the dial.")
    return _USAGE_BAKE


# ---------------------------------------------------------------- roast

_USAGE_ROAST = (
    "Usage: `roast <meat> <weight>kg|lb [doneness]` — "
    "e.g. `roast beef 1.5kg`, `roast chicken 4lb`, "
    "`roast lamb 2kg medium`."
)

# Per 500 g, in minutes, at the stated oven temperature.
# Poultry gets extra minutes on top; beef/lamb take a doneness.
_ROAST_MEATS = {
    "beef": {"oven_c": 200, "oven_f": 400, "rest_min": 15,
             "rates": {"rare": 15, "medium-rare": 20, "medium": 25,
                       "well": 30},
             "default": "medium-rare",
             "centre": "63°C centre for medium-rare"},
    "lamb": {"oven_c": 200, "oven_f": 400, "rest_min": 15,
             "rates": {"rare": 15, "medium-rare": 20, "medium": 25,
                       "well": 30},
             "default": "medium-rare",
             "centre": "63°C centre for medium-rare"},
    "pork": {"oven_c": 200, "oven_f": 400, "rest_min": 15,
             "rates": {"well": 25}, "default": "well",
             "centre": "71°C centre"},
    "chicken": {"oven_c": 190, "oven_f": 375, "rest_min": 20,
                "rates": {"well": 20}, "default": "well", "extra_min": 20,
                "centre": "74°C in the thickest part"},
    "turkey": {"oven_c": 190, "oven_f": 375, "rest_min": 20,
               "rates": {"well": 20}, "default": "well", "extra_min": 20,
               "centre": "74°C in the thickest part"},
}

_DONENESS_ALIASES = {
    "rare": "rare",
    "med-rare": "medium-rare",
    "medium-rare": "medium-rare",
    "medium": "medium",
    "med": "medium",
    "well": "well",
    "well-done": "well",
    "welldone": "well",
}

_KG_PER_LB = 0.45359237


def _run_roast(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) < 2 or len(tokens) > 3:
        return _USAGE_ROAST
    meat = tokens[0]
    spec = _ROAST_MEATS.get(meat)
    if spec is None:
        return (_USAGE_ROAST + " Meats: "
                + ", ".join(sorted(_ROAST_MEATS)) + ".")
    m = _WEIGHT_RE.match(tokens[1])
    if not m:
        return _USAGE_ROAST
    weight = float(m.group(1))
    metric = m.group(2) == "kg"
    if weight <= 0:
        return "Weight must be greater than 0."
    doneness = spec["default"]
    if len(tokens) == 3:
        if meat not in ("beef", "lamb"):
            return "Doneness only applies to beef and lamb."
        doneness = _DONENESS_ALIASES.get(tokens[2])
        if doneness is None:
            return (_USAGE_ROAST + " Doneness: rare, medium-rare, "
                    "medium, well.")
    rate = spec["rates"][doneness]
    weight_kg = weight if metric else weight * _KG_PER_LB
    minutes = math.ceil(round(weight_kg * 1000 / 500 * rate, 9))
    minutes += spec.get("extra_min", 0)
    weight_text = (f"{_fmt_num(weight)} kg" if metric
                   else f"{_fmt_num(weight)} lb ({_fmt_num(weight_kg)} kg)")
    return (f"{weight_text} {meat}, {doneness}: about "
            f"{_fmt_minutes(minutes)} roasting at {spec['oven_c']}°C "
            f"({spec['oven_f']}°F), plus {_fmt_minutes(spec['rest_min'])} "
            f"rest — check {spec['centre']} with a meat thermometer. "
            f"Times are estimates; ovens and joint shape vary.")


# ---------------------------------------------------------------- serving

_USAGE_SERVING = (
    "Usage: `serving <people> <dish>` — e.g. `serving 6 pasta`, "
    "`serving 4 rice`."
)

# Per person, main course: (amount, unit, label).
_SERVING_TABLE = {
    "pasta": (100, "g", "dry pasta"),
    "noodles": (100, "g", "dry noodles"),
    "rice": (75, "g", "dry rice"),
    "couscous": (75, "g", "dry couscous"),
    "potatoes": (200, "g", "potatoes"),
    "potato": (200, "g", "potatoes"),
    "meat": (175, "g", "meat"),
    "chicken": (175, "g", "chicken"),
    "fish": (150, "g", "fish"),
    "vegetables": (150, "g", "vegetables"),
    "veg": (150, "g", "vegetables"),
    "salad": (100, "g", "salad"),
    "bread": (50, "g", "bread"),
    "soup": (300, "ml", "soup"),
}

_G_PER_OZ = 28.3495
_ML_PER_CUP = 236.588


def _run_serving(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) != 2:
        return _USAGE_SERVING
    people = _num(tokens[0])
    if people is None or people != int(people):
        return _USAGE_SERVING
    people = int(people)
    dish = _SERVING_TABLE.get(tokens[1])
    if dish is None:
        return (_USAGE_SERVING + " Dishes: "
                + ", ".join(sorted(_SERVING_TABLE)) + ".")
    if people <= 0:
        return "People must be greater than 0."
    per_person, unit, label = dish
    total = per_person * people
    if unit == "g":
        oz = total / _G_PER_OZ
        amount = f"{_fmt_num(total)} g ({_fmt_num(round(oz, 1))} oz)"
    else:
        cups = total / _ML_PER_CUP
        amount = f"{_fmt_num(total)} ml ({_fmt_num(round(cups, 2))} cups)"
    return (f"{people} people, {label} (main course): {amount}. "
            f"Main-course amounts; appetites vary — scale down for a "
            f"side dish.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="recipe", description="Scale a recipe amount between serving counts.",
        usage="recipe <from-servings> <to-servings> <amount><unit> [ingredient]",
        triggers=["recipe", "scale"],
        run=_run_recipe,
        examples=["recipe 4 8 200g flour", "recipe 4 6 1.5cups rice"]))
    registry.register(Skill(
        name="bake", description="Oven temperature between Celsius, Fahrenheit, and gas mark.",
        usage="bake <temp>C | bake <temp>F | bake gas <1-9>",
        triggers=["bake", "oven"],
        run=_run_bake,
        examples=["bake 180C", "bake 350F", "bake gas 4"]))
    registry.register(Skill(
        name="roast", description="Roast time by meat and weight, with rest and thermometer target.",
        usage="roast <meat> <weight>kg|lb [doneness]",
        triggers=["roast", "roasting"],
        run=_run_roast,
        examples=["roast beef 1.5kg", "roast chicken 4lb", "roast lamb 2kg medium"]))
    registry.register(Skill(
        name="serving", description="Food amounts per person for a main-course dish.",
        usage="serving <people> <dish>",
        triggers=["serving", "servings", "portions"],
        run=_run_serving,
        examples=["serving 6 pasta", "serving 4 rice"]))
