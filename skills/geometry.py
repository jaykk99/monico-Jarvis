"""Geometry helpers: circles, triangles, trig, coordinate geometry.

All local, keyless, no network — same contract as the rest of skills/.
Plain textbook geometry for everyday questions: the size of a circle
from any one measurement, a triangle's area and missing side, sine and
cosine of an angle, and the distance, midpoint, and slope between two
points.

Rules used:
- Circle: diameter d = 2r, circumference C = 2 pi r, area A = pi r^2.
- Triangle: perimeter is the sum of the sides; area from three sides
  is Heron's formula, A = sqrt(s (s-a) (s-b) (s-c)) with
  s = (a+b+c)/2; two sides are read as the legs of a right triangle,
  hypotenuse c = sqrt(a^2 + b^2), area = a b / 2. A triangle is right
  when the squares of the two shorter sides add to the square of the
  longest (within rounding).
- Trig: angles in degrees. sin, cos, tan take an angle; asin, acos,
  atan take a ratio and return degrees. asin/acos only accept -1 to 1.
- Coordinates: distance d = sqrt((x2-x1)^2 + (y2-y1)^2), midpoint is
  the average of each coordinate, slope m = (y2-y1) / (x2-x1); a
  vertical line has no slope.

Conventions and explicit caveats:
- All lengths are in whatever unit you give — the answer comes back
  in the same unit, squared for area. No unit conversion happens.
- Angles are degrees unless stated; radians are not accepted.
- A two-side triangle is assumed right-angled at the corner between
  the two sides you give — if it isn't, the hypotenuse is wrong.
"""
from __future__ import annotations

import math
import re

from .base import Skill, SkillRegistry


def _fmt(x: float) -> str:
    """Short human number: integers plain, else up to 4 significant digits."""
    if x == int(x) and abs(x) < 1e15:
        return f"{int(x):,}"
    return f"{x:.4g}"


def _num(token: str) -> float | None:
    """Parse a plain number, tolerating thousands commas."""
    try:
        return float(token.strip().replace(",", ""))
    except ValueError:
        return None


# ---------------------------------------------------------------- circle

_CIRCLE_RE = re.compile(r"^([rdca])(\d+(?:\.\d+)?)$", re.IGNORECASE)

_USAGE_CIRCLE = (
    "Usage: `circle r<radius>` / `circle d<diameter>` / "
    "`circle c<circumference>` / `circle a<area>` — e.g. `circle r5`, "
    "`circle d10`, `circle c31.42`, `circle a78.54`. Gives radius, "
    "diameter, circumference, and area."
)


