"""Weather-math helpers: wind chill, heat index, dew point, humidex.

All local, keyless, no network — same contract as the rest of skills/.
These compute feels-like numbers from temperatures you give them; they
do NOT look up the weather (that needs an API key, see the honest
`weather` skill in builtin.py).

Formulas used (published, standard):
- Wind chill: the Environment Canada / US National Weather Service
  formula, valid at or below 10 C with wind at or above 4.8 km/h.
- Heat index: the Rothfusz regression, valid at or above 80 F (27 C)
  with relative humidity at or above 40%.
- Dew point: the Magnus formula from air temperature and relative
  humidity.
- Humidex: the Canadian humidex, from air temperature and dew point
  (via the Magnus formula), as used by Environment Canada.

Conventions and explicit caveats:
- All four are estimates from formulas, not measurements. Wind chill
  and heat index describe how the air feels on exposed skin, not the
  temperature a thermometer reads.
- Wind chill only applies in the cold (at or below 10 C); above that
  the wind does not make the air feel colder in any meaningful way.
  In near-calm air (under 4.8 km/h) there is no wind-chill effect.
- Heat index only applies in the heat (at or above 27 C / 80 F) with
  real humidity; below that it is just the air temperature.
- Frostbite and heat-danger times are rough Environment Canada / NWS
  guidance for exposed skin, not medical advice — wind, sun, clothing,
  age, and health all change the real risk.
- A plain number with no unit is read as Celsius for temperatures and
  km/h for wind speed; use F / mph suffixes for imperial.
"""
from __future__ import annotations

import math
import re

from .base import Skill, SkillRegistry


def _num(token: str) -> float | None:
    """Parse a number, tolerating thousands commas."""
    token = token.strip().replace(",", "")
    try:
        return float(token)
    except ValueError:
        return None


