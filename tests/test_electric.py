"""Tests for skills/electric.py: watts, circuit, bulb, runtime."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- watts
def test_watts_all_three_forms():
    # 120 V x 10 A = 1,200 W
    out = _ask("watts 120V 10A")
    assert "1,200 W" in out
    # 1,200 W at 120 V = 10 A
    out = _ask("watts 1200W 120V")
    assert "10 A" in out
    # 1,200 W at 10 A = 120 V
    out = _ask("watts 1200W 10A")
    assert "120 V" in out
    # Order of the two inputs does not matter
    out = _ask("watts 10A 120V")
    assert "1,200 W" in out


def test_watts_bad():
    assert "Usage" in _ask("watts")
    assert "Usage" in _ask("watts 120V")
    assert "Usage" in _ask("watts 120V 120V")  # duplicate unit
    assert "Usage" in _ask("watts 120 10")  # bare numbers, no units
    assert "greater than 0" in _ask("watts 0V 10A")
    assert "greater than 0" in _ask("watts 1200W 0V")


# ---------------------------------------------------------------- circuit
def test_circuit_within_guideline():
    # 15 A x 120 V = 1,800 W, 80% = 1,440 W; load 1,200 W is within
    out = _ask("circuit 15A 120V 800 400")
    assert "1,800 W capacity" in out and "1,440 W at 80%" in out
    assert "1,200 W is within" in out


def test_circuit_over_guideline_and_over_rating():
    # 1,500 W on a 15 A / 120 V circuit: over 80%, under rating
    out = _ask("circuit 15A 120V 1500")
    assert "over the 80% continuous guideline but under" in out
    # 2,000 W: over the breaker rating itself
    out = _ask("circuit 15A 120V 2000")
    assert "over the breaker rating" in out
    # Loads may carry a W suffix, and a 20 A circuit scales up
    out = _ask("circuit 20A 120V 1500W")
    assert "2,400 W capacity" in out and "1,920 W at 80%" in out
    assert "within the 80%" in out


def test_circuit_bad():
    assert "Usage" in _ask("circuit")
    assert "Usage" in _ask("circuit 15A 120V")  # needs at least one load
    assert "Usage" in _ask("circuit 15 120V 800")  # breaker needs an A suffix
    assert "Usage" in _ask("circuit 15A 120V abc")
    assert "greater than 0" in _ask("circuit 0A 120V 800")
    assert "greater than 0" in _ask("circuit 15A 120V 0")


# ---------------------------------------------------------------- bulb
def test_bulb_metric():
    # 20 m2 x 200 lm/m2 = 4,000 lm / 800 lm = 5 bulbs exactly
    out = _ask("bulb 20sqm")
    assert "4,000 lumens" in out and "buy 5 bulbs" in out
    # Explicit bulb brightness: 4,000 / 1,600 = 2.5 -> 3 bulbs
    out = _ask("bulb 20sqm 1600")
    assert "buy 3 bulbs" in out


def test_bulb_imperial():
    # 200 sq ft x 20 lm/sq ft = 4,000 lm / 800 lm = 5 bulbs
    out = _ask("bulb 200sqft")
    assert "4,000 lumens" in out and "buy 5 bulbs" in out


def test_bulb_bad():
    assert "Usage" in _ask("bulb")
    assert "Usage" in _ask("bulb 20")  # needs an area unit
    assert "Usage" in _ask("bulb 20sqm abc")
    assert "greater than 0" in _ask("bulb 0sqm")
    assert "greater than 0" in _ask("bulb 20sqm 0")


# ---------------------------------------------------------------- runtime
def test_runtime_amp_hours():
    # 100 Ah x 12 V = 1,200 Wh / 50 W = 24h, ideal (no efficiency given)
    out = _ask("runtime 100Ah 12V 50W")
    assert "1,200 Wh" in out and "24h (1440 minutes)" in out
    assert "ideal" in out


def test_runtime_watt_hours_and_efficiency():
    # 500 Wh / 50 W = 10h ideal
    out = _ask("runtime 500Wh 50W")
    assert "500 Wh" in out and "10h (600 minutes)" in out
    # At 85%: 425 Wh usable / 50 W = 8.5h = 8h 30m
    out = _ask("runtime 500Wh 50W 85%")
    assert "425 Wh usable" in out and "8h 30m (510 minutes)" in out
    # Minutes are plain integers, matching the existing fill skill
    # Short runtime formats in minutes only
    out = _ask("runtime 100Wh 200W")
    assert "30 minutes" in out


def test_runtime_bad():
    assert "Usage" in _ask("runtime")
    assert "Usage" in _ask("runtime 100Ah 50W")  # amp-hours form needs volts
    assert "Usage" in _ask("runtime 500Wh")  # needs a load
    assert "Usage" in _ask("runtime 500Wh 50W 85% extra")
    assert "greater than 0" in _ask("runtime 0Ah 12V 50W")
    assert "greater than 0" in _ask("runtime 500Wh 0W")
    assert "between 1% and 100%" in _ask("runtime 500Wh 50W 150%")
    assert "between 1% and 100%" in _ask("runtime 500Wh 50W 0%")


# ---------------------------------------------------------------- no trigger collisions
def test_no_existing_skill_lost_its_trigger():
    # `power` is new; the finance loan skill and household grade skill
    # must keep owning their own triggers.
    out = _ask("loan 10000 5 12")
    assert "payment" in out.lower() or "$" in out
    out = _ask("grade 90 0.3 80 0.7")
    assert "83.0 (B)" in out
