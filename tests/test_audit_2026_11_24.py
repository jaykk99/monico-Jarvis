"""Audit fixes 2026-11-24: calc pow guard, todo cap, corrupt JSON stores,
rate-limit bucket pruning.

Each test fails on the pre-fix code (verified via git stash) and passes
with the fix.
"""
import json
import os
import tempfile
import time
from collections import deque

_tmp = tempfile.mkdtemp()
os.environ["MONICO_DATA_DIR"] = os.path.join(_tmp, "data")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from agent import MonicoAgent  # noqa: E402
from skills import builtin, productivity  # noqa: E402

client = TestClient(main.app)


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------- calc pow guard

def test_calc_huge_pow_rejected_not_hung():
    a = MonicoAgent()
    started = time.monotonic()
    r = a.respond("calc 9**9**9")
    assert time.monotonic() - started < 5
    assert "too large" in r["response"]


def test_calc_huge_pow_boundary():
    a = MonicoAgent()
    assert "too large" in a.respond("calc 10**4001")["response"]
    assert a.respond("calc 10**4000")["response"] == "10**4000 = 1e+4000"
    assert a.respond("calc 2**1000")["response"] == "2**1000 = 1.07151e+301"


def test_calc_normal_powers_still_work():
    a = MonicoAgent()
    assert a.respond("calc 2**10")["response"] == "2**10 = 1024"
    assert a.respond("calc 2**2**2**2")["response"] == "2**2**2**2 = 65536"
    assert a.respond("calc 2**-3")["response"] == "2**-3 = 0.125"
    assert a.respond("calc (-2)**3")["response"] == "(-2)**3 = -8"


# ---------------------------------------------------------------- todo cap + corrupt stores

def test_todo_bare_text_respects_cap():
    path = builtin.DATA_DIR / "todos.json"
    try:
        _write(path, [{"text": f"t{i}", "done": False} for i in range(100)])
        a = MonicoAgent()
        r = a.respond("todo one more past the cap")
        assert "full" in r["response"].lower()
        assert len(json.loads(path.read_text())) == 100
    finally:
        path.unlink(missing_ok=True)


def test_corrupt_todos_degrade_and_heal():
    path = builtin.DATA_DIR / "todos.json"
    try:
        _write(path, ["not-a-dict", 42, {"text": "keep me", "done": False},
                      {"done": True}])
        a = MonicoAgent()
        r = a.respond("todos")
        assert "hit an error" not in r["response"]
        assert "keep me" in r["response"]
        # corrupt rows dropped and the file rewritten clean
        assert json.loads(path.read_text()) == [
            {"text": "keep me", "done": False}]
    finally:
        path.unlink(missing_ok=True)


def test_corrupt_timers_degrade_and_heal():
    path = builtin.DATA_DIR / "timers.json"
    try:
        now = time.time()
        _write(path, ["not-a-dict", {"label": "tea", "ends_at": now + 600},
                      {"label": "bad", "ends_at": "soon"}])
        a = MonicoAgent()
        r = a.respond("timers")
        assert "hit an error" not in r["response"]
        assert "tea" in r["response"]
        assert json.loads(path.read_text()) == [
            {"label": "tea", "ends_at": now + 600, "set_at": now + 600}]
    finally:
        path.unlink(missing_ok=True)


def test_corrupt_reminders_degrade_and_heal():
    path = productivity.DATA_DIR / "reminders.json"
    try:
        now = time.time()
        _write(path, ["junk", {"text": "call mom", "due_at": now + 600}])
        a = MonicoAgent()
        r = a.respond("reminders")
        assert "hit an error" not in r["response"]
        assert "call mom" in r["response"]
        assert json.loads(path.read_text()) == [
            {"text": "call mom", "due_at": now + 600, "set_at": now + 600}]
    finally:
        path.unlink(missing_ok=True)


def test_corrupt_stopwatch_degrades():
    path = productivity.DATA_DIR / "stopwatch.json"
    try:
        _write(path, {"running": "yes", "elapsed": "abc", "started_at": None,
                      "laps": "nope"})
        a = MonicoAgent()
        r = a.respond("stopwatch")
        assert "hit an error" not in r["response"]
        assert "Stopwatch stopped" in r["response"]
    finally:
        path.unlink(missing_ok=True)


# ---------------------------------------------------------------- rate-limit pruning

def test_rate_limit_buckets_pruned():
    main._rate_buckets.clear()
    stale = time.monotonic() - 120
    for i in range(600):
        main._rate_buckets[f"10.9.9.{i}"] = deque([stale])
    assert client.post("/chat", json={"query": "time"}).status_code == 200
    # stale buckets gone; only the live client bucket remains
    assert len(main._rate_buckets) == 1
    main._rate_buckets.clear()
