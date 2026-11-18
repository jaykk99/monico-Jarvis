"""Statistics II helpers: z-scores, weighted averages, moving averages,
and quartiles (five-number summary + IQR fences).

All local, keyless, no network — same contract as the rest of skills/.
Plain textbook statistics that build on the existing `stats` skill
(mean/median/std dev) and the `percentile` skill (linear interpolation):
where one value sits relative to a list, how to average values that
don't count equally, how to smooth a series, and how spread out the
middle half of a list is.

Rules used:
- Z-score: z = (x - mean) / sd, with the sample standard deviation
  (n - 1 in the denominator — the same sd `stats` reports). A z of
  +1.5 means the value sits 1.5 standard deviations above the mean.
  Given a mean and sd directly, the same formula applies.
- Weighted average: sum(value x weight) / sum(weight). Weights must
  be positive; a weight of 0 would say the value doesn't count at all,
  so it is rejected rather than silently ignored.
- Moving average: for window w, each output is the mean of w
  consecutive values, sliding one step at a time. The first window
  starts at the first value, so a list of n values gives n - w + 1
  averages.
- Quartiles: Q1, median, Q3 by the same linear-interpolation method
  as `percentile` — rank r = p / 100 x (n - 1) on the sorted list.
  IQR = Q3 - Q1. Outlier fences are Q1 - 1.5 x IQR and
  Q3 + 1.5 x IQR (Tukey); values outside the fences are listed as
  outliers.

Conventions and explicit caveats:
- A z-score describes the list you give, not the wider population —
  a small list gives a noisy mean and sd, and a z-score says nothing
  about whether the value is "good" or "bad".
- A weighted average is only as honest as the weights: weights that
  favour one value will pull the answer toward it.
- A moving average smooths a series but lags it: the average for a
  window only reflects values up to its end, and the first w - 1
  values have no average of their own.
- Quartile fences flag values worth a second look; an outlier is not
  automatically a mistake, and with a small list the fences move a
  lot if one value changes.
"""
from __future__ import annotations

import math
import re
import statistics

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


def _percentile_value(p: float, ordered: list[float]) -> float:
    """Linear-interpolation percentile, same method as skills/probability."""
    n = len(ordered)
    rank = p / 100.0 * (n - 1)
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return ordered[int(rank)]
    return ordered[lo] + (rank - lo) * (ordered[hi] - ordered[lo])


# ---------------------------------------------------------------- zscore

_USAGE_ZSCORE = (
    "Usage: `zscore <value> in <numbers...>` — e.g. `zscore 50 in "
    "10 20 30 40 50`; or `zscore <value> <mean> <sd>` — e.g. "
    "`zscore 50 30 15.81`. Needs at least 2 numbers in the list, and "
    "the standard deviation can't be 0."
)


def _run_zscore(trigger: str, args: str) -> str:
    text = (args or "").strip()
    if not text:
        return _USAGE_ZSCORE
    if re.search(r"\s+in\s+", text, flags=re.IGNORECASE):
        value_text, list_text = re.split(r"\s+in\s+", text, flags=re.IGNORECASE, maxsplit=1)
        value = _num(value_text.strip())
        data = _nums(list_text)
        if value is None or len(data) < 2:
            return _USAGE_ZSCORE
        mean = statistics.fmean(data)
        sd = statistics.stdev(data)
        if sd == 0:
            return "All the numbers are the same, so there's no spread to measure against."
        z = (value - mean) / sd
        direction = "above" if z > 0 else "below" if z < 0 else "at"
        return (f"{_fmt(value)} has a z-score of {_fmt(z)} against {len(data)} values "
                f"(mean {_fmt(mean)}, sd {_fmt(sd)}) — "
                f"{_fmt(abs(z))} standard deviations {direction} the mean.")
    tokens = text.split()
    if len(tokens) != 3:
        return _USAGE_ZSCORE
    value, mean, sd = _num(tokens[0]), _num(tokens[1]), _num(tokens[2])
    if value is None or mean is None or sd is None:
        return _USAGE_ZSCORE
    if sd == 0:
        return "The standard deviation can't be 0."
    if sd < 0:
        return "The standard deviation can't be negative."
    z = (value - mean) / sd
    direction = "above" if z > 0 else "below" if z < 0 else "at"
    return (f"{_fmt(value)} has a z-score of {_fmt(z)} (mean {_fmt(mean)}, "
            f"sd {_fmt(sd)}) — {_fmt(abs(z))} standard deviations "
            f"{direction} the mean.")


# ---------------------------------------------------------------- weighted

_USAGE_WEIGHTED = (
    "Usage: `weighted <value>x<weight> ...` — e.g. "
    "`weighted 90x3 80x2 70x1`. Weights must be positive, and you "
    "need at least 2 value-weight pairs."
)

