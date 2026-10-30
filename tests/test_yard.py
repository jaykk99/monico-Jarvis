"""Tests for skills/yard.py: fence, gravel, firewood, deck."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- fence
def test_fence_metric():
    # 30 m run, 15 cm boards: 200 boards, +10% = 220; posts every
    # 2.4 m: floor(30/2.4)+1 = 13; rails 2 per span = 24
    out = _ask("fence 30m")
    assert "buy 220" in out and "13 posts" in out and "24 rails" in out


def test_fence_imperial():
    # 50 ft run, 6 in boards: 100 boards, +10% = 110; posts every
    # 8 ft: floor(50/8)+1 = 7; rails 2 per span = 12
    out = _ask("fence 50ft")
    assert "buy 110" in out and "7 posts" in out and "12 rails" in out


def test_fence_explicit_no_waste():
    # Explicit board/spacing, 0% waste: exactly 200 boards
    out = _ask("fence 30m 15cm 2.4m 0%")
    assert "buy 200" in out and "13 posts" in out


def test_fence_bad():
    assert "Usage" in _ask("fence")
    assert "Usage" in _ask("fence 30")
    assert "Usage" in _ask("fence 30m 15in")  # metric run needs cm board
    assert "greater than 0" in _ask("fence 0m")
    assert "0% or more" in _ask("fence 30m -5%")


# ---------------------------------------------------------------- gravel
def test_gravel_metric():
    # 10 m² × 0.1 m = 1 m³, +5% = 1.05 m³, × 1.5 t/m³ = 1.58 t
    out = _ask("gravel 10sqm 10cm")
    assert "1 m³" in out and "1.05 m³" in out and "1.58 tonnes" in out


def test_gravel_imperial():
    # 200 sq ft × 4/12 ft = 66.67 cu ft = 2.47 cu yd, +5% = 2.59 cu yd,
    # × 1.4 tons/cu yd = 3.63 short tons
    out = _ask("gravel 10x20ft 4in")
    assert "66.67 cu ft" in out and "2.59 cu yd" in out and "3.63 short tons" in out


def test_gravel_bad():
    assert "Usage" in _ask("gravel")
    assert "Usage" in _ask("gravel 10sqm 10in")  # metric area needs cm depth
    assert "Usage" in _ask("gravel 10x20ft 4cm")  # imperial area needs in depth
    assert "greater than 0" in _ask("gravel 10sqm 0cm")
    assert "0% or more" in _ask("gravel 10sqm 10cm -5%")


# ---------------------------------------------------------------- firewood
def test_firewood_imperial():
    # 4 × 8 ft stack, 16 in logs: 42.67 cu ft = 0.33 cords = 1 face cord
    out = _ask("firewood 4x8ft 16in")
    assert "42.67 cu ft" in out and "0.33 full cords" in out and "1 face cord" in out


def test_firewood_metric():
    # 2.4 × 1.2 m stack, 40 cm logs: 1.15 m³ / 3.62 = 0.32 cords
    out = _ask("firewood 2.4x1.2m 40cm")
    assert "1.15 m³" in out and "0.32 full cords" in out


def test_firewood_bad():
    assert "Usage" in _ask("firewood")
    assert "Usage" in _ask("firewood 4x8ft")
    assert "Usage" in _ask("firewood 4x8ft 16")  # log length needs a unit
    assert "Usage" in _ask("firewood 4x8ft 40cm")  # imperial stack needs in logs
    assert "greater than 0" in _ask("firewood 0x8ft 16in")


# ---------------------------------------------------------------- deck
def test_deck_metric():
    # 5 m width / 14 cm boards = 35.71 -> 36, +10% = 40 boards of 4 m
    out = _ask("deck 4x5m 14cm")
    assert "buy 40 boards" in out and "160 m total" in out


def test_deck_imperial():
    # 16 ft width = 192 in / 5.5 in = 34.91 -> 35, +10% = 39 boards of 12 ft
    out = _ask("deck 12x16ft 5.5in")
    assert "buy 39 boards" in out and "468 ft total" in out


def test_deck_no_waste():
    # 0% waste: exactly 36 boards, 144 m total
    out = _ask("deck 4x5m 14cm 0%")
    assert "buy 36 boards" in out and "144 m total" in out


def test_deck_bad():
    assert "Usage" in _ask("deck")
    assert "Usage" in _ask("deck 4x5m")
    assert "Usage" in _ask("deck 4x5m 14in")  # metric deck needs cm boards
    assert "greater than 0" in _ask("deck 0x5m 14cm")
    assert "0% or more" in _ask("deck 4x5m 14cm -5%")
