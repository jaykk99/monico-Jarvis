"""Tests for skills/weather.py: windchill, heatindex, dewpoint, humidex."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- windchill
def test_windchill_winnipeg_winter():
    # Environment Canada wind chill for -15 C at 30 km/h is about -26 C.
    out = _ask("windchill -15C 30kmh")
    assert "Wind chill -26 C (-14.8 F)" in out
    assert "at -15 C with a 30 km/h wind" in out
    assert "no immediate frostbite risk" in out
    # The wind-chill alias routes to the same skill
    out = _ask("wind-chill -15C 30kmh")
    assert "Wind chill -26 C" in out


def test_windchill_imperial():
    # 5 F (-15 C) at 20 mph (32 km/h) is about -26 C wind chill.
    out = _ask("windchill 5F 20mph")
    assert "Wind chill -26.4 C (-15.5 F)" in out
    assert "at 5 F with a 20 mph wind" in out


def test_windchill_frostbite_bands():
    # -40 C at 50 km/h is well past the -48 wind-chill line: under 5 min.
    out = _ask("windchill -40C 50kmh")
    assert "Wind chill -62.7 C (-80.9 F)" in out
    assert "under 5 minutes" in out
    # -25 C at 20 km/h lands in the 10-30 minute band (-28 to -39).
    out = _ask("windchill -25C 20kmh")
    assert "10-30 minutes" in out


def test_windchill_out_of_range():
    assert "too warm" in _ask("windchill 15C 30kmh")
    assert "too warm" in _ask("windchill 60F 20mph")
    assert "near calm" in _ask("windchill -5C 2kmh")
    assert "near calm" in _ask("windchill -5C 0kmh")


def test_windchill_bad():
    assert "Usage" in _ask("windchill")
    assert "Usage" in _ask("windchill -15C")  # needs wind speed too
    assert "Usage" in _ask("windchill abc 30kmh")
    assert "Usage" in _ask("windchill -15C fast")
    assert "Usage" in _ask("windchill -15C 30kmh extra")


# ---------------------------------------------------------------- heatindex
def test_heatindex_metric():
    # 32 C / 70% RH is about 40 C on the Rothfusz heat index (NWS: 90 F
    # at 70% is ~106 F).
    out = _ask("heatindex 32C 70%")
    assert "Heat index 40.4 C (104.7 F)" in out
    assert "Danger" in out
    assert "full sun can add up to 8 C" in out


def test_heatindex_imperial():
    # 90 F / 65% RH is about 103 F — extreme caution band.
    out = _ask("heatindex 90F 65%")
    assert "Heat index 39.3 C (102.7 F)" in out
    assert "Extreme caution" in out


def test_heatindex_extreme():
    # 38 C / 80% RH is far past the danger line.
    out = _ask("heatindex 38C 80%")
    assert "Heat index 71.3 C (160.3 F)" in out
    assert "Extreme danger" in out


def test_heatindex_out_of_range():
    assert "too cool" in _ask("heatindex 20C 70%")
    assert "too cool" in _ask("heatindex 75F 60%")
    assert "too dry" in _ask("heatindex 30C 30%")
    assert "too dry" in _ask("heatindex 32C 39%")


def test_heatindex_bad():
    assert "Usage" in _ask("heatindex")
    assert "Usage" in _ask("heatindex 32C")
    assert "Usage" in _ask("heatindex hot 70%")
    assert "Usage" in _ask("heatindex 32C 150%")  # humidity over 100
    assert "Usage" in _ask("heatindex 32C 0%")  # humidity of zero
    # The heat-index alias routes to the same skill
    assert "Heat index 40.4 C" in _ask("heat-index 32C 70%")


# ---------------------------------------------------------------- dewpoint
def test_dewpoint_metric():
    # 25 C / 60% RH gives a 16.7 C dew point (standard Magnus result).
    out = _ask("dewpoint 25C 60%")
    assert "Dew point 16.7 C (62.1 F)" in out
    assert "a little sticky" in out


def test_dewpoint_imperial():
    # 77 F (25 C) / 50% RH gives a 13.8 C dew point.
    out = _ask("dewpoint 77F 50%")
    assert "Dew point 13.8 C (56.8 F)" in out
    assert "comfortable for most people" in out


def test_dewpoint_dry_and_frost():
    out = _ask("dewpoint 20C 30%")
    assert "Dew point 1.9 C (35.4 F)" in out
    assert "dry and comfortable" in out
    # Sub-freezing dew point warns about frost.
    out = _ask("dewpoint -5C 80%")
    assert "Dew point -7.9 C (17.8 F)" in out
    assert "frost can form" in out


def test_dewpoint_bad():
    assert "Usage" in _ask("dewpoint")
    assert "Usage" in _ask("dewpoint 25C")
    assert "Usage" in _ask("dewpoint 25C wet")
    assert "Usage" in _ask("dewpoint 25C 101%")


# ---------------------------------------------------------------- humidex
def test_humidex_metric():
    # 30 C / 60% RH: dew point 21.4 C, humidex 38.6 (some discomfort).
    out = _ask("humidex 30C 60%")
    assert "Humidex 38.6" in out
    assert "dew point 21.4 C (70.5 F)" in out
    assert "Some discomfort" in out


def test_humidex_imperial():
    # 86 F (30 C) / 50% RH: humidex 36.2.
    out = _ask("humidex 86F 50%")
    assert "Humidex 36.2" in out
    assert "dew point 18.4 C (65.1 F)" in out


def test_humidex_bands():
    out = _ask("humidex 20C 50%")
    assert "Humidex 20.9" in out
    assert "Comfortable" in out
    out = _ask("humidex 40C 70%")
    assert "Humidex 63" in out
    assert "Dangerous" in out


def test_humidex_bad():
    assert "Usage" in _ask("humidex")
    assert "Usage" in _ask("humidex 30C")
    assert "Usage" in _ask("humidex warm 60%")
    assert "Usage" in _ask("humidex 30C 0%")


# ---------------------------------------------------------------- registry
def test_weather_skills_registered():
    names = {s["name"] for s in agent.list_skills()}
    assert {"windchill", "heatindex", "dewpoint", "humidex"} <= names
    assert len(agent.list_skills()) == 114
    # The honest `weather` lookup fallback is untouched by the new math.
    out = _ask("weather")
    assert "needs a weather API key" in out
