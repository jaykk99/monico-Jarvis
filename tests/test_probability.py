"""Tests for skills/probability.py: percentile, prob, odds, regress."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


def test_skill_count():
    assert len(agent.list_skills()) == 150


# ---------------------------------------------------------------- percentile
def test_percentile_value():
    # Sorted 10 20 30 40 50, p=90: rank = 0.9 x 4 = 3.6, between 40 and
    # 50 -> 40 + 0.6 x 10 = 46.
    out = _ask("percentile 90 10 20 30 40 50")
    assert "The 90th percentile of 5 values is 46 (min 10, max 50)." in out


def test_percentile_median_quartile():
    # p=50 lands exactly on 30; p=25 lands exactly on 20.
    out = _ask("percentile 50 10 20 30 40 50")
    assert "The 50th percentile of 5 values is 30 (min 10, max 50)." in out
    out = _ask("percentile 25 10 20 30 40 50")
    assert "The 25th percentile of 5 values is 20 (min 10, max 50)." in out


def test_percentile_ends():
    # p=0 is the min, p=100 is the max.
    assert "The 0th percentile of 5 values is 10" in _ask("percentile 0 10 20 30 40 50")
    assert "The 100th percentile of 5 values is 50" in _ask("percentile 100 10 20 30 40 50")


def test_percentile_unsorted_input():
    # Input order doesn't matter: sorted 1..10, p=90 -> rank 8.1,
    # between 9 and 10 -> 9 + 0.1 x 1 = 9.1.
    out = _ask("percentile 90 5 2 9 1 7 3 10 4 8 6")
    assert "The 90th percentile of 10 values is 9.1 (min 1, max 10)." in out


def test_percentile_rank():
    # 30: values at or below it are 10, 20, 30 -> 3 of 5 = 60%.
    out = _ask("percentile rank 30 in 10 20 30 40 50")
    assert "30 is at the 60th percentile of 5 values (3 of 5 at or below it)." in out
    # 45: 10, 20, 30, 40 are at or below -> 4 of 5 = 80%.
    out = _ask("percentile rank 45 in 10 20 30 40 50")
    assert "45 is at the 80th percentile of 5 values (4 of 5 at or below it)." in out


def test_percentile_bad():
    assert "Usage" in _ask("percentile")
    assert "Usage" in _ask("percentile 50 10")
    assert "Usage" in _ask("percentile 101 10 20 30")
    assert "Usage" in _ask("percentile -5 10 20 30")
    assert "Usage" in _ask("percentile rank 30 in 10")
    assert "Usage" in _ask("percentile rank abc in 10 20 30")


# ---------------------------------------------------------------- prob
def test_prob_exact():
    # C(10,3) x 0.5^10 = 120/1024 = 0.1171875 -> 0.1172, 11.72%,
    # 1 in 8.533.
    out = _ask("prob 10 3 0.5")
    assert "With p = 0.5, the chance of exactly 3 successes in 10 tries is 0.1172 (11.72%, about 1 in 8.533)." in out


def test_prob_atleast():
    # P(>=9 in 10 fair flips) = (10 + 1)/1024 = 0.0107421875 -> 0.01074,
    # 1.074%, 1 in 93.09.
    out = _ask("prob atleast 10 9 0.5")
    assert "With p = 0.5, the chance of at least 9 successes in 10 tries is 0.01074 (1.074%, about 1 in 93.09)." in out


def test_prob_atmost():
    # P(<=1 in 10 fair flips) is the same 11/1024 by symmetry.
    out = _ask("prob atmost 10 1 0.5")
    assert "With p = 0.5, the chance of at most 1 success in 10 tries is 0.01074 (1.074%, about 1 in 93.09)." in out


def test_prob_loaded():
    # All 5 succeed with p = 0.2: 0.2^5 = 0.00032, 0.032%, 1 in 3125.
    out = _ask("prob 5 5 0.2")
    assert "With p = 0.2, the chance of exactly 5 successes in 5 tries is 0.00032 (0.032%, about 1 in 3125)." in out
    # None succeed in 20 tries with p = 0.1: 0.9^20 = 0.1215766... -> 0.1216.
    out = _ask("prob 20 0 0.1")
    assert "With p = 0.1, the chance of exactly 0 successes in 20 tries is 0.1216 (12.16%, about 1 in 8.225)." in out


def test_prob_bad():
    assert "Usage" in _ask("prob")
    assert "Usage" in _ask("prob 10 3")
    assert "Successes must be 0" in _ask("prob 10 11 0.5")
    assert "p must be 0" in _ask("prob 10 3 1.5")
    assert "whole numbers" in _ask("prob 10 3.5 0.5")
    assert "Trials must be 1" in _ask("prob 0 0 0.5")


# ---------------------------------------------------------------- odds
def test_odds_decimal():
    # 2.5: profit 1.5 -> 3/2, American +150, implied 1/2.5 = 40%.
    out = _ask("odds 2.5")
    assert "Decimal 2.5 = fractional 3/2 = American +150 — implied probability 40%." in out


def test_odds_american():
    # +150 is decimal 2.5 again; -200 is decimal 1.5, 1/2, implied 66.67%.
    out = _ask("odds +150")
    assert "Decimal 2.5 = fractional 3/2 = American +150 — implied probability 40%." in out
    out = _ask("odds -200")
    assert "Decimal 1.5 = fractional 1/2 = American -200 — implied probability 66.67%." in out


def test_odds_fraction():
    # 3/2 is decimal 2.5 again.
    out = _ask("odds 3/2")
    assert "Decimal 2.5 = fractional 3/2 = American +150 — implied probability 40%." in out
    # 2/1 is decimal 3, American +200, implied 33.33%.
    out = _ask("odds 2/1")
    assert "Decimal 3 = fractional 2/1 = American +200 — implied probability 33.33%." in out
    # 1/4 is decimal 1.25, American -400, implied 80%.
    out = _ask("odds 1/4")
    assert "Decimal 1.25 = fractional 1/4 = American -400 — implied probability 80%." in out


def test_odds_bad():
    assert "Usage" in _ask("odds")
    assert "above 1" in _ask("odds 1")
    assert "can't be 0" in _ask("odds +0")
    assert "Usage" in _ask("odds abc")


# ---------------------------------------------------------------- regress
def test_regress_basic():
    # Points (1,2)(2,4)(3,5)(4,4)(5,5): slope 0.6, intercept 2.2,
    # r = 0.7746, r^2 = 0.6.
    out = _ask("regress 1,2 2,4 3,5 4,4 5,5")
    assert "Best-fit line from 5 points: y = 0.6x + 2.2, r = 0.7746, r^2 = 0.6 (60% of the variation in y explained)." in out


def test_regress_predict():
    # Same line at x = 6: y = 2.2 + 0.6 x 6 = 5.8.
    out = _ask("regress 1,2 2,4 3,5 4,4 5,5 predict 6")
    assert "Best-fit line from 5 points: y = 0.6x + 2.2, r = 0.7746, r^2 = 0.6" in out
    assert "At x = 6, predicted y = 5.8." in out


def test_regress_perfect():
    # Points on y = x: slope 1, intercept 0, r = 1, r^2 = 1.
    out = _ask("regress 1,1 2,2 3,3")
    assert "Best-fit line from 3 points: y = 1x + 0, r = 1, r^2 = 1 (100% of the variation in y explained)." in out


def test_regress_bad():
    assert "Usage" in _ask("regress")
    assert "Usage" in _ask("regress 1,2 2,4")
    assert "Usage" in _ask("regress 1 2 3")
    assert "same" in _ask("regress 1,1 1,2 1,3")
