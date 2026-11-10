"""Car math helpers: stopping distance, tire pressure, oil changes, towing.

All local, keyless, no network — same contract as the rest of skills/.
These are estimates from published formulas and rules of thumb for
everyday driving questions; they do NOT read your car (no OBD, no
telematics) and they are not a substitute for your owner's manual or a
mechanic.

Formulas and rules used:
- Stopping distance: reaction distance (speed x 1.5 s reaction time)
  plus braking distance v^2 / (2 * mu * g), with textbook friction
  coefficients — dry asphalt 0.7, wet 0.4, snow 0.25, ice 0.1.
- Tire pressure: the ideal gas law on absolute pressure — a tire set
  cold holds its air, so pressure rises and falls with temperature.
  The rough rule of thumb (~1 psi per 10 F / 5.6 C) is shown as a
  cross-check, not the answer.
- Oil change: whichever limit hits first — kilometres driven since the
  last change against the interval, or months elapsed against the
  time interval.
- Towing: trailer weight against the vehicle's tow rating, with tongue
  weight at 10-15% of the trailer (the standard safe range), and a
  note that heavy trailers need their own brakes.

Conventions and explicit caveats:
- A plain number with no unit is read as km/h for speed, psi for
  tire pressure, kg for weights, and km for distances.
- Stopping distances assume good tires and brakes on a flat road.
  Worn tires, bad brakes, a downhill slope, or a slower reaction all
  make the real distance longer — leave extra room.
- Tire pressures are COLD pressures: check before driving or after
  the car has sat for a few hours. A tire driven on the highway runs
  about 4-6 psi higher than cold — never let air out of a hot tire
  to hit the cold number.
- Oil intervals come from your owner's manual, not from this skill:
  many cars say 8,000-16,000 km or 6-12 months, whichever comes
  first. Severe use (short trips, cold starts, towing, dust) shortens
  the interval.
- Tow ratings are the manufacturer's maximum for your exact vehicle
  and hitch — the rating on the hitch itself can be lower, and the
  lower of the two wins. Never exceed either.
"""
from __future__ import annotations

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


def _fmt_dist_m(metres: float) -> str:
    """Format a distance in metres with its feet equivalent in brackets."""
    feet = metres * 3.28084
    return f"{_fmt_num(round(metres, 1))} m ({_fmt_num(round(feet))} ft)"


# ---------------------------------------------------------------- parsing

_SPEED_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*(km/h|kmh|mph|kph)?$", re.IGNORECASE)
_PRESSURE_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*(psi|kpa|bar)?$", re.IGNORECASE)
_TEMP_RE = re.compile(r"^(-?\d+(?:\.\d+)?)\s*([cCfF])?$")
_WEIGHT_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*(kg|lb|lbs)?$", re.IGNORECASE)
_DIST_RE = re.compile(r"^(-?\d+(?:\.\d+)?)\s*(km|mi)?$", re.IGNORECASE)
_MONTHS_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*(mo|months?)?$", re.IGNORECASE)

_ATM_PSI = 14.696  # standard atmosphere, for gauge <-> absolute pressure


def _parse_speed(token: str) -> tuple[float, str] | None:
    """Parse a speed token. Returns (km/h, display) or None.

    Accepts `100kmh`, `100km/h`, `60mph`, `100`. A bare number is km/h.
    """
    m = _SPEED_RE.match(token.strip())
    if not m:
        return None
    value = float(m.group(1))
    unit = (m.group(2) or "kmh").lower()
    if unit == "mph":
        return value * 1.609344, f"{_fmt_num(value)} mph"
    return value, f"{_fmt_num(value)} km/h"


def _parse_pressure(token: str) -> tuple[float, str] | None:
    """Parse a tire-pressure token. Returns (psi, display) or None.

    Accepts `32psi`, `220kpa`, `2.2bar`, `32`. A bare number is psi.
    """
    m = _PRESSURE_RE.match(token.strip())
    if not m:
        return None
    value = float(m.group(1))
    unit = (m.group(2) or "psi").lower()
    if unit == "kpa":
        return value / 6.89476, f"{_fmt_num(value)} kPa"
    if unit == "bar":
        return value * 14.5038, f"{_fmt_num(value)} bar"
    return value, f"{_fmt_num(value)} psi"


def _parse_temp_c(token: str) -> float | None:
    """Parse a temperature token. Returns Celsius or None.

    Accepts `20C`, `68F`, `-20`. A bare number is Celsius.
    """
    m = _TEMP_RE.match(token.strip())
    if not m:
        return None
    value = float(m.group(1))
    unit = (m.group(2) or "C").upper()
    if unit == "F":
        return (value - 32.0) * 5.0 / 9.0
    return value