_PAIR_RE = re.compile(
    r"^\s*([-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?)\s*[xX]\s*"
    r"([-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?)\s*$"
)


def _run_weighted(trigger: str, args: str) -> str:
    tokens = (args or "").strip().split()
    if len(tokens) < 2:
        return _USAGE_WEIGHTED
    pairs: list[tuple[float, float]] = []
    for token in tokens:
        m = _PAIR_RE.match(token)
        if not m:
            return _USAGE_WEIGHTED
        pairs.append((float(m.group(1)), float(m.group(2))))
    if any(w <= 0 for _, w in pairs):
        return "Weights must be positive — a weight of 0 or less doesn't count."
    total_weight = sum(w for _, w in pairs)
    result = sum(v * w for v, w in pairs) / total_weight
    plain_mean = statistics.fmean([v for v, _ in pairs])
    return (f"Weighted average of {len(pairs)} values: {_fmt(result)} "
            f"(total weight {_fmt(total_weight)}; plain mean would be "
            f"{_fmt(plain_mean)}).")


# ---------------------------------------------------------------- movavg

_USAGE_MOVAVG = (
    "Usage: `movavg <window> <numbers...>` — e.g. `movavg 3 1 2 3 4 5`. "
    "The window must be at least 2 and no bigger than the list."
)


def _run_movavg(trigger: str, args: str) -> str:
    tokens = (args or "").strip().split()
    if len(tokens) < 3:
        return _USAGE_MOVAVG
    window_val = _num(tokens[0])
    data = _nums(" ".join(tokens[1:]))
    if window_val is None or window_val != int(window_val):
        return "The window must be a whole number."
    window = int(window_val)
    if window < 2 or window > len(data):
        return _USAGE_MOVAVG
    averages = [
        statistics.fmean(data[i:i + window])
        for i in range(len(data) - window + 1)
    ]
    shown = ", ".join(_fmt(v) for v in averages)
    return (f"Moving average (window {window}) of {len(data)} values: {shown}.")


# ---------------------------------------------------------------- quartile

_USAGE_QUARTILE = (
    "Usage: `quartile <numbers...>` — e.g. `quartile 1 2 3 4 5 6 7 8 9 10`. "
    "Needs at least 4 numbers."
)


def _run_quartile(trigger: str, args: str) -> str:
    data = _nums(args or "")
    if len(data) < 4:
        return _USAGE_QUARTILE
    ordered = sorted(data)
    q1 = _percentile_value(25, ordered)
    median = _percentile_value(50, ordered)
    q3 = _percentile_value(75, ordered)
    iqr = q3 - q1
    low_fence = q1 - 1.5 * iqr
    high_fence = q3 + 1.5 * iqr
    outliers = [v for v in ordered if v < low_fence or v > high_fence]
    out = (f"Five-number summary of {len(data)} values: min {_fmt(ordered[0])}, "
           f"Q1 {_fmt(q1)}, median {_fmt(median)}, Q3 {_fmt(q3)}, max {_fmt(ordered[-1])}. "
           f"IQR {_fmt(iqr)} (fences {_fmt(low_fence)} to {_fmt(high_fence)}).")
    if outliers:
        out += " Outliers: " + ", ".join(_fmt(v) for v in outliers) + "."
    else:
        out += " No outliers."
    return out


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="zscore", description="How many standard deviations a value sits from a mean — against a list or a given mean and sd.",
        usage="zscore <value> in <numbers...> | zscore <value> <mean> <sd>",
        triggers=["zscore", "z-score"],
        run=_run_zscore,
        examples=["zscore 50 in 10 20 30 40 50", "zscore 50 30 15.81"]))
    registry.register(Skill(
        name="weighted", description="Weighted average of value-weight pairs.",
        usage="weighted <value>x<weight> ...",
        triggers=["weighted", "wavg", "weightedavg", "weighted-average"],
        run=_run_weighted,
        examples=["weighted 90x3 80x2 70x1", "weighted 100x1 50x3"]))
    registry.register(Skill(
        name="movavg", description="Moving average of a list with a sliding window.",
        usage="movavg <window> <numbers...>",
        triggers=["movavg", "moving", "movingavg", "moving-average"],
        run=_run_movavg,
        examples=["movavg 3 1 2 3 4 5", "movavg 2 10 20 30"]))
    registry.register(Skill(
        name="quartile", description="Five-number summary, IQR, and Tukey outlier fences for a list.",
        usage="quartile <numbers...>",
        triggers=["quartile", "quartiles", "iqr", "boxplot"],
        run=_run_quartile,
        examples=["quartile 1 2 3 4 5 6 7 8 9 10", "quartile 2 4 4 4 5 5 7 9"]))
