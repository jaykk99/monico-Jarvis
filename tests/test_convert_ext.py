"""Tests for the extended convert categories: speed, volume, area, data.

Asserts real conversion math, not just "no crash".
"""
import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["MONICO_DATA_DIR"] = os.path.join(_tmp, "data")

from agent import agent  # noqa: E402


def ask(text: str):
    return agent.respond(text)


def test_convert_speed_mph_to_kmh():
    r = ask("convert 60 mph to kmh")
    assert r["ok"] is True
    assert "96.5606" in r["response"]


def test_convert_speed_knot_alias():
    r = ask("convert 10 knots to kmh")
    assert r["ok"] is True
    assert "18.52" in r["response"]


def test_convert_volume_gal_to_l():
    r = ask("convert 1 gal to l")
    assert r["ok"] is True
    assert "3.78541" in r["response"]


def test_convert_volume_cup_alias():
    r = ask("convert 2 cups to ml")
    assert r["ok"] is True
    assert "473.176" in r["response"]


def test_convert_area_acre_to_sqm():
    r = ask("convert 1 acre to sqm")
    assert r["ok"] is True
    assert "4046.86" in r["response"]


def test_convert_area_hectare_alias():
    r = ask("convert 1 hectare to acres")
    assert r["ok"] is True
    assert "2.47105" in r["response"]


def test_convert_data_gb_to_mb():
    r = ask("convert 1 gb to mb")
    assert r["ok"] is True
    assert "1000 mb" in r["response"]


def test_convert_data_binary_mib_to_kib():
    r = ask("convert 1 mib to kib")
    assert r["ok"] is True
    assert "1024 kib" in r["response"]


def test_convert_data_mixed_decimal_binary():
    r = ask("convert 1 gb to gib")
    assert r["ok"] is True
    assert "0.931323" in r["response"]


def test_convert_cross_category_rejected():
    r = ask("convert 5 m to kg")
    assert "I can convert" in r["response"]


def test_convert_unknown_unit():
    r = ask("convert 5 furlongs to m")
    assert "I can convert" in r["response"]


def test_convert_existing_categories_still_work():
    r = ask("convert 5 ft to m")
    assert "1.524" in r["response"]
    r = ask("convert 72 f to c")
    assert "22.2222" in r["response"]
