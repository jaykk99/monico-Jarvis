"""Text-tool skills: all local, keyless, no network.

hash, uuid, words, case, b64, url, json, pick — small utilities a personal
agent gets asked for constantly.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import random
import re
import uuid
from urllib.parse import quote, unquote

from .base import Skill, SkillRegistry

# ---------------------------------------------------------------- hash

_HASH_ALGOS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
    "blake2b": hashlib.blake2b,
}


def _run_hash(trigger: str, args: str) -> str:
    parts = (args or "").strip().split(None, 1)
    # `md5 hello` / `sha256 hello` — the trigger word itself names the algo
    trigger_algo = trigger.lower() if trigger.lower() in _HASH_ALGOS else None
    if trigger_algo and (not parts or parts[0].lower() not in _HASH_ALGOS):
        algo, text = trigger_algo, (args or "").strip()
    else:
        if not parts:
            return ("Usage: `hash <algo> <text>` — algos: "
                    + ", ".join(sorted(_HASH_ALGOS))
                    + ". e.g. `hash sha256 hello`.")
        algo = parts[0].lower()
        text = parts[1] if len(parts) > 1 else ""
    if algo not in _HASH_ALGOS:
        return ("Unknown algorithm. Pick one of: "
                + ", ".join(sorted(_HASH_ALGOS)) + ".")
    if not text.strip():
        return f"Usage: `hash {algo} <text>` — nothing to hash."
    digest = _HASH_ALGOS[algo](text.encode("utf-8")).hexdigest()
    return f"{algo}:\n`{digest}`"


# ---------------------------------------------------------------- uuid

def _run_uuid(trigger: str, args: str) -> str:
    args = (args or "").strip()
    count = 1
    if args:
        if not args.isdigit():
            return "Usage: `uuid [count]` — e.g. `uuid 5` (max 20)."
        count = int(args)
        if not (1 <= count <= 20):
            return "Count must be 1–20."
    ids = [str(uuid.uuid4()) for _ in range(count)]
    if count == 1:
        return f"`{ids[0]}`"
    return "\n".join(f"`{u}`" for u in ids)


# ---------------------------------------------------------------- words (counts)

def _run_words(trigger: str, args: str) -> str:
    text = args or ""
    if not text.strip():
        return "Usage: `words <text>` — I count words, characters, and lines."
    words = len(text.split())
    chars = len(text)
    chars_nospace = len(re.sub(r"\s", "", text))
    lines = text.count("\n") + 1
    return (f"{words} word{'s' if words != 1 else ''}, "
            f"{chars} characters ({chars_nospace} without spaces), "
            f"{lines} line{'s' if lines != 1 else ''}.")


# ---------------------------------------------------------------- case

_CASE_MODES = {
    "upper": str.upper, "uppercase": str.upper,
    "lower": str.lower, "lowercase": str.lower,
    "title": str.title, "capitalize": str.capitalize,
    "swap": str.swapcase,
}


def _to_camel(text: str) -> str:
    parts = re.split(r"[\s_\-]+", text.strip())
    if not parts:
        return text
    return parts[0].lower() + "".join(p[:1].upper() + p[1:].lower() for p in parts[1:])


def _to_snake(text: str) -> str:
    text = re.sub(r"[\s\-]+", "_", text.strip())
    text = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", text)
    return text.lower()


def _run_case(trigger: str, args: str) -> str:
    parts = (args or "").strip().split(None, 1)
    if len(parts) < 2:
        return ("Usage: `case <upper|lower|title|capitalize|swap|camel|snake> <text>` — "
                "e.g. `case title hello world`.")
    mode, text = parts[0].lower(), parts[1]
    if mode in _CASE_MODES:
        return _CASE_MODES[mode](text)
    if mode == "camel":
        return _to_camel(text)
    if mode == "snake":
        return _to_snake(text)
    return ("Unknown case. Use upper, lower, title, capitalize, swap, camel, or snake.")


# ---------------------------------------------------------------- base64

def _run_b64(trigger: str, args: str) -> str:
    parts = (args or "").strip().split(None, 1)
    if len(parts) < 2 or parts[0].lower() not in ("encode", "decode"):
        return "Usage: `b64 encode <text>` or `b64 decode <base64>`."
    mode, text = parts[0].lower(), parts[1]
    try:
        if mode == "encode":
            return base64.b64encode(text.encode("utf-8")).decode("ascii")
        raw = base64.b64decode(text.strip(), validate=True)
        return raw.decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return "That doesn't look like valid base64." if mode == "decode" \
            else "Couldn't encode that text."


# ---------------------------------------------------------------- url encode/decode

def _run_url(trigger: str, args: str) -> str:
    parts = (args or "").strip().split(None, 1)
    if len(parts) < 2 or parts[0].lower() not in ("encode", "decode"):
        return "Usage: `url encode <text>` or `url decode <text>`."
    mode, text = parts[0].lower(), parts[1]
    if mode == "encode":
        return quote(text, safe="")
    try:
        return unquote(text)
    except Exception:
        return "Couldn't decode that URL text."


# ---------------------------------------------------------------- json validate/pretty

def _run_json(trigger: str, args: str) -> str:
    text = (args or "").strip()
    if not text:
        return "Usage: `json <text>` — I validate it and pretty-print it."
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return f"Not valid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})."
    pretty = json.dumps(data, indent=2, ensure_ascii=False)
    if len(pretty) > 4000:
        return f"Valid JSON. Too long to print fully ({len(pretty)} chars) — first 4000:\n{pretty[:4000]}"
    return f"Valid JSON:\n```\n{pretty}\n```"


# ---------------------------------------------------------------- pick (random choice)

def _run_pick(trigger: str, args: str) -> str:
    raw = (args or "").strip()
    if not raw:
        return "Usage: `pick <option1>, <option2>, ...` — I choose one at random."
    options = [o.strip() for o in re.split(r"[,;]|\bor\b", raw) if o.strip()]
    if len(options) < 2:
        return "Give me at least two options separated by commas."
    if len(options) > 50:
        return "Too many options (max 50)."
    return f"I pick: **{random.choice(options)}**"


# ---------------------------------------------------------------- registration

def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="hash", description="Hash text locally (md5, sha1, sha256, sha512, blake2b).",
        usage="hash <algo> <text>", triggers=["hash", "sha256", "md5", "sha1"],
        run=_run_hash, examples=["hash sha256 hello"]))
    registry.register(Skill(
        name="uuid", description="Generate random UUIDs (v4), locally.",
        usage="uuid [count]", triggers=["uuid", "guid"],
        run=_run_uuid, examples=["uuid", "uuid 5"]))
    registry.register(Skill(
        name="words", description="Count words, characters, and lines in text.",
        usage="words <text>", triggers=["words", "count", "wc"],
        run=_run_words, examples=["words hello brave new world"]))
    registry.register(Skill(
        name="case", description="Change text case: upper, lower, title, camel, snake…",
        usage="case <mode> <text>", triggers=["case", "uppercase", "lowercase"],
        run=_run_case, examples=["case title hello world", "case camel my variable"]))
    registry.register(Skill(
        name="b64", description="Base64 encode/decode, locally.",
        usage="b64 <encode|decode> <text>", triggers=["b64", "base64"],
        run=_run_b64, examples=["b64 encode hello", "b64 decode aGVsbG8="]))
    registry.register(Skill(
        name="url", description="URL percent-encode/decode, locally.",
        usage="url <encode|decode> <text>", triggers=["url", "urlencode", "urldecode"],
        run=_run_url, examples=["url encode hello world?"]))
    registry.register(Skill(
        name="json", description="Validate JSON and pretty-print it.",
        usage="json <text>", triggers=["json", "jsonlint"],
        run=_run_json, examples=['json {"a":1}']))
    registry.register(Skill(
        name="pick", description="Pick one option at random from a list.",
        usage="pick <a>, <b>, ...", triggers=["pick", "choose", "decide"],
        run=_run_pick, examples=["pick pizza, sushi, tacos"]))
