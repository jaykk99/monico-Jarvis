"""Tests for skills/school.py: final, gpa, study, exam."""
from datetime import date, timedelta

from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- final
def test_final_needed_score():
    # 80% now, final worth 40%, want 85%: (85 - 80*0.6) / 0.4 = 92.5.
    out = _ask("final 80 40% 85")
    assert "you need 92.5% on the final" in out
    assert "worth 40%" in out
    # Same answer with the weight as a bare number and as a fraction.
    assert "92.5%" in _ask("final 80 40 85")
    assert "92.5%" in _ask("final 80 0.4 85")


def test_final_out_of_reach():
    # 85% now, final worth 30%, want 90%: needs 101.7%; best possible 89.5%.
    out = _ask("final 85 30% 90")
    assert "out of reach" in out
    assert "101.7%" in out
    assert "89.5%" in out


def test_final_already_locked_in():
    # 90% now, final worth 20%, want 70%: even a zero on the final gives 72%.
    out = _ask("final 90 20% 70")
    assert "already locked in" in out
    assert "72%" in out
    # The finalexam alias routes to the same skill.
    assert "already locked in" in _ask("finalexam 90 20% 70")


def test_final_bad():
    assert "Usage" in _ask("final")
    assert "Usage" in _ask("final 80 40%")
    assert "Usage" in _ask("final 80 40% 85 extra")
    assert "Usage" in _ask("final fast 40% 85")
    assert "0-100" in _ask("final 101 40% 85")
    assert "0-100" in _ask("final 80 40% 101")
    assert "above 0%" in _ask("final 80 0% 85")
    assert "above 0%" in _ask("final 80 101% 85")


# ---------------------------------------------------------------- gpa
def test_gpa_percents():
    # 92 -> A- 3.7, 88 -> B+ 3.3, 76 -> C 2.0: (3.7+3.3+2.0)/3 = 3.00.
    out = _ask("gpa 92 88 76")
    assert "GPA: 3.00" in out
    assert "92% (A-), 88% (B+), 76% (C)" in out


def test_gpa_letters():
    # A 4.0, B+ 3.3, C 2.0: 9.3/3 = 3.10. Lowercase works too.
    assert "GPA: 3.10" in _ask("gpa A B+ C")
    assert "GPA: 3.10" in _ask("gpa a b+ c")
    # A+ 4.0, A- 3.7, 95% (A+) 4.0: 11.7/3 = 3.90.
    assert "GPA: 3.90" in _ask("gpa A+ A- 95")


def test_gpa_band_edges():
    # 59 -> F 0.0, 60 -> D- 0.7, 93 -> A+ 4.0: 4.7/3 = 1.57.
    out = _ask("gpa 59 60 93")
    assert "GPA: 1.57" in out
    assert "59% (F), 60% (D-), 93% (A+)" in out


def test_gpa_credits_and_single():
    # 92x3 (3.7) and 88x1 (3.3): (11.1+3.3)/4 = 3.60.
    out = _ask("gpa 92x3 88x1")
    assert "GPA: 3.60" in out
    assert "credit-weighted over 4 credits" in out
    out = _ask("gpa 100")
    assert "4.00 GPA" in out
    assert "100% (A+)" in out


def test_gpa_bad():
    assert "Usage" in _ask("gpa")
    assert "Couldn't read a grade" in _ask("gpa Z")
    assert "Couldn't read a grade" in _ask("gpa E")
    assert "0-100" in _ask("gpa 101")
    assert "0-6" in _ask("gpa 92x7 88")


# ---------------------------------------------------------------- study
def test_study_days_given():
    # 20 hours over 5 days = 4.0 hours a day.
    out = _ask("study 20h 5d")
    assert "20 hours over 5 days is 4.0 hours a day" in out
    assert "solid stretch" in out
    # 10 hours over 3 days = 3.3 hours a day.
    assert "3.3 hours a day" in _ask("study 10h 3d")
    # The studyplan alias routes to the same skill.
    assert "4.0 hours a day" in _ask("studyplan 20h 5d")


def test_study_heavy_load_flagged():
    # 30 hours over 3 days = 10.0 hours a day: flagged as heavy.
    out = _ask("study 30h 3d")
    assert "10.0 hours a day" in out
    assert "heavy load" in out


def test_study_before_deadline():
    # 12 hours before a date 10 days out: 12/10 = 1.2 hours a day.
    deadline = (date.today() + timedelta(days=10)).isoformat()
    out = _ask(f"study 12h before {deadline}")
    assert f"12 hours over 10 days until {deadline} is 1.2 hours a day" in out
    assert "steady, doable pace" in out


def test_study_bad():
    assert "Usage" in _ask("study")
    assert "Usage" in _ask("study 5h")
    assert "Usage" in _ask("study 20h 5")
    assert "Usage" in _ask("study 20h next 2026-11-30")
    assert "0.5-500" in _ask("study 0.1h 5d")
    assert "1-365" in _ask("study 20h 400d")
    assert "already past" in _ask("study 12h before 2026-11-01")
    assert "isn't a real date" in _ask("study 12h before 2026-02-30")


# ---------------------------------------------------------------- exam
def test_exam_pace():
    # 60 questions in 90 min: 1 min 30 sec each; buffer pace 1 min 21 sec.
    out = _ask("exam 60q 90min")
    assert "60 questions in 1 h 30 min is 1 min 30 sec per question" in out
    assert "1 min 21 sec per question instead" in out
    assert "9 min to spare" in out
    assert "quarter (15 questions): 22 min 30 sec in" in out
    assert "halfway (30 questions): 45 min in" in out
    assert "three-quarters (45 questions): 1 h 7 min in" in out


def test_exam_long():
    # 40 questions in 120 min: 3 min each; buffer pace 2 min 42 sec.
    out = _ask("exam 40q 120m")
    assert "40 questions in 2 h is 3 min per question" in out
    assert "2 min 42 sec per question instead" in out
    assert "12 min to spare" in out
    # The testpace alias routes to the same skill.
    assert "3 min per question" in _ask("testpace 40q 120m")


def test_exam_bad():
    assert "Usage" in _ask("exam")
    assert "Usage" in _ask("exam 60q")
    assert "Usage" in _ask("exam sixty 90min")
    assert "1-500" in _ask("exam 0q 90min")
    assert "1-600" in _ask("exam 60q 0min")


# ---------------------------------------------------------------- registry
def test_school_skills_registered():
    names = {s["name"] for s in agent.list_skills()}
    assert {"final", "gpa", "study", "exam"} <= names
    assert len(agent.list_skills()) == 126
    # The existing `grade` weighted-average skill is untouched by `final`.
    out = _ask("grade 90 0.3 80 0.7")
    assert "Weighted average: 83.0" in out
