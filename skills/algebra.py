"""Algebra helpers: linear equations, quadratics, two-equation systems,
and the line through two points.

All local, keyless, no network — same contract as the rest of skills/.
Plain textbook algebra for everyday questions: the x that makes a
straight-line equation true, the roots and vertex of a parabola, where
two straight lines cross, and the slope-intercept equation of the line
through two points.

Rules used:
- Linear: a x + b = c has the single solution x = (c - b) / a when
  a is not 0. When a is 0, either every x works (b = c) or none does
  (b != c). An equation written as `2x+3=7` is read the same way.
- Quadratic: a x^2 + b x + c = 0 with a != 0. Discriminant
  D = b^2 - 4 a c. D > 0 gives two real roots
  (-b +- sqrt(D)) / (2a); D = 0 gives one repeated root -b / (2a);
  D < 0 gives no real roots, only the complex pair
  -b / (2a) +- sqrt(-D) / (2a) i. The vertex sits at
  x = -b / (2a), y = c - b^2 / (4a).
- Two equations: a1 x + b1 y = c1 and a2 x + b2 y = c2. With
  determinant det = a1 b2 - a2 b1 not 0, Cramer's rule gives
  x = (c1 b2 - c2 b1) / det and y = (a1 c2 - a2 c1) / det.
  With det = 0 the lines are parallel: either the same line (every
  point on it works) or two distinct parallel lines (no solution).
- Line through two points: slope m = (y2 - y1) / (x2 - x1),
  y-intercept b = y1 - m x1, equation y = m x + b, x-intercept
  -b / m when m is not 0. A vertical line (x1 = x2) has no slope
  and the equation x = x1; a horizontal line has slope 0.

Conventions and explicit caveats:
- A linear or quadratic equation is solved exactly as written —
  check the numbers you typed if the answer looks wrong.
- Complex roots are reported as a + bi pairs, not as real numbers;
  a parabola with D < 0 never touches the x-axis.
- Two equations with det = 0 have either infinitely many solutions
  or none — there is no single crossing point to report.
- `line` gives the equation of the line; `coord` already gives the
  distance, midpoint, and slope between the same two points.
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


def _signed_terms(terms: list[tuple[float, str]]) -> str:
    """Join (coefficient, variable) pairs into a polynomial left side.

    A coefficient of 1 prints as the bare variable, -1 as a minus
    sign; zero terms are dropped. E.g. [(1, 'x^2'), (-3, 'x'), (2, '')]
    gives "x^2 - 3x + 2".
    """
    parts: list[str] = []
    for coeff, var in terms:
        if coeff == 0:
            continue
        mag = abs(coeff)
        if var:
            body = var if mag == 1 else f"{_fmt(mag)}{var}"
        else:
            body = _fmt(mag)
        if not parts:
            parts.append(f"-{body}" if coeff < 0 else body)
        else:
            parts.append(f" - {body}" if coeff < 0 else f" + {body}")
    return "".join(parts) or "0"


def _signed_line(slope: float, intercept: float) -> str:
    """Slope-intercept form, e.g. 'y = 2x + 1' or 'y = 0.5x - 0.5'."""
    if slope == 0:
        return f"y = {_fmt(intercept)}"
    left = "x" if slope == 1 else "-x" if slope == -1 else f"{_fmt(slope)}x"
    if intercept == 0:
        return f"y = {left}"
    sign = "+" if intercept > 0 else "-"
    return f"y = {left} {sign} {_fmt(abs(intercept))}"


# ---------------------------------------------------------------- linear

_USAGE_LINEAR = (
    "Usage: `linear <a> <b>` solves a x + b = 0 — e.g. `linear 2 3` — "
    "or `linear <equation>` — e.g. `linear 2x+3=7`. a is the x "
    "coefficient, b and the right side are plain numbers."
)

_LINEAR_EQ_RE = re.compile(
    r"^([+-]?(?:\d+(?:\.\d+)?|\.\d+)?)x"
    r"([+-](?:\d+(?:\.\d+)?|\.\d+))?"
    r"=([+-]?(?:\d+(?:\.\d+)?|\.\d+))$"
)


def _parse_coeff(text: str) -> float | None:
    """Coefficient in front of x: '' means 1, '+' means 1, '-' means -1."""
    if text in ("", "+"):
        return 1.0
    if text == "-":
        return -1.0
    return _num(text)


def _run_linear(trigger: str, args: str) -> str:
    text = (args or "").strip()
    if not text:
        return _USAGE_LINEAR
    compact = re.sub(r"\s+", "", text)
    m = _LINEAR_EQ_RE.match(compact)
    if m:
        a = _parse_coeff(m.group(1))
        b = _num(m.group(2)) if m.group(2) is not None else 0.0
        c = _num(m.group(3))
        if a is None or b is None or c is None:
            return _USAGE_LINEAR
    else:
        parts = text.split()
        if len(parts) != 2:
            return _USAGE_LINEAR
        a, b = _num(parts[0]), _num(parts[1])
        c = 0.0
        if a is None or b is None:
            return _USAGE_LINEAR
    lhs = _signed_terms([(a, "x"), (b, "")])
    if a == 0:
        if b == c:
            return (f"{lhs} = {_fmt(c)} is true for every x — "
                    f"any number works.")
        return (f"{lhs} = {_fmt(c)} has no solution — "
                f"{_fmt(b)} is never {_fmt(c)}.")
    x = (c - b) / a
    return f"{lhs} = {_fmt(c)} has x = {_fmt(x)}."


# ---------------------------------------------------------------- quadratic

_USAGE_QUADRATIC = (
    "Usage: `quadratic <a> <b> <c>` solves a x^2 + b x + c = 0 — "
    "e.g. `quadratic 1 -3 2`. a can't be 0 (that is a linear "
    "equation, not a quadratic)."
)


def _run_quadratic(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 3:
        return _USAGE_QUADRATIC
    values = [_num(p) for p in parts]
    if any(v is None for v in values):
        return _USAGE_QUADRATIC
    a, b, c = values
    if a == 0:
        return ("a is 0, so this is not a quadratic — "
                "use `linear <b> <c>` instead.")
    equation = _signed_terms([(a, "x^2"), (b, "x"), (c, "")])
    disc = b * b - 4 * a * c
    vx = -b / (2 * a)
    vy = a * vx * vx + b * vx + c
    vertex = f"vertex ({_fmt(vx)}, {_fmt(vy)})"
    if disc > 0:
        root = math.sqrt(disc)
        r1 = (-b + root) / (2 * a)
        r2 = (-b - root) / (2 * a)
        return (f"{equation} = 0 has two roots, x = {_fmt(r1)} and "
                f"x = {_fmt(r2)} (discriminant {_fmt(disc)}); {vertex}.")
    if disc == 0:
        root = -b / (2 * a)
        return (f"{equation} = 0 has one repeated root, "
                f"x = {_fmt(root)} (discriminant 0); {vertex}.")
    real = -b / (2 * a)
    imag = math.sqrt(-disc) / (2 * a)
    return (f"{equation} = 0 has no real roots (discriminant "
            f"{_fmt(disc)}); complex roots x = {_fmt(real)} + {_fmt(imag)}i "
            f"and x = {_fmt(real)} - {_fmt(imag)}i; {vertex}.")


# ---------------------------------------------------------------- simul

_USAGE_SIMUL = (
    "Usage: `simul <a1> <b1> <c1> <a2> <b2> <c2>` solves "
    "a1 x + b1 y = c1 and a2 x + b2 y = c2 — e.g. "
    "`simul 1 1 5 1 -1 1`. Six plain numbers."
)


def _run_simul(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 6:
        return _USAGE_SIMUL
    values = [_num(p) for p in parts]
    if any(v is None for v in values):
        return _USAGE_SIMUL
    a1, b1, c1, a2, b2, c2 = values
    eq1 = f"{_signed_terms([(a1, 'x'), (b1, 'y')])} = {_fmt(c1)}"
    eq2 = f"{_signed_terms([(a2, 'x'), (b2, 'y')])} = {_fmt(c2)}"
    det = a1 * b2 - a2 * b1
    if det != 0:
        x = (c1 * b2 - c2 * b1) / det
        y = (a1 * c2 - a2 * c1) / det
        return (f"{eq1} and {eq2} meet at x = {_fmt(x)}, "
                f"y = {_fmt(y)}.")
    if a1 * c2 - a2 * c1 == 0 and b1 * c2 - b2 * c1 == 0:
        return (f"{eq1} and {eq2} are the same line — every point on "
                f"it is a solution.")
    return (f"{eq1} and {eq2} are parallel lines that never meet — "
            f"no solution.")


# ---------------------------------------------------------------- line

_USAGE_LINE = (
    "Usage: `line <x1> <y1> <x2> <y2>` — e.g. `line 0 0 2 4`. "
    "Gives the slope-intercept equation of the line through the two "
    "points, plus its intercepts."
)


def _run_line(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 4:
        return _USAGE_LINE
    values = [_num(p) for p in parts]
    if any(v is None for v in values):
        return _USAGE_LINE
    x1, y1, x2, y2 = values
    if x1 == x2 and y1 == y2:
        return "Those are the same point — no single line through it."
    if x1 == x2:
        return (f"Line through ({_fmt(x1)}, {_fmt(y1)}) and "
                f"({_fmt(x2)}, {_fmt(y2)}): x = {_fmt(x1)} (vertical "
                f"line), slope undefined, no y-intercept.")
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1
    equation = _signed_line(slope, intercept)
    if slope == 0:
        xint = "no x-intercept (it never crosses the x-axis)"
    else:
        xint = f"x-intercept {_fmt(-intercept / slope)}"
    return (f"Line through ({_fmt(x1)}, {_fmt(y1)}) and "
            f"({_fmt(x2)}, {_fmt(y2)}): {equation}, slope {_fmt(slope)}, "
            f"y-intercept {_fmt(intercept)}, {xint}.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="linear", description="Solve a linear equation a x + b = c for x.",
        usage="linear <a> <b> | linear <equation>",
        triggers=["linear", "solve"],
        run=_run_linear,
        examples=["linear 2 3", "linear 2x+3=7", "linear -4 8"]))
    registry.register(Skill(
        name="quadratic", description="Roots, discriminant, and vertex of a x^2 + b x + c = 0.",
        usage="quadratic <a> <b> <c>",
        triggers=["quadratic", "quad"],
        run=_run_quadratic,
        examples=["quadratic 1 -3 2", "quadratic 1 2 1", "quadratic 1 0 1"]))
    registry.register(Skill(
        name="simul", description="Solve two linear equations in x and y (Cramer's rule).",
        usage="simul <a1> <b1> <c1> <a2> <b2> <c2>",
        triggers=["simul", "simultaneous"],
        run=_run_simul,
        examples=["simul 1 1 5 1 -1 1", "simul 2 3 8 1 -1 -1"]))
    registry.register(Skill(
        name="line", description="Slope-intercept equation of the line through two points.",
        usage="line <x1> <y1> <x2> <y2>",
        triggers=["line"],
        run=_run_line,
        examples=["line 0 0 2 4", "line 0 1 2 5", "line 1 2 1 5"]))
