"""Chemistry helpers: molar mass, percent composition, empirical
formulas, the ideal gas law, dilution, titration, and half-life.

All local, keyless, no network — same contract as the rest of skills/.
Plain textbook chemistry for everyday questions: how heavy a mole
of a compound is, what fraction of it is each element, what the
simplest formula is for a given percent composition, what pressure,
volume, moles, or temperature an ideal gas has, how much to dilute
a solution, how strong the unknown side of a titration is, and how
much of a sample is left after some half-lives.

Rules used:
- Molar mass: add up each element's standard atomic weight times
  how many atoms of it the formula has. Formulae are written the
  usual way: an element symbol is a capital letter plus an optional
  lowercase letter, an optional number after it is the count, and
  parentheses group atoms with a multiplier after the closing
  bracket — Ca(OH)2, Al2(SO4)3, C6H12O6.
- Percent composition: each element's share is its mass in one mole
  divided by the molar mass, times 100.
- Empirical formula: divide each percent by that element's atomic
  weight to get relative moles, divide by the smallest, then scale
  to the nearest whole numbers (trying multipliers 1 through 6).
- Ideal gas law: PV = nRT with R = 0.082057 L atm / (mol K).
  Pressure in atmospheres, volume in litres, temperature in kelvin.
  Give any three and ask for the fourth with `?`.
- Dilution: M1 V1 = M2 V2. Give any three and ask for the fourth
  with `?`. Volumes must be in the same unit on both sides.
- Titration: at the equivalence point the moles that react are
  equal after the balanced ratio — Ma Va / a = Mb Vb / b, where a
  and b are the acid and base coefficients. Give the acid
  concentration and volume, the coefficients, and the base volume,
  and get the base concentration.
- Half-life: after n half-lives, amount = start / 2^n. Given a
  half-life and an elapsed time, n = time / half-life.

Conventions and explicit caveats:
- Only the elements in the table below are known (the 60 most
  common in school and lab chemistry); an unknown symbol is
  reported, not guessed.
- Atomic weights are the standard values rounded to three decimals
  where they matter (H 1.008, C 12.011, O 15.999, and so on), so a
  molar mass may differ in the third decimal from a table that
  rounds differently.
- The gas law is the ideal gas law: real gases deviate at high
  pressure and low temperature, and the answer says so when the
  pressure is above 10 atm.
- `empirical` needs percents that add up to roughly 100; anything
  below 90 or above 110 is refused as a typo, not silently used.
- Half-life answers are the amount left, not the amount decayed,
  and the number of half-lives elapsed is always shown.
- Huge values refuse to print rather than dumping a wall of digits.
"""
from __future__ import annotations

import math
import re

from .base import Skill, SkillRegistry

# Standard atomic weights (most common elements in school/lab use).
ATOMIC_WEIGHTS: dict[str, float] = {
    "H": 1.008, "He": 4.003, "Li": 6.94, "Be": 9.012, "B": 10.81,
    "C": 12.011, "N": 14.007, "O": 15.999, "F": 18.998, "Ne": 20.18,
    "Na": 22.99, "Mg": 24.305, "Al": 26.982, "Si": 28.085, "P": 30.974,
    "S": 32.06, "Cl": 35.45, "Ar": 39.948, "K": 39.098, "Ca": 40.078,
    "Sc": 44.956, "Ti": 47.867, "V": 50.942, "Cr": 51.996, "Mn": 54.938,
    "Fe": 55.845, "Co": 58.933, "Ni": 58.693, "Cu": 63.546, "Zn": 65.38,
    "Ga": 69.723, "Ge": 72.63, "As": 74.922, "Se": 78.971, "Br": 79.904,
    "Kr": 83.798, "Rb": 85.468, "Sr": 87.62, "Y": 88.906, "Zr": 91.224,
    "Mo": 95.95, "Ag": 107.868, "Cd": 112.414, "Sn": 118.71, "Sb": 121.76,
    "I": 126.904, "Ba": 137.327, "Pt": 195.084, "Au": 196.967,
    "Hg": 200.592, "Pb": 207.2, "Bi": 208.98, "U": 238.029,
}

R_GAS = 0.082057  # L atm / (mol K)

_FORMULA_TOKEN = re.compile(r"([A-Z][a-z]?|\(|\)|\d+)")


