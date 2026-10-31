"""Tests for skills/build.py: insulation, drywall, gutter, roof."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- insulation
def test_insulation_metric():
    # 50 m² / 10 m² per roll = 5, +10% = 5.5 -> 6 rolls
    out = _ask("insulation 50sqm")
    assert "buy 6 rolls" in out and "55 m²" in out


def test_insulation_imperial_and_explicit():
    # 1000 sq ft / 100 sq ft per roll = 10, +10% = 11 rolls
    out = _ask("insulation 1000sqft")
    assert "buy 11 rolls" in out
    # Explicit coverage + 0% waste: 50 m² / 7.5 m² = 6.67 -> 7 rolls
    out = _ask("insulation 50sqm 7.5m2 0%")
    assert "buy 7 rolls" in out


def test_insulation_area_form():
    # 10 x 5 m = 50 m² -> 6 rolls, same as the sqm form
    out = _ask("insulation 10x5m")
    assert "buy 6 rolls" in out


def test_insulation_bad():
    assert "Usage" in _ask("insulation")
    assert "Usage" in _ask("insulation 50")
    assert "Usage" in _ask("insulation 50sqm 10cm")  # coverage needs an area unit
    assert "greater than 0" in _ask("insulation 0sqm")
    assert "0% or more" in _ask("insulation 50sqm -5%")


# ---------------------------------------------------------------- drywall
def test_drywall_metric():
    # Perimeter 2*(4+5) = 18 m x 2.4 m = 43.2 m² / 2.88 m² per sheet
    # = 15, +10% = 16.5 -> 17 sheets
    out = _ask("drywall 4x5m 2.4m")
    assert "buy 17 sheets" in out and "43.2 m²" in out


def test_drywall_imperial():
    # Perimeter 2*(12+16) = 56 ft x 8 ft = 448 sq ft / 32 sq ft
    # per sheet = 14, +10% = 15.4 -> 16 sheets
    out = _ask("drywall 12x16ft 8ft")
    assert "buy 16 sheets" in out and "448 sq ft" in out


def test_drywall_no_waste():
    # 0% waste: exactly 15 sheets
    out = _ask("drywall 4x5m 2.4m 0%")
    assert "buy 15 sheets" in out


def test_drywall_bad():
    assert "Usage" in _ask("drywall")
    assert "Usage" in _ask("drywall 4x5m")
    assert "Usage" in _ask("drywall 4x5m 2.4ft")  # metric room needs m height
    assert "greater than 0" in _ask("drywall 0x5m 2.4m")
    assert "0% or more" in _ask("drywall 4x5m 2.4m -5%")


# ---------------------------------------------------------------- gutter
def test_gutter_metric():
    # 30 m: 3 m sections -> 10; downspouts every 10 m -> 3;
    # hangers every 0.6 m -> 50; 2 end caps
    out = _ask("gutter 30m")
    assert "10 sections" in out and "3 downspouts" in out
    assert "50 hangers" in out and "2 end caps" in out


def test_gutter_imperial():
    # 100 ft: 10 ft sections -> 10; downspouts every 30 ft -> 4;
    # hangers every 2 ft -> 50; 2 end caps
    out = _ask("gutter 100ft")
    assert "10 sections" in out and "4 downspouts" in out
    assert "50 hangers" in out and "2 end caps" in out


def test_gutter_explicit_spacing():
    # 25 m, downspout every 5 m -> 5 downspouts
    out = _ask("gutter 25m 5m")
    assert "5 downspouts" in out


def test_gutter_bad():
    assert "Usage" in _ask("gutter")
    assert "Usage" in _ask("gutter 30")
    assert "Usage" in _ask("gutter 30m 10ft")  # metric run needs m spacing
    assert "greater than 0" in _ask("gutter 0m")


# ---------------------------------------------------------------- roof
def test_roof_flat_metric():
    # 10 x 8 m = 80 m² flat, / 9.29 m² per square = 8.61 squares,
    # x 3 bundles = 25.84, +10% = 28.42 -> 29 bundles
    out = _ask("roof 10x8m")
    assert "buy 29 bundles" in out and "8.61 squares" in out


def test_roof_pitched_imperial():
    # 30 x 40 ft = 1200 sq ft x sqrt(1 + 0.5²) = 1341.64 sq ft,
    # / 100 = 13.42 squares, x 3 = 40.25, +10% = 44.28 -> 45 bundles
    out = _ask("roof 30x40ft 6/12")
    assert "buy 45 bundles" in out and "13.42 squares" in out


def test_roof_pitched_metric():
    # 80 m² x sqrt(1.25) = 89.44 m², / 9.29 = 9.63 squares,
    # x 3 = 28.88, +10% = 31.77 -> 32 bundles
    out = _ask("roof 10x8m 6/12")
    assert "buy 32 bundles" in out and "89.44 m²" in out


def test_roof_bad():
    assert "Usage" in _ask("roof")
    assert "Usage" in _ask("roof 10x8m 6")  # pitch needs rise/run form
    assert "Usage" in _ask("roof 10x8")
    assert "greater than 0" in _ask("roof 0x8m")
    assert "0% or more" in _ask("roof 10x8m 6/12 -5%")
