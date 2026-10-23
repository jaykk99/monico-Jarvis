"""Tests for skills/moretools.py: morse, roman, loan, system, epoch, tz,
shuffle, countdown, prime."""
from datetime import datetime, timedelta, timezone

from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- morse

def test_morse_encode():
    out = _ask("morse sos")
    assert out == "... --- ..."


def test_morse_encode_sentence():
    out = _ask("morse hi you")
    assert out == ".... .. / -.-- --- ..-"


def test_morse_decode():
    out = _ask("morse .... . .-.. .-.. ---")
    assert out == "hello"


def test_morse_decode_words():
    out = _ask("morse .... .. / -.-- --- ..-")
    assert out == "hi you"


def test_morse_encode_numbers():
    out = _ask("morse 911")
    assert out == "----. .---- .----"


def test_morse_bad_code():
    out = _ask("morse .-.-.-.-")
    assert "Not valid morse" in out


def test_morse_empty():
    assert "Usage" in _ask("morse")


# ---------------------------------------------------------------- roman

def test_roman_to_numeral():
    assert _ask("roman 2026") == "MMXXVI"
    assert _ask("roman 1") == "I"
    assert _ask("roman 3999") == "MMMCMXCIX"
    assert _ask("roman 4") == "IV"


def test_roman_from_numeral():
    assert _ask("roman MMXXVI") == "2026"
    assert _ask("roman iv") == "4"
    assert _ask("roman xiv") == "14"


def test_roman_out_of_range():
    out = _ask("roman 0")
    assert "1–3999" in out
    out = _ask("roman 4000")
    assert "1–3999" in out


def test_roman_garbage():
    out = _ask("roman xyz")
    assert "isn't a number" in out


# ---------------------------------------------------------------- loan

def test_loan_typical():
    out = _ask("loan 250000 6.5 25")
    assert "Monthly payment: $1,688.02" in out
    assert "Total interest:" in out


def test_loan_zero_rate():
    out = _ask("loan 12000 0 1")
    assert "Monthly payment: $1,000.00" in out


def test_loan_total_interest_sanity():
    out = _ask("loan 10000 10 1")
    # ~$879.16/mo * 12 = 10549.9x, interest ~549.9x
    assert "Monthly payment: $879.16" in out


def test_loan_bad_args():
    assert "Usage" in _ask("loan 100")
    assert "three numbers" in _ask("loan abc 5 10")


# ---------------------------------------------------------------- system

def test_system_reports_basics():
    out = _ask("system")
    assert "CPUs:" in out
    assert "Memory:" in out
    assert "Disk (/)" in out
    assert "Python:" in out


def test_sysinfo_trigger():
    assert agent.respond("sysinfo")["ok"]


# ---------------------------------------------------------------- epoch

def test_epoch_now():
    out = _ask("epoch")
    assert "Epoch:" in out
    assert "UTC" in out


def test_epoch_from_seconds():
    out = _ask("epoch 0")
    assert "1970-01-01 00:00:00" in out


def test_epoch_ms_detection():
    out = _ask("epoch 1000000000000")  # 1e12 ms = 2001-09-09 01:46:40 UTC
    assert "(ms)" in out
    assert "2001-09-09 01:46:40" in out


def test_epoch_seconds_above_threshold_not_ms():
    out = _ask("epoch 1000")
    assert "(s)" in out
    assert "1970-01-01 00:16:40" in out


def test_epoch_from_date():
    out = _ask("epoch 1970-01-02")
    assert "epoch 86400" in out


def test_epoch_out_of_range():
    out = _ask("epoch 99999999999999999999")
    assert "out of range" in out


def test_epoch_garbage():
    assert "Usage" in _ask("epoch notadate")


# ---------------------------------------------------------------- tz

def test_tz_current_in_zone():
    import re
    out = _ask("tz America/Winnipeg")
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", out)


def test_tz_convert():
    out = _ask("tz 15:00 UTC to America/Winnipeg")
    assert "15:00 UTC" in out
    assert "→" in out


def test_tz_convert_dates():
    out = _ask("tz 2026-12-25 12:00 UTC to America/Winnipeg")
    assert "2026-12-25" in out


def test_tz_unknown_zone():
    out = _ask("tz Narnia")
    assert "Unknown zone" in out


def test_tz_empty():
    assert "Usage" in _ask("tz")


# ---------------------------------------------------------------- shuffle

def test_shuffle_preserves_items():
    out = _ask("shuffle alice, bob, carol")
    items = [ln.split(". ", 1)[1] for ln in out.splitlines()]
    assert sorted(items) == ["alice", "bob", "carol"]


def test_shuffle_multiline():
    out = _ask("shuffle\nalpha\nbeta\ngamma")
    items = [ln.split(". ", 1)[1] for ln in out.splitlines()]
    assert sorted(items) == ["alpha", "beta", "gamma"]


def test_shuffle_too_few():
    assert "at least 2" in _ask("shuffle solo")


# ---------------------------------------------------------------- countdown

def test_countdown_future():
    future = (datetime.now() + timedelta(days=40)).strftime("%Y-%m-%d")
    out = _ask(f"countdown {future}")
    assert "day" in out
    assert "until" in out


def test_countdown_past():
    assert "already passed" in _ask("countdown 2000-01-01")


def test_countdown_garbage():
    assert "Couldn't parse" in _ask("countdown someday")


# ---------------------------------------------------------------- prime

def test_prime_small():
    assert _ask("prime 2") == "2 is prime."
    assert _ask("prime 97") == "97 is prime."
    assert _ask("prime 1") == "1 is neither prime nor composite."


def test_prime_composite():
    out = _ask("prime 100")
    assert "100 is composite = 2 × 2 × 5 × 5" == out


def test_prime_factor_large():
    out = _ask("prime 123456")
    assert out == "123456 is composite = 2 × 2 × 2 × 2 × 2 × 2 × 3 × 643"


def test_prime_known_big():
    # 2^31 - 1 is prime
    assert _ask("prime 2147483647") == "2147483647 is prime."


def test_prime_zero_one_not_prime():
    assert _ask("prime 1") == "1 is neither prime nor composite."
    assert _ask("prime 0") == "0 is neither prime nor composite."


def test_prime_garbage():
    assert "Usage" in _ask("prime abc")


def test_prime_too_big():
    assert "Too big" in _ask("prime 10000000000000000000")
