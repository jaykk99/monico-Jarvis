"""Electrical estimators: watts, circuit load, bulbs, battery runtime.

All local, keyless, no network — same contract as the rest of skills/.
Plain arithmetic only, following the build pattern: counts are rounded
up to whole buyable units, and every figure is an estimate.

Conventions and explicit caveats:
- Watts: any two of volts, amps, watts gives the third (P = V x I).
  This is the DC / resistive-AC arithmetic; real AC circuits with
  motors and power factor differ, so treat the result as planning
  math, not a measurement.
- Circuit: capacity is breaker amps x volts, and the 80% figure is
  the usual continuous-load planning guideline. It is NOT code
  advice: breaker and wire sizing, and any mains work, is a
  licensed-electrician question, not an arithmetic one.
- Bulb: target brightness defaults to 200 lumens per m2 (20 per
  sq ft), a general living-space level. Task lighting, high
  ceilings, and dark finishes need more; the count is a starting
  point, not a lighting design.
- Runtime: battery energy is amp-hours x volts, or watt-hours
  directly. The default figure is ideal — before inverter and
  conversion losses. Pass an efficiency (``85%``) to derate it;
  real runtime is shorter, and deep-discharging a battery past
  its rated limit damages it, so do not plan to use every last
  watt-hour.
"""
from __future__ import annotations

import math
import re

from .base import Skill, SkillRegistry


def _num(token: str) -> float | None:
    """Parse a number, tolerating a leading $ and thousands commas."""
    token = token.lstrip("$").replace(",", "")
    try:
        return float(token)
    except ValueError:
        return None


