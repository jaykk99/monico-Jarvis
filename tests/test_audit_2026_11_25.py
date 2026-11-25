"""Regression tests for the 2026-11-25 audit of monico-Jarvis.

- calc power towers (9**9**9) hung the worker: _safe_eval had no bound
  on the size of an integer power result.
- `todo <text>` (bare add) bypassed the MAX_TODOS cap enforced by
  `todo add`, so the list could grow without bound.
- `savings` with a tiny monthly amount pushed the finish year past 9999
  and answered with "skill hit an error" instead of an answer.
- `dewpoint`/`humidex` at -237.7 C hit the Magnus formula's pole and
  answered with a division-by-zero error instead of an answer.
"""
import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp()
os.environ["MONICO_DATA_DIR"] = os.path.join(_tmp, "data")

from agent import MonicoAgent  # noqa: E402
from skills import builtin  # noqa: E402
from skills.builtin import _safe_eval  # noqa: E402

agent = MonicoAgent()


# ---------------------------------------------------------------- calc


def test_calc_power_tower_rejected_fast():
    # Pre-fix this computed 9**387420489 (~370M digits) and never returned.
    with pytest.raises(ValueError, match="too large"):
        _safe_eval("9**9**9")
    with pytest.raises(ValueError, match="too large"):
        _safe_eval("3**3**3**3")


def test_calc_big_single_pow_capped():
    with pytest.raises(ValueError, match="too large"):
        _safe_eval("2**100000")
    assert _safe_eval("2**1000") == 2 ** 1000


def test_calc_normal_still_works():
    assert agent.respond("calc (12 + 8) * 3")["response"] == "(12 + 8) * 3 = 60"
    assert agent.respond("calc 2**10")["response"] == "2**10 = 1024"
    assert agent.respond("calc sqrt(16)")["response"] == "sqrt(16) = 4"


def test_calc_tower_reports_too_large_not_error():
    r = agent.respond("calc 9**9**9")
    assert r["ok"] is True
    assert "too large" in r["response"]


# ---------------------------------------------------------------- todo cap


def test_todo_bare_add_respects_cap(monkeypatch, tmp_path):
    monkeypatch.setattr(builtin, "TODOS_FILE", tmp_path / "todos.json")
    local = MonicoAgent()
    for i in range(builtin.MAX_TODOS):
        r = local.respond(f"todo item {i}")
        assert r["ok"] is True
    assert len(builtin._load_json(builtin.TODOS_FILE, [])) == builtin.MAX_TODOS
    r = local.respond("todo one too many")
    assert "full" in r["response"]
    assert len(builtin._load_json(builtin.TODOS_FILE, [])) == builtin.MAX_TODOS


# ---------------------------------------------------------------- savings


def test_savings_tiny_monthly_answers_without_date():
    r = agent.respond("savings 5000 0.01")
    assert r["ok"] is True
    assert "too far out" in r["response"]
    assert "41666 years" in r["response"]


def test_savings_normal_still_shows_date():
    r = agent.respond("savings 5000 200")
    assert r["ok"] is True
    assert "goal reached around" in r["response"]


# ---------------------------------------------------------------- weather pole


def test_dewpoint_at_magnus_pole_answers():
    r = agent.respond("dewpoint -237.7C 50%")
    assert r["ok"] is True
    assert "undefined at -237.7 C" in r["response"]


def test_humidex_at_magnus_pole_answers():
    r = agent.respond("humidex -237.7C 50%")
    assert r["ok"] is True
    assert "undefined at -237.7 C" in r["response"]


def test_dewpoint_normal_still_works():
    r = agent.respond("dewpoint 25C 60%")
    assert r["ok"] is True
    assert "Dew point" in r["response"]
