"""Utility skills: color conversion, age calculator, lorem ipsum, slugify.

All local, keyless, no network. Things a personal agent gets asked for
constantly and every one of them runs offline.
"""
from __future__ import annotations

import calendar
import colorsys
import random
import re
import unicodedata
from datetime import date

from .base import Skill, SkillRegistry

# ---------------------------------------------------------------- color

# Curated common CSS color names -> hex. A handy lookup, not a full palette.
_NAMED_COLORS = {
    "black": "000000", "white": "ffffff", "red": "ff0000",
    "green": "008000", "lime": "00ff00", "blue": "0000ff",
    "navy": "000080", "yellow": "ffff00", "orange": "ffa500",
    "purple": "800080", "pink": "ffc0cb", "brown": "a52a2a",
    "gray": "808080", "grey": "808080", "silver": "c0c0c0",
    "gold": "ffd700", "cyan": "00ffff", "aqua": "00ffff",
    "magenta": "ff00ff", "fuchsia": "ff00ff", "teal": "008080",
    "olive": "808000", "maroon": "800000", "coral": "ff7f50",
    "salmon": "fa8072", "crimson": "dc143c", "tomato": "ff6347",
    "indigo": "4b0082", "violet": "ee82ee", "turquoise": "40e0d0",
    "skyblue": "87ceeb", "royalblue": "4169e1", "steelblue": "4682b4",
    "khaki": "f0e68c", "beige": "f5f5dc", "ivory": "fffff0",
    "mint": "98ff98", "peach": "ffdab9", "lavender": "e6e6fa",
    "charcoal": "36454f", "slate": "708090", "burgundy": "800020",
    "forestgreen": "228b22", "darkgreen": "006400",
    "lightblue": "add8e6", "darkblue": "00008b",
}

_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")
_RGB_RE = re.compile(r"^\s*rgb\s*\(?\s*(\d{1,3})\s*[, ]\s*(\d{1,3})\s*[, ]\s*(\d{1,3})\s*\)?\s*$", re.IGNORECASE)
_TRIPLE_RE = re.compile(r"^\s*(\d{1,3})\s*[, ]\s*(\d{1,3})\s*[, ]\s*(\d{1,3})\s*$")
_HSL_RE = re.compile(
    r"^\s*hsl\s*\(?\s*(\d{1,3})\s*(?:[,°]?\s*)\s*(\d{1,3})\s*%?\s*[, ]\s*(\d{1,3})\s*%?\s*\)?\s*$",
    re.IGNORECASE,
)


def _expand_hex(h: str) -> str:
    h = h.lower()
    return "".join(c * 2 for c in h) if len(h) == 3 else h


def _rgb_from_hex(h: str) -> tuple[int, int, int]:
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _describe_color(hex6: str) -> str:
    r, g, b = _rgb_from_hex(hex6)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return (
        f"HEX `#{hex6}`\n"
        f"RGB ({r}, {g}, {b})\n"
        f"HSL ({round(h * 360)}°, {round(s * 100)}%, {round(l * 100)}%)"
    )


def _run_color(trigger: str, args: str) -> str:
    args = (args or "").strip()
    if not args:
        return ("Usage: `color <#hex>` or `color rgb <r> <g> <b>` or "
                "`color hsl <h> <s> <l>` or `color <name>` — e.g. `color #ff8800`.")
    low = args.lower()
    if low in _NAMED_COLORS:
        return _describe_color(_NAMED_COLORS[low])
    m = _HEX_RE.match(args)
    if m:
        return _describe_color(_expand_hex(m.group(1)))
    m = _RGB_RE.match(args) or _TRIPLE_RE.match(args)
    if m:
        r, g, b = (int(m.group(i)) for i in (1, 2, 3))
        if all(0 <= v <= 255 for v in (r, g, b)):
            return _describe_color(f"{r:02x}{g:02x}{b:02x}")
        return "RGB values must be 0–255."
    m = _HSL_RE.match(args)
    if m:
        h, s, l = (int(m.group(i)) for i in (1, 2, 3))
        if not (0 <= h <= 360 and 0 <= s <= 100 and 0 <= l <= 100):
            return "HSL ranges: hue 0–360, saturation 0–100, lightness 0–100."
        r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
        return _describe_color(f"{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}")
    return ("I didn't recognize that color. Try a hex like `#ff8800`, "
            "`rgb 255 136 0`, `hsl 32 100 50`, or a name like `orange`.")


# ---------------------------------------------------------------- age calculator

