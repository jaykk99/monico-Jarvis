"""Tests for skills/finish.py: trim, caulk, grout, adhesive."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- trim
def test_trim_metric():
    # 4 x 5 m room: perimeter 18 m, / 2.4 m = 7.5, +10% = 8.25 -> 9 pieces
    out = _ask("trim 4x5m")
    assert "buy 9 pieces" in out and "18 m of trim" in out
    # Explicit piece + 0% waste: 18 / 3 = 6 pieces exactly
    out = _ask("trim 4x5m 3m 0%")
    assert "buy 6 pieces" in out
    # Waste without an explicit piece: 18 / 2.4 = 7.5, +0% -> 8 pieces
    out = _ask("trim 4x5m 0%")
    assert "buy 8 pieces" in out


def test_trim_imperial():
    # 12 x 16 ft room: perimeter 56 ft, / 8 ft = 7, +10% = 7.7 -> 8 pieces
    out = _ask("trim 12x16ft")
    assert "buy 8 pieces" in out and "56 ft of trim" in out
    # Explicit piece: 56 / 10 = 5.6, +10% = 6.16 -> 7 pieces
    out = _ask("trim 12x16ft 10ft")
    assert "buy 7 pieces" in out


def test_trim_bad():
    assert "Usage" in _ask("trim")
    assert "Usage" in _ask("trim 4x5")
    assert "Usage" in _ask("trim 4x5m 8ft")  # metric room takes metres, not feet
    assert "Usage" in _ask("trim 4x5m 10cm")
    assert "greater than 0" in _ask("trim 0x5m")
    assert "greater than 0" in _ask("trim 4x5m 0m")  # piece length
    assert "0% or more" in _ask("trim 4x5m -5%")


# ---------------------------------------------------------------- caulk
def test_caulk_metric():
    # 30 m / 9 m per tube = 3.33, +10% = 3.67 -> 4 tubes
    out = _ask("caulk 30m")
    assert "buy 4 tubes" in out and "33 m" in out
    # Explicit coverage + 0% waste: 18 / 9 = 2 tubes
    out = _ask("caulk 18m 9m 0%")
    assert "buy 2 tubes" in out
    # Waste without explicit coverage: 9 / 9 = 1, +0% -> 1 tube
    out = _ask("caulk 9m 0%")
    assert "buy 1 tubes" in out


def test_caulk_imperial():
    # 100 ft / 30 ft per tube = 3.33, +10% = 3.67 -> 4 tubes
    out = _ask("caulk 100ft")
    assert "buy 4 tubes" in out
    # Explicit coverage: 80 / 40 = 2, +10% = 2.2 -> 3 tubes
    out = _ask("caulk 80ft 40ft")
    assert "buy 3 tubes" in out


def test_caulk_bad():
    assert "Usage" in _ask("caulk")
    assert "Usage" in _ask("caulk 30")
    assert "Usage" in _ask("caulk 30m 30ft")  # metric run takes metres, not feet
    assert "Usage" in _ask("caulk 30m 10cm")
    assert "greater than 0" in _ask("caulk 0m")
    assert "greater than 0" in _ask("caulk 30m 0m")  # tube coverage
    assert "0% or more" in _ask("caulk 30m -5%")


# ---------------------------------------------------------------- grout
def test_grout_metric():
    # 20 m² / 10 m² per bag = 2, +10% = 2.2 -> 3 bags
    out = _ask("grout 20sqm")
    assert "buy 3 bags" in out and "22 m²" in out
    # 0% waste: 30 / 10 = 3 bags exactly
    out = _ask("grout 30sqm 0%")
    assert "buy 3 bags" in out


def test_grout_imperial_and_explicit():
    # 200 sq ft / 100 sq ft per bag = 2, +10% = 2.2 -> 3 bags
    out = _ask("grout 200sqft")
    assert "buy 3 bags" in out
    # Explicit coverage + 0% waste: 100 / 50 = 2 bags
    out = _ask("grout 100sqft 50sqft 0%")
    assert "buy 2 bags" in out


def test_grout_area_form():
    # 4 x 5 m = 20 m² -> 3 bags, same as the sqm form
    out = _ask("grout 4x5m")
    assert "buy 3 bags" in out


def test_grout_bad():
    assert "Usage" in _ask("grout")
    assert "Usage" in _ask("grout 20")
    assert "Usage" in _ask("grout 20sqm 10cm")
    assert "greater than 0" in _ask("grout 0sqm")
    assert "greater than 0" in _ask("grout 20sqm 0sqm")  # bag coverage
    assert "0% or more" in _ask("grout 20sqm -5%")


# ---------------------------------------------------------------- adhesive
def test_adhesive_metric():
    # 20 m² / 5 m² per bag = 4, +10% = 4.4 -> 5 bags
    out = _ask("adhesive 20sqm")
    assert "buy 5 bags" in out and "22 m²" in out
    # 0% waste: 25 / 5 = 5 bags exactly
    out = _ask("adhesive 25sqm 0%")
    assert "buy 5 bags" in out


def test_adhesive_imperial_and_explicit():
    # 100 sq ft / 50 sq ft per bag = 2, +10% = 2.2 -> 3 bags
    out = _ask("adhesive 100sqft")
    assert "buy 3 bags" in out
    # Explicit coverage + 0% waste: 50 / 25 = 2 bags
    out = _ask("adhesive 50sqft 25sqft 0%")
    assert "buy 2 bags" in out


def test_adhesive_area_form():
    # 4 x 5 m = 20 m² -> 5 bags, same as the sqm form
    out = _ask("adhesive 4x5m")
    assert "buy 5 bags" in out


def test_adhesive_bad():
    assert "Usage" in _ask("adhesive")
    assert "Usage" in _ask("adhesive 20")
    assert "Usage" in _ask("adhesive 20sqm 10cm")
    assert "greater than 0" in _ask("adhesive 0sqm")
    assert "greater than 0" in _ask("adhesive 20sqm 0sqm")  # bag coverage
    assert "0% or more" in _ask("adhesive 20sqm -5%")
