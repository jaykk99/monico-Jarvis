"""School math helpers: final-exam score needed, GPA, study plan, exam pacing.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only, for the everyday school questions: what mark you
need on the final to hit a target average, what your GPA is from a set of
grades, how to split study hours across the days left before a deadline,
and how fast to work through an exam.

Formulas and rules used:
- Final needed: needed = (target - current x (1 - w)) / w, where w is the
  final's weight as a fraction of the course grade. If the answer is over
  100 the target is out of reach, and the reply says the best average
  possible with a perfect final. If it is zero or below, the target is
  already locked in even with a zero on the final.
- GPA: the common 4.0 scale — A 93-100 = 4.0, A- 90-92 = 3.7, B+ 87-89
  = 3.3, B 83-86 = 3.0, B- 80-82 = 2.7, C+ 77-79 = 2.3, C 73-76 = 2.0,
  C- 70-72 = 1.7, D+ 67-69 = 1.3, D 63-66 = 1.0, D- 60-62 = 0.7, below
  60 = 0. Letter grades map to the same points. An optional `x<credits>`
  suffix weights a grade by course credits.
- Study plan: total hours divided by the days left (or the days given),
  with a nudge to front-load if the daily load is heavy.
- Exam pace: total minutes divided by the number of questions, with
  quarter-way checkpoints and a 10% time buffer target.

Conventions and explicit caveats:
- A plain number with no unit is read as a percent for grades and the
  final's weight, hours for study time, and days for a study span.
- The GPA scale is the common 4.0 one — your school may use a different
  scale (some count A+ as 4.3, some use percent averages instead), so
  treat the number as an estimate and check your school's scale.
- A final's weight comes from your course outline, not from this skill:
  weights vary by course, and a wrong weight gives a wrong answer.
- Study hours are a plan, not a promise — a heavy daily load (over
  about 6 hours a day) is flagged as such because cramming that much
  rarely sticks.
"""
from __future__ import annotations

import re
from datetime import date

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


def _parse_pct(token: str) -> float | None:
    """Parse a 0-100 percent. Accepts `85`, `85%`."""
    value = _num(token)
    if value is None:
        return None
    return value


def _parse_weight(token: str) -> float | None:
    """Parse a final-exam weight as a fraction of the course grade.

    Accepts `30%`, `30` (read as 30%), and `0.3` (read as a fraction).
    Returns the fraction (0, 1] or None.
    """
    raw = token.strip()
    if raw.endswith("%"):
        value = _num(raw)
        if value is None:
            return None
        return value / 100.0
    value = _num(raw)
    if value is None:
        return None
    if value > 1:
        return value / 100.0
    return value


def _fmt_duration(minutes: float) -> str:
    """Format a length of time: `45 min`, `22 min 30 sec`, `1 h 30 min`."""
    total_seconds = round(minutes * 60)
    hours, rem = divmod(total_seconds, 3600)
    mins, secs = divmod(rem, 60)
    bits = []
    if hours:
        bits.append(f"{hours} h")
    if mins:
        bits.append(f"{mins} min")
    if secs and not hours:
        bits.append(f"{secs} sec")
    if not bits:
        return "0 min"
    return " ".join(bits)


# ---------------------------------------------------------------- final

_USAGE_FINAL = (
    "Usage: `final <current>% <final-weight> <target>%` — e.g. "
    "`final 80 40% 85`, `final 80 0.4 85`. The weight can be a percent "
    "(`40%`, `40`) or a fraction (`0.4`)."
)


