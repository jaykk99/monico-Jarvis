"""Tests for skills/sports.py: batting, era, qbrating, handicap."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- batting
def test_batting_average():
    # 100/300 = .333, star territory.
    out = _ask("batting 100 300")
    assert "Batting 100 for 300 is .333" in out
    assert "excellent" in out
    # 80/300 = .267, around league average.
    out = _ask("batting 80 300")
    assert "is .267" in out
    assert "around league average" in out
    # The `ba` alias routes to the same skill.
    assert "is .333" in _ask("ba 100 300")


def test_batting_below_mendoza():
    # 15/100 = .150, below the Mendoza line.
    out = _ask("batting 15 100")
    assert "is .150" in out
    assert "below the Mendoza line" in out


def test_batting_target_chase():
    # 80/300 = .267; to reach .300 needs x >= (90-80)/0.7 = 14.29 -> 15 hits.
    # (80+15)/(300+15) = 95/315 = .302.
    out = _ask("batting 80 300 .300")
    assert "need 15 consecutive hits" in out
    assert "to .302 (95 for 315)" in out
    # Target as a bare 300 reads as .300 too.
    assert "need 15 consecutive hits" in _ask("batting 80 300 300")
    # Already at the target: 90/300 = .300.
    out = _ask("batting 90 300 .300")
    assert "already at or above your .300 target" in out


def test_batting_bad():
    assert "Usage" in _ask("batting")
    assert "Usage" in _ask("batting 100")
    assert "Usage" in _ask("batting 100 300 .300 extra")
    assert "whole numbers" in _ask("batting 100.5 300")
    assert "at least 1" in _ask("batting 100 0")
    assert "can't be more than at-bats" in _ask("batting 301 300")
    assert "between .001 and .999" in _ask("batting 80 300 1.5")


# ---------------------------------------------------------------- era
def test_era_basic():
    # 9*18/60 = 2.70, excellent.
    out = _ask("era 18 60")
    assert "ERA: 2.70" in out
    assert "18 earned runs in 60 innings" in out
    assert "excellent" in out


def test_era_baseball_innings():
    # 6.1 = 6 1/3 innings: 9*10/(19/3) = 270/19 = 14.21.
    out = _ask("era 10 6.1")
    assert "ERA: 14.21" in out
    assert "10 earned runs in 6.1 innings" in out
    # 6.2 = 6 2/3 innings: 9*3/(20/3) = 81/20 = 4.05.
    out = _ask("era 3 6.2")
    assert "ERA: 4.05" in out
    # A shutout is a 0.00 ERA.
    out = _ask("era 0 9")
    assert "ERA: 0.00" in out
    assert "elite" in out


def test_era_bad():
    assert "Usage" in _ask("era")
    assert "Usage" in _ask("era 10")
    # .3 is not a baseball innings fraction — only .0, .1, .2.
    assert "Usage" in _ask("era 10 6.3")
    assert "Usage" in _ask("era 10 six")
    assert "0 or more" in _ask("era -1 9")
    assert "more than 0" in _ask("era 5 0")


# ---------------------------------------------------------------- qbrating
def test_qbrating_good_game():
    # 20/30, 250 yds, 2 TD, 1 INT: a=1.8333 b=1.3333 c=1.3333 d=1.5417
    # -> (6.0417/6)*100 = 100.7.
    out = _ask("qbrating 20 30 250 2 1")
    assert "Passer rating: 100.7" in out
    assert "20 of 30 for 250 yards, 2 touchdowns, 1 interception" in out
    assert "excellent" in out


def test_qbrating_perfect():
    # Every component clamps to 2.375: (4*2.375/6)*100 = 158.3.
    out = _ask("qbrating 20 20 300 4 0")
    assert "Passer rating: 158.3" in out
    assert "perfect 158.3" in out


def test_qbrating_bad_game():
    # 10/30, 100 yds, 0 TD, 3 INT: a=0.1667 b=0.0833 c=0 d clamps to 0
    # -> (0.25/6)*100 = 4.2.
    out = _ask("qbrating 10 30 100 0 3")
    assert "Passer rating: 4.2" in out
    assert "rough outing" in out
    # The `qbr` alias routes to the same skill.
    assert "Passer rating: 100.7" in _ask("qbr 20 30 250 2 1")


def test_qbrating_bad():
    assert "Usage" in _ask("qbrating")
    assert "Usage" in _ask("qbrating 20 30 250 2")
    assert "at least 1" in _ask("qbrating 20 0 250 2 1")
    assert "can't be more than attempts" in _ask("qbrating 31 30 250 2 1")
    assert "0 or more" in _ask("qbrating 20 30 -5 2 1")


# ---------------------------------------------------------------- handicap
def test_handicap_differential():
    # (85 - 72.1) * 113 / 128 = 1457.7/128 = 11.39 -> 11.4.
    out = _ask("handicap 85 72.1 128")
    assert "Handicap differential: 11.4" in out
    assert "(85 - 72.1) x 113 / 128" in out


def test_handicap_index_three_rounds():
    # 3 differentials -> best 1 (8.9), average 8.90 x 0.96 = 8.544 -> 8.5.
    out = _ask("handicap diffs 10.2 12.5 8.9")
    assert "Handicap index: 8.5" in out
    assert "from 3 differentials, the best 1 (8.9)" in out
    assert "average 8.90, times 0.96" in out


def test_handicap_index_five_rounds():
    # 5 differentials -> best 2 (9.0, 10.0), average 9.50 x 0.96 = 9.12 -> 9.1.
    out = _ask("handicap diffs 12.0 10.0 14.0 9.0 11.0")
    assert "Handicap index: 9.1" in out
    assert "the best 2 (9.0, 10.0)" in out


def test_handicap_index_twenty_rounds():
    # 20 differentials 5..24 -> best 8 (5..12), average 8.50 x 0.96 = 8.16 -> 8.2.
    diffs = " ".join(str(n) for n in range(5, 25))
    out = _ask(f"handicap diffs {diffs}")
    assert "Handicap index: 8.2" in out
    assert "from 20 differentials, the best 8" in out


def test_handicap_bad():
    assert "Usage" in _ask("handicap")
    assert "Usage" in _ask("handicap 85 72.1")
    assert "at least 3 differentials" in _ask("handicap diffs 10.2 12.5")
    assert "At most 20 differentials" in _ask(
        "handicap diffs " + " ".join(["10.0"] * 21))
    assert "55-155" in _ask("handicap 85 72.1 200")
    assert "55-85" in _ask("handicap 85 40 128")
    assert "30-200" in _ask("handicap 250 72.1 128")


# ---------------------------------------------------------------- registry
def test_sports_skills_registered():
    names = {s["name"] for s in agent.list_skills()}
    assert {"batting", "era", "qbrating", "handicap"} <= names
    assert len(agent.list_skills()) == 130
