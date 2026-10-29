"""Tests for skills/diy.py: concrete, mulch, wallpaper, sod."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- concrete
def test_concrete_metric():
    # 4x5 m slab, 10 cm deep: 20 m² × 0.1 = 2 m³, +10% = 2.2 m³,
    # 80 lb bags at ~0.017 m³ each -> 130 bags
    out = _ask("concrete 4x5m 10cm")
    assert "2 m³" in out and "2.2 m³" in out and "130" in out


def test_concrete_area_no_waste():
    # 20 m² × 0.1 = 2 m³, 0% waste -> 118 bags
    out = _ask("concrete 20sqm 10cm 0%")
    assert "buy 118" in out


def test_concrete_imperial():
    # 10x10 ft, 4 in deep: 100 × 4/12 = 33.33 cu ft (1.23 cu yd),
    # +10% = 36.67 cu ft -> 62 bags
    out = _ask("concrete 10x10ft 4in")
    assert "33.33 cu ft" in out and "1.23 cu yd" in out and "buy 62" in out


def test_concrete_bad():
    assert "Usage" in _ask("concrete")
    assert "Usage" in _ask("concrete 4x5m")
    assert "Usage" in _ask("concrete 4x5m 10in")  # metric area needs cm depth
    assert "Usage" in _ask("concrete 10x10ft 10cm")  # imperial area needs in depth
    assert "0% or more" in _ask("concrete 4x5m 10cm -5%")
    assert "greater than 0" in _ask("concrete 0sqm 10cm")


# ---------------------------------------------------------------- mulch
def test_mulch_metric():
    # 10 m² × 0.08 = 0.8 m³, +5% = 0.84 m³ (1.1 cu yd),
    # 0.84 m³ = 29.66 cu ft -> 15 × 2 cu ft bags
    out = _ask("mulch 10sqm 8cm")
    assert "0.8 m³" in out and "0.84 m³" in out and "1.1 cu yd" in out
    assert "buy 15" in out


def test_mulch_imperial():
    # 100 sq ft × 3/12 = 25 cu ft, +5% = 26.25 cu ft (0.97 cu yd)
    # -> 14 × 2 cu ft bags
    out = _ask("mulch 100sqft 3in")
    assert "25 cu ft" in out and "26.25 cu ft" in out and "buy 14" in out


def test_mulch_room_form():
    out = _ask("mulch 4x5m 10cm")
    assert "20 m²" in out and "2 m³" in out


def test_mulch_bad():
    assert "Usage" in _ask("mulch")
    assert "Usage" in _ask("mulch abc")
    assert "greater than 0" in _ask("mulch 10sqm 0cm")


# ---------------------------------------------------------------- wallpaper
def test_wallpaper_plain():
    # 4x5 room: 18 m around, 0.53 m rolls -> 34 drops;
    # 10.05 / 2.4 = 4 drops per roll -> 9 rolls
    out = _ask("wallpaper 4x5 2.4")
    assert "18 m around" in out and "34 drops" in out and "buy 9 rolls" in out


def test_wallpaper_repeat():
    # 32 cm repeat: drops are 2.72 m, so 3 per roll -> 12 rolls
    out = _ask("wallpaper 4x5 2.4 32")
    assert "32 cm repeat" in out and "buy 12 rolls" in out


def test_wallpaper_bad():
    assert "Usage" in _ask("wallpaper")
    assert "Usage" in _ask("wallpaper 4x5")
    assert "exceeds one roll length" in _ask("wallpaper 4x5 12")
    assert "greater than 0" in _ask("wallpaper 0x5 2.4")


# ---------------------------------------------------------------- sod
def test_sod_metric():
    # 50 m² + 5% = 52.5 m²; rolls are 0.929 m² -> 57 rolls, 2 pallets
    out = _ask("sod 50sqm")
    assert "52.5 m²" in out and "57 rolls" in out and "2 pallets" in out


def test_sod_imperial():
    # 1000 sq ft + 5% = 1050 sq ft; 10 sq ft rolls -> 105 rolls, 3 pallets
    out = _ask("sod 1000sqft")
    assert "1,050 sq ft" in out and "105 rolls" in out and "3 pallets" in out


def test_sod_room_no_waste():
    # 10x10 ft = 100 sq ft, 0% waste -> 10 rolls, 1 pallet (singular)
    out = _ask("sod 10x10ft 0%")
    assert "10 rolls" in out and "1 pallet." in out


def test_sod_bad():
    assert "Usage" in _ask("sod")
    assert "Usage" in _ask("sod abc")
    assert "greater than 0" in _ask("sod 0sqm")
    assert "0% or more" in _ask("sod 50sqm -5%")
