"""Productivity skills: stopwatch, reminders, stats, date math, currency.

All local and keyless. Honesty rules are baked in:
- reminders have no background scheduler — the skill says so and `reminders`
  lists what's due/overdue so the user can check;
- currency uses an offline snapshot table and says exactly that.
"""
from __future__ import annotations

import json
import math
import os
import re
import statistics
import time as _time
from datetime import date, datetime, timedelta
from pathlib import Path

from .base import Skill, SkillRegistry

DATA_DIR = Path(os.environ.get(
    "MONICO_DATA_DIR",
    Path(__file__).resolve().parent.parent / "data",
))
STOPWATCH_FILE = DATA_DIR / "stopwatch.json"
REMINDERS_FILE = DATA_DIR / "reminders.json"
MAX_REMINDERS = 100

_BOOT = _time.monotonic()


def _load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, type(default)) else default
    except (json.JSONDecodeError, OSError):
        return default


def _save_json(path: Path, data) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


_DURATION_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([smhd])\s*$", re.IGNORECASE)
_DURATION_SECS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _parse_duration(text: str):
    m = _DURATION_RE.match(text.strip())
    if not m:
        return None
    return float(m.group(1)) * _DURATION_SECS[m.group(2).lower()]


def _fmt_hms(total_secs: float) -> str:
    total = int(total_secs)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


# ---------------------------------------------------------------- stopwatch

def _run_stopwatch(trigger: str, args: str) -> str:
    action = (args or "").strip().lower()
    state = _load_json(STOPWATCH_FILE, {})
    running = bool(state.get("running"))
    elapsed_base = float(state.get("elapsed", 0.0))
    started_at = float(state.get("started_at", 0.0))
    laps = state.get("laps", [])

    def current_elapsed() -> float:
        if running:
            return elapsed_base + (_time.monotonic() - started_at)
        return elapsed_base

    if action in ("start", "go"):
        if running:
            return f"Stopwatch already running — {_fmt_hms(current_elapsed())} so far."
        state = {"running": True, "elapsed": elapsed_base,
                 "started_at": _time.monotonic(), "laps": laps}
        _save_json(STOPWATCH_FILE, state)
        return "Stopwatch started." + (f" Resumed at {_fmt_hms(elapsed_base)}." if elapsed_base else "")
    if action in ("stop", "pause"):
        if not running:
            return "Stopwatch isn't running. Say `stopwatch start` to begin."
        state = {"running": False, "elapsed": current_elapsed(),
                 "started_at": 0.0, "laps": laps}
        _save_json(STOPWATCH_FILE, state)
        return f"Stopped at {_fmt_hms(state['elapsed'])}."
    if action in ("lap",):
        if not running:
            return "Stopwatch isn't running — nothing to lap."
        lap_time = current_elapsed()
        laps.append({"lap": len(laps) + 1, "at": lap_time})
        state["laps"] = laps
        _save_json(STOPWATCH_FILE, state)
        prev = laps[-2]["at"] if len(laps) > 1 else 0.0
        return f"Lap {len(laps)}: {_fmt_hms(lap_time)} (split {_fmt_hms(lap_time - prev)})."
    if action in ("reset", "clear"):
        _save_json(STOPWATCH_FILE, {})
        return "Stopwatch reset."
    if action in ("status", "time"):
        action = ""
    if not action:
        status = "running" if running else "stopped"
        msg = f"Stopwatch {status} — {_fmt_hms(current_elapsed())}."
        if laps:
            msg += " Laps: " + ", ".join(
                f"#{l['lap']} {_fmt_hms(l['at'])}" for l in laps[-5:])
        return msg
    return ("Usage: `stopwatch start|stop|lap|status|reset` — e.g. `stopwatch start`, "
            "then `stopwatch lap`.")


# ---------------------------------------------------------------- reminders (manual-check, no scheduler)

