"""Physics helpers: force, speed, pressure, waves.

All local, keyless, no network — same contract as the rest of skills/.
Plain textbook formulas for everyday physics questions: how hard
something pushes, how fast it moves, how much pressure it exerts,
and how long a wave is.

Rules used:
- Force: F = m a, weight W = m g with g = 9.81 m/s^2. 1 N = 1 kg m/s^2.
- Speed: v = d / t, d = v t, t = d / v. 1 m/s = 3.6 km/h,
  1 mph = 1.60934 km/h, 1 mph = 0.44704 m/s.
- Pressure: P = F / A. 1 Pa = 1 N/m^2, 1 kPa = 1000 Pa,
  1 bar = 100,000 Pa, 1 atm = 101,325 Pa, 1 psi = 6,894.76 Pa,
  1 mmHg = 133.322 Pa.
- Waves: v = f x lambda, period T = 1 / f. Speed of sound in air
  is about 343 m/s at 20 C; speed of light c = 299,792,458 m/s.

Conventions and explicit caveats:
- Force and weight ignore friction, air resistance, and relativity;
  g is the standard 9.81 m/s^2, not your local value.
- Speed assumes a steady speed over the whole trip — no speeding
  up, slowing down, or stops.
- Pressure from F/A assumes the force is spread evenly over the
  area; gauge vs absolute pressure is not distinguished.
- Wave speed in air depends on temperature (343 m/s is for 20 C);
  light frequency from a wavelength assumes a vacuum.
"""
from __future__ import annotations

from .base import Skill, SkillRegistry

_G = 9.81  # m/s^2, standard gravity
_C = 299_792_458.0  # m/s, speed of light in vacuum
_SOUND = 343.0  # m/s, speed of sound in air at 20 C


def _fmt(x: float) -> str:
    """Short human number: integers plain, else up to 4 significant digits."""
    if x == int(x) and abs(x) < 1e15:
        return f"{int(x):,}"
    return f"{x:.4g}"


