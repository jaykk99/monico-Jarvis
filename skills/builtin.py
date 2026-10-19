"""Built-in keyless skills: time, calc, notes, status, help, timer, dice, coin,
password, convert, todo, weather. No API keys needed."""
from __future__ import annotations

import ast
import json
import math
import operator
import os
import random
import re
import secrets
import string
import time as _time
from datetime import datetime, timezone
from pathlib import Path

from .base import Skill, SkillRegistry

DATA_DIR = Path(os.environ.get("MONICO_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
NOTES_FILE = DATA_DIR / "notes.json"
TODOS_FILE = DATA_DIR / "todos.json"
TIMERS_FILE = DATA_DIR / "timers.json"
MAX_NOTES = 100
MAX_TODOS = 100

_BOOT = _time.monotonic()

# ---------------------------------------------------------------- safe calculator

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_ALLOWED_NAMES = {"pi": math.pi, "e": math.e, "tau": math.tau}
_ALLOWED_FUNCS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log, "log10": math.log10, "exp": math.exp,
    "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil,
}


def _safe_eval(expr: str) -> float:
    """Evaluate an arithmetic expression with zero eval/exec. Raises ValueError on junk."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"not a valid expression: {expr!r}") from exc

    def _node(node: ast.AST):
        if isinstance(node, ast.Expression):
            return _node(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                return node.value
            raise ValueError("only numbers allowed")
        if isinstance(node, ast.BinOp):
            op = _ALLOWED_BINOPS.get(type(node.op))
            if op is None:
                raise ValueError(f"operator {type(node.op).__name__} not allowed")
            return op(_node(node.left), _node(node.right))
        if isinstance(node, ast.UnaryOp):
            op = _ALLOWED_UNARYOPS.get(type(node.op))
            if op is None:
                raise ValueError(f"operator {type(node.op).__name__} not allowed")
            return op(_node(node.operand))
        if isinstance(node, ast.Name):
            if node.id in _ALLOWED_NAMES:
                return _ALLOWED_NAMES[node.id]
            raise ValueError(f"unknown name {node.id!r}")
        if isinstance(node, ast.Call):
            func = _ALLOWED_FUNCS.get(getattr(node.func, "id", ""))
            if func is None or node.keywords:
                raise ValueError("only whitelisted math functions allowed")
            return func(*[_node(a) for a in node.args])
        raise ValueError(f"not allowed: {type(node).__name__}")

    return _node(tree)


def _fmt_number(value: float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return f"{value:.6g}"


# ---------------------------------------------------------------- notes store

def _load_notes() -> list[str]:
    if not NOTES_FILE.exists():
        return []
    try:
        data = json.loads(NOTES_FILE.read_text(encoding="utf-8"))
        return [str(n) for n in data] if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_notes(notes: list[str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_FILE.write_text(json.dumps(notes, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- json stores

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


# ---------------------------------------------------------------- skill handlers (trigger, args) -> reply

def _run_time(trigger: str, args: str) -> str:
    if args.strip().lower().startswith("utc"):
        now = datetime.now(timezone.utc)
        return f"UTC time is {now.strftime('%H:%M:%S')} on {now.strftime('%A, %B %d, %Y')}."
    now = datetime.now().astimezone()
    return f"It is {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}."


def _run_date(trigger: str, args: str) -> str:
    now = datetime.now().astimezone()
    return f"Today is {now.strftime('%A, %B %d, %Y')}."


def _run_calc(trigger: str, args: str) -> str:
    expr = args.strip()
    if not expr:
        return "Usage: calc <expression> — e.g. `calc (12 + 8) * 3`."
    try:
        return f"{expr} = {_fmt_number(_safe_eval(expr))}"
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        return f"Can't compute that: {exc}."


def _run_echo(trigger: str, args: str) -> str:
    text = args.strip()
    return text if text else "Usage: echo <text> — I repeat it back."


def _run_notes(trigger: str, args: str) -> str:
    text = args.strip()
    if trigger == "notes" and not text:
        notes = _load_notes()
        if not notes:
            return "No notes yet. Save one with `note <text>`."
        return "Your notes:\n" + "\n".join(f"{i + 1}. {n}" for i, n in enumerate(notes))
    if text.lower() in ("clear", "delete all"):
        _save_notes([])
        return "All notes cleared."
    if not text:
        return "Usage: `note <text>` to save, `notes` to list, `note clear` to wipe."
    notes = _load_notes()
    if len(notes) >= MAX_NOTES:
        return f"Note list is full ({MAX_NOTES}). Use `note clear` to wipe it."
    notes.append(text)
    _save_notes(notes)
    return f"Noted ({len(notes)} saved)."


def _run_status(registry: SkillRegistry):
    def handler(trigger: str, args: str) -> str:
        uptime = int(_time.monotonic() - _BOOT)
        h, rem = divmod(uptime, 3600)
        m, s = divmod(rem, 60)
        return (
            f"Monico Jarvis online — uptime {h}h {m}m {s}s, "
            f"{len(registry.all())} skills loaded, all local, no API keys."
        )
    return handler


def _run_help(registry: SkillRegistry):
    def handler(trigger: str, args: str) -> str:
        lines = [f"• {s.usage} — {s.description}" for s in registry.all()]
        return "Commands I understand:\n" + "\n".join(lines)
    return handler


# ---------------------------------------------------------------- new skills

_DURATION_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([smhd])\s*$", re.IGNORECASE)
_DURATION_NAMES = {"s": "second", "m": "minute", "h": "hour", "d": "day"}
_DURATION_SECS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _parse_duration(text: str):
    m = _DURATION_RE.match(text.strip())
    if not m:
        return None
    amount = float(m.group(1))
    unit = m.group(2).lower()
    return amount * _DURATION_SECS[unit]


def _fmt_duration(total_secs: float) -> str:
    total_secs = int(total_secs)
    if total_secs < 60:
        return f"{total_secs} second{'s' if total_secs != 1 else ''}"
    if total_secs < 3600:
        m = total_secs // 60
        return f"{m} minute{'s' if m != 1 else ''}"
    h = total_secs // 3600
    rem_m = (total_secs % 3600) // 60
    s = f"{h} hour{'s' if h != 1 else ''}"
    return s + (f" {rem_m}m" if rem_m else "")


def _run_timer(trigger: str, args: str) -> str:
    args = args.strip()
    if trigger in ("timers",) or not args:
        timers = _load_json(TIMERS_FILE, [])
        now = _time.time()
        lines = []
        for t in timers:
            left = t["ends_at"] - now
            state = "DONE — time's up!" if left <= 0 else f"{_fmt_duration(left)} left"
            lines.append(f"• {t['label']} — {state}")
        _save_json(TIMERS_FILE, [t for t in timers if t["ends_at"] > now - 3600])
        if not lines:
            return "No timers set. Use `timer 5m` or `timer 30s` to start one."
        return "Timers:\n" + "\n".join(lines)
    if args.lower() in ("clear", "cancel", "delete all"):
        _save_json(TIMERS_FILE, [])
        return "All timers cleared."
    # allow "timer 5m label text here"
    parts = args.split(None, 1)
    secs = _parse_duration(parts[0])
    if secs is None or secs <= 0:
        return "Usage: `timer 5m` — units s/m/h/d, e.g. `timer 30s`, `timer 1h`."
    if secs > 86400 * 7:
        return "Max timer is 7 days."
    label = parts[1].strip() if len(parts) > 1 else f"{parts[0]} timer"
    timers = _load_json(TIMERS_FILE, [])
    ends_at = _time.time() + secs
    timers.append({"label": label[:80], "ends_at": ends_at, "set_at": _time.time()})
    _save_json(TIMERS_FILE, timers)
    end = datetime.fromtimestamp(ends_at).astimezone().strftime("%I:%M %p")
    return (
        f"Timer set: {label} — {_fmt_duration(secs)}, ends at {end}. "
        f"Ask me `timers` anytime to check it."
    )


_DICE_RE = re.compile(r"^\s*(\d{1,3})?\s*[dD]\s*(\d{1,4})\s*$")


def _run_dice(trigger: str, args: str) -> str:
    args = args.strip()
    if not args:
        n, sides = 1, 6
    else:
        m = _DICE_RE.match(args)
        if m:
            n = int(m.group(1) or 1)
            sides = int(m.group(2))
        elif args.isdigit():
            n, sides = 1, int(args)
        else:
            return "Usage: `dice` or `dice 20` or `dice 2d6`."
        if not (1 <= sides <= 1000):
            return "Dice need 1–1000 sides."
        if not (1 <= n <= 100):
            return "Roll at most 100 dice at once."
    rolls = [random.randint(1, sides) for _ in range(n)]
    total = sum(rolls)
    if n == 1:
        return f"Rolled d{sides}: **{rolls[0]}**"
    return f"Rolled {n}d{sides}: {', '.join(map(str, rolls))} = **{total}**"


def _run_coin(trigger: str, args: str) -> str:
    return f"It's **{random.choice(['heads', 'tails'])}**."


def _run_password(trigger: str, args: str) -> str:
    args = args.strip()
    length = 16
    if args:
        if not args.isdigit():
            return "Usage: `password [length]` — e.g. `password 20`."
        length = int(args)
        if not (8 <= length <= 128):
            return "Password length must be 8–128."
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_+=?"
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in pw) and any(c.isupper() for c in pw)
                and any(c.isdigit() for c in pw)):
            return f"Your password ({length} chars):\n`{pw}`\nI didn't save it — copy it now."


# unit conversions ----------------------------------------------------

_LENGTH_TO_M = {
    "mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0,
    "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344,
}
_WEIGHT_TO_KG = {
    "g": 0.001, "kg": 1.0, "oz": 0.028349523125, "lb": 0.45359237, "lbs": 0.45359237,
}
_TEMP_UNITS = {"c", "f", "k", "celsius", "fahrenheit", "kelvin"}

_CONVERT_RE = re.compile(
    r"^\s*([-+]?\d+(?:\.\d+)?)\s*([a-zA-Z°]+)\s+(?:to\s+)?([a-zA-Z°]+)\s*$"
)


def _norm_unit(u: str) -> str:
    u = u.lower().replace("°", "")
    aliases = {
        "millimeter": "mm", "millimeters": "mm",
        "centimeter": "cm", "centimeters": "cm",
        "meter": "m", "meters": "m",
        "kilometer": "km", "kilometers": "km",
        "inch": "in", "inches": "in",
        "foot": "ft", "feet": "ft",
        "yard": "yd", "yards": "yd",
        "mile": "mi", "miles": "mi",
        "gram": "g", "grams": "g",
        "kilogram": "kg", "kilograms": "kg", "kilo": "kg", "kilos": "kg",
        "ounce": "oz", "ounces": "oz",
        "pound": "lb", "pounds": "lb",
    }
    return aliases.get(u, u)


def _convert_temp(value: float, frm: str, to: str):
    f = frm[0]
    t = to[0]
    if f == t:
        return value
    # to celsius first
    if f == "f":
        c = (value - 32) * 5 / 9
    elif f == "k":
        c = value - 273.15
    else:
        c = value
    if t == "f":
        return c * 9 / 5 + 32
    if t == "k":
        return c + 273.15
    return c


def _run_convert(trigger: str, args: str) -> str:
    m = _CONVERT_RE.match(args or "")
    if not m:
        return ("Usage: `convert <value> <from> to <to>` — e.g. `convert 5 ft to m`, "
                "`convert 72 f to c`, `convert 10 lb to kg`.")
    value = float(m.group(1))
    frm = _norm_unit(m.group(2))
    to = _norm_unit(m.group(3))
    if frm in _TEMP_UNITS or to in _TEMP_UNITS:
        if frm[0] not in "cfk" or to[0] not in "cfk":
            return "Temperature units: c, f, k (celsius, fahrenheit, kelvin)."
        result = _convert_temp(value, frm, to)
        return f"{_fmt_number(value)}°{frm[0].upper()} = {_fmt_number(result)}°{to[0].upper()}"
    if frm in _LENGTH_TO_M and to in _LENGTH_TO_M:
        result = value * _LENGTH_TO_M[frm] / _LENGTH_TO_M[to]
        return f"{_fmt_number(value)} {frm} = {_fmt_number(result)} {to}"
    if frm in _WEIGHT_TO_KG and to in _WEIGHT_TO_KG:
        result = value * _WEIGHT_TO_KG[frm] / _WEIGHT_TO_KG[to]
        return f"{_fmt_number(value)} {frm} = {_fmt_number(result)} {to}"
    return ("I can convert length (mm, cm, m, km, in, ft, yd, mi), "
            "weight (g, kg, oz, lb), and temperature (c, f, k).")


# todo list ------------------------------------------------------------

def _run_todo(trigger: str, args: str) -> str:
    args = args.strip()
    todos = _load_json(TODOS_FILE, [])
    if trigger == "todos" and not args:
        args = "list"
    parts = args.split(None, 1)
    action = (parts[0] if parts else "list").lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    if action in ("list", "ls"):
        if not todos:
            return "Todo list is empty. Add one with `todo buy milk`."
        lines = []
        for i, t in enumerate(todos, 1):
            mark = "x" if t.get("done") else " "
            lines.append(f"{i}. [{mark}] {t['text']}")
        open_n = sum(1 for t in todos if not t.get("done"))
        return f"Todo ({open_n} open):\n" + "\n".join(lines)

    if action == "add":
        if not rest:
            return "Usage: `todo add <text>`."
        if len(todos) >= MAX_TODOS:
            return f"Todo list is full ({MAX_TODOS}). Clear done ones with `todo clear`."
        todos.append({"text": rest[:200], "done": False})
        _save_json(TODOS_FILE, todos)
        return f"Added: {rest[:200]} ({len(todos)} total)."

    if action in ("done", "check", "complete"):
        if not rest or not rest.isdigit():
            return "Usage: `todo done <number>` — see numbers with `todos`."
        idx = int(rest) - 1
        if not (0 <= idx < len(todos)):
            return f"No todo #{rest}."
        todos[idx]["done"] = True
        _save_json(TODOS_FILE, todos)
        return f"Done: {todos[idx]['text']}"

    if action in ("clear", "clean"):
        todos = [t for t in todos if not t.get("done")]
        _save_json(TODOS_FILE, todos)
        return f"Cleared completed. {len(todos)} remaining."

    if action in ("del", "delete", "rm", "remove"):
        if not rest or not rest.isdigit():
            return "Usage: `todo del <number>`."
        idx = int(rest) - 1
        if not (0 <= idx < len(todos)):
            return f"No todo #{rest}."
        removed = todos.pop(idx)
        _save_json(TODOS_FILE, todos)
        return f"Removed: {removed['text']}"

    # bare text after "todo" = add it
    if args and action not in ("add", "list", "done", "clear", "del"):
        todos.append({"text": args[:200], "done": False})
        _save_json(TODOS_FILE, todos)
        return f"Added: {args[:200]} ({len(todos)} total)."

    return ("Usage: `todo <text>` to add, `todos` to list, `todo done <n>`, "
            "`todo del <n>`, `todo clear`.")


def _run_weather(trigger: str, args: str) -> str:
    return ("I can't check the weather — that needs a weather API key, and I run "
            "100% keyless with no network calls. Try your phone's weather app.")


# ---------------------------------------------------------------- registration

def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="time", description="Current local time (say `time utc` for UTC).",
        usage="time [utc]", triggers=["time"], run=_run_time,
        examples=["time", "time utc"]))
    registry.register(Skill(
        name="date", description="Today's date.",
        usage="date", triggers=["date"], run=_run_date,
        examples=["date"]))
    registry.register(Skill(
        name="calc", description="Safe arithmetic calculator (no keys, no network).",
        usage="calc <expression>", triggers=["calc", "calculate"], run=_run_calc,
        examples=["calc (12 + 8) * 3", "calc sqrt(144)"]))
    registry.register(Skill(
        name="echo", description="Repeat text back.",
        usage="echo <text>", triggers=["echo", "say"], run=_run_echo,
        examples=["echo hello world"]))
    registry.register(Skill(
        name="notes", description="Save and list quick notes (stored locally).",
        usage="note <text> | notes | note clear",
        triggers=["note", "notes", "remember"], run=_run_notes,
        examples=["note buy milk", "notes", "note clear"]))
    registry.register(Skill(
        name="status", description="Service status and uptime.",
        usage="status", triggers=["status", "ping", "health"],
        run=_run_status(registry), examples=["status"]))
    registry.register(Skill(
        name="timer", description="Set a countdown timer; `timers` checks them.",
        usage="timer <5m|30s|1h> [label] | timers | timer clear",
        triggers=["timer", "timers", "countdown"],
        run=_run_timer,
        examples=["timer 5m", "timer 30s pizza", "timers"]))
    registry.register(Skill(
        name="dice", description="Roll dice — d6, d20, or NdM like 2d6.",
        usage="dice [sides] | dice <NdM>",
        triggers=["dice", "roll"],
        run=_run_dice,
        examples=["dice", "dice 20", "dice 2d6"]))
    registry.register(Skill(
        name="coin", description="Flip a coin.",
        usage="coin", triggers=["coin", "flip"],
        run=_run_coin,
        examples=["coin"]))
    registry.register(Skill(
        name="password", description="Generate a secure random password (never saved).",
        usage="password [length]", triggers=["password", "pass", "genpass"],
        run=_run_password,
        examples=["password", "password 20"]))
    registry.register(Skill(
        name="convert", description="Convert length, weight, and temperature units.",
        usage="convert <value> <from> to <to>",
        triggers=["convert", "conversion"],
        run=_run_convert,
        examples=["convert 5 ft to m", "convert 72 f to c", "convert 10 lb to kg"]))
    registry.register(Skill(
        name="todo", description="Simple todo list, saved locally.",
        usage="todo <text> | todos | todo done <n> | todo del <n> | todo clear",
        triggers=["todo", "todos"],
        run=_run_todo,
        examples=["todo buy milk", "todos", "todo done 1"]))
    registry.register(Skill(
        name="weather", description="Weather lookup (honest: needs an API key, not available).",
        usage="weather", triggers=["weather", "forecast"],
        run=_run_weather,
        examples=["weather"]))
    registry.register(Skill(
        name="help", description="List every command.",
        usage="help", triggers=["help", "commands", "?"],
        run=_run_help(registry), examples=["help"]))
