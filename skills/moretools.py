"""More everyday-agent tools: morse, roman numerals, loan math, system stats,
epoch/timestamp conversion, timezone conversion, shuffle, countdown, primality.

All local, keyless, no network — same contract as the rest of skills/.
"""
from __future__ import annotations

import math
import os
import platform
import random
import re
import shutil
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

from .base import Skill, SkillRegistry

# ---------------------------------------------------------------- morse

_MORSE = {
    "a": ".-", "b": "-...", "c": "-.-.", "d": "-..", "e": ".",
    "f": "..-.", "g": "--.", "h": "....", "i": "..", "j": ".---",
    "k": "-.-", "l": ".-..", "m": "--", "n": "-.", "o": "---",
    "p": ".--.", "q": "--.-", "r": ".-.", "s": "...", "t": "-",
    "u": "..-", "v": "...-", "w": ".--", "x": "-..-", "y": "-.--",
    "z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.",
    "!": "-.-.--", "/": "-..-.", "(": "-.--.", ")": "-.--.-",
    "&": ".-...", ":": "---...", ";": "-.-.-.", "=": "-...-",
    "+": ".-.-.", "-": "-....-", "_": "..--.-", '"': ".-..-.",
    "$": "...-..-", "@": ".--.-.",
}
_UNMORSE = {v: k for k, v in _MORSE.items()}

_MORSE_LOOKING = re.compile(r"^[\s.\-/]+$")


def _run_morse(trigger: str, args: str) -> str:
    args = (args or "").strip()
    if not args:
        return ("Usage: `morse <text>` to encode, `morse .- ...` to decode. "
                "Words are separated by `/`.")
    if _MORSE_LOOKING.match(args):
        # decode
        words = []
        for word in re.split(r"\s*/\s*", args):
            chars = []
            for token in word.split():
                ch = _UNMORSE.get(token)
                if ch is None:
                    return f"Not valid morse: `{token}` isn't a known code."
                chars.append(ch)
            words.append("".join(chars))
        return " ".join(words)
    # encode
    codes, skipped = [], 0
    for ch in args.lower():
        if ch == " ":
            codes.append("/")
        elif ch in _MORSE:
            codes.append(_MORSE[ch])
        else:
            skipped += 1
    out = " ".join(codes)
    if skipped:
        out += f"\n(skipped {skipped} unsupported character{'s' if skipped != 1 else ''})"
    return out


# ---------------------------------------------------------------- roman

_ROMAN_TABLE = (
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
)
_ROMAN_RE = re.compile(
    r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", re.IGNORECASE
)


def _to_roman(n: int) -> str:
    out = []
    for value, glyph in _ROMAN_TABLE:
        while n >= value:
            out.append(glyph)
            n -= value
    return "".join(out)


def _from_roman(s: str) -> int:
    total, prev = 0, 0
    for ch in reversed(s.upper()):
        val = {"I": 1, "V": 5, "X": 10, "L": 50,
               "C": 100, "D": 500, "M": 1000}[ch]
        total = total - val if val < prev else total + val
        prev = val
    return total


def _run_roman(trigger: str, args: str) -> str:
    args = (args or "").strip().upper()
    if not args:
        return "Usage: `roman <number>` (1–3999) or `roman <numeral>` — e.g. `roman 2026`, `roman MMXXVI`."
    if re.fullmatch(r"\d+", args):
        n = int(args)
        if not 1 <= n <= 3999:
            return "Roman numerals cover 1–3999 only."
        return _to_roman(n)
    if _ROMAN_RE.fullmatch(args):
        return str(_from_roman(args))
    return f"`{args}` isn't a number 1–3999 or a valid roman numeral."


# ---------------------------------------------------------------- loan

