"""Tests for skills/astronomy.py: planet, orbit, lighttime, star,
gravity, scope, season."""
import re
from datetime import date

from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


def test_skill_count():
    assert len(agent.list_skills()) == 183


# ---------------------------------------------------------------- planet
def test_planet_list():
    out = _ask("planet")
    assert "Mars: 1.524 AU, 687 days" in out
    assert "Jupiter: 5.203 AU" in out


def test_planet_mars():
    out = _ask("planet mars")
    assert "1.524 AU" in out
    assert "687" in out
    assert "6,779 km" in out
    assert "2 known moons" in out
    assert "-65 C" in out
    assert "24.6 hours" in out


def test_planet_venus_retrograde():
    # Venus spins backwards: the answer must say so, not just give hours.
    out = _ask("planet venus")
    assert "retrograde" in out
    assert "464 C" in out


def test_planet_unknown():
    resp = agent.respond("planet vulcan")
    assert "don't know a planet called 'vulcan'" in resp["response"]


# ---------------------------------------------------------------- orbit
def test_orbit_mars_period():
    # Kepler: 1.524 AU -> 1.524^1.5 = 1.88 years, NOT 1.524 years.
    out = _ask("orbit a 1.524")
    assert "1.881 Earth years" in out
    assert "687" in out
    assert "1.524 Earth years" not in out


def test_orbit_jupiter_distance():
    # Kepler: 11.86-year period -> 11.86^(2/3) = 5.201 AU, NOT 11.86 AU.
    out = _ask("orbit p 11.86")
    assert "5.201 AU" in out
    assert "11.86 AU" not in out


def test_orbit_earth_identity():
    out = _ask("orbit a 1")
    assert "1 Earth years" in out


def test_orbit_usage():
    resp = agent.respond("orbit")
    assert "orbit a <AU>" in resp["response"]


# ---------------------------------------------------------------- lighttime
def test_lighttime_mars():
    # 1.524 AU at c: ~760 s = ~12.67 minutes, not 1.524 minutes.
    out = _ask("lighttime mars")
    assert "12.67 minutes" in out


def test_lighttime_one_au():
    # 1 AU is 8.32 light-minutes, not 1 minute.
    out = _ask("lighttime 1 au")
    assert "8.317 minutes" in out


def test_lighttime_eight_minutes():
    # In 8 minutes light travels ~144 million km, not 8 million.
    out = _ask("lighttime 8 min")
    assert "143,900,380 km" in out
    assert "1.439e" not in out


def test_lighttime_one_lightyear():
    # Light takes a year to cross a light-year: 365.3 days.
    out = _ask("lighttime 1 ly")
    assert "365.3 days" in out


# ---------------------------------------------------------------- star
def test_star_list():
    out = _ask("star")
    assert "Proxima Centauri: 4.246 ly" in out
    assert "Sirius: 8.6 ly" in out


def test_star_sirius():
    # 8.6 ly = 2.637 pc, not 8.6 pc.
    out = _ask("star sirius")
    assert "8.6 light-years" in out
    assert "2.637 parsecs" in out
    assert "8.6 parsecs" not in out


def test_star_proxima_nearest():
    out = _ask("star proxima centauri")
    assert "4.246 light-years" in out


# ---------------------------------------------------------------- gravity
def test_gravity_mars_weight():
    # 80 kg at 0.38x is 30.4 kg, not 80 kg and not 13.3 kg (1/6).
    out = _ask("gravity 80kg mars")
    assert "30.4 kg" in out


def test_gravity_moon_pounds():
    # 176 lb at 0.17x is 29.92 lb.
    out = _ask("gravity 176lb moon")
    assert "29.92 lb" in out


def test_gravity_jupiter_factor():
    out = _ask("gravity jupiter")
    assert "2.53x" in out
    assert "gas giants have no solid surface" in out


def test_gravity_usage():
    resp = agent.respond("gravity 80kg vulcan")
    assert "gravity <weight> <world>" in resp["response"]


# ---------------------------------------------------------------- scope
def test_scope_basic():
    # 1200 / 25 = 48x, not 1200x and not 25x.
    out = _ask("scope 1200 25")
    assert "48x magnification" in out


def test_scope_with_aperture():
    # 150 mm aperture: max useful 300x, exit pupil 150/48 = 3.125 mm.
    out = _ask("scope 1200 25 150")
    assert "48x magnification" in out
    assert "300x" in out
    assert "3.125 mm" in out


def test_scope_over_magnified():
    # 1200 / 3 = 400x past the 300x useful limit for 150 mm.
    out = _ask("scope 1200 3 150")
    assert "400x" in out
    assert "past the useful limit" in out


def test_scope_not_over_at_limit():
    # 1200 / 4 = 300x is exactly the limit, not past it.
    out = _ask("scope 1200 4 150")
    assert "past the useful limit" not in out


# ---------------------------------------------------------------- season
def _dates_in(out: str) -> list[date]:
    found = re.findall(r"\d{4}-\d{2}-\d{2}", out)
    return [date.fromisoformat(d) for d in found]


def test_season_2026_within_a_day():
    # Real 2026 dates: Mar 20, Jun 21, Sep 22, Dec 21.
    # Low-precision formulae are approximate: allow 1 day either way.
    out = _ask("season 2026")
    got = _dates_in(out)
    real = [date(2026, 3, 20), date(2026, 6, 21),
            date(2026, 9, 22), date(2026, 12, 21)]
    assert len(got) == 4
    for g, r in zip(got, real):
        assert abs((g - r).days) <= 1, f"{g} vs real {r}"


def test_season_2025_within_a_day():
    out = _ask("season 2025")
    got = _dates_in(out)
    real = [date(2025, 3, 20), date(2025, 6, 21),
            date(2025, 9, 22), date(2025, 12, 21)]
    assert len(got) == 4
    for g, r in zip(got, real):
        assert abs((g - r).days) <= 1, f"{g} vs real {r}"


def test_season_default_year():
    out = _ask("season")
    assert str(date.today().year) in out
    assert "southern hemisphere" in out


def test_season_bad_year():
    resp = agent.respond("season 1800")
    assert "between 1900 and 2200" in resp["response"]