def _run_circle(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 1:
        return _USAGE_CIRCLE
    m = _CIRCLE_RE.match(parts[0])
    if not m:
        return _USAGE_CIRCLE
    kind, value = m.group(1).lower(), float(m.group(2))
    if value <= 0:
        return "A circle measurement must be above 0."
    if kind == "r":
        radius = value
    elif kind == "d":
        radius = value / 2
    elif kind == "c":
        radius = value / (2 * math.pi)
    else:  # "a"
        radius = math.sqrt(value / math.pi)
    diameter = 2 * radius
    circumference = 2 * math.pi * radius
    area = math.pi * radius * radius
    return (f"Circle with radius {_fmt(radius)}: diameter {_fmt(diameter)}, "
            f"circumference {_fmt(circumference)}, area {_fmt(area)}.")


# ---------------------------------------------------------------- triangle

_USAGE_TRIANGLE = (
    "Usage: `triangle <leg> <leg>` for a right triangle — e.g. "
    "`triangle 3 4` — or `triangle <side> <side> <side>` — e.g. "
    "`triangle 3 4 5`. Gives the missing side, perimeter, area, and "
    "whether it is right-angled."
)


def _run_triangle(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) not in (2, 3):
        return _USAGE_TRIANGLE
    sides = [_num(p) for p in parts]
    if any(s is None for s in sides):
        return _USAGE_TRIANGLE
    if any(s <= 0 for s in sides):
        return "Triangle sides must be above 0."
    if len(sides) == 2:
        a, b = sides
        hyp = math.hypot(a, b)
        area = a * b / 2
        perimeter = a + b + hyp
        return (f"Right triangle with legs {_fmt(a)} and {_fmt(b)}: "
                f"hypotenuse {_fmt(hyp)}, area {_fmt(area)}, "
                f"perimeter {_fmt(perimeter)}.")
    a, b, c = sorted(sides)
    if a + b <= c:
        return (f"Those sides can't make a triangle: "
                f"{_fmt(a)} + {_fmt(b)} is not more than {_fmt(c)}.")
    perimeter = a + b + c
    s = perimeter / 2
    area = math.sqrt(s * (s - a) * (s - b) * (s - c))
    if a == b == c:
        kind = "equilateral"
    elif a == b or b == c:
        kind = "isosceles"
    else:
        kind = "scalene"
    if abs(a * a + b * b - c * c) < 1e-9 * c * c:
        right = (f"right triangle "
                 f"({_fmt(a)}^2 + {_fmt(b)}^2 = {_fmt(c)}^2)")
    else:
        right = "not right-angled"
    return (f"Triangle with sides {_fmt(a)}, {_fmt(b)}, {_fmt(c)}: "
            f"perimeter {_fmt(perimeter)}, area {_fmt(area)}, {right}, "
            f"{kind}.")


# ---------------------------------------------------------------- trig

_TRIG_FUNCS = ("sin", "cos", "tan", "asin", "acos", "atan")

_USAGE_TRIG = (
    "Usage: `trig <sin|cos|tan> <degrees>` or "
    "`trig <asin|acos|atan> <ratio>` — e.g. `trig sin 30`, "
    "`trig tan 45`, `trig asin 0.5`. Angles in degrees."
)


def _run_trig(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 2:
        return _USAGE_TRIG
    func, value = parts[0].lower(), _num(parts[1])
    if func not in _TRIG_FUNCS or value is None:
        return _USAGE_TRIG
    if func in ("sin", "cos", "tan"):
        radians = math.radians(value)
        if func == "sin":
            result = math.sin(radians)
        elif func == "cos":
            result = math.cos(radians)
        else:
            if abs(math.cos(radians)) < 1e-12:
                return (f"tan({_fmt(value)}°) is undefined — the angle "
                        f"points straight up, so cosine is zero.")
            result = math.tan(radians)
        if abs(result) < 1e-12:
            result = 0.0
        return f"{func}({_fmt(value)}°) = {_fmt(result)}."
    if not -1 <= value <= 1:
        return f"{func} only takes -1 to 1, got `{parts[1]}`."
    if func == "asin":
        result = math.degrees(math.asin(value))
    elif func == "acos":
        result = math.degrees(math.acos(value))
    else:
        result = math.degrees(math.atan(value))
    return f"{func}({_fmt(value)}) = {_fmt(result)}°."


# ---------------------------------------------------------------- coord

_USAGE_COORD = (
    "Usage: `coord <x1> <y1> <x2> <y2>` — e.g. `coord 0 0 3 4`. "
    "Gives the distance, midpoint, and slope between the two points."
)


def _run_coord(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 4:
        return _USAGE_COORD
    values = [_num(p) for p in parts]
    if any(v is None for v in values):
        return _USAGE_COORD
    x1, y1, x2, y2 = values
    dx, dy = x2 - x1, y2 - y1
    distance = math.hypot(dx, dy)
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    if dx == 0:
        slope = "undefined (vertical line)"
    else:
        slope = _fmt(dy / dx)
    return (f"From ({_fmt(x1)}, {_fmt(y1)}) to ({_fmt(x2)}, {_fmt(y2)}): "
            f"distance {_fmt(distance)}, midpoint "
            f"({_fmt(mid_x)}, {_fmt(mid_y)}), slope {slope}.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="circle", description="Circle radius, diameter, circumference, and area from any one of them.",
        usage="circle r<radius> | d<diameter> | c<circumference> | a<area>",
        triggers=["circle"],
        run=_run_circle,
        examples=["circle r5", "circle d10", "circle c31.42", "circle a78.54"]))
    registry.register(Skill(
        name="triangle", description="Right-triangle hypotenuse or a triangle's area, perimeter, and type from its sides.",
        usage="triangle <leg> <leg> | triangle <side> <side> <side>",
        triggers=["triangle", "tri"],
        run=_run_triangle,
        examples=["triangle 3 4", "triangle 3 4 5", "triangle 5 5 6"]))
    registry.register(Skill(
        name="trig", description="Sine, cosine, tangent of an angle in degrees, or the inverse trig of a ratio.",
        usage="trig <sin|cos|tan> <degrees> | trig <asin|acos|atan> <ratio>",
        triggers=["trig", "trigonometry"],
        run=_run_trig,
        examples=["trig sin 30", "trig tan 45", "trig asin 0.5"]))
    registry.register(Skill(
        name="coord", description="Distance, midpoint, and slope between two points.",
        usage="coord <x1> <y1> <x2> <y2>",
        triggers=["coord", "midpoint"],
        run=_run_coord,
        examples=["coord 0 0 3 4", "coord 1 2 1 5"]))
