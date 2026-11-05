"""Tests for skills/garden.py: soil, seed, planter, spacing."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- soil
def test_soil_metric():
    # 4 x 2 m at 15 cm = 1.2 m3; +10% waste = 1.32 m3 = 1,320 L / 40 L = 33 bags
    out = _ask("soil 4x2m 15cm")
    assert "1.2 m³" in out and "1.32 m³" in out and "1,320 L" in out
    assert "buy 33 bags" in out
    # Area form works, and waste can be set to 0%
    out = _ask("soil 10sqm 10cm 0%")
    assert "1 m³" in out and "1,000 L" in out and "buy 25 bags" in out
    # The topsoil alias routes to the same skill
    out = _ask("topsoil 4x2m 15cm")
    assert "buy 33 bags" in out


def test_soil_imperial():
    # 12 x 6 ft at 6 in = 36 cu ft = 1.33 cu yd; +10% = 1.47 cu yd;
    # 39.6 cu ft / 1.5 cu ft bags = 26.4 -> 27 bags
    out = _ask("soil 12x6ft 6in")
    assert "36 cu ft" in out and "1.33 cu yd" in out
    assert "1.47 cu yd" in out and "buy 27 bags" in out


def test_soil_bad():
    assert "Usage" in _ask("soil")
    assert "Usage" in _ask("soil 4x2m")  # needs a depth
    assert "Usage" in _ask("soil 4x2m 15in")  # metric run needs cm depth
    assert "Waste must be 0% or more" in _ask("soil 4x2m 15cm abc")
    assert "greater than 0" in _ask("soil 0x2m 15cm")
    assert "greater than 0" in _ask("soil 4x2m 0cm")
    assert "Waste must be 0% or more" in _ask("soil 4x2m 15cm -5%")


# ---------------------------------------------------------------- seed
def test_seed_metric():
    # 100 m2 at the 35 g/m2 default = 3,500 g = 3.5 kg
    out = _ask("seed 100sqm")
    assert "3,500 g" in out and "3.5 kg" in out
    # An explicit rate overrides the default
    out = _ask("seed 100sqm 50")
    assert "5,000 g" in out and "5 kg" in out
    # The grass alias routes to the same skill
    out = _ask("grass 100sqm")
    assert "3,500 g" in out


def test_seed_imperial():
    # 5,000 sq ft at 7 lb per 1,000 sq ft = 35 lb
    out = _ask("seed 5000sqft")
    assert "35 lb of seed" in out
    out = _ask("seed 2000sqft 10")
    assert "20 lb of seed" in out


def test_seed_bad():
    assert "Usage" in _ask("seed")
    assert "Usage" in _ask("seed 100")  # needs an area unit
    assert "Usage" in _ask("seed 100sqm abc")
    assert "greater than 0" in _ask("seed 0sqm")
    assert "greater than 0" in _ask("seed 100sqm 0")


# ---------------------------------------------------------------- planter
def test_planter_rectangular():
    # 60 x 30 x 30 cm = 54,000 cm3 = 54 L / 40 L = 1.35 -> 2 bags
    out = _ask("planter 60x30x30cm")
    assert "54 L of soil" in out and "buy 2 bags" in out
    # 24 x 12 x 12 in = 2 cu ft (14.96 US gal) / 1.5 cu ft = 1.33 -> 2 bags
    out = _ask("planter 24x12x12in")
    assert "2 cu ft" in out and "14.96 US gallons" in out
    assert "buy 2 bags" in out


def test_planter_round():
    # Round 30 cm across, 25 cm deep = pi x 15^2 x 25 = 17.67 L -> 1 bag
    out = _ask("planter round 30cm 25cm")
    assert "17.67 L of soil" in out and "buy 1 bag" in out
    # Round 12 in across, 10 in deep = 0.65 cu ft (4.9 US gal) -> 1 bag
    out = _ask("planter round 12in 10in")
    assert "0.65 cu ft" in out and "4.9 US gallons" in out
    assert "buy 1 bag" in out
    # The pot alias routes to the same skill
    out = _ask("pot 60x30x30cm")
    assert "54 L of soil" in out


def test_planter_bad():
    assert "Usage" in _ask("planter")
    assert "Usage" in _ask("planter 60x30cm")  # needs three dimensions
    assert "Usage" in _ask("planter round 30cm")  # round needs diameter + depth
    assert "Usage" in _ask("planter round 30in 25cm")  # mixed units
    assert "Usage" in _ask("planter 60x30x30")  # needs a unit
    assert "greater than 0" in _ask("planter 0x30x30cm")
    assert "greater than 0" in _ask("planter round 0cm 25cm")


# ---------------------------------------------------------------- spacing
def test_spacing_metric():
    # 4 x 2 m at 30 cm: floor(400/30)+1 = 14 along, floor(200/30)+1 = 7
    # across -> 98 plants
    out = _ask("spacing 4x2m 30cm")
    assert "14 along the length" in out and "7 across" in out
    assert "= 98 plants" in out


def test_spacing_imperial():
    # 12 x 6 ft at 12 in: 13 along, 7 across -> 91 plants
    out = _ask("spacing 12x6ft 12in")
    assert "13 along the length" in out and "7 across" in out
    assert "= 91 plants" in out
    # The plants alias routes to the same skill
    out = _ask("plants 4x2m 30cm")
    assert "= 98 plants" in out


def test_spacing_bad():
    assert "Usage" in _ask("spacing")
    assert "Usage" in _ask("spacing 4x2m")  # needs a spacing
    assert "Usage" in _ask("spacing 4x2m 30in")  # metric run needs cm spacing
    assert "Usage" in _ask("spacing 4x2 30cm")  # bed needs a unit
    assert "greater than 0" in _ask("spacing 0x2m 30cm")
    assert "greater than 0" in _ask("spacing 4x2m 0cm")


# ---------------------------------------------------------------- no trigger collisions
def test_no_existing_skill_lost_its_trigger():
    # `mulch` (diy) and `gravel` (yard) are the nearest neighbours;
    # both must keep owning their own triggers.
    out = _ask("mulch 10sqm 10cm")
    assert "1.05 m³" in out and "bags" in out
    out = _ask("gravel 10sqm 10cm")
    assert "1.58 tonnes" in out
