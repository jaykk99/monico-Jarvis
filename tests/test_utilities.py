"""Tests for skills/utilities.py: color, age, lorem, slug."""
from datetime import date, timedelta

from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- color

def test_color_hex():
    out = _ask("color #ff8800")
    assert "RGB (255, 136, 0)" in out
    assert "HSL (32" in out


def test_color_hex_no_hash_and_short():
    out = _ask("color f80")
    assert "RGB (255, 136, 0)" in out


def test_color_rgb():
    out = _ask("color rgb 255 136 0")
    assert "#ff8800" in out


def test_color_rgb_out_of_range():
    resp = agent.respond("color rgb 999 0 0")
    assert "0–255" in resp["response"]


def test_color_hsl():
    out = _ask("color hsl 0 100 50")
    assert "RGB (255, 0, 0)" in out
    assert "#ff0000" in out


def test_color_named():
    out = _ask("color orange")
    assert "#ffa500" in out


def test_color_unknown():
    resp = agent.respond("color notacolor")
    assert "didn't recognize" in resp["response"]


def test_color_usage():
    resp = agent.respond("color")
    assert "Usage" in resp["response"]


# ---------------------------------------------------------------- age

def test_age_basic():
    out = _ask("age 2000-01-01")
    today = date.today()
    years = today.year - 2000 - ((today.month, today.day) < (1, 1))
    assert f"{years} year" in out
    assert "days total" in out


def test_age_slash_format():
    out = _ask("age 05/01/1990")
    assert "1990-05-01" in out


def test_age_future():
    resp = agent.respond("age 2999-01-01")
    assert "not born yet" in resp["response"]


def test_age_feb29_birthday():
    out = _ask("age 2000-02-29")
    assert "2000-02-29" in out
    assert "old" in out


def test_age_today_birthday():
    today = date.today().isoformat()
    out = _ask(f"age {today}")
    assert "0 years" in out
    assert "happy birthday" in out.lower()


def test_age_months_days_remainder_sane():
    # born exactly 400 days ago: years breakdown must reconcile with total
    born = date.today() - timedelta(days=400)
    out = _ask(f"age {born.isoformat()}")
    assert "400 days total" in out


def test_age_usage():
    resp = agent.respond("age")
    assert "Usage" in resp["response"]


# ---------------------------------------------------------------- lorem

def test_lorem_default_paragraphs():
    out = _ask("lorem")
    assert len(out.split("\n\n")) == 3


def test_lorem_two_paragraphs():
    out = _ask("lorem 2")
    assert len(out.split("\n\n")) == 2


def test_lorem_sentences():
    out = _ask("lorem 3 sentences")
    assert out.count(".") == 3


def test_lorem_words():
    out = _ask("lorem 10 words")
    assert len(out.split()) == 10


def test_lorem_bad_count():
    resp = agent.respond("lorem 99")
    assert "1–20" in resp["response"]


def test_lorem_bad_unit():
    resp = agent.respond("lorem banana")
    assert "Usage" in resp["response"]


# ---------------------------------------------------------------- slug

def test_slug_basic():
    out = _ask("slug Hello World!")
    assert out == "`hello-world`"


def test_slug_accents_and_punct():
    out = _ask("slug Café au lait — fresh!")
    assert out == "`cafe-au-lait-fresh`"


def test_slug_collapses_dashes():
    out = _ask("slug a   b---c")
    assert out == "`a-b-c`"


def test_slug_empty():
    resp = agent.respond("slug !!!")
    assert "Nothing slug-worthy" in resp["response"]


def test_slug_usage():
    resp = agent.respond("slug")
    assert "Usage" in resp["response"]


# ---------------------------------------------------------------- registry wiring

def test_utilities_registered():
    names = {s["name"] for s in agent.list_skills()}
    assert {"color", "age", "lorem", "slug"} <= names
    caps = agent.capabilities()
    assert set(caps["implemented"]) >= {"color", "age", "lorem", "slug"}
