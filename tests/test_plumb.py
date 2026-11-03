"""Tests for skills/plumb.py: pipe, slope, tank, fill."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- pipe
def test_pipe_metric():
    # 30 m run, / 3 m = 10, +10% = 11 lengths exactly
    out = _ask("pipe 30m")
    assert "buy 11 lengths" in out and "33 m" in out
    # Explicit piece + 0% waste: 30 / 6 = 5 lengths exactly
    out = _ask("pipe 30m 6m 0%")
    assert "buy 5 lengths" in out
    # Waste without an explicit piece: 30 / 3 = 10, +0% -> 10 lengths
    out = _ask("pipe 30m 0%")
    assert "buy 10 lengths" in out


def test_pipe_imperial():
    # 100 ft run, / 10 ft = 10, +10% = 11 lengths
    out = _ask("pipe 100ft")
    assert "buy 11 lengths" in out and "110 ft" in out
    # Explicit piece: 100 / 20 = 5, +10% = 5.5 -> 6 lengths
    out = _ask("pipe 100ft 20ft")
    assert "buy 6 lengths" in out


def test_pipe_bad():
    assert "Usage" in _ask("pipe")
    assert "Usage" in _ask("pipe 30")
    assert "Usage" in _ask("pipe 30m 10ft")  # metric run takes metres, not feet
    assert "greater than 0" in _ask("pipe 0m")
    assert "greater than 0" in _ask("pipe 30m 0m")  # pipe length
    assert "0% or more" in _ask("pipe 30m -5%")


# ---------------------------------------------------------------- slope
def test_slope_metric():
    # 10 m at default 2%: 20 cm drop
    out = _ask("slope 10m")
    assert "drop 20 cm" in out and "2% grade" in out
    # Explicit grade: 10 m at 1% = 10 cm
    out = _ask("slope 10m 1%")
    assert "drop 10 cm" in out


def test_slope_imperial():
    # 40 ft at default 1/4 in per ft: 10 in drop
    out = _ask("slope 40ft")
    assert "drop 10 in" in out and "0.25 in per ft" in out
    # Explicit grade: 40 ft at 0.5 in per ft = 20 in
    out = _ask("slope 40ft 0.5in")
    assert "drop 20 in" in out


def test_slope_bad():
    assert "Usage" in _ask("slope")
    assert "Usage" in _ask("slope 10")
    assert "Usage" in _ask("slope 10m abc")
    assert "greater than 0" in _ask("slope 0m")
    assert "greater than 0" in _ask("slope 10m 0%")


# ---------------------------------------------------------------- tank
def test_tank_metric():
    # 2 x 1 x 1 m = 2 m3 = 2,000 litres = 528.34 US gallons
    out = _ask("tank 2x1x1m")
    assert "2 m³" in out and "2,000 litres" in out and "528.34 US gallons" in out


def test_tank_imperial():
    # 4 x 3 x 2 ft = 24 cu ft = 179.53 US gallons
    out = _ask("tank 4x3x2ft")
    assert "24 cu ft" in out and "179.53 US gallons" in out


def test_tank_bad():
    assert "Usage" in _ask("tank")
    assert "Usage" in _ask("tank 2x1m")  # needs three dimensions
    assert "Usage" in _ask("tank 2x1x1m extra")
    assert "greater than 0" in _ask("tank 0x1x1m")


# ---------------------------------------------------------------- fill
def test_fill_metric():
    out = _ask("fill 1000L 50L/min")
    assert "fills in 20 minutes" in out
    # 100 minutes formats as hours + minutes
    out = _ask("fill 5000L 50L/min")
    assert "1h 40m (100 minutes)" in out


def test_fill_imperial():
    out = _ask("fill 100gal 5gpm")
    assert "fills in 20 minutes" in out


def test_fill_bad():
    assert "Usage" in _ask("fill")
    assert "Usage" in _ask("fill 1000 50")
    assert "must match" in _ask("fill 1000L 5gpm")  # litres vs gpm
    assert "greater than 0" in _ask("fill 0L 50L/min")
    assert "greater than 0" in _ask("fill 1000L 0L/min")


# ---------------------------------------------------------------- no trigger collisions
def test_grade_skill_still_routes_to_grades():
    # `grade` was deliberately NOT added as a slope alias: the household
    # grade skill must keep owning that trigger.
    out = _ask("grade 90 0.3 80 0.7")
    assert "83.0 (B)" in out