def _parse_weight_kg(token: str) -> tuple[float, str] | None:
    """Parse a weight token. Returns (kg, display) or None.

    Accepts `1500kg`, `3300lb`, `1500`. A bare number is kg.
    """
    m = _WEIGHT_RE.match(token.strip())
    if not m:
        return None
    value = float(m.group(1))
    unit = (m.group(2) or "kg").lower()
    if unit in ("lb", "lbs"):
        return value * 0.45359237, f"{_fmt_num(value)} lb"
    return value, f"{_fmt_num(value)} kg"


def _parse_dist_km(token: str) -> float | None:
    """Parse a distance token. Returns km or None.

    Accepts `8000km`, `5000mi`, `8000`. A bare number is km.
    """
    m = _DIST_RE.match(token.strip())
    if not m:
        return None
    value = float(m.group(1))
    unit = (m.group(2) or "km").lower()
    if unit == "mi":
        return value * 1.609344
    return value


def _parse_months(token: str) -> float | None:
    """Parse a months token (`6mo`, `6months`, `6`). Returns months or None."""
    m = _MONTHS_RE.match(token.strip())
    if not m:
        return None
    return float(m.group(1))


def _fmt_pressure_psi(psi: float, original_unit: str) -> str:
    """Format a psi value back in the unit the user gave (psi/kPa/bar)."""
    if original_unit == "kpa":
        return f"{_fmt_num(round(psi * 6.89476))} kPa ({_fmt_num(round(psi, 1))} psi)"
    if original_unit == "bar":
        return f"{_fmt_num(round(psi / 14.5038, 2))} bar ({_fmt_num(round(psi, 1))} psi)"
    return f"{_fmt_num(round(psi, 1))} psi"


def _fmt_weight_kg(kg: float) -> str:
    """Format a weight in kg with its lb equivalent in brackets."""
    lb = kg * 2.20462
    return f"{_fmt_num(round(kg))} kg ({_fmt_num(round(lb))} lb)"


# ---------------------------------------------------------------- brake

_ROAD_MU = {
    "dry": (0.7, "dry asphalt"),
    "wet": (0.4, "wet asphalt"),
    "snow": (0.25, "snow"),
    "ice": (0.1, "ice"),
}

_USAGE_BRAKE = (
    "Usage: `brake <speed>kmh|mph [dry|wet|snow|ice]` — e.g. "
    "`brake 100kmh dry`, `brake 60mph snow`. Road defaults to dry."
)


def _run_brake(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) not in (1, 2):
        return _USAGE_BRAKE
    speed = _parse_speed(parts[0])
    if speed is None:
        return _USAGE_BRAKE
    condition = "dry"
    if len(parts) == 2:
        condition = parts[1].lower()
        if condition not in _ROAD_MU:
            return _USAGE_BRAKE
    speed_kmh, speed_display = speed
    if speed_kmh <= 0:
        return "Speed has to be above 0."
    if speed_kmh > 300:
        return "That speed is past any road car — check the number and try again."
    mu, road_label = _ROAD_MU[condition]
    v = speed_kmh / 3.6  # m/s
    reaction = v * 1.5  # 1.5 s reaction time
    braking = v * v / (2 * mu * 9.81)
    total = reaction + braking
    car_lengths = total / 4.5  # a typical car is about 4.5 m long
    if condition == "dry":
        note = "On dry asphalt with good tires and brakes."
    elif condition == "wet":
        note = ("Wet roads roughly double the braking distance — and "
                "standing water can hydroplane, which is worse still.")
    elif condition == "snow":
        note = ("Snow roughly quadruples the braking distance versus "
                "dry — leave a much bigger gap.")
    else:
        note = ("Ice is the worst case here: about seven times the dry "
                "braking distance. Slow right down and leave a very "
                "big gap.")
    return (f"Stopping from {speed_display} on {road_label}: "
            f"{_fmt_dist_m(total)} in total — "
            f"{_fmt_dist_m(reaction)} reacting (1.5 s) plus "
            f"{_fmt_dist_m(braking)} braking, about "
            f"{_fmt_num(round(car_lengths, 1))} car lengths. {note} "
            "These assume good tires and brakes on a flat road — worn "
            "tires, bad brakes, a downhill, or a slower reaction all "
            "make it longer.")


# ---------------------------------------------------------------- tire

_USAGE_TIRE = (
    "Usage: `tire <pressure>psi|kpa|bar <from-temp>C|F <to-temp>C|F` — e.g. "
    "`tire 32psi -20C 20C`, `tire 220kpa -30C 20C`. "
    "Shows what a tire set at one temperature reads at another."
)