def _fmt(x: float) -> str:
    """Short human number: integers plain, else up to 4 significant digits."""
    if x == int(x) and abs(x) < 1e15:
        return f"{int(x):,}"
    return f"{x:.4g}"


def _num(token: str) -> float | None:
    """Parse a plain number, tolerating thousands commas."""
    try:
        return float(token.strip().replace(",", ""))
    except ValueError:
        return None


def _too_big() -> str:
    return "That answer is too large to print — try smaller numbers."


def _parse_formula(formula: str) -> dict[str, int] | str:
    """Parse a chemical formula into {element: count}.

    Returns an error string when the formula is malformed or uses an
    element outside the table.
    """
    if not formula or not re.fullmatch(r"[A-Za-z0-9()]+", formula):
        return "That does not look like a chemical formula — e.g. `H2O`, `Ca(OH)2`."
    tokens = _FORMULA_TOKEN.findall(formula)
    if "".join(tokens) != formula:
        return "That does not look like a chemical formula — e.g. `H2O`, `Ca(OH)2`."
    # Stack of count dicts, one per open parenthesis level.
    stack: list[dict[str, int]] = [{}]
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "(":
            stack.append({})
            i += 1
        elif tok == ")":
            if len(stack) == 1:
                return "Unmatched `)` in that formula — check the brackets."
            group = stack.pop()
            i += 1
            mult = 1
            if i < len(tokens) and tokens[i].isdigit():
                mult = int(tokens[i])
                i += 1
            for el, n in group.items():
                stack[-1][el] = stack[-1].get(el, 0) + n * mult
        elif tok.isdigit():
            return "A number in a formula must follow an element or `)` — e.g. `H2O`, not `2H2O`."
        else:
            if tok not in ATOMIC_WEIGHTS:
                return (f"I do not know the element `{tok}` — the table "
                        f"covers the 60 most common elements.")
            count = 1
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                count = int(tokens[i + 1])
                i += 1
            stack[-1][tok] = stack[-1].get(tok, 0) + count
            i += 1
    if len(stack) != 1:
        return "Unmatched `(` in that formula — check the brackets."
    counts = stack[0]
    if not counts:
        return "That formula has no elements in it — e.g. `H2O`."
    return counts


def _molar_mass(counts: dict[str, int]) -> float:
    return sum(ATOMIC_WEIGHTS[el] * n for el, n in counts.items())


def _formula_str(counts: dict[str, int]) -> str:
    """Counts back to a formula string, in first-appearance order."""
    out = []
    for el, n in counts.items():
        out.append(el if n == 1 else f"{el}{n}")
    return "".join(out)


# ---------------------------------------------------------------- molarmass

_USAGE_MOLARMASS = (
    "Usage: `molarmass <formula>` gives the molar mass in g/mol — "
    "e.g. `molarmass H2O`, `molarmass Ca(OH)2`."
)


def _run_molarmass(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) != 1:
        return _USAGE_MOLARMASS
    counts = _parse_formula(tokens[0])
    if isinstance(counts, str):
        return counts
    mass = _molar_mass(counts)
    if mass != mass or mass in (math.inf, -math.inf) or mass > 1e15:
        return _too_big()
    parts = " + ".join(
        f"{n} x {ATOMIC_WEIGHTS[el]}" for el, n in counts.items())
    return (f"The molar mass of {tokens[0]} is {_fmt(mass)} g/mol "
            f"({parts}).")


# ---------------------------------------------------------------- pctcomp

_USAGE_PCTCOMP = (
    "Usage: `pctcomp <formula>` gives the percent composition by "
    "mass — e.g. `pctcomp H2O`, `pctcomp C6H12O6`."
)


def _run_pctcomp(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) != 1:
        return _USAGE_PCTCOMP
    counts = _parse_formula(tokens[0])
    if isinstance(counts, str):
        return counts
    mass = _molar_mass(counts)
    if mass != mass or mass in (math.inf, -math.inf) or mass > 1e15:
        return _too_big()
    bits = []
    for el, n in counts.items():
        pct = ATOMIC_WEIGHTS[el] * n / mass * 100
        bits.append(f"{el} {_fmt(pct)}%")
    return (f"{tokens[0]} is {_fmt(mass)} g/mol: "
            + ", ".join(bits) + " by mass.")


