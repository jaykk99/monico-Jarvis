"""Calculus helpers: derivatives, definite integrals, limits, and
tangent lines for polynomials.

All local, keyless, no network — same contract as the rest of skills/.
Plain textbook calculus for everyday questions: how fast a polynomial
is changing at a point, the signed area under it between two bounds,
what a polynomial or a ratio of polynomials approaches at a point,
and the straight line that touches the curve at that point.

Rules used:
- Derivative (power rule): the derivative of a x^n is n a x^(n-1),
  applied term by term. f'(x0) > 0 means the curve is rising at
  x0, f'(x0) < 0 means falling, f'(x0) = 0 means flat there.
- Definite integral (fundamental theorem): the integral of a x^n
  from lo to hi is a (hi^(n+1) - lo^(n+1)) / (n+1), applied term
  by term through the antiderivative F, so the answer is
  F(hi) - F(lo). Bounds that run backwards flip the sign.
- Limit of a polynomial: polynomials are continuous everywhere, so
  the limit at x0 is just the value f(x0). For a ratio of
  polynomials, direct substitution works when the denominator is
  not 0 at x0; when both top and bottom are 0, the shared factor
  (x - x0) is cancelled out (synthetic division) and the limit is
  the value of the simplified function — a hole, not a wall.
- Tangent line (point-slope): at x0 the curve passes through
  (x0, f(x0)) with slope m = f'(x0), so the tangent is
  y = m (x - x0) + f(x0), written in slope-intercept form.

Conventions and explicit caveats:
- Coefficients are always given highest-degree first: `deriv 1 -3 2`
  means f(x) = x^2 - 3x + 2. The point goes after `at`, the bounds
  after `from` and `to`.
- `deriv` and `tangent` work on any degree; a constant has
  derivative 0 everywhere, and a straight line is its own tangent.
- A definite integral is signed area: parts of the curve below the
  x-axis count negative, so a negative answer means the curve sits
  below the axis on balance, not that the area is negative.
- `limit` only cancels whole (x - x0) factors; a ratio that is
  still 0/0 after cancelling, or one whose denominator is 0 while
  the numerator is not, has no finite limit and says so.
- Huge values refuse to print rather than dumping a wall of digits.
"""
from __future__ import annotations

import math
from fractions import Fraction

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


def _is_zero(value: float, scale: float = 1.0) -> bool:
    """Close enough to 0 to treat as 0, relative to the numbers involved."""
    return abs(value) <= 1e-9 * max(1.0, scale)


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


def _var(power: int) -> str:
    if power == 0:
        return ""
    if power == 1:
        return "x"
    return f"x^{power}"


def _poly_str(coeffs: list[float]) -> str:
    """Polynomial in x, coefficients highest-degree first."""
    terms = [
        (c, _var(len(coeffs) - 1 - i)) for i, c in enumerate(coeffs)
    ]
    return _signed_terms(terms)


def _eval(coeffs: list[float], x: float) -> float:
    """Evaluate a polynomial (Horner), coefficients highest-degree first."""
    result = 0.0
    for c in coeffs:
        result = result * x + c
    return result


def _deriv_coeffs(coeffs: list[float]) -> list[float]:
    """Power-rule derivative coefficients, highest-degree first."""
    degree = len(coeffs) - 1
    if degree == 0:
        return [0.0]
    return [c * (degree - i) for i, c in enumerate(coeffs[:-1])]


def _antideriv_str(coeffs: list[float]) -> str:
    """Antiderivative as a polynomial string, exact fractions (x^3/3)."""
    degree = len(coeffs) - 1
    parts: list[str] = []
    for i, c in enumerate(coeffs):
        power = degree - i + 1
        if c == 0:
            continue
        frac = Fraction(c).limit_denominator(10000) / power
        var = _var(power)
        if frac == 1:
            body = var
        elif frac == -1:
            body = var
        else:
            mag = abs(frac)
            if mag.denominator == 1:
                body = f"{mag.numerator}{var}" if var else f"{mag.numerator}"
            elif mag.numerator == 1:
                body = f"{var}/{mag.denominator}"
            else:
                body = f"{mag.numerator}{var}/{mag.denominator}"
        if not parts:
            parts.append(f"-{body}" if frac < 0 else body)
        else:
            parts.append(f" - {body}" if frac < 0 else f" + {body}")
    return "".join(parts) or "0"


