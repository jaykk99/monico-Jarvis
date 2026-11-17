"""Probability and inference helpers: percentiles, binomial probability,
odds conversion, and linear regression.

All local, keyless, no network — same contract as the rest of skills/.
Plain textbook statistics for everyday questions: where a value sits in
a list of numbers, the chance of k successes in n independent tries,
what betting odds mean as a probability, and the straight line that
best fits a set of points.

Rules used:
- Percentile (value mode): linear interpolation on the sorted list —
  the standard "linear" method. Rank r = p / 100 x (n - 1); the value
  is interpolated between the two surrounding sorted values. p = 0
  gives the minimum, p = 100 the maximum. Rank mode counts how many
  values are at or below the one you give.
- Binomial probability: P(exactly k in n tries) = C(n, k) p^k (1-p)^(n-k);
  "at least" and "at most" add up the exact chances from k to n, or
  from 0 to k. Tries are independent and p is the same every try.
- Odds: decimal odds d mean a $1 stake returns $d (profit d - 1).
  Implied probability = 1 / d. Fractional odds are (d - 1) as a
  fraction; American odds are +100 x (d - 1) when d >= 2 and
  -100 / (d - 1) when d < 2. American +150 means a $100 stake wins
  $150; American -200 means you stake $200 to win $100.
- Linear regression: least-squares line y = a + b x, with b =
  sum((x - mean x)(y - mean y)) / sum((x - mean x)^2), a = mean y -
  b x mean x, and r the Pearson correlation; r^2 is the share of the
  variation in y the line explains.

Conventions and explicit caveats:
- A percentile is a property of the list you give, not of the wider
  population — a small list gives a noisy percentile.
- Binomial answers assume every try is independent with the same
  chance of success; a loaded coin or a streak breaks that.
- Odds conversion is pure arithmetic on the odds you give — it says
  nothing about whether a bet is good value, and the implied
  probability is not a prediction. No real money is involved.
- Regression shows association, not cause: a high r^2 does not mean
  x causes y, and predicting far outside the x range you give is a
  guess, not a measurement.
"""
from __future__ import annotations

import math
import re
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


def _nums(text: str) -> list[float]:
    """All plain numbers found in text, in order."""
    out = []
    for token in re.findall(r"[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?", text or ""):
        value = _num(token)
        if value is not None:
            out.append(value)
    return out


# ---------------------------------------------------------------- percentile

_USAGE_PERCENTILE = (
    "Usage: `percentile <p> <numbers...>` — the value at the pth percentile, "
    "e.g. `percentile 90 10 20 30 40 50`; or `percentile rank <value> in "
    "<numbers...>` — e.g. `percentile rank 30 in 10 20 30 40 50`. "
    "p must be 0–100 and you need at least 2 numbers."
)


def _run_percentile(trigger: str, args: str) -> str:
    text = (args or "").strip()
    if not text:
        return _USAGE_PERCENTILE
    if text.lower().startswith("rank"):
        rest = text[4:].strip()
        if " in " in rest.lower():
            value_text, list_text = re.split(r"\s+in\s+", rest, flags=re.IGNORECASE, maxsplit=1)
        else:
            parts = rest.split()
            value_text, list_text = (parts[0], " ".join(parts[1:])) if parts else ("", "")
        value = _num(value_text)
        data = _nums(list_text)
        if value is None or len(data) < 2:
            return _USAGE_PERCENTILE
        below = sum(1 for v in data if v <= value)
        rank = 100.0 * below / len(data)
        return (f"{_fmt(value)} is at the {_fmt(rank)}th percentile of "
                f"{len(data)} values ({below} of {len(data)} at or below it).")
    tokens = text.split()
    p = _num(tokens[0])
    data = _nums(" ".join(tokens[1:]))
    if p is None or p < 0 or p > 100 or len(data) < 2:
        return _USAGE_PERCENTILE
    ordered = sorted(data)
    n = len(ordered)
    rank = p / 100.0 * (n - 1)
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        result = ordered[int(rank)]
    else:
        result = ordered[lo] + (rank - lo) * (ordered[hi] - ordered[lo])
    return (f"The {_fmt(p)}th percentile of {n} values is {_fmt(result)} "
            f"(min {_fmt(ordered[0])}, max {_fmt(ordered[-1])}).")