def _parse_mass(token: str) -> float | None:
    """Parse a mass token (10kg, 500g, 2mg) to kilograms, or None."""
    raw = token.lower()
    for suffix, factor in (("kg", 1.0), ("mg", 1e-6), ("g", 0.001)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            if value <= 0:
                return None
            return value * factor
    return None


def _parse_force(token: str) -> float | None:
    """Parse a force token (50N, 2kN, 50) to newtons, or None."""
    raw = token.lower()
    for suffix, factor in (("kn", 1000.0), ("n", 1.0)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            if value <= 0:
                return None
            return value * factor
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def _parse_accel(token: str) -> float | None:
    """Parse an acceleration token (5, 5m/s2, 5m/s^2) to m/s^2, or None."""
    raw = token.lower()
    for suffix in ("m/s^2", "m/s2"):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            return value if value >= 0 else None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


# ---------------------------------------------------------------- force

_USAGE_FORCE = (
    "Usage: `force <mass> <acceleration>` — e.g. `force 10kg 5` — "
    "or `force weight <mass>`, e.g. `force weight 80kg` — "
    "or `force accel <force> <mass>`, e.g. `force accel 100N 20kg` — "
    "or `force mass <force> <acceleration>`, e.g. `force mass 50N 5`. "
    "Mass: g, kg, mg. Acceleration in m/s^2. F = m a."
)


def _force_in_n(newtons: float) -> str:
    """Force in N plus kN when it reads better."""
    if newtons >= 1000:
        return f"{_fmt(newtons)} N ({_fmt(newtons / 1000)} kN)"
    return f"{_fmt(newtons)} N"


def _run_force(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if not parts:
        return _USAGE_FORCE
    if parts[0].lower() in ("weight", "w"):
        if len(parts) != 2:
            return _USAGE_FORCE
        mass_kg = _parse_mass(parts[1])
        if mass_kg is None:
            return _USAGE_FORCE
        weight = mass_kg * _G
        return (f"Weight of {_fmt(mass_kg)} kg: {_force_in_n(weight)}. "
                f"W = m g, g = 9.81 m/s^2 — standard gravity, not local.")
    if parts[0].lower() in ("accel", "acceleration", "a"):
        if len(parts) != 3:
            return _USAGE_FORCE
        force = _parse_force(parts[1])
        mass_kg = _parse_mass(parts[2])
        if force is None or mass_kg is None:
            return _USAGE_FORCE
        accel = force / mass_kg
        return (f"Acceleration from {_fmt(force)} N on {_fmt(mass_kg)} kg: "
                f"{_fmt(accel)} m/s^2. a = F / m.")
    if parts[0].lower() in ("mass", "m"):
        if len(parts) != 3:
            return _USAGE_FORCE
        force = _parse_force(parts[1])
        accel = _parse_accel(parts[2])
        if force is None or accel is None or accel == 0:
            return _USAGE_FORCE
        mass_kg = force / accel
        return (f"Mass from {_fmt(force)} N at {_fmt(accel)} m/s^2: "
                f"{_fmt(mass_kg)} kg. m = F / a.")
    if len(parts) != 2:
        return _USAGE_FORCE
    mass_kg = _parse_mass(parts[0])
    accel = _parse_accel(parts[1])
    if mass_kg is None or accel is None:
        return _USAGE_FORCE
    force = mass_kg * accel
    return (f"Force of {_fmt(mass_kg)} kg at {_fmt(accel)} m/s^2: "
            f"{_force_in_n(force)}. F = m a — no friction included.")


# ---------------------------------------------------------------- speed

def _parse_dist(token: str) -> float | None:
    """Parse a distance token (100km, 500m, 26mi) to kilometres, or None."""
    raw = token.lower()
    for suffix, factor in (("km", 1.0), ("mi", 1.60934),
                           ("m", 0.001)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            if value <= 0:
                return None
            return value * factor
    return None


def _parse_time(token: str) -> float | None:
    """Parse a time token (2h, 90s, 30min) to hours, or None."""
    raw = token.lower()
    for suffix, factor in (("min", 1 / 60), ("h", 1.0),
                           ("s", 1 / 3600)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            if value <= 0:
                return None
            return value * factor
    return None


def _parse_speed(token: str) -> float | None:
    """Parse a speed token (50kmh, 60mph, 10m/s, 50) to km/h, or None."""
    raw = token.lower()
    for suffix, factor in (("km/h", 1.0), ("kmh", 1.0),
                           ("mph", 1.60934), ("m/s", 3.6)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            return value * factor if value >= 0 else None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


_USAGE_SPEED = (
    "Usage: `speed <distance> <time>` — e.g. `speed 100km 2h` — "
    "or `speed dist <speed> <time>`, e.g. `speed dist 60kmh 2h` — "
    "or `speed time <distance> <speed>`, e.g. `speed time 120km 60kmh`. "
    "Distance: m, km, mi. Time: s, min, h. Speed: km/h, mph, m/s "
    "(plain number means km/h)."
)


def _speed_both(kmh: float) -> str:
    """Speed in km/h plus m/s."""
    return f"{_fmt(kmh)} km/h ({_fmt(kmh / 3.6)} m/s)"


def _run_speed(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if not parts:
        return _USAGE_SPEED
    if parts[0].lower() in ("dist", "distance", "d"):
        if len(parts) != 3:
            return _USAGE_SPEED
        speed = _parse_speed(parts[1])
        hours = _parse_time(parts[2])
        if speed is None or hours is None:
            return _USAGE_SPEED
        dist_km = speed * hours
        return (f"Distance at {_speed_both(speed)} for {_fmt(hours)} h: "
                f"{_fmt(dist_km)} km ({_fmt(dist_km * 1000)} m). "
                f"d = v t, steady speed assumed.")
    if parts[0].lower() in ("time", "t"):
        if len(parts) != 3:
            return _USAGE_SPEED
        dist_km = _parse_dist(parts[1])
        speed = _parse_speed(parts[2])
        if dist_km is None or speed is None or speed == 0:
            return _USAGE_SPEED
        hours = dist_km / speed
        return (f"Time for {_fmt(dist_km)} km at {_speed_both(speed)}: "
                f"{_fmt(hours)} h ({_fmt(hours * 60)} min). "
                f"t = d / v, steady speed assumed.")
    if len(parts) != 2:
        return _USAGE_SPEED
    dist_km = _parse_dist(parts[0])
    hours = _parse_time(parts[1])
    if dist_km is None or hours is None:
        return _USAGE_SPEED
    speed = dist_km / hours
    return (f"Speed for {_fmt(dist_km)} km in {_fmt(hours)} h: "
            f"{_speed_both(speed)}. v = d / t, steady speed assumed.")


# ---------------------------------------------------------------- pressure

_PRESSURE_TO_PA = {
    "pa": 1.0, "pascal": 1.0, "pascals": 1.0,
    "kpa": 1e3, "kilopascal": 1e3, "kilopascals": 1e3,
    "mpa": 1e6, "megapascal": 1e6, "megapascals": 1e6,
    "bar": 1e5, "bars": 1e5,
    "atm": 101325.0, "atmosphere": 101325.0, "atmospheres": 101325.0,
    "psi": 6894.76, "psia": 6894.76,
    "mmhg": 133.322, "torr": 133.322,
}

_USAGE_PRESSURE = (
    "Usage: `pressure <force> <area>` — e.g. `pressure 100N 2m2` — "
    "or `pressure <value> <unit> to <unit>`, e.g. "
    "`pressure 1 atm to psi`. Force: N, kN. Area: m2, cm2. "
    "Pressure units: Pa, kPa, MPa, bar, atm, psi, mmHg."
)


def _parse_area(token: str) -> float | None:
    """Parse an area token (2m2, 200cm2) to square metres, or None."""
    raw = token.lower()
    for suffix, factor in (("cm2", 1e-4), ("cm^2", 1e-4),
                           ("m2", 1.0), ("m^2", 1.0)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            if value <= 0:
                return None
            return value * factor
    return None


def _run_pressure(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if not parts:
        return _USAGE_PRESSURE
    if len(parts) == 4 and parts[2].lower() == "to":
        try:
            value = float(parts[0])
        except ValueError:
            return _USAGE_PRESSURE
        if value < 0:
            return "Pressure must be 0 or more."
        from_unit = parts[1].lower()
        to_unit = parts[3].lower()
        if from_unit not in _PRESSURE_TO_PA or to_unit not in _PRESSURE_TO_PA:
            return (f"Unknown pressure unit "
                    f"`{parts[1] if from_unit not in _PRESSURE_TO_PA else parts[3]}`. "
                    + _USAGE_PRESSURE)
        pascals = value * _PRESSURE_TO_PA[from_unit]
        out = pascals / _PRESSURE_TO_PA[to_unit]
        if to_unit in ("pa", "pascal", "pascals"):
            return f"{_fmt(value)} {parts[1]} = {_fmt(out)} {parts[3]}."
        return (f"{_fmt(value)} {parts[1]} = {_fmt(out)} {parts[3]} "
                f"({_fmt(pascals)} Pa).")
    if len(parts) != 2:
        return _USAGE_PRESSURE
    force = _parse_force(parts[0])
    area = _parse_area(parts[1])
    if force is None or area is None:
        return _USAGE_PRESSURE
    pascals = force / area
    return (f"Pressure of {_fmt(force)} N over {_fmt(area)} m^2: "
            f"{_fmt(pascals)} Pa ({_fmt(pascals / 1000)} kPa). "
            f"P = F / A, force spread evenly — gauge vs absolute "
            f"not distinguished.")


# ---------------------------------------------------------------- wave

_USAGE_WAVE = (
    "Usage: `wave <frequency> <speed>` — e.g. `wave 440Hz 343` (m/s) — "
    "or `wave freq <wavelength> <speed>`, e.g. `wave freq 2m 343` — "
    "or `wave period <frequency>`, e.g. `wave period 440Hz` — "
    "or `wave light <wavelength>`, e.g. `wave light 500nm`. "
    "Frequency: Hz, kHz. Wavelength: m, cm, nm, um. v = f x lambda."
)


def _parse_freq(token: str) -> float | None:
    """Parse a frequency token (440Hz, 2kHz, 440) to hertz, or None."""
    raw = token.lower()
    for suffix, factor in (("khz", 1000.0), ("hz", 1.0)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            return value * factor if value > 0 else None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def _parse_wavelength(token: str) -> float | None:
    """Parse a wavelength token (2m, 50cm, 500nm, 0.5um) to metres, or None."""
    raw = token.lower()
    for suffix, factor in (("nm", 1e-9), ("um", 1e-6),
                           ("cm", 0.01), ("m", 1.0)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            return value * factor if value > 0 else None
    return None


def _parse_wave_speed(token: str) -> float | None:
    """Parse a wave speed token (343, 343m/s) to m/s, or None."""
    raw = token.lower()
    if raw.endswith("m/s"):
        try:
            value = float(raw[:-3])
        except ValueError:
            return None
        return value if value > 0 else None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def _run_wave(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if not parts:
        return _USAGE_WAVE
    if parts[0].lower() in ("freq", "frequency", "f"):
        if len(parts) != 3:
            return _USAGE_WAVE
        wavelength = _parse_wavelength(parts[1])
        speed = _parse_wave_speed(parts[2])
        if wavelength is None or speed is None:
            return _USAGE_WAVE
        freq = speed / wavelength
        return (f"Frequency for {_fmt(wavelength)} m at {_fmt(speed)} m/s: "
                f"{_fmt(freq)} Hz. f = v / lambda.")
    if parts[0].lower() in ("period", "t"):
        if len(parts) != 2:
            return _USAGE_WAVE
        freq = _parse_freq(parts[1])
        if freq is None:
            return _USAGE_WAVE
        period = 1 / freq
        return (f"Period of {_fmt(freq)} Hz: {_fmt(period)} s "
                f"({_fmt(period * 1000)} ms). T = 1 / f.")
    if parts[0].lower() in ("light", "photon"):
        if len(parts) != 2:
            return _USAGE_WAVE
        wavelength = _parse_wavelength(parts[1])
        if wavelength is None:
            return _USAGE_WAVE
        freq = _C / wavelength
        return (f"Light of {_fmt(wavelength)} m: {freq:.4g} Hz "
                f"({_fmt(freq / 1e12)} THz). f = c / lambda, "
                f"c = 299,792,458 m/s in vacuum.")
    if len(parts) != 2:
        return _USAGE_WAVE
    freq = _parse_freq(parts[0])
    speed = _parse_wave_speed(parts[1])
    if freq is None or speed is None:
        return _USAGE_WAVE
    wavelength = speed / freq
    return (f"Wavelength of {_fmt(freq)} Hz at {_fmt(speed)} m/s: "
            f"{_fmt(wavelength)} m ({_fmt(wavelength * 100)} cm). "
            f"lambda = v / f — {_fmt(speed)} m/s is sound in air at 20 C "
            f"unless you gave another speed.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="force", description="Force from mass and acceleration, weight, or the rearranged F = m a.",
        usage="force <mass> <acceleration> | force weight <mass> | force accel <force> <mass> | force mass <force> <acceleration>",
        triggers=["force", "weight", "newton"],
        run=_run_force,
        examples=["force 10kg 5", "force weight 80kg", "force accel 100N 20kg"]))
    registry.register(Skill(
        name="speed", description="Speed from distance and time, or distance/time from speed.",
        usage="speed <distance> <time> | speed dist <speed> <time> | speed time <distance> <speed>",
        triggers=["speed", "velocity"],
        run=_run_speed,
        examples=["speed 100km 2h", "speed dist 60kmh 2h", "speed time 120km 60kmh"]))
    registry.register(Skill(
        name="pressure", description="Pressure from force and area, or pressure unit conversion.",
        usage="pressure <force> <area> | pressure <value> <unit> to <unit>",
        triggers=["pressure", "psi"],
        run=_run_pressure,
        examples=["pressure 100N 2m2", "pressure 1 atm to psi", "pressure 100 kPa to Pa"]))
    registry.register(Skill(
        name="wave", description="Wavelength, frequency, period, or light frequency from wavelength.",
        usage="wave <frequency> <speed> | wave freq <wavelength> <speed> | wave period <frequency> | wave light <wavelength>",
        triggers=["wave", "wavelength", "frequency"],
        run=_run_wave,
        examples=["wave 440Hz 343", "wave freq 2m 343", "wave period 440Hz", "wave light 500nm"]))