def _antideriv_value(coeffs: list[float], x: float) -> float:
    """F(x) for the antiderivative, computed from exact fractions."""
    degree = len(coeffs) - 1
    total = 0.0
    for i, c in enumerate(coeffs):
        power = degree - i + 1
        if c == 0:
            continue
        frac = Fraction(c).limit_denominator(10000) / power
        total += float(frac) * (x ** power)
    return total


def _deflate(coeffs: list[float], x0: float) -> tuple[list[float], float]:
    """Divide a polynomial by (x - x0): (quotient, remainder)."""
    if len(coeffs) == 1:
        return [], coeffs[0]
    quotient: list[float] = [coeffs[0]]
    for c in coeffs[1:]:
        quotient.append(c + x0 * quotient[-1])
    return quotient[:-1], quotient[-1]


def _signed_line(slope: float, intercept: float) -> str:
    """Slope-intercept form, e.g. 'y = 2x + 1' or 'y = 0.5x - 0.5'."""
    if slope == 0:
        return f"y = {_fmt(intercept)}"
    left = "x" if slope == 1 else "-x" if slope == -1 else f"{_fmt(slope)}x"
    if intercept == 0:
        return f"y = {left}"
    sign = "+" if intercept > 0 else "-"
    return f"y = {left} {sign} {_fmt(abs(intercept))}"


def _parse_coeffs(tokens: list[str]) -> list[float] | None:
    """A run of plain numbers, or None when any token is not a number."""
    values = [_num(t) for t in tokens]
    if any(v is None for v in values):
        return None
    return [v for v in values if v is not None]


def _split_keyword(tokens: list[str], keyword: str) -> tuple[list[str], list[str]] | None:
    """Split tokens on a keyword token; None when it is missing or doubled."""
    hits = [i for i, t in enumerate(tokens) if t.lower() == keyword]
    if len(hits) != 1:
        return None
    i = hits[0]
    return tokens[:i], tokens[i + 1:]


# ---------------------------------------------------------------- deriv

_USAGE_DERIV = (
    "Usage: `deriv <coefficients> at <x>` gives the derivative of a "
    "polynomial at a point — e.g. `deriv 1 -3 2 at 4` for "
    "f(x) = x^2 - 3x + 2. Coefficients highest-degree first."
)


