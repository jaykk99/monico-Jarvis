"""Built-in keyless skills: time, calc, notes, status, help. No API keys needed."""
from __future__ import annotations

import ast
import json
import math
import operator
import os
import time as _time
from datetime import datetime, timezone
from pathlib import Path

from .base import Skill, SkillRegistry

DATA_DIR = Path(os.environ.get("MONICO_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
NOTES_FILE = DATA_DIR / "notes.json"
MAX_NOTES = 100

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
        name="help", description="List every command.",
        usage="help", triggers=["help", "commands", "?"],
        run=_run_help(registry), examples=["help"]))
