"""Tests for skills/household.py: unitprice, pace, sleep, grade."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- unitprice
def test_unitprice_single():
    out = _ask("unitprice 5.99 12oz")
    assert "$0.50 per oz" in out


def test_unitprice_compare():
    out = _ask("unitprice 5.99 12oz vs 9.99 24oz")
    assert "$0.50 per oz" in out and "$0.42 per oz" in out
    assert "Second pack is cheaper" in out
    out = _ask("unitprice 4.00 10 vs 4.00 10")
    assert "same per unit" in out


def test_unitprice_bad():
    assert "Usage" in _ask("unitprice 5.99")
    assert "Couldn't read" in _ask("unitprice abc 12oz")
    assert "don't match" in _ask("unitprice 5.99 12oz vs 9.99 24g")


# ---------------------------------------------------------------- pace
def test_pace_km():
    out = _ask("pace 5km 25:00")
    assert "5:00/km" in out and "8:03/mi" in out
    assert "12.0 km/h" in out and "7.5 mph" in out


def test_pace_miles_hours():
    out = _ask("pace 10mi 1:20:00")
    assert "8:00/mi" in out and "4:58/km" in out
    assert "12.1 km/h" in out


def test_pace_bad():
    assert "Usage" in _ask("pace 5km")
    assert "Couldn't read" in _ask("pace 5km fast")
    assert "Couldn't read" in _ask("pace 5parsecs 25:00")


# ---------------------------------------------------------------- sleep
def test_sleep_24h():
    out = _ask("sleep 22:30")
    # asleep 22:45; 4 cycles -> 04:45, 5 -> 06:15, 6 -> 07:45
    assert "4 cycles (6.0h): 4:45 AM" in out
    assert "5 cycles (7.5h): 6:15 AM" in out
    assert "6 cycles (9.0h): 7:45 AM" in out
    assert "not medical advice" in out


def test_sleep_ampm_matches_24h():
    assert _ask("sleep 10:30pm") == _ask("sleep 22:30")


def test_sleep_bad():
    assert "Usage" in _ask("sleep")
    assert "valid HH:MM" in _ask("sleep 25:00")
    assert "1–12" in _ask("sleep 13:00pm")


# ---------------------------------------------------------------- grade
def test_grade_decimal_weights():
    out = _ask("grade 90 0.3 80 0.7")
    assert "83.0 (B)" in out


def test_grade_percent_weights_and_scaling():
    out = _ask("grade 90 30% 80 70%")
    assert "83.0 (B)" in out
    # weights summing to 50 scale up to 100%
    out = _ask("grade 100 0.25 80 0.25")
    assert "90.0 (A)" in out


def test_grade_bad():
    assert "Usage" in _ask("grade 90")
    assert "Usage" in _ask("grade 90 0.3 80")
    assert "0–100" in _ask("grade 120 0.5 80 0.5")
    assert "more than 0" in _ask("grade 90 0 80 0")