def _fmt_num(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _fmt_temp_c(celsius: float) -> str:
    """Format a Celsius value with its Fahrenheit equivalent in brackets."""
    fahr = celsius * 9.0 / 5.0 + 32.0
    return f"{_fmt_num(round(celsius, 1))} C ({_fmt_num(round(fahr, 1))} F)"


# ---------------------------------------------------------------- parsing

_TEMP_RE = re.compile(r"^(-?\d+(?:\.\d+)?)\s*([cCfF])?$")
_SPEED_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*(km/h|kmh|mph|kph)?$", re.IGNORECASE)
_RH_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*%?$")


def _parse_temp(token: str) -> tuple[float, str] | None:
    """Parse a temperature token. Returns (celsius, display) or None.

    Accepts `30C`, `86F`, `-15`, `30 C`. A bare number is Celsius.
    """
    m = _TEMP_RE.match(token.strip())
    if not m:
        return None
    value = float(m.group(1))
    unit = (m.group(2) or "C").upper()
    if unit == "F":
        return (value - 32.0) * 5.0 / 9.0, f"{_fmt_num(value)} F"
    return value, f"{_fmt_num(value)} C"


def _parse_speed(token: str) -> tuple[float, str] | None:
    """Parse a wind-speed token. Returns (km/h, display) or None.

    Accepts `30kmh`, `30km/h`, `20mph`, `30`. A bare number is km/h.
    """
    m = _SPEED_RE.match(token.strip())
    if not m:
        return None
    value = float(m.group(1))
    unit = (m.group(2) or "kmh").lower()
    if unit == "mph":
        return value * 1.609344, f"{_fmt_num(value)} mph"
    return value, f"{_fmt_num(value)} km/h"


def _parse_rh(token: str) -> float | None:
    """Parse a relative-humidity token (`60%` or `60`). Returns 0-100 or None."""
    m = _RH_RE.match(token.strip())
    if not m:
        return None
    value = float(m.group(1))
    if value <= 0 or value > 100:
        return None
    return value


def _dewpoint_c(temp_c: float, rh: float) -> float:
    """Dew point in Celsius (Magnus formula, a=17.27, b=237.7)."""
    a, b = 17.27, 237.7
    alpha = (a * temp_c) / (b + temp_c) + math.log(rh / 100.0)
    return (b * alpha) / (a - alpha)


def _humidex(temp_c: float, dewpoint_c: float) -> float:
    """Canadian humidex from air temp and dew point, both Celsius."""
    vapour = 6.11 * 10.0 ** ((7.5 * dewpoint_c) / (237.7 + dewpoint_c))
    return temp_c + 0.5555 * (vapour - 10.0)


# ---------------------------------------------------------------- windchill

_USAGE_WINDCHILL = (
    "Usage: `windchill <temp>C|F <wind>kmh|mph` — e.g. "
    "`windchill -15C 30kmh`, `windchill 5F 20mph`. "
    "Only applies at or below 10 C with wind at or above 4.8 km/h."
)


def _run_windchill(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 2:
        return _USAGE_WINDCHILL
    temp = _parse_temp(parts[0])
    wind = _parse_speed(parts[1])
    if temp is None or wind is None:
        return _USAGE_WINDCHILL
    temp_c, temp_display = temp
    wind_kmh, wind_display = wind
    if temp_c > 10:
        return (f"At {temp_display} it is too warm for wind chill — the "
                "formula only applies at or below 10 C (50 F). It just "
                f"feels like {temp_display}.")
    if wind_kmh < 4.8:
        return (f"At {wind_display} the air is near calm, so there is no "
                f"wind-chill effect — it feels like {temp_display}.")
    v_pow = wind_kmh ** 0.16
    wc = 13.12 + 0.6215 * temp_c - 11.37 * v_pow + 0.3965 * temp_c * v_pow
    wc = round(wc, 1)
    if wc <= -48:
        risk = ("Dangerous cold — exposed skin can freeze in under "
                "5 minutes. Stay inside if you can.")
    elif wc <= -40:
        risk = ("Exposed skin can freeze in 5-10 minutes. Cover all "
                "exposed skin.")
    elif wc <= -28:
        risk = ("Exposed skin can freeze in 10-30 minutes. Cover up "
                "and limit time outside.")
    else:
        risk = "Cold, but no immediate frostbite risk for brief exposure."
    return (f"Wind chill {_fmt_temp_c(wc)} at {temp_display} with a "
            f"{wind_display} wind. {risk} Wind chill is how cold it feels "
            "on exposed skin, not the air temperature — and the "
            "frostbite times are rough guidance, not medical advice.")


# ---------------------------------------------------------------- heatindex

_USAGE_HEATINDEX = (
    "Usage: `heatindex <temp>C|F <humidity>%` — e.g. "
    "`heatindex 32C 70%`, `heatindex 90F 65%`. "
    "Only applies at or above 27 C (80 F) with humidity at or above 40%."
)


def _run_heatindex(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 2:
        return _USAGE_HEATINDEX
    temp = _parse_temp(parts[0])
    rh = _parse_rh(parts[1])
    if temp is None or rh is None:
        return _USAGE_HEATINDEX
    temp_c, temp_display = temp
    temp_f = temp_c * 9.0 / 5.0 + 32.0
    if temp_f < 80:
        return (f"At {temp_display} it is too cool for a heat index — the "
                "formula only applies at or above 27 C (80 F). It just "
                f"feels like {temp_display}.")
    if rh < 40:
        return (f"At {rh:g}% humidity the air is too dry for a heat "
                "index — the formula needs at least 40% humidity. It just "
                f"feels like {temp_display}.")
    t, r = temp_f, rh
    hi = (-42.379 + 2.04901523 * t + 10.14333127 * r
          - 0.22475541 * t * r - 0.00683783 * t * t
          - 0.05481717 * r * r + 0.00122874 * t * t * r
          + 0.00085282 * t * r * r - 0.00000199 * t * t * r * r)
    if r < 13 and 80 <= t <= 112:
        hi -= ((13 - r) / 4) * math.sqrt((17 - abs(t - 95)) / 17)
    elif r > 85 and 80 <= t <= 87:
        hi += ((r - 85) / 10) * ((87 - t) / 5)
    hi_f = round(hi, 1)
    hi_c = round((hi_f - 32.0) * 5.0 / 9.0, 1)
    if hi_f < 80:
        band = "No real heat concern."
    elif hi_f < 91:
        band = ("Caution — fatigue is possible with prolonged activity. "
                "Take breaks and drink water.")
    elif hi_f < 104:
        band = ("Extreme caution — heat cramps or exhaustion are "
                "possible. Limit exertion and stay hydrated.")
    elif hi_f < 125:
        band = ("Danger — heat cramps or exhaustion are likely, and "
                "heat stroke is possible. Avoid exertion outdoors.")
    else:
        band = ("Extreme danger — heat stroke is highly likely. Stay "
                "out of the heat.")
    return (f"Heat index {_fmt_temp_c(hi_c)} at {temp_display} and "
            f"{rh:g}% humidity. {band} The heat index is how hot it feels "
            "in the shade — full sun can add up to 8 C (15 F) — and the "
            "danger bands are rough guidance, not medical advice.")


# ---------------------------------------------------------------- dewpoint

_USAGE_DEWPOINT = (
    "Usage: `dewpoint <temp>C|F <humidity>%` — e.g. "
    "`dewpoint 25C 60%`, `dewpoint 77F 50%`."
)


def _run_dewpoint(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 2:
        return _USAGE_DEWPOINT
    temp = _parse_temp(parts[0])
    rh = _parse_rh(parts[1])
    if temp is None or rh is None:
        return _USAGE_DEWPOINT
    temp_c, temp_display = temp
    td = round(_dewpoint_c(temp_c, rh), 1)
    if td < 10:
        feel = "dry and comfortable — the air feels crisp."
    elif td < 13:
        feel = "very comfortable."
    elif td < 16:
        feel = "comfortable for most people."
    elif td < 18:
        feel = "a little sticky — most people start to notice the humidity."
    elif td < 21:
        feel = "sticky and muggy."
    elif td < 24:
        feel = "oppressive — the air feels heavy and uncomfortable."
    else:
        feel = "miserable — extremely humid, like a tropical afternoon."
    extra = ""
    if td <= 0:
        extra = (" With a dew point at or below freezing, frost can form "
                 "on cold surfaces overnight.")
    return (f"Dew point {_fmt_temp_c(td)} at {temp_display} and "
            f"{rh:g}% humidity — {feel}{extra} The dew point is the "
            "temperature the air must cool to before dew (or frost) forms.")


# ---------------------------------------------------------------- humidex

_USAGE_HUMIDEX = (
    "Usage: `humidex <temp>C|F <humidity>%` — e.g. "
    "`humidex 30C 60%`, `humidex 86F 50%`. "
    "Canadian humidex, from temperature and humidity."
)


def _run_humidex(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 2:
        return _USAGE_HUMIDEX
    temp = _parse_temp(parts[0])
    rh = _parse_rh(parts[1])
    if temp is None or rh is None:
        return _USAGE_HUMIDEX
    temp_c, temp_display = temp
    td = _dewpoint_c(temp_c, rh)
    hx = round(_humidex(temp_c, td), 1)
    if hx < 30:
        band = "Comfortable — little to no discomfort."
    elif hx < 40:
        band = ("Some discomfort — pace yourself and drink water if you "
                "are working outside.")
    elif hx < 46:
        band = ("Great discomfort — avoid exertion outdoors, stay in the "
                "shade and drink plenty of water.")
    else:
        band = ("Dangerous — heat stroke is possible. Stay out of the "
                "heat and check on anyone working outside.")
    return (f"Humidex {_fmt_num(hx)} at {temp_display} and {rh:g}% "
            f"humidity (dew point {_fmt_temp_c(round(td, 1))}). {band} "
            "The humidex is Environment Canada's feels-like number for "
            "hot, humid air — a formula estimate, not medical advice.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="windchill", description="Wind chill from air temperature and wind speed.",
        usage="windchill <temp>C|F <wind>kmh|mph",
        triggers=["windchill", "wind-chill", "windchillfactor"],
        run=_run_windchill,
        examples=["windchill -15C 30kmh", "windchill 5F 20mph"]))
    registry.register(Skill(
        name="heatindex", description="Heat index from air temperature and humidity.",
        usage="heatindex <temp>C|F <humidity>%",
        triggers=["heatindex", "heat-index", "feelslike"],
        run=_run_heatindex,
        examples=["heatindex 32C 70%", "heatindex 90F 65%"]))
    registry.register(Skill(
        name="dewpoint", description="Dew point and humidity comfort from temperature and humidity.",
        usage="dewpoint <temp>C|F <humidity>%",
        triggers=["dewpoint", "dew-point"],
        run=_run_dewpoint,
        examples=["dewpoint 25C 60%", "dewpoint 77F 50%"]))
    registry.register(Skill(
        name="humidex", description="Canadian humidex from temperature and humidity.",
        usage="humidex <temp>C|F <humidity>%",
        triggers=["humidex"],
        run=_run_humidex,
        examples=["humidex 30C 60%", "humidex 86F 50%"]))
