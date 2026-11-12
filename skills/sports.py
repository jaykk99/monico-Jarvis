"""Sports stats helpers: batting average, ERA, NFL passer rating, golf handicap.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic from the standard formulas, for the everyday sports
questions: what a hitter is batting, how good a pitcher's ERA is, what a
quarterback's passer rating works out to, and what a golf handicap index
is from recent rounds.

Formulas and rules used:
- Batting average: hits / at-bats, shown to three decimals the way
  baseball does (.333, not 0.333). An optional target average says how
  many consecutive hits it takes to reach it: x >= (t*ab - h) / (1 - t).
- ERA: 9 x earned runs / innings pitched. Innings use baseball notation,
  where .1 is one out (a third of an inning) and .2 is two outs — so
  6.1 means 6 and 1/3 innings, not 6.1 decimal innings.
- NFL passer rating: a = ((comp/att) - 0.3) x 5, b = ((yds/att) - 3)
  x 0.25, c = (td/att) x 20, d = 2.375 - (int/att) x 25, each clamped
  to 0-2.375, then ((a + b + c + d) / 6) x 100. A perfect game is 158.3.
- Golf handicap: one round's differential is (score - course rating)
  x 113 / slope. A handicap index from 3-20 differentials takes the
  best few per the WHS table (3-4 rounds: best 1, 5-6: best 2, 7-8:
  best 3, 9-10: best 4, 11-12: best 5, 13-14: best 6, 15-16: best 7,
  17-20: best 8), averages them, and multiplies by 0.96.

Conventions and explicit caveats:
- A batting average is a rate, not a prediction — 100 hits in 300
  at-bats is .333, but the next at-bat is still a coin flip weighted
  by the hitter.
- ERA credits the pitcher only with earned runs; errors and passed
  balls don't count, and the number here uses the runs you give it.
- Passer rating is the NFL formula, not ESPN's QBR and not college
  passer efficiency — the three are different numbers for the same game.
- The golf index is the WHS calculation from the differentials you
  supply; an official index comes from your golf association, and
  course rating/slope come from the scorecard, not from this skill.
"""
from __future__ import annotations

from .base import Skill, SkillRegistry


def _num(token: str) -> float | None:
    """Parse a number, tolerating thousands commas and a trailing %."""
    token = token.strip().replace(",", "")
    if token.endswith("%"):
        token = token[:-1]
    try:
        return float(token)
    except ValueError:
        return None


