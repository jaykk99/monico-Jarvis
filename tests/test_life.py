"""Tests for skills/life.py: split, fuel, readtime, water."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- split
def test_split_even():
    out = _ask("split 120 4")
    assert "$30.00 each" in out


def test_split_with_tip_and_remainder():
    # 100 + 15% = 115.00 split 4 ways: 28.75 each, exact.
    out = _ask("split 100 4 15%")
    assert "$115.00" in out and "$28.75 each" in out
    # 10.00 split 3 ways: 3.34, 3.33, 3.33.
    out = _ask("split 10 3")
    assert "first 1 pay $3.34 each" in out
    assert "remaining 2 pay $3.33 each" in out


def test_split_bad():
    assert "Usage" in _ask("split 120")
    assert "Couldn't read" in _ask("split abc 4")
    assert "whole number" in _ask("split 120 2.5")
    assert "greater than 0" in _ask("split 120 0")


# ---------------------------------------------------------------- fuel
def test_fuel_km():
    out = _ask("fuel 400km 8 1.50")
    assert "32.00 L" in out and "$48.00" in out and "$0.12 per km" in out


def test_fuel_miles():
    out = _ask("fuel 300mi 30 4.00")
    assert "10.00 gal" in out and "$40.00" in out and "$0.13 per mile" in out


def test_fuel_bad():
    assert "Usage" in _ask("fuel 400km 8")
    assert "Couldn't read" in _ask("fuel 400km fast 1.50")
    assert "Couldn't read" in _ask("fuel 400parsecs 8 1.50")


# ---------------------------------------------------------------- readtime
def test_readtime_default_and_custom():
    out = _ask("readtime 12000")
    assert "12,000 words at 200 wpm" in out and "about 1h 0m" in out
    out = _ask("readtime 6000 300")
    assert "about 20 minutes" in out
    out = _ask("readtime 100")
    assert "about 30 seconds" in out


def test_readtime_bad():
    assert "Usage" in _ask("readtime")
    assert "Couldn't read" in _ask("readtime abc")
    assert "greater than 0" in _ask("readtime 0")


# ---------------------------------------------------------------- water
def test_water_kg():
    out = _ask("water 70kg")
    assert "2.31 L" in out and "78.1 fl oz" in out
    assert "not medical advice" in out


def test_water_lb_and_exercise():
    # 154 lb ~ 69.85 kg -> 2.31 L base; +60 min exercise -> 2.81 L.
    out = _ask("water 154lb 60")
    assert "2.81 L" in out


def test_water_bad():
    assert "Usage" in _ask("water")
    assert "Couldn't read" in _ask("water 70stones")
    assert "must be > 0" in _ask("water 0kg")