def _run_tire(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) != 3:
        return _USAGE_TIRE
    pressure = _parse_pressure(parts[0])
    t1 = _parse_temp_c(parts[1])
    t2 = _parse_temp_c(parts[2])
    if pressure is None or t1 is None or t2 is None:
        return _USAGE_TIRE
    psi, pressure_display = pressure
    if psi <= 0:
        return "Pressure has to be above 0."
    if psi > 120:
        return "That pressure is past any road tire — check the number and try again."
    if t1 < -60 or t1 > 60 or t2 < -60 or t2 > 60:
        return "Temperatures should be between -60 C and 60 C."
    unit = (re.search(r"(psi|kpa|bar)$", parts[0].strip(), re.IGNORECASE) or [None])[0]
    unit = (unit or "psi").lower()
    # Ideal gas law on absolute pressure (gauge + atmosphere).
    new_psi = (psi + _ATM_PSI) * (t2 + 273.15) / (t1 + 273.15) - _ATM_PSI
    delta = new_psi - psi
    # Rule-of-thumb cross-check: about 1 psi per 10 F (5.6 C).
    thumb = (t2 - t1) / 5.6
    direction = "rises" if delta > 0.05 else ("falls" if delta < -0.05 else "barely changes")
    if abs(delta) < 0.05:
        return (f"A tire set to {pressure_display} at "
                f"{_fmt_num(t1)} C reads about the same at "
                f"{_fmt_num(t2)} C — the temperature barely changed, so "
                "the pressure barely changes either. Always check "
                "pressures cold, before driving.")
    return (f"A tire set to {pressure_display} at {_fmt_num(t1)} C "
            f"{direction} to about {_fmt_pressure_psi(new_psi, unit)} at "
            f"{_fmt_num(t2)} C ({delta:+.1f} psi). As a rough check, the "
            f"rule of thumb says about {thumb:+.1f} psi for that "
            "temperature change. Set pressures cold — a tire driven on "
            "the highway runs 4-6 psi higher than cold, so never let "
            "air out of a hot tire to hit the cold number.")


# ---------------------------------------------------------------- oil

_USAGE_OIL = (
    "Usage: `oil <km-since>km <interval>km [months-since]mo [months-interval]mo` — e.g. "
    "`oil 8000km 10000km`, `oil 8000km 10000km 5mo 6mo`. "
    "Whichever limit hits first — km or months — is the due date."
)


def _run_oil(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) not in (2, 4):
        return _USAGE_OIL
    km_since = _parse_dist_km(parts[0])
    interval = _parse_dist_km(parts[1])
    if km_since is None or interval is None:
        return _USAGE_OIL
    if km_since < 0 or interval <= 0:
        return "Kilometres since the change can't be negative, and the interval has to be above 0."
    months_since = months_interval = None
    if len(parts) == 4:
        months_since = _parse_months(parts[2])
        months_interval = _parse_months(parts[3])
        if months_since is None or months_interval is None:
            return _USAGE_OIL
        if months_since < 0 or months_interval <= 0:
            return "Months since the change can't be negative, and the months interval has to be above 0."
    km_left = interval - km_since
    km_pct = km_since / interval * 100
    bits = []
    if km_left <= 0:
        bits.append(f"overdue by {_fmt_num(-km_left)} km — change it now")
    elif km_left <= interval * 0.1:
        bits.append(f"due soon — only {_fmt_num(km_left)} km left of the {_fmt_num(interval)} km interval")
    else:
        bits.append(f"{_fmt_num(km_left)} km left of the {_fmt_num(interval)} km interval")
    months_msg = ""
    if months_since is not None:
        months_left = months_interval - months_since
        if months_left <= 0:
            months_msg = f", and overdue by {_fmt_num(-months_left)} month(s) on time"
        elif months_left <= 1:
            months_msg = f", and only {_fmt_num(months_left)} month(s) left on time"
        else:
            months_msg = f", with {_fmt_num(months_left)} month(s) left on time"
    if km_left <= 0 or (months_since is not None and months_interval - months_since <= 0):
        verdict = "Time for an oil change."
    elif km_left <= interval * 0.1 or (months_since is not None and months_interval - months_since <= 1):
        verdict = "Almost due — book it in."
    else:
        verdict = "Not due yet."
    return (f"Oil: {_fmt_num(km_since)} km since the last change, "
            f"{km_pct:.0f}% through the {_fmt_num(interval)} km interval — "
            f"{bits[0]}{months_msg}. {verdict} Use the interval in your "
            "owner's manual (often 8,000-16,000 km or 6-12 months, "
            "whichever comes first); short trips, cold starts, towing, "
            "and dust shorten it.")