def _fmt_num(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


# ---------------------------------------------------------------- batting

_USAGE_BATTING = (
    "Usage: `batting <hits> <at-bats> [target]` — e.g. `batting 100 300`, "
    "`batting 80 300 .300`. The optional target is the average to chase, "
    "as `.300`, `0.300`, or `300`."
)


def _parse_target(token: str) -> float | None:
    raw = token.strip()
    if raw.startswith("."):
        raw = "0" + raw
    value = _num(raw)
    if value is None:
        return None
    if value > 1:
        # A whole number like 300 reads as .300; a decimal like 1.5 is
        # not a batting average in any form, so reject it.
        if value != int(value):
            return None
        return value / 1000.0
    return value


def _run_batting(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) not in (2, 3):
        return _USAGE_BATTING
    hits = _num(parts[0])
    at_bats = _num(parts[1])
    if hits is None or at_bats is None:
        return _USAGE_BATTING
    if hits != int(hits) or at_bats != int(at_bats):
        return "Hits and at-bats must be whole numbers."
    hits, at_bats = int(hits), int(at_bats)
    if hits < 0 or at_bats < 1:
        return "Hits must be 0 or more and at-bats at least 1."
    if hits > at_bats:
        return f"Hits ({hits}) can't be more than at-bats ({at_bats})."
    avg = hits / at_bats
    avg_text = f".{round(avg * 1000):03d}"
    if avg >= 0.300:
        note = " That's an excellent average — .300 or better is star territory."
    elif avg >= 0.280:
        note = " That's a solid average, comfortably above the middle of the pack."
    elif avg >= 0.250:
        note = " That's around league average."
    elif avg >= 0.200:
        note = " That's below average — the Mendoza line is .200."
    else:
        note = " That's below the Mendoza line (.200) — a rough stretch."
    base = f"Batting {_fmt_num(hits)} for {_fmt_num(at_bats)} is {avg_text}.{note}"
    if len(parts) == 2:
        return base
    target = _parse_target(parts[2])
    if target is None or not 0 < target < 1:
        return f"Target average must be between .001 and .999, got `{parts[2]}`. " + _USAGE_BATTING
    target_text = f".{round(target * 1000):03d}"
    if avg >= target:
        return (base + f" You're already at or above your {target_text} target — "
                f"no hot streak needed.")
    # (h + x) / (ab + x) >= t  ->  x >= (t*ab - h) / (1 - t)
    import math

    needed = math.ceil((target * at_bats - hits) / (1 - target))
    new_avg = (hits + needed) / (at_bats + needed)
    new_text = f".{round(new_avg * 1000):03d}"
    return (base + f" To reach {target_text} you'd need {needed} consecutive "
            f"hit{'s' if needed != 1 else ''} — that would take you to "
            f"{new_text} ({_fmt_num(hits + needed)} for {_fmt_num(at_bats + needed)}).")


# ---------------------------------------------------------------- era

_USAGE_ERA = (
    "Usage: `era <earned-runs> <innings>` — e.g. `era 18 60`, `era 10 6.1`. "
    "Innings use baseball notation: .1 is one out (a third of an inning), "
    ".2 is two outs, so 6.1 means 6 and 1/3 innings."
)


def _parse_innings(token: str) -> float | None:
    """Parse baseball innings: 6, 6.0, 6.1 (= 6 1/3), 6.2 (= 6 2/3)."""
    raw = token.strip()
    if "." not in raw:
        value = _num(raw)
        if value is None or value != int(value):
            return None
        return value
    whole, frac = raw.split(".", 1)
    if frac not in ("0", "1", "2") or not whole.lstrip("-").isdigit():
        return None
    whole_value = _num(whole)
    if whole_value is None or whole_value != int(whole_value):
        return None
    return whole_value + {"0": 0.0, "1": 1 / 3, "2": 2 / 3}[frac]


def _run_era(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 2:
        return _USAGE_ERA
    runs = _num(parts[0])
    innings = _parse_innings(parts[1])
    if runs is None or innings is None:
        return _USAGE_ERA
    if runs != int(runs):
        return "Earned runs must be a whole number."
    if runs < 0:
        return "Earned runs must be 0 or more."
    if innings <= 0:
        return "Innings pitched must be more than 0."
    era = 9 * runs / innings
    if era < 2.00:
        note = " That's elite — under 2.00 over a season is Cy Young territory."
    elif era < 3.00:
        note = " That's excellent, well ahead of the pack."
    elif era < 4.00:
        note = " That's solid, around or a bit better than average."
    elif era < 5.00:
        note = " That's below average — a rough year so far."
    else:
        note = " That's a tough year — 5.00 or above usually costs a rotation spot."
    return (f"ERA: {era:.2f} — {_fmt_num(int(runs))} earned run"
            f"{'s' if runs != 1 else ''} in {parts[1]} innings "
            f"(9 x runs / innings).{note}")


# ---------------------------------------------------------------- qbrating

_USAGE_QBRATING = (
    "Usage: `qbrating <completions> <attempts> <yards> <touchdowns> "
    "<interceptions>` — e.g. `qbrating 20 30 250 2 1`. The NFL passer "
    "rating formula, max 158.3."
)


def _run_qbrating(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 5:
        return _USAGE_QBRATING
    values = [_num(p) for p in parts]
    if any(v is None for v in values):
        return _USAGE_QBRATING
    comp, att, yds, td, inter = (int(v) if v == int(v) else v for v in values)
    if any(v != int(v) for v in values):
        return "All five numbers must be whole numbers."
    comp, att, yds, td, inter = (int(v) for v in values)
    if att < 1:
        return "Attempts must be at least 1."
    if comp < 0 or yds < 0 or td < 0 or inter < 0:
        return "Completions, yards, touchdowns, and interceptions must be 0 or more."
    if comp > att:
        return f"Completions ({comp}) can't be more than attempts ({att})."
    if td > att or inter > att:
        return "Touchdowns and interceptions can't be more than attempts."
    a = _clamp(((comp / att) - 0.3) * 5, 0, 2.375)
    b = _clamp(((yds / att) - 3) * 0.25, 0, 2.375)
    c = _clamp((td / att) * 20, 0, 2.375)
    d = _clamp(2.375 - (inter / att) * 25, 0, 2.375)
    rating = ((a + b + c + d) / 6) * 100
    if rating >= 158.3:
        note = " A perfect 158.3 — the best the formula allows."
    elif rating >= 100:
        note = " That's excellent — 100 or better is a great day at quarterback."
    elif rating >= 90:
        note = " That's a good game, above the usual starter line."
    elif rating >= 80:
        note = " That's around average for a starter."
    elif rating >= 70:
        note = " That's below average — a game to forget."
    else:
        note = " That's a rough outing — under 70 usually means turnovers hurt."
    return (f"Passer rating: {rating:.1f} (max 158.3) — {comp} of {att} for "
            f"{_fmt_num(yds)} yards, {td} touchdown{'s' if td != 1 else ''}, "
            f"{inter} interception{'s' if inter != 1 else ''}.{note}")


# ---------------------------------------------------------------- handicap

# WHS table: rounds in the last 20 -> how many of the lowest differentials count.
_WHS_BEST_OF = {
    3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3, 9: 4, 10: 4,
    11: 5, 12: 5, 13: 6, 14: 6, 15: 7, 16: 7,
    17: 8, 18: 8, 19: 8, 20: 8,
}

_USAGE_HANDICAP = (
    "Usage: `handicap <score> <course-rating> <slope>` for one round's "
    "differential — e.g. `handicap 85 72.1 128` — or `handicap diffs "
    "<d1> <d2> ...` for an index from 3-20 differentials, e.g. "
    "`handicap diffs 10.2 12.5 8.9`."
)


def _run_handicap(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if not parts:
        return _USAGE_HANDICAP
    if parts[0].lower() == "diffs":
        diffs = [_num(p) for p in parts[1:]]
        if not diffs or any(d is None for d in diffs):
            return _USAGE_HANDICAP
        if len(diffs) < 3:
            return (f"Need at least 3 differentials for an index, got {len(diffs)}. "
                    "Give 3-20, e.g. `handicap diffs 10.2 12.5 8.9`.")
        if len(diffs) > 20:
            return (f"At most 20 differentials — the index uses your most recent 20. "
                    f"Got {len(diffs)}.")
        if any(not -10 <= d <= 60 for d in diffs):
            return "Differentials should be between -10 and 60."
        best_n = _WHS_BEST_OF[len(diffs)]
        best = sorted(diffs)[:best_n]
        index = (sum(best) / len(best)) * 0.96
        best_text = ", ".join(f"{d:.1f}" for d in best)
        return (f"Handicap index: {index:.1f} — from {len(diffs)} differentials, "
                f"the best {best_n} ({best_text}) average "
                f"{sum(best) / len(best):.2f}, times 0.96. Your official "
                f"index comes from your golf association.")
    if len(parts) != 3:
        return _USAGE_HANDICAP
    score, rating, slope = (_num(p) for p in parts)
    if score is None or rating is None or slope is None:
        return _USAGE_HANDICAP
    if not 30 <= score <= 200:
        return f"Score must be 30-200, got `{parts[0]}`."
    if not 55 <= rating <= 85:
        return f"Course rating must be 55-85, got `{parts[1]}`."
    if not 55 <= slope <= 155:
        return f"Slope rating must be 55-155, got `{parts[2]}`."
    differential = (score - rating) * 113 / slope
    return (f"Handicap differential: {differential:.1f} — ({_fmt_num(score)} - "
            f"{rating}) x 113 / {_fmt_num(slope)}. Feed it to `handicap diffs ...` "
            f"with your other recent rounds to get an index.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="batting", description="Batting average from hits and at-bats, with a target chase.",
        usage="batting <hits> <at-bats> [target]",
        triggers=["batting", "battingaverage", "batting-average", "ba"],
        run=_run_batting,
        examples=["batting 100 300", "batting 80 300 .300"]))
    registry.register(Skill(
        name="era", description="Earned run average from earned runs and innings pitched.",
        usage="era <earned-runs> <innings>",
        triggers=["era"],
        run=_run_era,
        examples=["era 18 60", "era 10 6.1"]))
    registry.register(Skill(
        name="qbrating", description="NFL passer rating from completions, attempts, yards, TDs, INTs.",
        usage="qbrating <completions> <attempts> <yards> <touchdowns> <interceptions>",
        triggers=["qbrating", "passerrating", "passer-rating", "qbr"],
        run=_run_qbrating,
        examples=["qbrating 20 30 250 2 1"]))
    registry.register(Skill(
        name="handicap", description="Golf handicap differential or index from differentials.",
        usage="handicap <score> <course-rating> <slope> | handicap diffs <d1> <d2> ...",
        triggers=["handicap", "golfhandicap", "golf-handicap"],
        run=_run_handicap,
        examples=["handicap 85 72.1 128", "handicap diffs 10.2 12.5 8.9"]))
