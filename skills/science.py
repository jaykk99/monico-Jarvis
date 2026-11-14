"""Science helpers: pH, moles/molarity, energy, density.

All local, keyless, no network — same contract as the rest of skills/.
Plain formulas for the everyday science questions: how acidic a solution
is, how many moles a mass holds, how much energy something carries or
takes, and how dense a thing is (and whether it floats).

Rules used:
- pH = -log10[H+], pOH = -log10[OH-], and at 25 C pH + pOH = 14, so
  [H+] x [OH-] = 10^-14 mol/L. Below pH 7 is acidic, 7 is neutral,
  above 7 is basic.
- Moles: n = mass / molar mass, mass = n x molar mass; molecules =
  n x Avogadro's number (6.02214076 x 10^23). Molarity = moles / litres.
- Energy: 1 cal = 4.184 J, 1 kcal = 4184 J, 1 kWh = 3.6 x 10^6 J,
  1 BTU = 1055.06 J, 1 eV = 1.602176634 x 10^-19 J. Kinetic energy
  KE = 1/2 m v^2; gravitational potential PE = m g h with g = 9.81 m/s^2.
- Density: rho = mass / volume. 1 g/cm^3 = 1 g/mL = 1000 kg/m^3 =
  62.428 lb/ft^3. Water is 1 g/cm^3, so denser things sink, lighter
  things float.

Conventions and explicit caveats:
- pH math assumes dilute water solutions at 25 C; strong acids and
  bases only — a weak acid's real pH needs its dissociation constant.
- Energy conversions are exact unit conversions; KE and PE are the
  textbook formulas, ignoring friction, air resistance, and relativity.
- Density uses the water benchmark at room temperature; salty or hot
  water differs slightly, and a floating object still needs its shape
  to hold (a steel boat floats because of its shape, not its density).
"""
from __future__ import annotations

import math

from .base import Skill, SkillRegistry

_AVOGADRO = 6.02214076e23
_G = 9.81  # m/s^2, standard gravity


def _fmt(x: float) -> str:
    """Short human number: integers plain, else up to 4 significant digits."""
    if x == int(x) and abs(x) < 1e15:
        return f"{int(x):,}"
    return f"{x:.4g}"


def _fmt_conc(x: float) -> str:
    """Format a concentration in mol/L: plain decimals down to 0.001, else sci."""
    if x >= 0.001:
        return f"{x:.4g}"
    return f"{x:.2e}"


# ---------------------------------------------------------------- ph

_USAGE_PH = (
    "Usage: `ph <concentration>` — [H+] in mol/L, e.g. `ph 0.01` — "
    "or `ph oh <concentration>` for [OH-], e.g. `ph oh 0.001` — "
    "or `ph value <pH>` to start from a pH, e.g. `ph value 3`. "
    "Concentrations 10^-14 to 1 mol/L (pH 0-14)."
)


def _ph_report(ph: float) -> str:
    if ph == 0:  # -log10(1) is -0.0; show 0.00, not -0.00
        ph = 0.0
    poh = 14 - ph
    h = 10 ** (-ph)
    oh = 10 ** (-poh)
    if ph < 7:
        label = "acidic"
    elif ph == 7:
        label = "neutral"
    else:
        label = "basic (alkaline)"
    return (f"pH {ph:.2f} ({label}): [H+] {_fmt_conc(h)} mol/L, "
            f"pOH {poh:.2f}, [OH-] {_fmt_conc(oh)} mol/L. "
            f"Dilute water solution at 25 C — weak acids need their "
            f"dissociation constant for a real pH.")


