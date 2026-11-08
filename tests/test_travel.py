"""Tests for skills/travel.py: distance, pack, jetlag, luggage."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- distance
def test_distance_winnipeg_toronto():
    # Straight-line Winnipeg-Toronto is about 1,500 km; haversine
    # over the built-in table gives 1,508 km / 937 mi.
    out = _ask("distance winnipeg to toronto")
    assert "Winnipeg to Toronto: about 1,508 km (937 mi)" in out
    assert "2h 16m" in out
    assert "as the crow flies" in out
    # The dist alias routes to the same skill
    out = _ask("dist winnipeg to toronto")
    assert "1,508 km" in out


def test_distance_toronto_london():
    # Straight-line Toronto-London is about 5,700 km.
    out = _ask("distance toronto to london")
    assert "Toronto to London: about 5,712 km (3,550 mi)" in out
    assert "7h 13m" in out


def test_distance_aliases_and_multiword():
    # nyc alias + multi-word city names both work
    out = _ask("distance nyc to london")
    assert "New York to London: about 5,573 km (3,463 mi)" in out
    out = _ask("distance quebec city to halifax")
    assert "Quebec City to Halifax" in out
    # Case-insensitive
    out = _ask("distance WINNIPEG to Vancouver")
    assert "Winnipeg to Vancouver: about 1,866 km (1,159 mi)" in out


def test_distance_bad():
    assert "Usage" in _ask("distance")
    assert "Usage" in _ask("distance toronto")  # needs "to <city>"
    assert "Usage" in _ask("distance toronto to")  # missing second city
    assert "Unknown city" in _ask("distance winnipeg to atlantis")
    assert "Unknown city" in _ask("distance atlantis to toronto")
    assert "same city" in _ask("distance toronto to toronto")


# ---------------------------------------------------------------- pack
def test_pack_beach():
    out = _ask("pack beach 5")
    assert "Packing list for a 5-days beach trip (12 items)" in out
    assert "swimsuit" in out
    assert "sunscreen" in out
    assert "underwear x 5" in out
    assert "shorts x 3" in out  # ceil(5 * 0.5)
    assert "Check the weather" in out


def test_pack_business():
    out = _ask("pack business 3")
    assert "Packing list for a 3-days business trip (11 items)" in out
    assert "suit or blazer" in out
    assert "dress shirts x 3" in out
    assert "ties x 2" in out  # ceil(3 * 0.5)


def test_pack_default_days():
    # No days given: defaults to 3
    out = _ask("pack camping")
    assert "3-days camping trip (13 items)" in out
    assert "tent" in out
    assert "t-shirts x 3" in out


def test_pack_long_trip_laundry_note():
    out = _ask("pack winter 10")
    assert "10-days winter trip (12 items)" in out
    assert "sweaters x 5" in out
    assert "laundry day mid-trip" in out


def test_pack_bad():
    assert "Usage" in _ask("pack")
    assert "Usage" in _ask("pack moon 3")  # unknown trip type
    assert "Usage" in _ask("pack beach two")  # days must be a number
    assert "between 1 and 30" in _ask("pack beach 0")
    assert "between 1 and 30" in _ask("pack beach 31")


# ---------------------------------------------------------------- jetlag
def test_jetlag_east():
    # Eastbound: 1 day per hour crossed
    out = _ask("jetlag 8 east")
    assert "Crossing 8 time zones east takes about 8 days" in out
    assert "1 day per hour crossed" in out
    assert "bright light in the morning" in out
    assert "not medical advice" in out


def test_jetlag_west():
    # Westbound: 0.5 days per hour crossed
    out = _ask("jetlag 5 west")
    assert "Crossing 5 time zones west takes about 2.5 days" in out
    assert "0.5 days per hour crossed" in out
    assert "late afternoon and evening" in out


def test_jetlag_singular_and_default():
    out = _ask("jetlag 1 east")
    assert "Crossing 1 time zone east takes about 1 day" in out
    # No direction given: defaults to east
    out = _ask("jetlag 3")
    assert "Crossing 3 time zones east takes about 3 days" in out


def test_jetlag_bad():
    assert "Usage" in _ask("jetlag")
    assert "Usage" in _ask("jetlag 8 north")  # direction must be east/west
    assert "between 1 and 12" in _ask("jetlag 0")
    assert "between 1 and 12" in _ask("jetlag 13")


# ---------------------------------------------------------------- luggage
def test_luggage_over_checked():
    out = _ask("luggage 25kg")
    assert "25 kg is 2 kg (4.4 lb) over the checked bag" in out
    assert "overweight fee" in out


def test_luggage_under_checked():
    out = _ask("luggage 20kg")
    assert "20 kg fits the checked bag (23 kg / 50 lb) limit" in out
    assert "3 kg (6.6 lb) to spare" in out


def test_luggage_carryon_imperial():
    # 18 lb = 8.16 kg; 10 kg limit leaves 1.8 kg / 4 lb headroom
    out = _ask("luggage 18lb carryon")
    assert "18 lb fits the carry-on (10 kg / 22 lb) limit" in out
    assert "1.8 kg (4 lb) to spare" in out
    # Exactly at the limit: 0 to spare
    out = _ask("luggage 10kg carryon")
    assert "10 kg fits the carry-on" in out
    assert "0 kg (0 lb) to spare" in out


def test_luggage_bad():
    assert "Usage" in _ask("luggage")
    assert "Usage" in _ask("luggage 25")  # weight needs a unit
    assert "Usage" in _ask("luggage 25kg hand")  # kind must be checked/carryon
    assert "greater than 0" in _ask("luggage 0kg")


# ---------------------------------------------------------------- regression
def test_distance_keeps_convert_trigger():
    # Adding travel must not steal the convert trigger
    out = _ask("convert 10 km to mi")
    assert "10 km = 6.21371 mi" in out