def _run_remind(trigger: str, args: str) -> str:
    args = (args or "").strip()
    if trigger in ("reminders",) or not args or args.lower() in ("list", "ls"):
        reminders = _load_json(REMINDERS_FILE, [])
        now = _time.time()
        if not reminders:
            return ("No reminders. Set one with `remind 30m call mom`.\n"
                    "Note: I have no background scheduler — ask me `reminders` to check.")
        lines = []
        for r in reminders:
            left = r["due_at"] - now
            state = "**DUE**" if left <= 0 else f"in {_fmt_hms(left)}"
            lines.append(f"• {r['text']} — {state}")
        _save_json(REMINDERS_FILE, [r for r in reminders if r["due_at"] > now - 86400])
        return ("Reminders (I can't push notifications — check with `reminders`):\n"
                + "\n".join(lines))
    if args.lower() in ("clear", "delete all"):
        _save_json(REMINDERS_FILE, [])
        return "All reminders cleared."
    parts = args.split(None, 1)
    secs = _parse_duration(parts[0]) if parts else None
    if secs is None or secs <= 0:
        return "Usage: `remind 30m <text>` — units s/m/h/d, e.g. `remind 2h take meds`."
    if len(parts) < 2 or not parts[1].strip():
        return "Usage: `remind 30m <text>` — what should I remind you about?"
    if secs > 86400 * 30:
        return "Max reminder is 30 days out."
    text = parts[1].strip()[:200]
    reminders = _load_json(REMINDERS_FILE, [])
    if len(reminders) >= MAX_REMINDERS:
        return f"Reminder list is full ({MAX_REMINDERS}). Clear old ones with `remind clear`."
    due_at = _time.time() + secs
    reminders.append({"text": text, "due_at": due_at, "set_at": _time.time()})
    _save_json(REMINDERS_FILE, reminders)
    due = datetime.fromtimestamp(due_at).astimezone().strftime("%a %I:%M %p")
    return (f"Reminder set: {text} — in {_fmt_hms(secs)} ({due}).\n"
            f"I'm keyless with no scheduler, so ask me `reminders` to check — I won't ping you.")


# ---------------------------------------------------------------- stats

_NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?")


def _run_stats(trigger: str, args: str) -> str:
    nums = [float(n) for n in _NUMBER_RE.findall(args or "")]
    if len(nums) < 2:
        return ("Usage: `stats <numbers>` — e.g. `stats 4 8 15 16 23 42`.\n"
                "I report count, min, max, mean, median, and std dev.")
    if len(nums) > 10000:
        return "Too many numbers (max 10,000)."
    mean = statistics.fmean(nums)
    median = statistics.median(nums)
    stdev = statistics.stdev(nums) if len(nums) > 2 else 0.0

    def fmt(v: float) -> str:
        return str(int(v)) if float(v).is_integer() else f"{v:.4g}"

    return (
        f"n={len(nums)}, min={fmt(min(nums))}, max={fmt(max(nums))}, "
        f"mean={fmt(mean)}, median={fmt(median)}, stddev={fmt(stdev)}"
    )


# ---------------------------------------------------------------- date math