def _run_ph(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if not parts:
        return _USAGE_PH
    if parts[0].lower() in ("oh", "oh-", "hydroxide"):
        if len(parts) != 2:
            return _USAGE_PH
        try:
            oh = float(parts[1])
        except ValueError:
            return _USAGE_PH
        if not 1e-14 <= oh <= 1:
            return "[OH-] must be 10^-14 to 1 mol/L (pOH 0-14)."
        return _ph_report(14 + math.log10(oh))
    if parts[0].lower() in ("value", "ph"):
        if len(parts) != 2:
            return _USAGE_PH
        try:
            ph = float(parts[1])
        except ValueError:
            return _USAGE_PH
        if not 0 <= ph <= 14:
            return "pH must be 0-14."
        return _ph_report(ph)
    if len(parts) != 1:
        return _USAGE_PH
    try:
        h = float(parts[0])
    except ValueError:
        return _USAGE_PH
    if not 1e-14 <= h <= 1:
        return "[H+] must be 10^-14 to 1 mol/L (pH 0-14)."
    return _ph_report(-math.log10(h))


# ---------------------------------------------------------------- moles

_USAGE_MOLES = (
    "Usage: `moles <mass>g <molar-mass>` — e.g. `moles 36g 18` — "
    "or `moles <n>mol <molar-mass>` for the mass, e.g. `moles 2mol 18` — "
    "or `moles molarity <n>mol <volume>L`, e.g. `moles molarity 2mol 0.5L` — "
    "or `moles molarity <mass>g <molar-mass> <volume>L`, "
    "e.g. `moles molarity 36g 18 2L`. Molar mass in g/mol."
)


def _parse_mass(token: str) -> float | None:
    """Parse a mass token (36g, 0.036kg) to grams, or None."""
    raw = token.lower()
    for suffix, factor in (("kg", 1000.0), ("mg", 0.001), ("g", 1.0)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            if value <= 0:
                return None
            return value * factor
    return None


def _parse_moles(token: str) -> float | None:
    """Parse a moles token (2mol) to moles, or None."""
    raw = token.lower()
    if not raw.endswith("mol"):
        return None
    try:
        value = float(raw[:-3])
    except ValueError:
        return None
    return value if value > 0 else None


def _parse_volume(token: str) -> float | None:
    """Parse a volume token (2L, 500ml) to litres, or None."""
    raw = token.lower()
    for suffix, factor in (("ml", 0.001), ("l", 1.0)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            if value <= 0:
                return None
            return value * factor
    return None


def _run_moles(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if not parts:
        return _USAGE_MOLES
    if parts[0].lower() in ("molarity", "conc", "concentration"):
        rest = parts[1:]
        if len(rest) == 2:
            n = _parse_moles(rest[0])
            vol = _parse_volume(rest[1])
            if n is None or vol is None:
                return _USAGE_MOLES
            conc = n / vol
            return (f"{_fmt(n)} mol in {_fmt(vol)} L is {_fmt(conc)} mol/L "
                    f"({_fmt(conc)} M).")
        if len(rest) == 3:
            mass = _parse_mass(rest[0])
            vol = _parse_volume(rest[2])
            try:
                molar_mass = float(rest[1])
            except ValueError:
                return _USAGE_MOLES
            if mass is None or vol is None or molar_mass <= 0:
                return _USAGE_MOLES
            n = mass / molar_mass
            conc = n / vol
            return (f"{_fmt(mass)} g at {_fmt(molar_mass)} g/mol is "
                    f"{_fmt(n)} mol, in {_fmt(vol)} L that is "
                    f"{_fmt(conc)} mol/L ({_fmt(conc)} M).")
        return _USAGE_MOLES
    if len(parts) != 2:
        return _USAGE_MOLES
    try:
        molar_mass = float(parts[1])
    except ValueError:
        return _USAGE_MOLES
    if molar_mass <= 0:
        return "Molar mass must be more than 0 g/mol."
    mass = _parse_mass(parts[0])
    if mass is not None:
        n = mass / molar_mass
        molecules = n * _AVOGADRO
        return (f"{_fmt(mass)} g at {_fmt(molar_mass)} g/mol is {_fmt(n)} mol "
                f"— about {_fmt(molecules)} molecules.")
    n = _parse_moles(parts[0])
    if n is not None:
        mass = n * molar_mass
        return (f"{_fmt(n)} mol at {_fmt(molar_mass)} g/mol is {_fmt(mass)} g.")
    return _USAGE_MOLES


# ---------------------------------------------------------------- energy

_ENERGY_TO_J = {
    "j": 1.0, "joule": 1.0, "joules": 1.0,
    "kj": 1e3, "kilojoule": 1e3, "kilojoules": 1e3,
    "mj": 1e6, "megajoule": 1e6, "megajoules": 1e6,
    "cal": 4.184, "calorie": 4.184, "calories": 4.184,
    "kcal": 4184.0, "kilocalorie": 4184.0, "kilocalories": 4184.0,
    "ev": 1.602176634e-19, "electronvolt": 1.602176634e-19,
    "electronvolts": 1.602176634e-19,
    "kwh": 3.6e6, "kilowatthour": 3.6e6, "kilowatthours": 3.6e6,
    "btu": 1055.06, "btus": 1055.06,
}

_USAGE_ENERGY = (
    "Usage: `energy <value> <unit> to <unit>` — e.g. `energy 1 kWh to J`, "
    "`energy 500 cal to J` — or `energy ke <mass>kg <speed>` for kinetic "
    "energy, e.g. `energy ke 80kg 10` (m/s, or `36kmh`) — or "
    "`energy pe <mass>kg <height>m` for gravitational potential, "
    "e.g. `energy pe 10kg 5m`. Units: J, kJ, MJ, cal, kcal, eV, kWh, BTU."
)


def _parse_speed(token: str) -> float | None:
    """Parse a speed token (10, 10m/s, 36kmh) to m/s, or None."""
    raw = token.lower()
    for suffix, factor in (("kmh", 1 / 3.6), ("km/h", 1 / 3.6),
                           ("m/s", 1.0), ("mph", 0.44704)):
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


def _parse_height(token: str) -> float | None:
    """Parse a height token (5m, 500cm) to metres, or None."""
    raw = token.lower()
    for suffix, factor in (("cm", 0.01), ("mm", 0.001), ("m", 1.0)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            return value if value >= 0 else None
    return None


def _energy_in_j(joules: float) -> str:
    """One-line summary of an energy in J plus the handiest other unit."""
    if joules >= 3.6e6:
        return f"{_fmt(joules)} J ({_fmt(joules / 3.6e6)} kWh)"
    if joules >= 1000:
        return f"{_fmt(joules)} J ({_fmt(joules / 1000)} kJ)"
    if joules < 1 and joules > 0:
        return f"{_fmt(joules)} J ({_fmt(joules / 1.602176634e-19)} eV)"
    return f"{_fmt(joules)} J"


def _run_energy(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if not parts:
        return _USAGE_ENERGY
    if parts[0].lower() in ("ke", "kinetic"):
        if len(parts) != 3:
            return _USAGE_ENERGY
        mass = _parse_mass(parts[1])
        speed = _parse_speed(parts[2])
        if mass is None or speed is None:
            return _USAGE_ENERGY
        mass_kg = mass / 1000
        ke = 0.5 * mass_kg * speed ** 2
        return (f"Kinetic energy of {_fmt(mass_kg)} kg at {_fmt(speed)} m/s: "
                f"{_energy_in_j(ke)}. KE = 1/2 m v^2 — no friction or "
                f"air resistance included.")
    if parts[0].lower() in ("pe", "potential"):
        if len(parts) != 3:
            return _USAGE_ENERGY
        mass = _parse_mass(parts[1])
        height = _parse_height(parts[2])
        if mass is None or height is None:
            return _USAGE_ENERGY
        mass_kg = mass / 1000
        pe = mass_kg * _G * height
        return (f"Potential energy of {_fmt(mass_kg)} kg at {_fmt(height)} m: "
                f"{_energy_in_j(pe)}. PE = m g h, g = 9.81 m/s^2.")
    if len(parts) != 4 or parts[2].lower() != "to":
        return _USAGE_ENERGY
    try:
        value = float(parts[0])
    except ValueError:
        return _USAGE_ENERGY
    if value < 0:
        return "Energy must be 0 or more."
    from_unit = parts[1].lower()
    to_unit = parts[3].lower()
    if from_unit not in _ENERGY_TO_J or to_unit not in _ENERGY_TO_J:
        return (f"Unknown energy unit `{parts[1] if from_unit not in _ENERGY_TO_J else parts[3]}`. "
                + _USAGE_ENERGY)
    joules = value * _ENERGY_TO_J[from_unit]
    out = joules / _ENERGY_TO_J[to_unit]
    if to_unit in ("j", "joule", "joules"):
        return f"{_fmt(value)} {parts[1]} = {_fmt(out)} {parts[3]}."
    return (f"{_fmt(value)} {parts[1]} = {_fmt(out)} {parts[3]} "
            f"({_fmt(joules)} J).")


# ---------------------------------------------------------------- density

_DENSITY_TO_GCM3 = {
    "g/cm3": 1.0, "g/ml": 1.0, "g/cc": 1.0,
    "kg/m3": 0.001, "kg/m^3": 0.001,
    "lb/ft3": 1 / 62.428, "lb/ft^3": 1 / 62.428,
}

_USAGE_DENSITY = (
    "Usage: `density <mass> <volume>` — e.g. `density 100g 50ml`, "
    "`density 2kg 1L` — or `density <value> <unit> to <unit>` for a unit "
    "conversion, e.g. `density 2.7 g/cm3 to kg/m3`. Mass: g, kg, mg, lb, "
    "oz. Volume: mL, L, cm3, m3. Density units: g/cm3, kg/m3, lb/ft3."
)


def _parse_mass_lb(token: str) -> float | None:
    """Parse a mass token (100g, 2kg, 1lb, 16oz) to grams, or None."""
    raw = token.lower()
    for suffix, factor in (("kg", 1000.0), ("mg", 0.001),
                           ("lb", 453.59237), ("oz", 28.349523125),
                           ("g", 1.0)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            if value <= 0:
                return None
            return value * factor
    return None


def _parse_volume_full(token: str) -> float | None:
    """Parse a volume token (50ml, 2L, 100cm3, 1m3) to mL, or None."""
    raw = token.lower()
    for suffix, factor in (("cm3", 1.0), ("m3", 1e6), ("ml", 1.0),
                           ("l", 1000.0)):
        if raw.endswith(suffix):
            try:
                value = float(raw[: -len(suffix)])
            except ValueError:
                return None
            if value <= 0:
                return None
            return value * factor
    return None


def _run_density(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if not parts:
        return _USAGE_DENSITY
    if len(parts) == 4 and parts[2].lower() == "to":
        try:
            value = float(parts[0])
        except ValueError:
            return _USAGE_DENSITY
        if value < 0:
            return "Density must be 0 or more."
        from_unit = parts[1].lower()
        to_unit = parts[3].lower()
        if from_unit not in _DENSITY_TO_GCM3 or to_unit not in _DENSITY_TO_GCM3:
            return (f"Unknown density unit "
                    f"`{parts[1] if from_unit not in _DENSITY_TO_GCM3 else parts[3]}`. "
                    + _USAGE_DENSITY)
        gcm3 = value * _DENSITY_TO_GCM3[from_unit]
        out = gcm3 / _DENSITY_TO_GCM3[to_unit]
        if from_unit in ("g/cm3", "g/ml", "g/cc"):
            return f"{_fmt(value)} {parts[1]} = {_fmt(out)} {parts[3]}."
        return (f"{_fmt(value)} {parts[1]} = {_fmt(out)} {parts[3]} "
                f"({_fmt(gcm3)} g/cm3).")
    if len(parts) != 2:
        return _USAGE_DENSITY
    mass_g = _parse_mass_lb(parts[0])
    vol_ml = _parse_volume_full(parts[1])
    if mass_g is None or vol_ml is None:
        return _USAGE_DENSITY
    gcm3 = mass_g / vol_ml
    kgm3 = gcm3 * 1000
    if gcm3 > 1:
        verdict = "denser than water (1 g/cm3) — it sinks"
    elif gcm3 < 1:
        verdict = "less dense than water (1 g/cm3) — it floats"
    else:
        verdict = "the same density as water (1 g/cm3) — it hangs suspended"
    return (f"Density: {_fmt(gcm3)} g/cm3 ({_fmt(kgm3)} kg/m3) — {verdict}. "
            f"Shape still matters: a steel boat floats because of its "
            f"shape, not its density.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="ph", description="pH, pOH and ion concentrations for a solution.",
        usage="ph <[H+]> | ph oh <[OH-]> | ph value <pH>",
        triggers=["ph", "acidity", "poh"],
        run=_run_ph,
        examples=["ph 0.01", "ph oh 0.001", "ph value 3"]))
    registry.register(Skill(
        name="moles", description="Moles from mass and molar mass, or molarity.",
        usage="moles <mass>g <molar-mass> | moles <n>mol <molar-mass> | moles molarity ...",
        triggers=["moles", "molarity", "mol"],
        run=_run_moles,
        examples=["moles 36g 18", "moles 2mol 18", "moles molarity 2mol 0.5L"]))
    registry.register(Skill(
        name="energy", description="Energy unit conversions, kinetic and potential energy.",
        usage="energy <value> <unit> to <unit> | energy ke <mass>kg <speed> | energy pe <mass>kg <height>m",
        triggers=["energy", "kinetic", "potential"],
        run=_run_energy,
        examples=["energy 1 kWh to J", "energy ke 80kg 10", "energy pe 10kg 5m"]))
    registry.register(Skill(
        name="density", description="Density from mass and volume, or density unit conversion.",
        usage="density <mass> <volume> | density <value> <unit> to <unit>",
        triggers=["density", "float"],
        run=_run_density,
        examples=["density 100g 50ml", "density 2kg 1L", "density 2.7 g/cm3 to kg/m3"]))