def _fmt_num(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _fmt_minutes(minutes: float) -> str:
    whole = int(round(minutes))
    if whole < 60:
        return f"{whole} minutes"
    hours, mins = divmod(whole, 60)
    if mins == 0:
        return f"{hours}h ({whole} minutes)"
    return f"{hours}h {mins}m ({whole} minutes)"


_VOLT_RE = re.compile(r"^([0-9]*\.?[0-9]+)v$")
_AMP_RE = re.compile(r"^([0-9]*\.?[0-9]+)a$")
_WATT_RE = re.compile(r"^([0-9]*\.?[0-9]+)w$")
_AH_RE = re.compile(r"^([0-9]*\.?[0-9]+)ah$")
_WH_RE = re.compile(r"^([0-9]*\.?[0-9]+)wh$")
_AREA_M_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqm$")
_AREA_FT_RE = re.compile(r"^([0-9]*\.?[0-9]+)sqft$")


# ---------------------------------------------------------------- watts

_USAGE_WATTS = (
    "Usage: `watts <volts>V <amps>A` | `watts <watts>W <volts>V` | "
    "`watts <watts>W <amps>A` — e.g. `watts 120V 10A`, `watts 1200W 120V`."
)


def _run_watts(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) != 2:
        return _USAGE_WATTS
    values: dict[str, float] = {}
    for token in tokens:
        for key, rx in (("V", _VOLT_RE), ("A", _AMP_RE), ("W", _WATT_RE)):
            m = rx.match(token)
            if m:
                if key in values:
                    return _USAGE_WATTS
                values[key] = float(m.group(1))
                break
        else:
            return _USAGE_WATTS
    if len(values) != 2:
        return _USAGE_WATTS
    if any(v <= 0 for v in values.values()):
        return "Volts, amps, and watts must be greater than 0."
    if "V" in values and "A" in values:
        watts = values["V"] * values["A"]
        return (f"{_fmt_num(values['V'])} V x {_fmt_num(values['A'])} A = "
                f"{_fmt_num(watts)} W.")
    if "W" in values and "V" in values:
        amps = values["W"] / values["V"]
        return (f"{_fmt_num(values['W'])} W at {_fmt_num(values['V'])} V = "
                f"{_fmt_num(amps)} A.")
    amps = values["A"]
    volts = values["W"] / amps
    return (f"{_fmt_num(values['W'])} W at {_fmt_num(amps)} A = "
            f"{_fmt_num(volts)} V.")


# ---------------------------------------------------------------- circuit

_USAGE_CIRCUIT = (
    "Usage: `circuit <breaker>A <volts>V <load>W...` — e.g. "
    "`circuit 15A 120V 800 400`, `circuit 20A 120V 1500`."
)


def _run_circuit(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) < 3:
        return _USAGE_CIRCUIT
    bm = _AMP_RE.match(tokens[0])
    vm = _VOLT_RE.match(tokens[1])
    if not bm or not vm:
        return _USAGE_CIRCUIT
    breaker = float(bm.group(1))
    volts = float(vm.group(1))
    loads = []
    for token in tokens[2:]:
        wm = _WATT_RE.match(token)
        if wm:
            loads.append(float(wm.group(1)))
        else:
            w = _num(token)
            if w is None:
                return _USAGE_CIRCUIT
            loads.append(w)
    if breaker <= 0 or volts <= 0:
        return "Breaker amps and volts must be greater than 0."
    if any(w <= 0 for w in loads):
        return "Loads must be greater than 0."
    capacity = breaker * volts
    continuous = capacity * 0.8
    load = sum(loads)
    if load <= continuous:
        verdict = "within the 80% continuous guideline"
    elif load <= capacity:
        verdict = "over the 80% continuous guideline but under the breaker rating"
    else:
        verdict = "over the breaker rating"
    return (f"{_fmt_num(breaker)} A x {_fmt_num(volts)} V = "
            f"{_fmt_num(capacity)} W capacity "
            f"({_fmt_num(continuous)} W at 80% continuous) — "
            f"load {_fmt_num(load)} W is {verdict} "
            f"(planning guideline only, not code advice).")


# ---------------------------------------------------------------- bulb

_USAGE_BULB = (
    "Usage: `bulb <area>sqm [lumens-per-bulb]` | "
    "`bulb <area>sqft [lumens-per-bulb]` — e.g. "
    "`bulb 20sqm`, `bulb 200sqft 1600`."
)

_BULB_LM_M = 200.0
_BULB_LM_FT = 20.0
_BULB_DEFAULT = 800.0


def _run_bulb(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if not tokens or len(tokens) > 2:
        return _USAGE_BULB
    mm = _AREA_M_RE.match(tokens[0])
    mf = _AREA_FT_RE.match(tokens[0])
    if mm:
        area = float(mm.group(1))
        target = _BULB_LM_M
        unit = "m²"
    elif mf:
        area = float(mf.group(1))
        target = _BULB_LM_FT
        unit = "sq ft"
    else:
        return _USAGE_BULB
    per_bulb = _BULB_DEFAULT
    if len(tokens) == 2:
        per = _num(tokens[1])
        if per is None:
            return _USAGE_BULB
        per_bulb = per
    if area <= 0:
        return "Area must be greater than 0."
    if per_bulb <= 0:
        return "Lumens per bulb must be greater than 0."
    total = area * target
    bulbs = math.ceil(round(total / per_bulb, 9))
    return (f"{_fmt_num(area)} {unit} at {_fmt_num(target)} lumens per {unit} "
            f"needs {_fmt_num(total)} lumens — "
            f"buy {bulbs} bulbs ({_fmt_num(per_bulb)} lumens each).")


# ---------------------------------------------------------------- runtime

_USAGE_RUNTIME = (
    "Usage: `runtime <amp-hours>Ah <volts>V <load>W [efficiency%]` | "
    "`runtime <watt-hours>Wh <load>W [efficiency%]` — e.g. "
    "`runtime 100Ah 12V 50W`, `runtime 500Wh 50W 85%`."
)


def _parse_efficiency(rest: list[str]) -> float | None:
    """Optional trailing efficiency percent (``85%`` or bare ``85``)."""
    if not rest:
        return 100.0
    if len(rest) > 1:
        return None
    eff = _num(rest[0].rstrip("%"))
    if eff is None or eff <= 0 or eff > 100:
        return None
    return eff


def _run_runtime(trigger: str, args: str) -> str:
    tokens = (args or "").strip().lower().split()
    if len(tokens) < 2:
        return _USAGE_RUNTIME
    ahm = _AH_RE.match(tokens[0])
    whm = _WH_RE.match(tokens[0])
    if ahm:
        amp_hours = float(ahm.group(1))
        if len(tokens) < 3:
            return _USAGE_RUNTIME
        vm = _VOLT_RE.match(tokens[1])
        wm = _WATT_RE.match(tokens[2])
        if not vm or not wm:
            return _USAGE_RUNTIME
        volts = float(vm.group(1))
        load = float(wm.group(1))
        rest = tokens[3:]
        energy_label = (f"{_fmt_num(amp_hours)} Ah x {_fmt_num(volts)} V = "
                        f"{_fmt_num(amp_hours * volts)} Wh")
        watt_hours = amp_hours * volts
        if amp_hours <= 0 or volts <= 0:
            return "Amp-hours and volts must be greater than 0."
    elif whm:
        watt_hours = float(whm.group(1))
        wm = _WATT_RE.match(tokens[1])
        if not wm:
            return _USAGE_RUNTIME
        load = float(wm.group(1))
        rest = tokens[2:]
        energy_label = f"{_fmt_num(watt_hours)} Wh"
        if watt_hours <= 0:
            return "Watt-hours must be greater than 0."
    else:
        return _USAGE_RUNTIME
    if load <= 0:
        return "Load must be greater than 0."
    if len(rest) > 1:
        return _USAGE_RUNTIME
    efficiency = _parse_efficiency(rest)
    if efficiency is None:
        return "Efficiency must be between 1% and 100%."
    usable = watt_hours * efficiency / 100
    minutes = usable / load * 60
    ideal_note = "" if efficiency < 100 else " (ideal — before inverter losses)"
    if efficiency < 100:
        energy_label += f" at {_fmt_num(efficiency)}% efficiency = {_fmt_num(usable)} Wh usable"
    return (f"{energy_label} at {_fmt_num(load)} W — "
            f"runs about {_fmt_minutes(minutes)}{ideal_note}.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="watts", description="Any two of volts, amps, watts gives the third (P = V x I).",
        usage="watts <volts>V <amps>A | watts <watts>W <volts>V | watts <watts>W <amps>A",
        triggers=["watts", "power"],
        run=_run_watts,
        examples=["watts 120V 10A", "watts 1200W 120V"]))
    registry.register(Skill(
        name="circuit", description="Circuit load against breaker capacity and the 80% continuous guideline.",
        usage="circuit <breaker>A <volts>V <load>W...",
        triggers=["circuit", "load"],
        run=_run_circuit,
        examples=["circuit 15A 120V 800 400", "circuit 20A 120V 1500"]))
    registry.register(Skill(
        name="bulb", description="Bulbs for a room area at 200 lumens/m² (20 per sq ft).",
        usage="bulb <area>sqm [lumens-per-bulb] | bulb <area>sqft [lumens-per-bulb]",
        triggers=["bulb", "bulbs", "lighting"],
        run=_run_bulb,
        examples=["bulb 20sqm", "bulb 200sqft 1600"]))
    registry.register(Skill(
        name="runtime", description="Battery runtime from amp-hours/volts or watt-hours and a load.",
        usage="runtime <amp-hours>Ah <volts>V <load>W [efficiency%] | runtime <watt-hours>Wh <load>W [efficiency%]",
        triggers=["runtime", "battery"],
        run=_run_runtime,
        examples=["runtime 100Ah 12V 50W", "runtime 500Wh 50W 85%"]))