# ---------------------------------------------------------------- empirical

_USAGE_EMPIRICAL = (
    "Usage: `empirical <element> <percent> ...` gives the empirical "
    "formula from percent composition — e.g. "
    "`empirical C 40 H 6.7 O 53.3`."
)


def _run_empirical(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) < 4 or len(tokens) % 2 != 0:
        return _USAGE_EMPIRICAL
    percents: dict[str, float] = {}
    for i in range(0, len(tokens), 2):
        el = tokens[i]
        if el not in ATOMIC_WEIGHTS:
            return (f"I do not know the element `{el}` — the table "
                    f"covers the 60 most common elements.")
        value = _num(tokens[i + 1])
        if value is None or value <= 0:
            return _USAGE_EMPIRICAL
        percents[el] = percents.get(el, 0.0) + value
    total = sum(percents.values())
    if total < 90 or total > 110:
        return (f"Those percents add up to {_fmt(total)}, not about 100 "
                f"— check for a typo and try again.")
    moles = {el: p / ATOMIC_WEIGHTS[el] for el, p in percents.items()}
    smallest = min(moles.values())
    ratios = {el: m / smallest for el, m in moles.items()}
    # Find the smallest multiplier (1..6) that makes every ratio near whole.
    counts: dict[str, int] | None = None
    for mult in range(1, 7):
        trial = {el: r * mult for el, r in ratios.items()}
        if all(abs(v - round(v)) <= 0.12 for v in trial.values()):
            counts = {el: max(1, int(round(v))) for el, v in trial.items()}
            break
    if counts is None:
        ratio_str = ", ".join(
            f"{el} {_fmt(r)}" for el, r in ratios.items())
        return (f"Those percents give mole ratios {ratio_str} — no small "
                f"whole-number formula fits, so the compound may need a "
                f"molecular mass to pin down.")
    formula = _formula_str(counts)
    ratio_str = ", ".join(f"{el} {_fmt(r)}" for el, r in ratios.items())
    return (f"Relative moles are {ratio_str}, so the empirical formula "
            f"is {formula}.")


# ---------------------------------------------------------------- gaslaw

_USAGE_GASLAW = (
    "Usage: `gaslaw P <atm> V <L> n <mol> T <K>` with one value as `?` "
    "— e.g. `gaslaw P 2 V 5 n 0.5 T ?` solves for T. Pressure in atm, "
    "volume in litres, temperature in kelvin."
)


def _run_gaslaw(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) != 8:
        return _USAGE_GASLAW
    values: dict[str, float | None] = {}
    for i in range(0, 8, 2):
        key = tokens[i].upper()
        if key not in ("P", "V", "N", "T"):
            return _USAGE_GASLAW
        if key in values:
            return _USAGE_GASLAW
        raw = tokens[i + 1]
        if raw == "?":
            values[key] = None
        else:
            parsed = _num(raw)
            if parsed is None:
                return _USAGE_GASLAW
            values[key] = parsed
    missing = [k for k, v in values.items() if v is None]
    if len(missing) != 1:
        return _USAGE_GASLAW + " Exactly one value must be `?`."
    if any(v is not None and v <= 0 for v in values.values()):
        return "Pressure, volume, moles, and temperature must all be positive."
    target = missing[0]
    p = values["P"]
    v = values["V"]
    n = values["N"]
    t = values["T"]
    assert p is not None or target == "P"
    assert v is not None or target == "V"
    assert n is not None or target == "N"
    assert t is not None or target == "T"
    if target == "P":
        assert v is not None and n is not None and t is not None
        result = n * R_GAS * t / v
        label = f"P = {_fmt(result)} atm"
    elif target == "V":
        assert p is not None and n is not None and t is not None
        result = n * R_GAS * t / p
        label = f"V = {_fmt(result)} L"
    elif target == "N":
        assert p is not None and v is not None and t is not None
        result = p * v / (R_GAS * t)
        label = f"n = {_fmt(result)} mol"
    else:
        assert p is not None and v is not None and n is not None
        result = p * v / (n * R_GAS)
        label = f"T = {_fmt(result)} K"
    if result != result or result in (math.inf, -math.inf) or result > 1e15:
        return _too_big()
    given = ", ".join(
        f"{k} = {_fmt(val)}" for k, val in
        (("P", p), ("V", v), ("n", n), ("T", t)) if val is not None)
    out = f"PV = nRT with {given} gives {label}."
    if target == "P" and result > 10:
        out += (" At pressures above 10 atm real gases start to deviate "
                "from the ideal gas law, so treat this as an estimate.")
    return out


