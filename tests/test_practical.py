"""Tests for skills/practical.py: percent, paint, tiles, commute."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- percent
def test_percent_of():
    assert "20% of 80 = 16" in _ask("percent 20% of 80")


def test_percent_share():
    assert "20 is 25% of 80" in _ask("percent 20 of 80")


def test_percent_change():
    assert "25% increase" in _ask("percent 80 to 100")
    assert "20% decrease" in _ask("percent 100 to 80")
    assert "0% change" in _ask("percent 50 to 50")


def test_percent_up_down():
    assert "80 up 20% = 96" in _ask("percent 80 +20%")
    assert "80 down 25% = 60" in _ask("percent 80 -25%")


def test_percent_bad():
    assert "Usage" in _ask("percent")
    assert "Usage" in _ask("percent 80")
    assert "Couldn't read" in _ask("percent abc of 80")
    assert "must not be 0" in _ask("percent 20% of 0")
    assert "from 0" in _ask("percent 0 to 100")


# ---------------------------------------------------------------- paint
def test_paint_room():
    # 4x5 room, 2.4m walls: 2*(4+5)*2.4 = 43.2 m², 1 coat at 10 m²/L = 4.32 L -> 5 L
    out = _ask("paint 4x5 2.4")
    assert "43.2 m²" in out and "buy 5 L" in out


def test_paint_area_coats():
    # 43 m², 2 coats at 10 m²/L = 8.6 L -> 9 L
    out = _ask("paint 43sqm 2")
    assert "buy 9 L" in out
    # custom coverage: 20 m², 1 coat at 5 m²/L = 4 L exactly
    out = _ask("paint 20sqm 1 5")
    assert "buy 4 L" in out


def test_paint_bad():
    assert "Usage" in _ask("paint")
    assert "Usage" in _ask("paint 4x5")
    assert "Usage" in _ask("paint abc")
    assert "whole number" in _ask("paint 43sqm 1.5")
    assert "positive" in _ask("paint 43sqm 1 0")


# ---------------------------------------------------------------- tiles
def test_tiles_area():
    # 12 m², 30x30cm tiles (0.09 m²): 134 tiles, +10% -> 148
    out = _ask("tiles 12sqm 30x30cm")
    assert "134 tiles" in out and "148 tiles" in out


def test_tiles_room_custom_waste():
    # 4x5m = 20 m², 60x60cm tiles (0.36 m²): 56 tiles, +15% -> 65
    out = _ask("tiles 4x5m 60x60cm 15%")
    assert "56 tiles" in out and "65 tiles" in out


def test_tiles_bad():
    assert "Usage" in _ask("tiles")
    assert "Usage" in _ask("tiles 12sqm")
    assert "Usage" in _ask("tiles 12sqm 30cm")
    assert "0% or more" in _ask("tiles 12sqm 30x30cm -5%")


# ---------------------------------------------------------------- commute
def test_commute_km():
    out = _ask("commute 25km 50")
    assert "25 km at 50 km/h takes 30 min" in out


def test_commute_miles_depart():
    out = _ask("commute 30mi 60 08:30")
    assert "30 mi at 60 mph takes 30 min" in out
    assert "Depart 08:30 → arrive 09:00" in out


def test_commute_hours_format():
    out = _ask("commute 100km 40")
    assert "takes 2h 30m" in out


def test_commute_bad():
    assert "Usage" in _ask("commute")
    assert "Usage" in _ask("commute 25km")
    assert "greater than 0" in _ask("commute 0km 50")
    assert "greater than 0" in _ask("commute 25km 0")
    assert "HH:MM" in _ask("commute 25km 50 25:00")