_DATE_RES = [
    (re.compile(r"^\s*(\d{4})-(\d{1,2})-(\d{1,2})\s*$"),
     lambda m: date(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
    (re.compile(r"^\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$"),
     lambda m: date(int(m.group(3)), int(m.group(1)), int(m.group(2)))),
]


def _parse_date(text: str):
    text = text.strip().lower()
    today = date.today()
    if text in ("today",):
        return today
    if text in ("tomorrow",):
        return today + timedelta(days=1)
    if text in ("yesterday",):
        return today - timedelta(days=1)
    for rx, build in _DATE_RES:
        m = rx.match(text)
        if m:
            try:
                return build(m)
            except ValueError:
                return None
    return None


def _run_datemath(trigger: str, args: str) -> str:
    """Date math. The router strips the trigger word, so `trigger` decides
    the mode and `args` holds only what follows it."""
    args = (args or "").strip()
    mode = trigger.lower()
    if not args:
        return ("Usage: `days <date1> to <date2>` or `dateadd <date> <+|-><n>d` — "
                "dates like 2026-12-25, 12/25/2026, today, tomorrow.")
    if mode in ("days", "datediff"):
        for sep in (" to ", " - ", " "):
            if sep in args:
                left, _, right = args.partition(sep)
                d1, d2 = _parse_date(left), _parse_date(right)
                if d1 and d2:
                    delta = (d2 - d1).days
                    word = "day" if abs(delta) == 1 else "days"
                    direction = "after" if delta >= 0 else "before"
                    return (f"{d1.isoformat()} → {d2.isoformat()}: "
                            f"{abs(delta)} {word} {direction}.")
        return "Usage: `days 2026-10-20 to 2026-12-25`."
    if mode == "dateadd":
        m = re.match(r"^(.+?)\s*([+-])\s*(\d+)\s*d?\s*$", args)
        if not m:
            return "Usage: `dateadd 2026-10-20 +30d` or `dateadd today -7`."
        d = _parse_date(m.group(1))
        if not d:
            return "Couldn't read that date. Try 2026-12-25, 12/25/2026, or today."
        delta = int(m.group(3)) * (1 if m.group(2) == "+" else -1)
        result = d + timedelta(days=delta)
        return (f"{d.isoformat()} {'+' if delta >= 0 else ''}{delta}d = "
                f"{result.isoformat()} ({result.strftime('%A')}).")
    return ("Usage: `days <date1> to <date2>` or `dateadd <date> <+|-><n>d`.")


# ---------------------------------------------------------------- currency (offline snapshot)

# Snapshot rates vs 1 USD. Offline by design (keyless, no network).
# Verify before any real money decision.
_CURRENCY_RATES = {
    "USD": 1.0, "CAD": 1.38, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5,
    "AUD": 1.52, "CHF": 0.88, "CNY": 7.09, "INR": 83.9, "MXN": 19.8,
    "BRL": 5.65, "KRW": 1380.0, "SGD": 1.34, "NZD": 1.64, "SEK": 10.5,
    "BTC": 0.0000149,  # ~$67k snapshot — volatile, verify before use
}
_CURRENCY_ALIASES = {
    "dollar": "USD", "dollars": "USD", "usd": "USD",
    "cad": "CAD", "loonie": "CAD",
    "euro": "EUR", "euros": "EUR",
    "pound": "GBP", "pounds": "GBP", "quid": "GBP",
    "yen": "JPY", "bitcoin": "BTC", "btc": "BTC", "sats": "BTC",
}


def _run_currency(trigger: str, args: str) -> str:
    try:
        from config import settings
        rates_date = settings.currency_rates_date
    except Exception:
        rates_date = "2026-10-20"
    m = re.match(
        r"^\s*([-+]?\d+(?:\.\d+)?)\s*([a-zA-Z$]+)\s+(?:to\s+)?([a-zA-Z$]+)\s*$",
        args or "",
    )
    if not m:
        return ("Usage: `currency <value> <from> to <to>` — e.g. `currency 100 usd to cad`.\n"
                "Offline snapshot rates only — verify before any real money move.")
    value = float(m.group(1))
    frm = _CURRENCY_ALIASES.get(m.group(2).lower().lstrip("$"), m.group(2).upper())
    to = _CURRENCY_ALIASES.get(m.group(3).lower().lstrip("$"), m.group(3).upper())
    if frm not in _CURRENCY_RATES or to not in _CURRENCY_RATES:
        return ("I know: " + ", ".join(sorted(_CURRENCY_RATES))
                + ". (Offline snapshot — not live rates.)")
    if frm == "BTC" or to == "BTC":
        extra = " BTC is volatile — this snapshot is stale the moment you read it."
    else:
        extra = ""
    usd_value = value / _CURRENCY_RATES[frm]
    result = usd_value * _CURRENCY_RATES[to]

    def fmt(v: float) -> str:
        return f"{v:,.8f}".rstrip("0").rstrip(".") if v < 0.01 else f"{v:,.2f}"

    return (f"{fmt(value)} {frm} ≈ {fmt(result)} {to}\n"
            f"Offline snapshot from {rates_date} — not live. Verify before real use.{extra}")


# ---------------------------------------------------------------- registration

def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="stopwatch", description="Start/stop/lap a stopwatch (persists across restarts).",
        usage="stopwatch <start|stop|lap|status|reset>", triggers=["stopwatch", "sw"],
        run=_run_stopwatch, examples=["stopwatch start", "stopwatch lap", "stopwatch stop"]))
    registry.register(Skill(
        name="remind", description="Set reminders checked with `reminders` (no push — keyless).",
        usage="remind <5m|2h|1d> <text> | reminders | remind clear",
        triggers=["remind", "reminders", "reminder"],
        run=_run_remind, examples=["remind 30m call mom", "reminders"]))
    registry.register(Skill(
        name="stats", description="Descriptive stats for a list of numbers.",
        usage="stats <n1 n2 ...>", triggers=["stats", "average", "mean"],
        run=_run_stats, examples=["stats 4 8 15 16 23 42"]))
    registry.register(Skill(
        name="datemath", description="Days between dates; add/subtract days from a date.",
        usage="days <d1> to <d2> | dateadd <date> <+|-><n>d",
        triggers=["days", "dateadd", "datediff"],
        run=_run_datemath, examples=["days 2026-10-20 to 2026-12-25", "dateadd today +30d"]))
    registry.register(Skill(
        name="currency", description="Convert money with offline snapshot rates (honest: not live).",
        usage="currency <value> <from> to <to>",
        triggers=["currency", "convert-money", "fx"],
        run=_run_currency, examples=["currency 100 usd to cad", "currency 1 btc to usd"]))