# ---------------------------------------------------------------- tow

_USAGE_TOW = (
    "Usage: `tow <trailer-weight>kg|lb <tow-rating>kg|lb [tongue-%]` — e.g. "
    "`tow 1500kg 2000kg`, `tow 5000lb 7000lb 12`. "
    "Tongue weight defaults to 12% of the trailer."
)


def _run_tow(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) not in (2, 3):
        return _USAGE_TOW
    trailer = _parse_weight_kg(parts[0])
    rating = _parse_weight_kg(parts[1])
    if trailer is None or rating is None:
        return _USAGE_TOW
    tongue_pct = 12.0
    if len(parts) == 3:
        tongue_pct = _num(parts[2].rstrip("%"))
        if tongue_pct is None:
            return _USAGE_TOW
    trailer_kg, trailer_display = trailer
    rating_kg, rating_display = rating
    if trailer_kg <= 0 or rating_kg <= 0:
        return "Trailer weight and tow rating both have to be above 0."
    if tongue_pct < 5 or tongue_pct > 25:
        return "Tongue weight should be 5-25% of the trailer — 10-15% is the usual safe range."
    margin_kg = rating_kg - trailer_kg
    pct_of_rating = trailer_kg / rating_kg * 100
    tongue_kg = trailer_kg * tongue_pct / 100
    if margin_kg < 0:
        verdict = (f"OVER the tow rating by {_fmt_weight_kg(-margin_kg)} — "
                   "do not tow this. Overloading the rating strains the "
                   "transmission and brakes and can void insurance.")
    elif pct_of_rating >= 90:
        verdict = (f"Within the rating, but only {_fmt_weight_kg(margin_kg)} "
                   "of headroom left — pack light and keep speeds down, "
                   "and remember cargo in the truck counts too.")
    else:
        verdict = (f"Within the rating with {_fmt_weight_kg(margin_kg)} "
                   "to spare — the trailer is "
                   f"{pct_of_rating:.0f}% of the rated maximum.")
    if tongue_pct < 10:
        tongue_note = ("That tongue weight is light — under 10% the "
                       "trailer can sway. Aim for 10-15%.")
    elif tongue_pct > 15:
        tongue_note = ("That tongue weight is heavy — over 15% overloads "
                       "the rear axle and lightens the steering. Aim for "
                       "10-15%.")
    else:
        tongue_note = "That tongue weight is in the safe 10-15% range."
    brakes_note = ""
    if trailer_kg > 910:
        brakes_note = (" Trailers over about 910 kg (2,000 lb) need their "
                       "own brakes in most places — check your local rules.")
    return (f"Towing: a {_fmt_weight_kg(trailer_kg)} trailer against a "
            f"{_fmt_weight_kg(rating_kg)} tow rating "
            f"({pct_of_rating:.0f}% of the rating). {verdict} Tongue "
            f"weight at {tongue_pct:g}% is {_fmt_weight_kg(tongue_kg)}. "
            f"{tongue_note}{brakes_note} The rating on the hitch itself "
            "can be lower than the vehicle's — the lower of the two wins.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="brake", description="Stopping distance from speed and road condition.",
        usage="brake <speed>kmh|mph [dry|wet|snow|ice]",
        triggers=["brake", "braking", "stoppingdistance", "stopping-distance"],
        run=_run_brake,
        examples=["brake 100kmh dry", "brake 60mph snow"]))
    registry.register(Skill(
        name="tire", description="Tire pressure change with temperature (ideal gas law).",
        usage="tire <pressure>psi|kpa|bar <from-temp>C|F <to-temp>C|F",
        triggers=["tire", "tirepressure", "tire-pressure", "tirepsi"],
        run=_run_tire,
        examples=["tire 32psi -20C 20C", "tire 220kpa -30C 20C"]))
    registry.register(Skill(
        name="oil", description="Oil-change due check by km and months since the last change.",
        usage="oil <km-since>km <interval>km [months-since]mo [months-interval]mo",
        triggers=["oil", "oilchange", "oil-change"],
        run=_run_oil,
        examples=["oil 8000km 10000km", "oil 8000km 10000km 5mo 6mo"]))
    registry.register(Skill(
        name="tow", description="Towing check: trailer weight vs tow rating and tongue weight.",
        usage="tow <trailer-weight>kg|lb <tow-rating>kg|lb [tongue-%]",
        triggers=["tow", "towing", "towrating"],
        run=_run_tow,
        examples=["tow 1500kg 2000kg", "tow 5000lb 7000lb 12"]))