def _run_loan(trigger: str, args: str) -> str:
    parts = (args or "").strip().split()
    if len(parts) != 3:
        return ("Usage: `loan <principal> <annual-rate-%> <years>` — "
                "e.g. `loan 250000 6.5 25` for a $250k mortgage at 6.5% over 25 years.")
    try:
        principal = float(parts[0].replace("$", "").replace(",", ""))
        rate_pct = float(parts[1].rstrip("%"))
        years = float(parts[2])
    except ValueError:
        return "I need three numbers: principal, annual rate %, and years — e.g. `loan 250000 6.5 25`."
    if principal <= 0 or years <= 0 or rate_pct < 0:
        return "Principal and years must be positive; rate can't be negative."
    months = int(round(years * 12))
    if months == 0:
        return "Term is too short — needs at least one month."
    monthly_rate = rate_pct / 100 / 12
    if monthly_rate == 0:
        payment = principal / months
    else:
        payment = principal * monthly_rate / (1 - (1 + monthly_rate) ** -months)
    total = payment * months
    interest = total - principal
    return (
        f"Monthly payment: ${payment:,.2f}\n"
        f"Total paid over {years:g} yr: ${total:,.2f}\n"
        f"Total interest: ${interest:,.2f}"
    )


# ---------------------------------------------------------------- system

def _read_meminfo() -> dict[str, int]:
    info: dict[str, int] = {}
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                k, _, rest = line.partition(":")
                info[k.strip()] = int(rest.strip().split()[0])
    except OSError:
        pass
    return info  # kB


def _fmt_gb(kb: int) -> str:
    return f"{kb / 1024 / 1024:.1f} GB"


def _run_system(trigger: str, args: str) -> str:
    lines = [f"Host: {platform.node() or 'unknown'}",
             f"OS: {platform.system()} {platform.release()} ({platform.machine()})",
             f"Python: {platform.python_version()}"]
    lines.append(f"CPUs: {os.cpu_count() or '?'}")
    try:
        load1, load5, load15 = os.getloadavg()
        lines.append(f"Load (1/5/15 min): {load1:.2f} / {load5:.2f} / {load15:.2f}")
    except OSError:
        pass
    mem = _read_meminfo()
    if mem:
        total = mem.get("MemTotal", 0)
        avail = mem.get("MemAvailable", mem.get("MemFree", 0))
        used_pct = (1 - avail / total) * 100 if total else 0
        lines.append(f"Memory: {_fmt_gb(total - avail)} / {_fmt_gb(total)} used ({used_pct:.0f}%)")
    try:
        d = shutil.disk_usage("/")
        pct = d.used / d.total * 100 if d.total else 0
        lines.append(f"Disk (/): {_fmt_gb(d.used // 1024)} / {_fmt_gb(d.total // 1024)} used ({pct:.0f}%)")
    except OSError:
        pass
    try:
        with open("/proc/uptime") as fh:
            up = float(fh.read().split()[0])
        days, rem = divmod(int(up), 86400)
        hrs, rem = divmod(rem, 3600)
        mins = rem // 60
        lines.append(f"Uptime: {days}d {hrs}h {mins}m")
    except (OSError, ValueError):
        pass
    return "\n".join(lines)


# ---------------------------------------------------------------- epoch

_ISO_DATE_RES = (
    re.compile(r"^(\d{4})-(\d{2})-(\d{2})$"),
    re.compile(r"^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?$"),
)


