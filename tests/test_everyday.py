"""Tests for skills/everyday.py: tip, discount, bmi, base, weekday, moon."""
from datetime import date, timedelta

from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- tip

def test_tip_basic():
    out = _ask("tip 80 20")
    assert "Tip (20%): $16.00" in out and "Total: $96.00" in out


def test_tip_split_and_default():
    out = _ask("tip 80 20% for 4")
    assert "$24.00 each (4 people)" in out
    out = _ask("tip 100")
    assert "Tip (15%): $15.00" in out and "Total: $115.00" in out


def test_tip_dollar_sign_and_bad():
    assert "Total: $120.00" in _ask("tip $100 20")
    assert "must be 0" in _ask("tip 100 150")
    assert "bill amount" in _ask("tip abc")
    assert "Usage" in _ask("tip")


# ---------------------------------------------------------------- discount

def test_discount_basic():
    out = _ask("discount 80 25")
    assert "Was $80.00, 25% off" in out
    assert "$60.00" in out and "you save $20.00" in out


def test_discount_with_tax():
    assert "$63.00" in _ask("discount 80 25 5")


def test_discount_bad():
    assert "must be 0" in _ask("discount 80 101")
    assert "Usage" in _ask("discount 80")


# ---------------------------------------------------------------- bmi

def test_bmi_metric():
    out = _ask("bmi 80kg 180cm")
    assert "BMI 24.7 (healthy weight)" in out


def test_bmi_bare_and_imperial():
    assert "BMI 24.7" in _ask("bmi 80 1.8")
    out = _ask("bmi 176lb 70in")
    assert "BMI 25.3 (overweight)" in out


def test_bmi_categories_and_bad():
    assert "(underweight)" in _ask("bmi 45kg 180cm")
    assert "(obese)" in _ask("bmi 120kg 170cm")
    assert "weight" in _ask("bmi abc 180cm")
    assert "Usage" in _ask("bmi 80")


# ---------------------------------------------------------------- base

def test_base_hex_to_dec():
    out = _ask("base ff hex to dec")
    assert "255 (dec)" in out and "0xFF (hex)" in out
    assert "0b11111111 (bin)" in out and "0o377 (oct)" in out


def test_base_bin_and_negative():
    assert "10 (dec)" in _ask("base 1010 bin to dec")
    assert "-10 (dec)" in _ask("base -1010 bin to dec")


def test_base_bad():
    assert "isn't valid" in _ask("base 12 bin to dec")
    assert "Bases must be" in _ask("base 10 foo to dec")
    assert "Usage" in _ask("base ff hex")


# ---------------------------------------------------------------- weekday

def test_weekday_known_date():
    # 2026-12-25 is a Friday (verified against calendar math in the test).
    out = _ask("weekday 2026-12-25")
    assert "2026-12-25 is a Friday" in out


def test_weekday_today_tomorrow():
    today = date.today()
    out = _ask("weekday today")
    assert f"{today.isoformat()} is a {today.strftime('%A')} (today)" in out
    tomorrow = today + timedelta(days=1)
    assert "(tomorrow)" in _ask("weekday tomorrow")


def test_weekday_bad():
    assert "Usage" in _ask("weekday not-a-date")
    assert "Usage" in _ask("weekday 2026-02-30")


# ---------------------------------------------------------------- moon

def test_moon_known_new_moon():
    # 2000-01-06 18:14 UTC is the reference new moon.
    out = _ask("moon 2000-01-06")
    assert "New Moon" in out
    assert "illumination 0%" in out or "illumination 1%" in out


def test_moon_fullish_and_default():
    out = _ask("moon 2000-01-21")
    assert "Full Moon" in out
    out = _ask("moon")
    assert date.today().isoformat() in out and "illumination" in out


def test_moon_bad():
    assert "Usage" in _ask("moon not-a-date")
