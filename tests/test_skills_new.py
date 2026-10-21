"""Tests for the new keyless skill modules: texttools + productivity.

All skills run locally with no network and no API keys; tests assert real
behavior (hashes, conversions, persistence round-trips), not just "no crash".
"""
import hashlib
import json
import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp()
os.environ["MONICO_DATA_DIR"] = os.path.join(_tmp, "data")

from agent import agent  # noqa: E402


def ask(text: str):
    """Route a command through the agent; return the reply dict."""
    return agent.respond(text)


# ---------------------------------------------------------------- hash

def test_hash_sha256_known_vector():
    r = ask("hash sha256 hello")
    assert r["ok"] is True and r["skill"] == "hash"
    assert hashlib.sha256(b"hello").hexdigest() in r["response"]


def test_hash_md5_trigger_alias():
    r = ask("md5 hello")
    assert r["ok"] is True
    assert hashlib.md5(b"hello").hexdigest() in r["response"]


def test_hash_bad_algo():
    r = ask("hash rot13 hello")
    assert "Unknown algorithm" in r["response"]


def test_hash_missing_text():
    r = ask("hash sha256")
    assert "Usage" in r["response"]


# ---------------------------------------------------------------- uuid

def test_uuid_format():
    import uuid as _uuid

    r = ask("uuid")
    assert r["ok"] is True
    _uuid.UUID(r["response"].strip("`"))  # raises if malformed


def test_uuid_count():
    r = ask("uuid 3")
    assert len(r["response"].strip().splitlines()) == 3


def test_uuid_rejects_huge_count():
    assert "1–20" in ask("uuid 99")["response"]


def test_uuid_unique():
    a = ask("uuid")["response"]
    b = ask("uuid")["response"]
    assert a != b


# ---------------------------------------------------------------- words

def test_words_counts():
    r = ask("words hello brave new world")
    assert r["ok"] is True
    assert "4 words" in r["response"]
    assert "21 characters" in r["response"]


def test_words_empty_usage():
    assert "Usage" in ask("words")["response"]


# ---------------------------------------------------------------- case

def test_case_title():
    assert ask("case title hello world")["response"] == "Hello World"


def test_case_camel():
    assert ask("case camel my variable name")["response"] == "myVariableName"


def test_case_snake():
    assert ask("case snake myVariableName")["response"] == "my_variable_name"


def test_case_upper():
    assert ask("case upper hello")["response"] == "HELLO"


def test_case_bad_mode():
    assert "Unknown case" in ask("case fancy hello")["response"]


# ---------------------------------------------------------------- b64

def test_b64_roundtrip():
    enc = ask("b64 encode hello world")["response"]
    assert enc == "aGVsbG8gd29ybGQ="
    assert ask(f"b64 decode {enc}")["response"] == "hello world"


def test_b64_bad_input():
    assert "valid base64" in ask("b64 decode !!!notbase64!!!")["response"]


# ---------------------------------------------------------------- url

def test_url_roundtrip():
    enc = ask("url encode hello world?")["response"]
    assert enc == "hello%20world%3F"
    assert ask(f"url decode {enc}")["response"] == "hello world?"


# ---------------------------------------------------------------- json

def test_json_pretty():
    r = ask('json {"a":1,"b":[1,2]}')
    assert "Valid JSON" in r["response"]
    assert '"a": 1' in r["response"]


def test_json_invalid_reports_position():
    r = ask('json {"a": }')
    assert "Not valid JSON" in r["response"]
    assert "line" in r["response"]


# ---------------------------------------------------------------- pick

def test_pick_returns_one_option():
    r = ask("pick pizza, sushi, tacos")
    assert r["ok"] is True
    assert any(o in r["response"] for o in ("pizza", "sushi", "tacos"))


def test_pick_needs_two_options():
    assert "at least two" in ask("pick pizza")["response"]


# ---------------------------------------------------------------- stopwatch

def test_stopwatch_lifecycle():
    ask("stopwatch reset")
    assert "stopped" in ask("stopwatch")["response"]
    assert "started" in ask("stopwatch start")["response"].lower()
    status = ask("stopwatch status")["response"]
    assert "running" in status
    assert "Lap 1" in ask("stopwatch lap")["response"]
    stopped = ask("stopwatch stop")["response"]
    assert "Stopped at" in stopped
    ask("stopwatch reset")
    assert "0s" in ask("stopwatch")["response"]


def test_stopwatch_persists_across_instances():
    from skills import productivity

    ask("stopwatch reset")
    ask("stopwatch start")
    # fresh handler read from disk, like a restarted process would
    assert "running" in productivity._run_stopwatch("stopwatch", "status")
    ask("stopwatch reset")


# ---------------------------------------------------------------- remind

def test_remind_set_and_list():
    ask("remind clear")
    r = ask("remind 30m call mom")
    assert "Reminder set" in r["response"]
    assert "no scheduler" in r["response"]  # honest about no push
    listed = ask("reminders")["response"]
    assert "call mom" in listed
    ask("remind clear")
    assert "No reminders" in ask("reminders")["response"]


def test_remind_bad_duration():
    assert "Usage" in ask("remind someday party")["response"]


# ---------------------------------------------------------------- stats

def test_stats_known_values():
    r = ask("stats 4 8 15 16 23 42")
    assert r["ok"] is True
    body = r["response"]
    assert "n=6" in body and "min=4" in body and "max=42" in body
    assert "mean=18" in body and "median=15.5" in body


def test_stats_needs_numbers():
    assert "Usage" in ask("stats hello")["response"]


# ---------------------------------------------------------------- datemath

def test_days_between():
    r = ask("days 2026-10-20 to 2026-12-25")
    assert "66 days" in r["response"]


def test_dateadd():
    r = ask("dateadd 2026-10-20 +30d")
    assert "2026-11-19" in r["response"]
    assert "Thursday" in r["response"]


def test_dateadd_today_keyword():
    r = ask("dateadd today +1d")
    assert r["ok"] is True


def test_days_bad_input():
    assert "Usage" in ask("days someday")["response"]


# ---------------------------------------------------------------- currency

def test_currency_usd_cad():
    r = ask("currency 100 usd to cad")
    assert r["ok"] is True
    assert "138.00 CAD" in r["response"]
    assert "Offline snapshot" in r["response"]  # honesty label present


def test_currency_unknown_unit():
    assert "Offline snapshot" in ask("currency 5 xyz to usd")["response"]


def test_currency_btc_warns_volatility():
    r = ask("currency 1 btc to usd")
    assert "volatile" in r["response"]


# ---------------------------------------------------------------- registry integrity

def test_all_new_skills_registered():
    names = {s["name"] for s in agent.list_skills()}
    for expected in ("hash", "uuid", "words", "case", "b64", "url", "json",
                     "pick", "stopwatch", "remind", "stats", "datemath", "currency"):
        assert expected in names, f"missing skill: {expected}"


def test_help_lists_new_skills():
    body = ask("help")["response"]
    assert "stopwatch" in body and "currency" in body and "hash" in body