def _run_epoch(trigger: str, args: str) -> str:
    args = (args or "").strip()
    if not args:
        now = datetime.now(timezone.utc)
        ms = int(now.timestamp() * 1000)
        return (f"Now (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Epoch: {int(now.timestamp())} (ms: {ms})")
    if re.fullmatch(r"-?\d+", args):
        n = int(args)
        seconds = n / 1000 if abs(n) >= 10 ** 12 else float(n)
        try:
            dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return f"`{args}` is out of range for a timestamp."
        label = "ms" if abs(n) >= 10 ** 12 else "s"
        return (f"{args} ({label}) → {dt.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"Local: {dt.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    for rx in _ISO_DATE_RES:
        m = rx.match(args)
        if m:
            parts = [int(g) for g in m.groups() if g is not None]
            try:
                dt = datetime(*parts, tzinfo=timezone.utc)
            except ValueError as exc:
                return f"Not a real date/time: {exc}."
            ts = int(dt.timestamp())
            return (f"{args} (UTC) → epoch {ts}\n"
                    f"Local: {dt.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    return ("Usage: `epoch` for now, `epoch <seconds>` to convert a timestamp "
            "(ms detected automatically), or `epoch 2026-10-23 15:00` for the reverse.")


# ---------------------------------------------------------------- tz

_TZ_CONVERT_RE = re.compile(
    r"^(?:(\d{4}-\d{2}-\d{2})\s+)?(\d{1,2}:\d{2}(?::\d{2})?)\s+(\S+)\s+to\s+(\S+)$",
    re.IGNORECASE,
)


def _fmt_zone(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M %Z")


def _run_tz(trigger: str, args: str) -> str:
    args = (args or "").strip()
    if not args:
        return ("Usage: `tz <Zone>` for the current time there, or "
                "`tz <HH:MM> <ZoneA> to <ZoneB>` — e.g. `tz America/Winnipeg`, "
                "`tz 15:00 UTC to America/Winnipeg`.")
    m = _TZ_CONVERT_RE.match(args)
    if m:
        day_s, time_s, from_z, to_z = m.groups()
        try:
            from_zone = ZoneInfo(from_z)
        except ZoneInfoNotFoundError:
            return f"Unknown zone `{from_z}`. Use an IANA zone like `America/Winnipeg`."
        try:
            to_zone = ZoneInfo(to_z)
        except ZoneInfoNotFoundError:
            return f"Unknown zone `{to_z}`. Use an IANA zone like `America/Winnipeg`."
        day = day_s or datetime.now(from_zone).strftime("%Y-%m-%d")
        try:
            dt = datetime.strptime(f"{day} {time_s}", "%Y-%m-%d %H:%M:%S" if time_s.count(":") == 2 else "%Y-%m-%d %H:%M")
        except ValueError:
            return f"Couldn't parse `{time_s}` — use HH:MM, e.g. `15:00`."
        src = dt.replace(tzinfo=from_zone)
        dst = src.astimezone(to_zone)
        return f"{_fmt_zone(src)} → {_fmt_zone(dst)}"
    zone_name = args
    try:
        zone = ZoneInfo(zone_name)
    except ZoneInfoNotFoundError:
        known = [z for z in available_timezones() if zone_name.lower().replace(" ", "_") in z.lower()]
        hint = f" Did you mean: {', '.join(sorted(known)[:5])}?" if known else ""
        return f"Unknown zone `{zone_name}`.{hint}"
    return _fmt_zone(datetime.now(zone))


# ---------------------------------------------------------------- shuffle

def _run_shuffle(trigger: str, args: str) -> str:
    args = (args or "").strip()
    if not args:
        return ("Usage: `shuffle <item1>, <item2>, ...` or space-separated items — "
                "e.g. `shuffle alice, bob, carol`.")
    if "," in args:
        items = [i.strip() for i in args.split(",") if i.strip()]
    else:
        items = args.split()
    if len(items) < 2:
        return "Give me at least 2 items to shuffle — e.g. `shuffle alice, bob, carol`."
    shuffled = items[:]
    random.shuffle(shuffled)
    return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(shuffled))


# ---------------------------------------------------------------- countdown

_COUNTDOWN_RES = (
    re.compile(r"^(\d{4})-(\d{2})-(\d{2})$"),
    re.compile(r"^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?$"),
)


def _run_countdown(trigger: str, args: str) -> str:
    args = (args or "").strip()
    if not args:
        return "Usage: `countdown <YYYY-MM-DD [HH:MM]>` — e.g. `countdown 2026-12-25`, `countdown 2026-10-24 09:00`."
    for rx in _COUNTDOWN_RES:
        m = rx.match(args)
        if m:
            parts = [int(g) for g in m.groups() if g is not None]
            try:
                target = datetime(*parts)
            except ValueError as exc:
                return f"Not a real date/time: {exc}."
            delta = target - datetime.now()
            if delta.total_seconds() <= 0:
                return f"`{args}` already passed."
            days = delta.days
            hrs, rem = divmod(delta.seconds, 3600)
            mins, secs = divmod(rem, 60)
            bits = []
            if days:
                bits.append(f"{days} day{'s' if days != 1 else ''}")
            if hrs:
                bits.append(f"{hrs} hour{'s' if hrs != 1 else ''}")
            if mins:
                bits.append(f"{mins} minute{'s' if mins != 1 else ''}")
            if not bits:
                bits.append(f"{secs} second{'s' if secs != 1 else ''}")
            return f"{', '.join(bits)} until {target.strftime('%Y-%m-%d %H:%M')}"
    return "Couldn't parse that — use `YYYY-MM-DD` or `YYYY-MM-DD HH:MM`."


# ---------------------------------------------------------------- prime

_MR_BASES = (2, 3, 5, 7, 11, 13)  # deterministic for n < 3.3e24


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    if n in small:
        return True
    if any(n % p == 0 for p in small):
        return False
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in _MR_BASES:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _factorize(n: int, limit: int = 1_000_000) -> tuple[list[int], int]:
    """Trial division up to `limit`; returns (factors, remainder)."""
    factors: list[int] = []
    d = 2
    while d * d <= n and d <= limit:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1 if d == 2 else 2
    return factors, n


def _run_prime(trigger: str, args: str) -> str:
    args = (args or "").strip()
    if not re.fullmatch(r"\d+", args):
        return "Usage: `prime <integer>` — tests primality and factors it. E.g. `prime 97`, `prime 123456`."
    n = int(args)
    if n > 10 ** 18:
        return "Too big — I handle integers up to 10^18."
    if n < 2:
        return f"{n} is neither prime nor composite."
    if _is_prime(n):
        return f"{n} is prime."
    factors, rest = _factorize(n)
    if rest > 1 and not _is_prime(rest):
        return (f"{n} is composite = {' × '.join(map(str, factors))} × … "
                f"(remaining factor {rest} is too large to factor by trial division)")
    if rest > 1:
        factors.append(rest)
    return f"{n} is composite = {' × '.join(map(str, factors))}"


# ---------------------------------------------------------------- registration

def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="morse", description="Encode/decode morse code (auto-detects).",
        usage="morse <text> | morse <code>",
        triggers=["morse", "morsecode"],
        run=_run_morse,
        examples=["morse hello world", "morse .... . .-.. .-.. ---"]))
    registry.register(Skill(
        name="roman", description="Convert numbers to/from roman numerals.",
        usage="roman <number|numeral>", triggers=["roman", "numerals"],
        run=_run_roman,
        examples=["roman 2026", "roman MMXXVI"]))
    registry.register(Skill(
        name="loan", description="Loan/mortgage payment calculator.",
        usage="loan <principal> <annual-rate-%> <years>",
        triggers=["loan", "mortgage"],
        run=_run_loan,
        examples=["loan 250000 6.5 25", "loan 10000 5 3"]))
    registry.register(Skill(
        name="system", description="Local box stats: CPU, load, memory, disk, uptime.",
        usage="system", triggers=["system", "sysinfo"],
        run=_run_system,
        examples=["system"]))
    registry.register(Skill(
        name="epoch", description="Unix timestamp <-> date/time conversion.",
        usage="epoch [seconds|ms|YYYY-MM-DD [HH:MM]]",
        triggers=["epoch", "unixtime", "timestamp"],
        run=_run_epoch,
        examples=["epoch", "epoch 1760000000", "epoch 2026-10-23"]))
    registry.register(Skill(
        name="tz", description="Current time in a zone, or convert between zones.",
        usage="tz <Zone> | tz <HH:MM> <ZoneA> to <ZoneB>",
        triggers=["tz", "timezone"],
        run=_run_tz,
        examples=["tz America/Winnipeg", "tz 15:00 UTC to America/Winnipeg"]))
    registry.register(Skill(
        name="shuffle", description="Shuffle a list of items.",
        usage="shuffle <a>, <b>, ... | space-separated items",
        triggers=["shuffle", "randomize"],
        run=_run_shuffle,
        examples=["shuffle alice, bob, carol"]))
    registry.register(Skill(
        name="countdown", description="Time remaining until a date/time.",
        usage="countdown <YYYY-MM-DD [HH:MM]>",
        triggers=["countdown", "until"],
        run=_run_countdown,
        examples=["countdown 2026-12-25", "countdown 2026-10-24 09:00"]))
    registry.register(Skill(
        name="prime", description="Primality test + factorization.",
        usage="prime <integer>", triggers=["prime", "factor", "factors"],
        run=_run_prime,
        examples=["prime 97", "prime 123456"]))
