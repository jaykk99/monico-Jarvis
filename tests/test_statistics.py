"""Tests for skills/statistics.py: zscore, weighted, movavg, quartile."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


def test_skill_count():
    assert len(agent.list_skills()) == 150


# ---------------------------------------------------------------- zscore
def test_zscore_above():
    # Data 10 20 30 40 50: mean 30, sample sd sqrt(250) = 15.81;
    # z(50) = 20 / 15.81 = 1.265.
    out = _ask("zscore 50 in 10 20 30 40 50")
    assert "50 has a z-score of 1.265 against 5 values (mean 30, sd 15.81)" in out
    assert "1.265 standard deviations above the mean." in out


def test_zscore_below():
    # z(10) = -20 / 15.81 = -1.265.
    out = _ask("zscore 10 in 10 20 30 40 50")
    assert "10 has a z-score of -1.265 against 5 values (mean 30, sd 15.81)" in out
    assert "1.265 standard deviations below the mean." in out


def test_zscore_at_mean():
    # z(30) = 0 / 15.81 = 0.
    out = _ask("zscore 30 in 10 20 30 40 50")
    assert "30 has a z-score of 0 against 5 values (mean 30, sd 15.81)" in out
    assert "0 standard deviations at the mean." in out


def test_zscore_unsorted_input():
    # Order doesn't matter: same mean/sd, z(40) = 10 / 15.81 = 0.6325.
    out = _ask("zscore 40 in 50 10 30 20 40")
    assert "40 has a z-score of 0.6325 against 5 values (mean 30, sd 15.81)" in out


def test_zscore_mean_sd_form():
    # z = (50 - 30) / 15.81 = 1.265.
    out = _ask("zscore 50 30 15.81")
    assert "50 has a z-score of 1.265 (mean 30, sd 15.81)" in out
    assert "1.265 standard deviations above the mean." in out


def test_zscore_alias():
    assert "z-score of 1.265" in _ask("z-score 50 in 10 20 30 40 50")


def test_zscore_bad():
    assert "Usage" in _ask("zscore")
    assert "Usage" in _ask("zscore 50 in 10")
    assert "Usage" in _ask("zscore 50 30")
    assert "can't be 0" in _ask("zscore 50 30 0")
    assert "can't be negative" in _ask("zscore 50 30 -5")
    assert "no spread" in _ask("zscore 50 in 10 10 10")


# ---------------------------------------------------------------- weighted
def test_weighted_basic():
    # (90x3 + 80x2 + 70x1) / 6 = 500 / 6 = 83.33; plain mean 80.
    out = _ask("weighted 90x3 80x2 70x1")
    assert "Weighted average of 3 values: 83.33 (total weight 6; plain mean would be 80)." in out


def test_weighted_two_pairs():
    # (100x1 + 50x3) / 4 = 250 / 4 = 62.5; plain mean 75.
    out = _ask("weighted 100x1 50x3")
    assert "Weighted average of 2 values: 62.5 (total weight 4; plain mean would be 75)." in out


def test_weighted_alias():
    assert "83.33" in _ask("wavg 90x3 80x2 70x1")


def test_weighted_bad():
    assert "Usage" in _ask("weighted")
    assert "Usage" in _ask("weighted 90x3")
    assert "Usage" in _ask("weighted 90 80x2")
    assert "must be positive" in _ask("weighted 90x0 80x2")
    assert "must be positive" in _ask("weighted 90x-1 80x2")


# ---------------------------------------------------------------- movavg
def test_movavg_window3():
    # Windows [1,2,3] [2,3,4] [3,4,5] -> 2, 3, 4.
    out = _ask("movavg 3 1 2 3 4 5")
    assert "Moving average (window 3) of 5 values: 2, 3, 4." in out


def test_movavg_window2():
    # Windows [10,20] [20,30] -> 15, 25.
    out = _ask("movavg 2 10 20 30")
    assert "Moving average (window 2) of 3 values: 15, 25." in out


def test_movavg_full_window():
    # Window == list length: one average, (1+2+3+4+5)/5 = 3.
    out = _ask("movavg 5 1 2 3 4 5")
    assert "Moving average (window 5) of 5 values: 3." in out


def test_movavg_decimals():
    # Windows [1.5,2.5] [2.5,3.5] -> 2, 3.
    out = _ask("movavg 2 1.5 2.5 3.5")
    assert "Moving average (window 2) of 3 values: 2, 3." in out


def test_movavg_alias():
    assert "2, 3, 4." in _ask("moving 3 1 2 3 4 5")


def test_movavg_bad():
    assert "Usage" in _ask("movavg")
    assert "Usage" in _ask("movavg 1 1 2 3")
    assert "Usage" in _ask("movavg 4 1 2 3")
    assert "whole number" in _ask("movavg 2.5 1 2 3")


# ---------------------------------------------------------------- quartile
def test_quartile_basic():
    # Sorted 1..10, linear method: Q1 3.25, median 5.5, Q3 7.75,
    # IQR 4.5, fences -3.5 to 14.5, no outliers.
    out = _ask("quartile 1 2 3 4 5 6 7 8 9 10")
    assert "Five-number summary of 10 values: min 1, Q1 3.25, median 5.5, Q3 7.75, max 10." in out
    assert "IQR 4.5 (fences -3.5 to 14.5)." in out
    assert "No outliers." in out


def test_quartile_small_list():
    # 2 4 4 4 5 5 7 9: Q1 4, median 4.5, Q3 5.5, IQR 1.5,
    # fences 1.75 to 7.75, so 9 is an outlier.
    out = _ask("quartile 2 4 4 4 5 5 7 9")
    assert "Five-number summary of 8 values: min 2, Q1 4, median 4.5, Q3 5.5, max 9." in out
    assert "IQR 1.5 (fences 1.75 to 7.75)." in out
    assert "Outliers: 9." in out


def test_quartile_high_outlier():
    # Same quartiles as 1..10, but 100 sits past the 14.5 fence.
    out = _ask("quartile 1 2 3 4 5 6 7 8 9 100")
    assert "Q1 3.25, median 5.5, Q3 7.75, max 100." in out
    assert "Outliers: 100." in out


def test_quartile_alias():
    assert "IQR 4.5" in _ask("iqr 1 2 3 4 5 6 7 8 9 10")


def test_quartile_bad():
    assert "Usage" in _ask("quartile")
    assert "Usage" in _ask("quartile 1 2 3")