def _run_final(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 3:
        return _USAGE_FINAL
    current = _parse_pct(parts[0])
    weight = _parse_weight(parts[1])
    target = _parse_pct(parts[2])
    if current is None or weight is None or target is None:
        return _USAGE_FINAL
    if not 0 <= current <= 100:
        return f"Current average must be 0-100, got `{parts[0]}`."
    if not 0 <= target <= 100:
        return f"Target average must be 0-100, got `{parts[2]}`."
    if not 0 < weight <= 1:
        return f"Final weight must be above 0% and at most 100%, got `{parts[1]}`."
    needed = (target - current * (1 - weight)) / weight
    weight_pct = weight * 100
    if needed <= 0:
        return (f"You're already there: with a {_fmt_num(current)}% average "
                f"and the final worth {_fmt_num(weight_pct)}%, you'd finish "
                f"at {_fmt_num(current * (1 - weight))}% or better even with "
                f"a zero on the final — your target of {_fmt_num(target)}% "
                f"is already locked in.")
    if needed > 100:
        best = current * (1 - weight) + 100 * weight
        return (f"That target is out of reach: even a perfect 100% on the "
                f"final (worth {_fmt_num(weight_pct)}%) only gets you to "
                f"{best:.1f}% from a {_fmt_num(current)}% average. To hit "
                f"{_fmt_num(target)}% you'd need {needed:.1f}% on the final. "
                f"Either lower the target or raise the current average first.")
    return (f"To finish at {_fmt_num(target)}% from a {_fmt_num(current)}% "
            f"average with the final worth {_fmt_num(weight_pct)}%, you need "
            f"{needed:.1f}% on the final. That's the exact mark — a point "
            f"above it and you're over the target.")


# ---------------------------------------------------------------- gpa

_GRADE_POINTS = {
    "a+": 4.0, "a": 4.0, "a-": 3.7,
    "b+": 3.3, "b": 3.0, "b-": 2.7,
    "c+": 2.3, "c": 2.0, "c-": 1.7,
    "d+": 1.3, "d": 1.0, "d-": 0.7,
    "f": 0.0,
}

# (lowest percent in the band, points) — the common 4.0 scale.
_PCT_BANDS = [
    (93, 4.0), (90, 3.7), (87, 3.3), (83, 3.0), (80, 2.7),
    (77, 2.3), (73, 2.0), (70, 1.7), (67, 1.3), (63, 1.0),
    (60, 0.7), (0, 0.0),
]


def _pct_to_points(pct: float) -> tuple[float, str]:
    for low, points in _PCT_BANDS:
        if pct >= low:
            return points, _points_to_letter(points)
    return 0.0, "F"


def _points_to_letter(points: float) -> str:
    for letter, value in _GRADE_POINTS.items():
        if value == points and len(letter) <= 2:
            return letter.upper()
    return "F"


_USAGE_GPA = (
    "Usage: `gpa <grade> <grade> ...` — letters or percents, e.g. "
    "`gpa A B+ C`, `gpa 92 88 76`. Add `x<credits>` to weight a course, "
    "e.g. `gpa 92x3 88x1`."
)

_GRADE_RE = re.compile(r"^([A-Fa-f][+-]?|\d+(?:\.\d+)?%?)(?:x(\d+(?:\.\d+)?))?$")


def _run_gpa(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if not tokens or len(tokens) > 12:
        return _USAGE_GPA
    entries = []  # (points, credits, display)
    for token in tokens:
        m = _GRADE_RE.match(token.strip())
        if not m:
            return f"Couldn't read a grade from `{token}`. " + _USAGE_GPA
        grade_part, credits_part = m.group(1), m.group(2)
        credits = float(credits_part) if credits_part else 1.0
        if not 0 < credits <= 6:
            return f"Credits must be 0-6, got `{token}`."
        if grade_part.rstrip("%").replace(".", "", 1).isdigit():
            pct = _num(grade_part)
            if pct is None or not 0 <= pct <= 100:
                return f"Percents must be 0-100, got `{token}`."
            points, letter = _pct_to_points(pct)
            display = f"{_fmt_num(pct)}% ({letter})"
        else:
            letter = grade_part.lower()
            if letter not in _GRADE_POINTS:
                return f"Couldn't read a grade from `{token}`. " + _USAGE_GPA
            points = _GRADE_POINTS[letter]
            display = letter.upper()
        entries.append((points, credits, display))
    total_credits = sum(c for _, c, _ in entries)
    gpa = sum(p * c for p, c, _ in entries) / total_credits
    shown = ", ".join(display for _, _, display in entries)
    if len(entries) == 1:
        return (f"One grade {shown} is a {gpa:.2f} GPA on the common 4.0 "
                f"scale — your school may use a different scale, so treat "
                f"it as an estimate.")
    credit_note = ""
    if any(c != 1.0 for _, c, _ in entries):
        credit_note = f" (credit-weighted over {_fmt_num(total_credits)} credits)"
    return (f"GPA: {gpa:.2f} on the common 4.0 scale{credit_note}, from "
            f"{shown}. That's the plain average of the grade points — "
            f"check your school's scale, since some count A+ as 4.3 or use "
            f"percent averages instead.")


# ---------------------------------------------------------------- study

_HOURS_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*h(?:ours?|rs?)?$", re.IGNORECASE)
_DAYS_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*d(?:ays?)?$", re.IGNORECASE)
_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")

_USAGE_STUDY = (
    "Usage: `study <hours>h <days>d` or `study <hours>h before <YYYY-MM-DD>` "
    "— e.g. `study 20h 5d`, `study 12h before 2026-11-30`. Splits the hours "
    "across the days left."
)


def _run_study(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) not in (2, 3):
        return _USAGE_STUDY
    m_hours = _HOURS_RE.match(parts[0])
    if not m_hours:
        return _USAGE_STUDY
    hours = float(m_hours.group(1))
    if not 0.5 <= hours <= 500:
        return "Study hours must be 0.5-500."
    days: float | None = None
    deadline_note = ""
    if len(parts) == 2:
        m_days = _DAYS_RE.match(parts[1])
        if not m_days:
            return _USAGE_STUDY
        days = float(m_days.group(1))
    else:
        if parts[1].lower() != "before":
            return _USAGE_STUDY
        m_date = _DATE_RE.match(parts[2])
        if not m_date:
            return _USAGE_STUDY
        year, month, day = (int(g) for g in m_date.groups())
        try:
            deadline = date(year, month, day)
        except ValueError:
            return f"`{parts[2]}` isn't a real date."
        days_left = (deadline - date.today()).days
        if days_left <= 0:
            return f"`{parts[2]}` is today or already past — no days left to plan over."
        days = float(days_left)
        deadline_note = f" until {deadline.isoformat()}"
    if not 1 <= days <= 365:
        return "Days must be 1-365."
    per_day = hours / days
    per_day_text = f"{per_day:.1f} hour{'s' if per_day != 1 else ''} a day"
    if per_day > 6:
        load_note = (f" That's a heavy load — over 6 hours a day rarely "
                     f"sticks, so start now and split it into focused "
                     f"blocks with breaks.")
    elif per_day > 3:
        load_note = (" That's a solid stretch — split it into focused "
                     "blocks with short breaks between them.")
    else:
        load_note = " That's a steady, doable pace."
    return (f"Study plan: {_fmt_num(hours)} hours over {_fmt_num(days)} "
            f"day{'s' if days != 1 else ''}{deadline_note} is "
            f"{per_day_text}.{load_note} Do a bit more on the early days "
            f"if you can, so the last day is review, not new material.")


# ---------------------------------------------------------------- exam

_QUESTIONS_RE = re.compile(r"^(\d+)\s*q(?:uestions?)?$", re.IGNORECASE)
_MINUTES_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*m(?:in(?:utes?)?)?$", re.IGNORECASE)

_USAGE_EXAM = (
    "Usage: `exam <questions>q <minutes>min` — e.g. `exam 60q 90min`, "
    "`exam 40q 120m`. Gives your pace per question plus quarter-way "
    "checkpoints."
)


def _run_exam(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 2:
        return _USAGE_EXAM
    m_q = _QUESTIONS_RE.match(parts[0])
    m_min = _MINUTES_RE.match(parts[1])
    if not m_q or not m_min:
        return _USAGE_EXAM
    questions = int(m_q.group(1))
    minutes = float(m_min.group(1))
    if not 1 <= questions <= 500:
        return "Questions must be 1-500."
    if not 1 <= minutes <= 600:
        return "Exam length must be 1-600 minutes."
    per_question = minutes / questions
    buffer_minutes = minutes * 0.9
    buffer_per_q = buffer_minutes / questions
    checkpoints = []
    for frac, label in ((0.25, "quarter"), (0.5, "halfway"), (0.75, "three-quarters")):
        q_at = round(questions * frac)
        t_at = minutes * frac
        checkpoints.append(f"{label} ({q_at} questions): {_fmt_duration(t_at)} in")
    return (f"Exam pace: {questions} questions in {_fmt_duration(minutes)} "
            f"is {_fmt_duration(per_question)} per question. Aim for "
            f"{_fmt_duration(buffer_per_q)} per question instead, so you "
            f"finish with about {_fmt_duration(minutes * 0.1)} to spare for "
            f"checking. Checkpoints — {'; '.join(checkpoints)}. If you're "
            f"behind at a checkpoint, skip the hard ones and come back.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="final", description="Score needed on the final to hit a target average.",
        usage="final <current>% <final-weight> <target>%",
        triggers=["final", "finalexam", "final-exam"],
        run=_run_final,
        examples=["final 80 40% 85", "final 80 0.4 85"]))
    registry.register(Skill(
        name="gpa", description="GPA on the common 4.0 scale from letters or percents.",
        usage="gpa <grade> <grade> ...",
        triggers=["gpa"],
        run=_run_gpa,
        examples=["gpa A B+ C", "gpa 92 88 76", "gpa 92x3 88x1"]))
    registry.register(Skill(
        name="study", description="Split study hours across days before a deadline.",
        usage="study <hours>h <days>d | study <hours>h before <YYYY-MM-DD>",
        triggers=["study", "studyplan", "study-plan"],
        run=_run_study,
        examples=["study 20h 5d", "study 12h before 2026-11-30"]))
    registry.register(Skill(
        name="exam", description="Exam pace per question with quarter-way checkpoints.",
        usage="exam <questions>q <minutes>min",
        triggers=["exam", "testpace", "exampace"],
        run=_run_exam,
        examples=["exam 60q 90min", "exam 40q 120m"]))