# ---------------------------------------------------------------- dilute

_USAGE_DILUTE = (
    "Usage: `dilute M1 <M> V1 <volume> M2 <M> V2 <volume>` with one "
    "value as `?` — e.g. `dilute M1 2 V1 100 M2 0.5 V2 ?` (volumes in "
    "the same unit, e.g. mL)."
)


def _run_dilute(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) != 8:
        return _USAGE_DILUTE
    values: dict[str, float | None] = {}
    for i in range(0, 8, 2):
        key = tokens[i].upper()
        if key not in ("M1", "V1", "M2", "V2"):
            return _USAGE_DILUTE
        if key in values:
            return _USAGE_DILUTE
        raw = tokens[i + 1]
        if raw == "?":
            values[key] = None
        else:
            parsed = _num(raw)
            if parsed is None:
                return _USAGE_DILUTE
            values[key] = parsed
    missing = [k for k, v in values.items() if v is None]
    if len(missing) != 1:
        return _USAGE_DILUTE + " Exactly one value must be `?`."
    if any(v is not None and v <= 0 for v in values.values()):
        return "Concentrations and volumes must all be positive."
    target = missing[0]
    m1 = values["M1"]
    v1 = values["V1"]
    m2 = values["M2"]
    v2 = values["V2"]
    if target == "M1":
        assert v1 is not None and m2 is not None and v2 is not None
        result = m2 * v2 / v1
        label = f"M1 = {_fmt(result)} M"
    elif target == "V1":
        assert m1 is not None and m2 is not None and v2 is not None
        result = m2 * v2 / m1
        label = f"V1 = {_fmt(result)}"
    elif target == "M2":
        assert m1 is not None and v1 is not None and v2 is not None
        result = m1 * v1 / v2
        label = f"M2 = {_fmt(result)} M"
    else:
        assert m1 is not None and v1 is not None and m2 is not None
        result = m1 * v1 / m2
        label = f"V2 = {_fmt(result)}"
    if result != result or result in (math.inf, -math.inf) or result > 1e15:
        return _too_big()
    if target == "V1":
        return (f"M1V1 = M2V2 gives {label} of the stock solution — "
                f"measure that out and top up to {_fmt(v2 or 0)} total.")
    if target == "V2":
        return (f"M1V1 = M2V2 gives {label} total volume — add "
                f"{_fmt(result - (v1 or 0))} of solvent to the "
                f"{_fmt(v1 or 0)} of stock.")
    return f"M1V1 = M2V2 gives {label}."


# ---------------------------------------------------------------- titrate

_USAGE_TITRATE = (
    "Usage: `titrate <acid M> <acid mL> <acid coeff> <base coeff> "
    "<base mL>` gives the base concentration at the equivalence "
    "point — e.g. `titrate 0.1 25 1 1 10`."
)


def _run_titrate(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) != 5:
        return _USAGE_TITRATE
    nums = [_num(t) for t in tokens]
    if any(v is None for v in nums):
        return _USAGE_TITRATE
    ma, va, a, b, vb = [float(v) for v in nums if v is not None]
    if ma <= 0 or va <= 0 or a <= 0 or b <= 0 or vb <= 0:
        return "Concentrations, volumes, and coefficients must all be positive."
    if a != int(a) or b != int(b):
        return "The coefficients must be whole numbers from the balanced equation."
    moles_acid = ma * va / 1000
    moles_base = moles_acid * b / a
    mb = moles_base / (vb / 1000)
    if mb != mb or mb in (math.inf, -math.inf) or mb > 1e15:
        return _too_big()
    out = (f"At the equivalence point, {_fmt(ma)} M x {_fmt(va)} mL of "
           f"acid is {_fmt(moles_acid * 1000)} mmol, so with a "
           f"{int(a)}:{int(b)} acid:base ratio the base needs "
           f"{_fmt(moles_base * 1000)} mmol in {_fmt(vb)} mL — the base "
           f"is {_fmt(mb)} M.")
    return out