_DATE_RES = [
    (re.compile(r"^\s*(\d{4})-(\d{1,2})-(\d{1,2})\s*$"),
     lambda m: date(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
    (re.compile(r"^\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$"),
     lambda m: date(int(m.group(3)), int(m.group(1)), int(m.group(2)))),
]


def _parse_birthdate(text: str):
    for rx, build in _DATE_RES:
        m = rx.match(text.strip())
        if m:
            try:
                return build(m)
            except ValueError:
                return None
    return None


def _shift_months(d: date, months: int) -> date:
    """Add months to a date, clamping the day to the month length (Feb 29 safe)."""
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _run_age(trigger: str, args: str) -> str:
    born = _parse_birthdate(args or "")
    if not born:
        return ("Usage: `age <birthdate>` — e.g. `age 1990-05-01` or "
                "`age 05/01/1990`.")
    today = date.today()
    if born > today:
        return f"{born.isoformat()} is in the future — not born yet."
    years = today.year - born.year - (
        (today.month, today.day) < (born.month, born.day)
    )
    # walk month-by-month from the last birthday for the months/days remainder
    anchor = _shift_months(born, years * 12)
    months = 0
    while _shift_months(anchor, months + 1) <= today:
        months += 1
    anchor = _shift_months(anchor, months)
    days = (today - anchor).days
    total_days = (today - born).days
    # next birthday (Feb 29 birthdays land on Mar 1 in non-leap years)
    next_bday = None
    for y in (today.year, today.year + 1):
        try:
            cand = date(y, born.month, born.day)
        except ValueError:
            cand = date(y, 3, 1)
        if cand >= today:
            next_bday = cand
            break
    assert next_bday is not None
    to_bday = (next_bday - today).days
    bday_line = ("Birthday is today — happy birthday!"
                 if to_bday == 0
                 else f"Next birthday in {to_bday} day{'s' if to_bday != 1 else ''} "
                      f"({next_bday.strftime('%A, %B %d, %Y')}).")
    return (
        f"Born {born.isoformat()} ({born.strftime('%A')}): "
        f"{years} year{'s' if years != 1 else ''}, "
        f"{months} month{'s' if months != 1 else ''}, "
        f"{days} day{'s' if days != 1 else ''} old "
        f"({total_days:,} days total).\n{bday_line}"
    )


# ---------------------------------------------------------------- lorem ipsum

_LOREM_WORDS = (
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua enim ad minim veniam "
    "quis nostrud exercitation ullamco laboris nisi aliquip ex ea commodo "
    "consequat duis aute irure in reprehenderit voluptate velit esse cillum "
    "fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt "
    "culpa qui officia deserunt mollit anim id est laborum perspiciatis unde "
    "omnis iste natus error voluptatem accusantium doloremque laudantium totam "
    "rem aperiam eaque ipsa quae ab illo inventore veritatis quasi architecto "
    "beatae vitae dicta explicabo nemo enim ipsam voluptatem quia voluptas sit "
    "aspernatur aut odit fugit consequuntur magni dolores eos ratione "
    "sequi nesciunt neque porro quisquam dolorem numquam eius modi tempora "
    "incidunt magnam quaerat".split()
)


def _lorem_sentence() -> str:
    words = [random.choice(_LOREM_WORDS)
             for _ in range(random.randint(6, 14))]
    words[0] = words[0].capitalize()
    return " ".join(words) + "."


def _lorem_paragraph() -> str:
    return " ".join(_lorem_sentence() for _ in range(random.randint(3, 6)))


def _run_lorem(trigger: str, args: str) -> str:
    args = (args or "").strip().lower()
    if not args:
        count, unit = 3, "paragraphs"
    else:
        m = re.match(r"^(\d+)\s*(paragraphs?|sentences?|words?)?$", args)
        if not m:
            return ("Usage: `lorem [n] [paragraphs|sentences|words]` — e.g. "
                    "`lorem 2`, `lorem 3 sentences`, `lorem 50 words`.")
        count = int(m.group(1))
        unit = (m.group(2) or "paragraphs").rstrip("s") + "s"
        if count < 1 or count > 20:
            return "Count must be 1–20."
    if unit == "paragraphs":
        return "\n\n".join(_lorem_paragraph() for _ in range(count))
    if unit == "sentences":
        return " ".join(_lorem_sentence() for _ in range(count))
    words = [random.choice(_LOREM_WORDS) for _ in range(count)]
    words[0] = words[0].capitalize()
    return " ".join(words) + "."


# ---------------------------------------------------------------- slugify

def _run_slug(trigger: str, args: str) -> str:
    text = (args or "").strip()
    if not text:
        return "Usage: `slug <text>` — e.g. `slug Hello World!` → `hello-world`."
    # strip accents, drop non-ascii
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug:
        return "Nothing slug-worthy in that text."
    if len(slug) > 80:
        slug = slug[:80].rstrip("-")
    return f"`{slug}`"


# ---------------------------------------------------------------- registration

def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="color", description="Convert colors: hex, RGB, HSL, and named colors.",
        usage="color <#hex|rgb r g b|hsl h s l|name>",
        triggers=["color", "colour"],
        run=_run_color,
        examples=["color #ff8800", "color rgb 255 136 0", "color orange"]))
    registry.register(Skill(
        name="age", description="Age calculator: years/months/days from a birthdate.",
        usage="age <birthdate>", triggers=["age", "birthday", "howold"],
        run=_run_age,
        examples=["age 1990-05-01", "age 05/01/1990"]))
    registry.register(Skill(
        name="lorem", description="Generate lorem ipsum placeholder text.",
        usage="lorem [n] [paragraphs|sentences|words]",
        triggers=["lorem", "ipsum", "placeholder"],
        run=_run_lorem,
        examples=["lorem", "lorem 2", "lorem 3 sentences", "lorem 50 words"]))
    registry.register(Skill(
        name="slug", description="Slugify text for URLs/filenames.",
        usage="slug <text>", triggers=["slug", "slugify"],
        run=_run_slug,
        examples=["slug Hello World!", "slug My Cool Post"]))
