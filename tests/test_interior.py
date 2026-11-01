"""Tests for skills/interior.py: siding, floor, studs, brick."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- siding
def test_siding_metric():
    # 50 m² / 9.29 m² per square = 5.38, +10% = 5.92 -> 6 squares
    out = _ask("siding 50sqm")
    assert "buy 6 squares" in out and "55 m²" in out


def test_siding_imperial_and_explicit():
    # 1000 sq ft / 100 sq ft per square = 10, +10% = 11 squares
    out = _ask("siding 1000sqft")
    assert "buy 11 squares" in out
    # 0% waste: 929 sq ft / 100 = 9.29 -> 10 squares
    out = _ask("siding 929sqft 0%")
    assert "buy 10 squares" in out


def test_siding_area_form():
    # 10 x 5 m = 50 m² -> 6 squares, same as the sqm form
    out = _ask("siding 10x5m")
    assert "buy 6 squares" in out


def test_siding_bad():
    assert "Usage" in _ask("siding")
    assert "Usage" in _ask("siding 50")
    assert "Usage" in _ask("siding 50sqm 10cm")  # coverage is not an option here
    assert "greater than 0" in _ask("siding 0sqm")
    assert "0% or more" in _ask("siding 50sqm -5%")


# ---------------------------------------------------------------- floor
def test_floor_metric():
    # 20 m² / 2 m² per box = 10, +10% = 11 boxes
    out = _ask("floor 20sqm")
    assert "buy 11 boxes" in out and "22 m²" in out


def test_floor_imperial_and_explicit():
    # 400 sq ft / 20 sq ft per box = 20, +10% = 22 boxes
    out = _ask("floor 400sqft")
    assert "buy 22 boxes" in out
    # Explicit coverage + 0% waste: 48 sq ft / 24 sq ft = 2 boxes
    out = _ask("floor 48sqft 24sqft 0%")
    assert "buy 2 boxes" in out


def test_floor_area_form():
    # 4 x 5 m = 20 m² -> 11 boxes, same as the sqm form
    out = _ask("floor 4x5m")
    assert "buy 11 boxes" in out


def test_floor_bad():
    assert "Usage" in _ask("floor")
    assert "Usage" in _ask("floor 20")
    assert "Usage" in _ask("floor 20sqm 10cm")  # coverage needs an area unit
    assert "greater than 0" in _ask("floor 0sqm")
    assert "greater than 0" in _ask("floor 20sqm 0sqm")  # box coverage
    assert "0% or more" in _ask("floor 20sqm -5%")


# ---------------------------------------------------------------- studs
def test_studs_metric():
    # 10 m / 0.4 m = 25 bays + 1 end stud = 26 studs
    out = _ask("studs 10m")
    assert "buy 26 studs" in out and "25 bays" in out
    # Explicit spacing: 10 m / 0.5 m = 20 bays + 1 = 21 studs
    out = _ask("studs 10m 0.5m")
    assert "buy 21 studs" in out


def test_studs_imperial():
    # 12 ft = 144 in / 16 in = 9 bays + 1 = 10 studs
    out = _ask("studs 12ft")
    assert "buy 10 studs" in out and "9 bays" in out
    # Explicit spacing: 144 in / 24 in = 6 bays + 1 = 7 studs
    out = _ask("studs 12ft 24in")
    assert "buy 7 studs" in out


def test_studs_bad():
    assert "Usage" in _ask("studs")
    assert "Usage" in _ask("studs 10")
    assert "Usage" in _ask("studs 10m 16in")  # metric run takes metres, not inches
    assert "Usage" in _ask("studs 12ft 0.4m")  # imperial run takes inches, not metres
    assert "greater than 0" in _ask("studs 0m")
    assert "greater than 0" in _ask("studs 10m 0m")


# ---------------------------------------------------------------- brick
def test_brick_metric():
    # 20 m² x 60 bricks = 1200, +10% = 1320 bricks
    out = _ask("brick 20sqm")
    assert "buy 1,320 bricks" in out


def test_brick_imperial_and_explicit():
    # 200 sq ft x 7 bricks = 1400, +10% = 1540 bricks
    out = _ask("brick 200sqft")
    assert "buy 1,540 bricks" in out
    # 0% waste: 10 m² x 60 = 600 bricks
    out = _ask("brick 10sqm 0%")
    assert "buy 600 bricks" in out


def test_brick_area_form():
    # 4 x 5 m = 20 m² -> 1,320 bricks, same as the sqm form
    out = _ask("brick 4x5m")
    assert "buy 1,320 bricks" in out


def test_brick_bad():
    assert "Usage" in _ask("brick")
    assert "Usage" in _ask("brick 20")
    assert "Usage" in _ask("brick 20sqm 10cm")
    assert "greater than 0" in _ask("brick 0sqm")
    assert "0% or more" in _ask("brick 20sqm -5%")