# ---------------------------------------------------------------- prob

_USAGE_PROB = (
    "Usage: `prob <trials> <successes> <p>` — exact chance, e.g. "
    "`prob 10 3 0.5`; `prob atleast <trials> <successes> <p>` or "
    "`prob atmost <trials> <successes> <p>`. p is 0–1, successes "
    "can't be more than trials."
)


def _binom_pmf(n: int, k: int, p: float) -> float:
    return math.comb(n, k) * p ** k * (1.0 - p) ** (n - k)


def _run_prob(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens:
        return _USAGE_PROB
    mode = "exact"
    if tokens[0] in ("atleast", "at-least", "atmost", "at-most"):
        mode = "atleast" if tokens[0].startswith("atleast") or tokens[0] == "at-least" else "atmost"
        tokens = tokens[1:]
    if len(tokens) != 3:
        return _USAGE_PROB
    n_val, k_val, p = _num(tokens[0]), _num(tokens[1]), _num(tokens[2])
    if n_val is None or k_val is None or p is None:
        return _USAGE_PROB
    if n_val != int(n_val) or k_val != int(k_val):
        return "Trials and successes must be whole numbers."
    n, k = int(n_val), int(k_val)
    if n < 1 or n > 1000:
        return "Trials must be 1–1000."
    if k < 0 or k > n:
        return f"Successes must be 0–{n}, got {k}."
    if p < 0 or p > 1:
        return "p must be 0–1."
    noun = "success" if k == 1 else "successes"
    if mode == "exact":
        chance = _binom_pmf(n, k, p)
        wording = f"exactly {k} {noun} in {n} tries"
    elif mode == "atleast":
        chance = sum(_binom_pmf(n, j, p) for j in range(k, n + 1))
        wording = f"at least {k} {noun} in {n} tries"
    else:
        chance = sum(_binom_pmf(n, j, p) for j in range(0, k + 1))
        wording = f"at most {k} {noun} in {n} tries"
    return (f"With p = {_fmt(p)}, the chance of {wording} is {_fmt(chance)} "
            f"({_fmt(chance * 100)}%, about 1 in {_fmt(1 / chance) if chance > 0 else 'inf'}).")


# ---------------------------------------------------------------- odds

_USAGE_ODDS = (
    "Usage: `odds <decimal>` (e.g. `odds 2.5`), `odds <american>` "
    "(e.g. `odds +150`, `odds -200`), or `odds <fraction>` (e.g. "
    "`odds 3/2`). Shows decimal, fractional, and American odds plus "
    "the implied probability."
)


def _show_odds(decimal: float) -> str:
    frac = Fraction(decimal - 1).limit_denominator(1000)
    if decimal >= 2:
        american = f"+{int(round(100 * (decimal - 1)))}"
    else:
        american = f"-{int(round(100 / (decimal - 1)))}"
    implied = 1.0 / decimal
    frac_text = f"{frac.numerator}/{frac.denominator}" if frac.denominator != 1 else f"{frac.numerator}/1"
    return (f"Decimal {decimal:g} = fractional {frac_text} = American {american} "
            f"— implied probability {_fmt(implied * 100)}%.")


def _run_odds(trigger: str, args: str) -> str:
    text = (args or "").strip()
    if not text:
        return _USAGE_ODDS
    tokens = text.split()
    if len(tokens) != 1:
        return _USAGE_ODDS
    token = tokens[0]
    frac_match = re.fullmatch(r"(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)", token)
    if frac_match:
        num, den = float(frac_match.group(1)), float(frac_match.group(2))
        if den == 0 or num < 0:
            return "Fractional odds need a positive numerator and a non-zero denominator."
        return _show_odds(1.0 + num / den)
    value = _num(token)
    if value is None:
        return _USAGE_ODDS
    if token.startswith(("+", "-")):
        if value == 0:
            return "American odds can't be 0."
        if value > 0:
            return _show_odds(1.0 + value / 100.0)
        return _show_odds(1.0 + 100.0 / abs(value))
    if value <= 1:
        return "Decimal odds must be above 1."
    if value > 10001:
        return "Decimal odds above 10001 look like a typo — check the number."
    return _show_odds(value)


# ---------------------------------------------------------------- regress

_USAGE_REGRESS = (
    "Usage: `regress <x1,y1> <x2,y2> ...` — e.g. `regress 1,2 2,4 3,5 4,4 5,5`; "
    "add `predict <x>` to predict y at that x. Needs at least 3 points, "
    "and the x values can't all be the same."
)

_PAIR_RE = re.compile(
    r"^\s*([-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?)\s*,\s*"
    r"([-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?)\s*$"
)


def _run_regress(trigger: str, args: str) -> str:
    text = (args or "").strip()
    if not text:
        return _USAGE_REGRESS
    predict: float | None = None
    predict_match = re.search(r"\bpredict\s+([-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?)\s*$", text, re.IGNORECASE)
    if predict_match:
        predict = _num(predict_match.group(1))
        text = text[:predict_match.start()].strip()
    points: list[tuple[float, float]] = []
    for token in text.split():
        m = _PAIR_RE.match(token)
        if not m:
            return _USAGE_REGRESS
        points.append((float(m.group(1)), float(m.group(2))))
    if len(points) < 3:
        return _USAGE_REGRESS
    n = len(points)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return "All the x values are the same, so no line fits — vary x."
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in points)
    slope = sxy / sxx
    intercept = my - slope * mx
    if syy == 0:
        r = 0.0
    else:
        r = sxy / math.sqrt(sxx * syy)
    sign = "+" if intercept >= 0 else "-"
    out = (f"Best-fit line from {n} points: y = {_fmt(slope)}x {sign} {_fmt(abs(intercept))}, "
           f"r = {_fmt(r)}, r^2 = {_fmt(r * r)} "
           f"({_fmt(r * r * 100)}% of the variation in y explained).")
    if predict is not None:
        out += f" At x = {_fmt(predict)}, predicted y = {_fmt(intercept + slope * predict)}."
    return out


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="percentile", description="Value at a percentile of a list, or the percentile rank of a value in it.",
        usage="percentile <p> <numbers...> | percentile rank <value> in <numbers...>",
        triggers=["percentile"],
        run=_run_percentile,
        examples=["percentile 90 10 20 30 40 50", "percentile rank 30 in 10 20 30 40 50"]))
    registry.register(Skill(
        name="prob", description="Binomial chance of exactly, at least, or at most k successes in n tries.",
        usage="prob <trials> <successes> <p> | prob atleast|atmost <trials> <successes> <p>",
        triggers=["prob", "probability", "binomial"],
        run=_run_prob,
        examples=["prob 10 3 0.5", "prob atleast 10 9 0.5", "prob atmost 10 1 0.5"]))
    registry.register(Skill(
        name="odds", description="Convert between decimal, fractional, and American odds, with implied probability.",
        usage="odds <decimal> | odds <american> | odds <fraction>",
        triggers=["odds"],
        run=_run_odds,
        examples=["odds 2.5", "odds +150", "odds -200", "odds 3/2"]))
    registry.register(Skill(
        name="regress", description="Least-squares line, correlation, and prediction for x,y points.",
        usage="regress <x1,y1> <x2,y2> ... [predict <x>]",
        triggers=["regress", "regression", "linreg"],
        run=_run_regress,
        examples=["regress 1,2 2,4 3,5 4,4 5,5", "regress 1,2 2,4 3,5 4,4 5,5 predict 6"]))