# ---------------------------------------------------------------- halflife

_USAGE_HALFLIFE = (
    "Usage: `halflife <amount> n <half-lives>` or "
    "`halflife <amount> after <time> hl <half-life>` — e.g. "
    "`halflife 100 n 3`, `halflife 100 after 10 hl 5.27`."
)


def _run_halflife(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) not in (3, 5):
        return _USAGE_HALFLIFE
    amount = _num(tokens[0])
    if amount is None or amount <= 0:
        return _USAGE_HALFLIFE
    if len(tokens) == 3:
        if tokens[1].lower() != "n":
            return _USAGE_HALFLIFE
        n = _num(tokens[2])
        if n is None or n < 0:
            return _USAGE_HALFLIFE
    else:
        if tokens[1].lower() != "after" or tokens[3].lower() != "hl":
            return _USAGE_HALFLIFE
        elapsed = _num(tokens[2])
        hl = _num(tokens[4])
        if elapsed is None or hl is None or elapsed < 0 or hl <= 0:
            return _USAGE_HALFLIFE
        n = elapsed / hl
    try:
        remaining = amount / (2 ** n)
    except OverflowError:
        return _too_big()
    if remaining != remaining or remaining in (math.inf, -math.inf):
        return _too_big()
    decayed = amount - remaining
    out = (f"After {_fmt(n)} half-lives, {_fmt(remaining)} is left of "
           f"the original {_fmt(amount)} "
           f"({_fmt(decayed)} decayed).")
    if n == 0:
        out += " Nothing has decayed yet."
    return out


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="molarmass", description="Molar mass of a compound from its formula.",
        usage="molarmass <formula>",
        triggers=["molarmass", "molar", "molmass"],
        run=_run_molarmass,
        examples=["molarmass H2O", "molarmass Ca(OH)2", "molarmass C6H12O6"]))
    registry.register(Skill(
        name="pctcomp", description="Percent composition by mass of a compound.",
        usage="pctcomp <formula>",
        triggers=["pctcomp", "composition", "percentcomp"],
        run=_run_pctcomp,
        examples=["pctcomp H2O", "pctcomp C6H12O6", "pctcomp NaCl"]))
    registry.register(Skill(
        name="empirical", description="Empirical formula from percent composition.",
        usage="empirical <element> <percent> ...",
        triggers=["empirical", "empformula"],
        run=_run_empirical,
        examples=["empirical C 40 H 6.7 O 53.3", "empirical C 92.3 H 7.7", "empirical Na 39.3 Cl 60.7"]))
    registry.register(Skill(
        name="gaslaw", description="Ideal gas law PV = nRT, solve for any one variable.",
        usage="gaslaw P <atm> V <L> n <mol> T <K>",
        triggers=["gaslaw", "idealgas"],
        run=_run_gaslaw,
        examples=["gaslaw P 2 V 5 n 0.5 T ?", "gaslaw P ? V 10 n 1 T 300", "gaslaw P 1 V 22.4 n 1 T ?"]))
    registry.register(Skill(
        name="dilute", description="Dilution M1V1 = M2V2, solve for any one value.",
        usage="dilute M1 <M> V1 <volume> M2 <M> V2 <volume>",
        triggers=["dilute", "dilution"],
        run=_run_dilute,
        examples=["dilute M1 2 V1 100 M2 0.5 V2 ?", "dilute M1 ? V1 25 M2 0.1 V2 250", "dilute M1 1 V1 50 M2 ? V2 200"]))
    registry.register(Skill(
        name="titrate", description="Titration: base concentration at the equivalence point.",
        usage="titrate <acid M> <acid mL> <acid coeff> <base coeff> <base mL>",
        triggers=["titrate", "titration"],
        run=_run_titrate,
        examples=["titrate 0.1 25 1 1 10", "titrate 0.5 20 1 2 40", "titrate 0.1 50 2 1 25"]))
    registry.register(Skill(
        name="halflife", description="Amount left after a number of half-lives, or after a time.",
        usage="halflife <amount> n <half-lives> | halflife <amount> after <time> hl <half-life>",
        triggers=["halflife", "decay"],
        run=_run_halflife,
        examples=["halflife 100 n 3", "halflife 100 after 10 hl 5.27", "halflife 80 n 2"]))
