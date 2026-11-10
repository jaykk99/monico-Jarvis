"""Tests for skills/car.py: brake, tire, oil, tow."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- brake
def test_brake_dry_metric():
    # 100 km/h dry: 41.7 m reacting + 56.2 m braking = 97.8 m (321 ft).
    out = _ask("brake 100kmh dry")
    assert "Stopping from 100 km/h on dry asphalt: 97.8 m (321 ft)" in out
    assert "41.7 m (137 ft) reacting" in out
    assert "56.2 m (184 ft) braking" in out
    assert "21.7 car lengths" in out


def test_brake_default_is_dry():
    out = _ask("brake 50kmh")
    assert "Stopping from 50 km/h on dry asphalt: 34.9 m (114 ft)" in out
    assert "7.8 car lengths" in out


def test_brake_imperial_snow():
    # 60 mph (96.6 km/h) on snow: about 186.9 m total, 41.5 car lengths.
    out = _ask("brake 60mph snow")
    assert "Stopping from 60 mph on snow: 186.9 m (613 ft)" in out
    assert "41.5 car lengths" in out
    assert "quadruples" in out
    # The braking alias routes to the same skill
    out = _ask("braking 60mph snow")
    assert "186.9 m (613 ft)" in out


def test_brake_ice_and_wet():
    # 100 km/h on ice: about 434.9 m — seven times the dry distance.
    out = _ask("brake 100kmh ice")
    assert "434.9 m (1,427 ft)" in out
    assert "seven times" in out
    # 60 km/h wet: 25.0 m reacting + 35.4 m braking = 60.4 m.
    out = _ask("brake 60kmh wet")
    assert "60.4 m (198 ft)" in out
    assert "roughly double" in out


def test_brake_bad():
    assert "Usage" in _ask("brake")
    assert "Usage" in _ask("brake fast")
    assert "Usage" in _ask("brake 100kmh mud")
    assert "Usage" in _ask("brake 100kmh dry extra")
    assert "above 0" in _ask("brake 0kmh")
    assert "past any road car" in _ask("brake 400kmh")


# ---------------------------------------------------------------- tire
def test_tire_winter_warmup():
    # 32 psi set at -20 C reads 39.4 psi at 20 C (ideal gas law).
    out = _ask("tire 32psi -20C 20C")
    assert "set to 32 psi at -20 C rises to about 39.4 psi at 20 C" in out
    assert "(+7.4 psi)" in out
    assert "rule of thumb says about +7.1 psi" in out
    assert "check" in out and "cold" in out


def test_tire_metric_kpa():
    # 220 kPa set at -30 C reads about 286 kPa at 20 C.
    out = _ask("tire 220kpa -30C 20C")
    assert "set to 220 kPa at -30 C rises to about 286 kPa (41.5 psi) at 20 C" in out


def test_tire_cold_drop_and_bar():
    # 32 psi set at 20 C falls to 24.0 psi at -30 C.
    out = _ask("tire 32psi 20C -30C")
    assert "falls to about 24 psi at -30 C" in out
    assert "(-8.0 psi)" in out
    # Bar input comes back in bar with psi in brackets.
    out = _ask("tire 2.2bar 20C -20C")
    assert "1.76 bar (25.5 psi)" in out


def test_tire_no_change():
    out = _ask("tire 32psi 20C 20C")
    assert "reads about the same" in out
    assert "barely changes" in out


def test_tire_bad():
    assert "Usage" in _ask("tire")
    assert "Usage" in _ask("tire 32psi -20C")
    assert "Usage" in _ask("tire flat -20C 20C")
    assert "Usage" in _ask("tire 32psi warm 20C")
    assert "above 0" in _ask("tire 0psi -20C 20C")
    assert "past any road tire" in _ask("tire 200psi -20C 20C")
    assert "between -60 C and 60 C" in _ask("tire 32psi -70C 20C")


# ---------------------------------------------------------------- oil
def test_oil_km_only():
    out = _ask("oil 8000km 10000km")
    assert "8,000 km since the last change" in out
    assert "80% through the 10,000 km interval" in out
    assert "2,000 km left" in out
    assert "Not due yet" in out


def test_oil_due_soon():
    out = _ask("oil 9500km 10000km")
    assert "only 500 km left" in out
    assert "Almost due" in out


def test_oil_overdue():
    out = _ask("oil 12000km 10000km")
    assert "overdue by 2,000 km" in out
    assert "Time for an oil change" in out


def test_oil_with_months():
    out = _ask("oil 8000km 10000km 5mo 6mo")
    assert "2,000 km left" in out
    assert "only 1 month(s) left on time" in out
    assert "Almost due" in out
    out = _ask("oil 8000km 10000km 7mo 6mo")
    assert "overdue by 1 month(s) on time" in out
    assert "Time for an oil change" in out


def test_oil_bad():
    assert "Usage" in _ask("oil")
    assert "Usage" in _ask("oil 8000km")
    assert "Usage" in _ask("oil 8000km 10000km 5mo")
    assert "Usage" in _ask("oil soon 10000km")
    assert "can't be negative" in _ask("oil -100km 10000km")
    assert "above 0" in _ask("oil 8000km 0km")


# ---------------------------------------------------------------- tow
def test_tow_within_rating():
    out = _ask("tow 1500kg 2000kg")
    assert "1,500 kg (3,307 lb) trailer against a 2,000 kg (4,409 lb) tow rating" in out
    assert "75% of the rating" in out
    assert "500 kg (1,102 lb) to spare" in out
    assert "Tongue weight at 12% is 180 kg (397 lb)" in out
    assert "safe 10-15% range" in out
    assert "own brakes" in out  # over 910 kg, trailer brakes note


def test_tow_imperial():
    # 5,000 lb trailer vs 7,000 lb rating: 71%, 2,000 lb margin.
    out = _ask("tow 5000lb 7000lb 12")
    assert "2,268 kg (5,000 lb) trailer against a 3,175 kg (7,000 lb) tow rating" in out
    assert "71% of the rating" in out
    assert "907 kg (2,000 lb) to spare" in out
    assert "Tongue weight at 12% is 272 kg (600 lb)" in out


def test_tow_over_and_close():
    out = _ask("tow 2500kg 2000kg")
    assert "OVER the tow rating by 500 kg (1,102 lb)" in out
    assert "do not tow this" in out
    out = _ask("tow 1900kg 2000kg")
    assert "only 100 kg (220 lb) of headroom left" in out


def test_tow_tongue_notes():
    out = _ask("tow 1500kg 2000kg 8")
    assert "under 10% the trailer can sway" in out
    out = _ask("tow 1500kg 2000kg 20")
    assert "over 15% overloads the rear axle" in out
    # No brakes note for a light trailer.
    out = _ask("tow 500kg 2000kg")
    assert "own brakes" not in out


def test_tow_bad():
    assert "Usage" in _ask("tow")
    assert "Usage" in _ask("tow 1500kg")
    assert "Usage" in _ask("tow heavy 2000kg")
    assert "Usage" in _ask("tow 1500kg 2000kg 12 13")
    assert "above 0" in _ask("tow 0kg 2000kg")
    assert "5-25%" in _ask("tow 1500kg 2000kg 3")
    assert "5-25%" in _ask("tow 1500kg 2000kg 30")


# ---------------------------------------------------------------- registry
def test_car_skills_registered():
    names = {s["name"] for s in agent.list_skills()}
    assert {"brake", "tire", "oil", "tow"} <= names
    assert len(agent.list_skills()) == 114