def _run_deriv(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    split = _split_keyword(tokens, "at")
    if split is None:
        return _USAGE_DERIV
    coeff_tokens, point_tokens = split
    coeffs = _parse_coeffs(coeff_tokens)
    point = _parse_coeffs(point_tokens)
    if coeffs is None or point is None or len(point) != 1 or not coeffs:
        return _USAGE_DERIV
    x0 = point[0]
    deriv = _deriv_coeffs(coeffs)
    try:
        value = _eval(deriv, x0)
    except OverflowError:
        return "That derivative is too large to print — try smaller numbers."
    if value != value or value in (math.inf, -math.inf):
        return "That derivative is too large to print — try smaller numbers."
    if value > 0:
        direction = "rising"
    elif value < 0:
        direction = "falling"
    else:
        direction = "flat — a possible maximum, minimum, or flat point"
    return (f"f(x) = {_poly_str(coeffs)}, so f'(x) = {_poly_str(deriv)}. "
            f"At x = {_fmt(x0)}, f'({_fmt(x0)}) = {_fmt(value)} — "
            f"the curve is {direction} there.")


# ---------------------------------------------------------------- integral

_USAGE_INTEGRAL = (
    "Usage: `integral <coefficients> from <lo> to <hi>` gives the "
    "definite integral of a polynomial — e.g. `integral 1 0 0 from 0 "
    "to 3` for the area under x^2 from 0 to 3. Coefficients "
    "highest-degree first."
)


def _run_integral(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    split_from = _split_keyword(tokens, "from")
    if split_from is None:
        return _USAGE_INTEGRAL
    coeff_tokens, rest = split_from
    split_to = _split_keyword(rest, "to")
    if split_to is None:
        return _USAGE_INTEGRAL
    lo_tokens, hi_tokens = split_to
    coeffs = _parse_coeffs(coeff_tokens)
    lo = _parse_coeffs(lo_tokens)
    hi = _parse_coeffs(hi_tokens)
    if coeffs is None or lo is None or hi is None:
        return _USAGE_INTEGRAL
    if len(lo) != 1 or len(hi) != 1 or not coeffs:
        return _USAGE_INTEGRAL
    lo_v, hi_v = lo[0], hi[0]
    try:
        value = _antideriv_value(coeffs, hi_v) - _antideriv_value(coeffs, lo_v)
    except OverflowError:
        return "That integral is too large to print — try smaller numbers."
    if value != value or value in (math.inf, -math.inf):
        return "That integral is too large to print — try smaller numbers."
    out = (f"The integral of {_poly_str(coeffs)} from {_fmt(lo_v)} to "
           f"{_fmt(hi_v)} is {_fmt(value)} "
           f"(antiderivative F(x) = {_antideriv_str(coeffs)}).")
    if lo_v > hi_v:
        out += (f" The bounds run backwards, so this is the negative of "
                f"the integral from {_fmt(hi_v)} to {_fmt(lo_v)}.")
    if value < 0:
        out += (" Negative because the curve sits below the x-axis on "
                "balance — this is signed area, not total area.")
    elif value == 0 and lo_v != hi_v:
        out += " The positive and negative parts cancel exactly."
    return out


# ---------------------------------------------------------------- limit

_USAGE_LIMIT = (
    "Usage: `limit <coefficients> at <x>` for a polynomial — e.g. "
    "`limit 1 -3 2 at 4` — or `limit <top> / <bottom> at <x>` for a "
    "ratio of polynomials — e.g. `limit 1 0 -1 / 1 -1 at 1`. "
    "Coefficients highest-degree first."
)


def _run_limit(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    split = _split_keyword(tokens, "at")
    if split is None:
        return _USAGE_LIMIT
    head, point_tokens = split
    point = _parse_coeffs(point_tokens)
    if point is None or len(point) != 1:
        return _USAGE_LIMIT
    x0 = point[0]
    if "/" in head:
        slash = head.index("/")
        num = _parse_coeffs(head[:slash])
        den = _parse_coeffs(head[slash + 1:])
        if num is None or den is None or not num or not den:
            return _USAGE_LIMIT
        return _limit_rational(num, den, x0)
    coeffs = _parse_coeffs(head)
    if coeffs is None or not coeffs:
        return _USAGE_LIMIT
    try:
        value = _eval(coeffs, x0)
    except OverflowError:
        return "That limit is too large to print — try smaller numbers."
    if value != value or value in (math.inf, -math.inf):
        return "That limit is too large to print — try smaller numbers."
    return (f"The limit of {_poly_str(coeffs)} as x approaches "
            f"{_fmt(x0)} is {_fmt(value)} — polynomials are continuous "
            f"everywhere, so the limit is just the value at that point.")


def _limit_rational(num: list[float], den: list[float], x0: float) -> str:
    scale = max([abs(c) for c in num + den] + [1.0])
    try:
        num_v = _eval(num, x0)
        den_v = _eval(den, x0)
    except OverflowError:
        return "That limit is too large to print — try smaller numbers."
    label = (f"The limit of ({_poly_str(num)}) / ({_poly_str(den)}) as x "
             f"approaches {_fmt(x0)}")
    if not _is_zero(den_v, scale):
        value = num_v / den_v
        if value != value or value in (math.inf, -math.inf):
            return "That limit is too large to print — try smaller numbers."
        return (f"{label} is {_fmt(value)} — direct substitution works "
                f"because the denominator is not 0 there.")
    if not _is_zero(num_v, scale):
        return (f"{label} has no finite limit — the numerator is "
                f"{_fmt(num_v)} while the denominator is 0, so the "
                f"function grows without bound near x = {_fmt(x0)}.")
    # Both 0: cancel shared (x - x0) factors, then try again.
    cancelled = 0
    while len(num) > 1 and len(den) > 1:
        num_q, num_r = _deflate(num, x0)
        den_q, den_r = _deflate(den, x0)
        if not _is_zero(num_r, scale) or not _is_zero(den_r, scale):
            break
        num, den = num_q, den_q
        cancelled += 1
    try:
        num_v = _eval(num, x0)
        den_v = _eval(den, x0)
    except OverflowError:
        return "That limit is too large to print — try smaller numbers."
    if not _is_zero(den_v, scale):
        value = num_v / den_v
        if value != value or value in (math.inf, -math.inf):
            return "That limit is too large to print — try smaller numbers."
        times = "once" if cancelled == 1 else f"{cancelled} times"
        return (f"{label} is {_fmt(value)} — both top and bottom are 0 "
                f"at x = {_fmt(x0)}, but (x - {_fmt(x0)}) cancels {times}, "
                f"a hole at x = {_fmt(x0)}, and the limit is the value of "
                f"the simplified function.")
    if _is_zero(num_v, scale):
        return (f"{label} is still 0/0 after cancelling (x - {_fmt(x0)}) "
                f"{cancelled} time(s) — factor it by hand to go further.")
    return (f"{label} has no finite limit — after cancelling, the "
            f"numerator is {_fmt(num_v)} while the denominator is still 0, "
            f"so the function grows without bound near x = {_fmt(x0)}.")


# ---------------------------------------------------------------- tangent

_USAGE_TANGENT = (
    "Usage: `tangent <coefficients> at <x>` gives the tangent line to "
    "a polynomial at a point — e.g. `tangent 1 0 0 at 2` for the "
    "tangent to x^2 at x = 2. Coefficients highest-degree first."
)


def _run_tangent(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    split = _split_keyword(tokens, "at")
    if split is None:
        return _USAGE_TANGENT
    coeff_tokens, point_tokens = split
    coeffs = _parse_coeffs(coeff_tokens)
    point = _parse_coeffs(point_tokens)
    if coeffs is None or point is None or len(point) != 1 or not coeffs:
        return _USAGE_TANGENT
    x0 = point[0]
    deriv = _deriv_coeffs(coeffs)
    try:
        y0 = _eval(coeffs, x0)
        slope = _eval(deriv, x0)
    except OverflowError:
        return "That tangent is too large to print — try smaller numbers."
    if y0 in (math.inf, -math.inf) or slope in (math.inf, -math.inf):
        return "That tangent is too large to print — try smaller numbers."
    intercept = y0 - slope * x0
    out = (f"At x = {_fmt(x0)} the curve f(x) = {_poly_str(coeffs)} "
           f"passes through ({_fmt(x0)}, {_fmt(y0)}) with slope "
           f"{_fmt(slope)}, so the tangent line is "
           f"{_signed_line(slope, intercept)}.")
    if slope == 0:
        out += " The tangent is horizontal there."
    elif len(coeffs) <= 2:
        out += " The tangent is the line itself — a straight line is its own tangent."
    return out


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="deriv", description="Derivative of a polynomial at a point (power rule).",
        usage="deriv <coefficients> at <x>",
        triggers=["deriv", "derivative"],
        run=_run_deriv,
        examples=["deriv 1 -3 2 at 4", "deriv 3 0 -2 5 at 1", "deriv 2 1 at 3"]))
    registry.register(Skill(
        name="integral", description="Definite integral of a polynomial between two bounds.",
        usage="integral <coefficients> from <lo> to <hi>",
        triggers=["integral", "integrate"],
        run=_run_integral,
        examples=["integral 1 0 0 from 0 to 3", "integral 2 0 from 0 to 4", "integral 1 0 from -1 to 1"]))
    registry.register(Skill(
        name="limit", description="Limit of a polynomial, or of a ratio of polynomials, at a point.",
        usage="limit <coefficients> at <x> | limit <top> / <bottom> at <x>",
        triggers=["limit"],
        run=_run_limit,
        examples=["limit 1 -3 2 at 4", "limit 1 0 -1 / 1 -1 at 1", "limit 1 0 -4 / 1 -2 at 2"]))
    registry.register(Skill(
        name="tangent", description="Tangent line to a polynomial at a point.",
        usage="tangent <coefficients> at <x>",
        triggers=["tangent", "tangentline"],
        run=_run_tangent,
        examples=["tangent 1 0 0 at 2", "tangent 1 -3 2 at 1.5", "tangent 2 1 at 3"]))
