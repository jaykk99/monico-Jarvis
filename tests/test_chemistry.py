"""Tests for skills/chemistry.py: molarmass, pctcomp, empirical,
gaslaw, dilute, titrate, halflife."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


def test_skill_count():
    assert len(agent.list_skills()) == 176


# ---------------------------------------------------------------- molarmass
def test_molarmass_water():
    # 2 x 1.008 + 15.999 = 18.015 g/mol.
    out = _ask("molarmass H2O")
    assert "molar mass of H2O is 18.02 g/mol" in out


def test_molarmass_calcium_hydroxide():
    # Ca(OH)2: 40.078 + 2 x (15.999 + 1.008) = 74.092 g/mol.
    out = _ask("molarmass Ca(OH)2")
    assert "molar mass of Ca(OH)2 is 74.09 g/mol" in out


def test_molarmass_glucose_and_alias():
    # C6H12O6: 6 x 12.011 + 12 x 1.008 + 6 x 15.999 = 180.156 g/mol.
    out = _ask("molar C6H12O6")
    assert "molar mass of C6H12O6 is 180.2 g/mol" in out


def test_molarmass_nested_parens():
    # Al2(SO4)3: 2 x 26.982 + 3 x (32.06 + 4 x 15.999) = 342.15 g/mol.
    out = _ask("molarmass Al2(SO4)3")
    assert "molar mass of Al2(SO4)3 is 342.1 g/mol" in out


def test_molarmass_bad():
    assert "Usage" in _ask("molarmass")
    assert "Usage" in _ask("molarmass H2O NaCl")
    assert "must follow an element or `)`" in _ask("molarmass 2H2O")
    assert "Unmatched" in _ask("molarmass Ca(OH2")
    assert "do not know the element" in _ask("molarmass Xx2")


# ---------------------------------------------------------------- pctcomp
def test_pctcomp_water():
    # H 2.016/18.015 = 11.19%, O 15.999/18.015 = 88.81%.
    out = _ask("pctcomp H2O")
    assert "H2O is 18.02 g/mol" in out
    assert "H 11.19%" in out
    assert "O 88.81%" in out


def test_pctcomp_glucose_and_alias():
    out = _ask("composition C6H12O6")
    assert "C6H12O6 is 180.2 g/mol" in out
    assert "C 40%" in out
    assert "H 6.714%" in out
    assert "O 53.28%" in out


def test_pctcomp_bad():
    assert "Usage" in _ask("pctcomp")
    assert "do not know the element" in _ask("pctcomp ZzO")


# ---------------------------------------------------------------- empirical
def test_empirical_ch2o():
    # C 40/12.011 = 3.33, H 6.7/1.008 = 6.65, O 53.3/15.999 = 3.33 -> CH2O.
    out = _ask("empirical C 40 H 6.7 O 53.3")
    assert "empirical formula is CH2O" in out


def test_empirical_ch():
    # C 92.3/12.011 = 7.69, H 7.7/1.008 = 7.64 -> 1:1 -> CH.
    out = _ask("empirical C 92.3 H 7.7")
    assert "empirical formula is CH" in out


def test_empirical_nacl_and_alias():
    out = _ask("empformula Na 39.3 Cl 60.7")
    assert "empirical formula is NaCl" in out


def test_empirical_bad_total():
    out = _ask("empirical C 40 H 6.7")
    assert "add up to 46.7" in out
    assert "not about 100" in out


def test_empirical_bad():
    assert "Usage" in _ask("empirical")
    assert "Usage" in _ask("empirical C 40 H")
    assert "do not know the element" in _ask("empirical Xx 50 H 50")


# ---------------------------------------------------------------- gaslaw
def test_gaslaw_solve_t():
    # T = PV/nR = 2 x 5 / (0.5 x 0.082057) = 243.7 K.
    out = _ask("gaslaw P 2 V 5 n 0.5 T ?")
    assert "T = 243.7 K" in out


def test_gaslaw_solve_p():
    # P = nRT/V = 1 x 0.082057 x 300 / 10 = 2.462 atm.
    out = _ask("gaslaw P ? V 10 n 1 T 300")
    assert "P = 2.462 atm" in out


def test_gaslaw_molar_volume_and_alias():
    # At STP, 1 mol at 1 atm takes 22.4 L -> T = 273 K.
    out = _ask("idealgas P 1 V 22.4 n 1 T ?")
    assert "T = 273 K" in out


def test_gaslaw_high_pressure_warning():
    # P = 1 x 0.082057 x 300 / 1 = 24.62 atm -> ideal-gas warning.
    out = _ask("gaslaw P ? V 1 n 1 T 300")
    assert "P = 24.62 atm" in out
    assert "deviate from the ideal gas law" in out


def test_gaslaw_bad():
    assert "Usage" in _ask("gaslaw")
    assert "Usage" in _ask("gaslaw P 2 V 5 n 0.5")
    assert "Exactly one value must be" in _ask("gaslaw P ? V 5 n 0.5 T ?")
    assert "must all be positive" in _ask("gaslaw P -2 V 5 n 0.5 T ?")


# ---------------------------------------------------------------- dilute
def test_dilute_solve_v2():
    # V2 = M1V1/M2 = 2 x 100 / 0.5 = 400; 300 of solvent added.
    out = _ask("dilute M1 2 V1 100 M2 0.5 V2 ?")
    assert "V2 = 400" in out
    assert "add 300 of solvent" in out


def test_dilute_solve_m1():
    # M1 = M2V2/V1 = 0.1 x 250 / 25 = 1 M.
    out = _ask("dilute M1 ? V1 25 M2 0.1 V2 250")
    assert "M1 = 1 M" in out


def test_dilute_solve_m2_and_alias():
    # M2 = M1V1/V2 = 1 x 50 / 200 = 0.25 M.
    out = _ask("dilution M1 1 V1 50 M2 ? V2 200")
    assert "M2 = 0.25 M" in out


def test_dilute_solve_v1():
    # V1 = M2V2/M1 = 0.5 x 400 / 2 = 100 of stock, topped up to 400.
    out = _ask("dilute M1 2 V1 ? M2 0.5 V2 400")
    assert "V1 = 100 of the stock solution" in out
    assert "top up to 400 total" in out


def test_dilute_bad():
    assert "Usage" in _ask("dilute")
    assert "Exactly one value must be" in _ask("dilute M1 ? V1 ? M2 0.5 V2 400")
    assert "must all be positive" in _ask("dilute M1 0 V1 100 M2 0.5 V2 ?")


# ---------------------------------------------------------------- titrate
def test_titrate_one_to_one():
    # 0.1 M x 25 mL = 2.5 mmol acid -> 2.5 mmol base in 10 mL = 0.25 M.
    out = _ask("titrate 0.1 25 1 1 10")
    assert "the base is 0.25 M" in out
    assert "2.5 mmol" in out


def test_titrate_two_to_one_and_alias():
    # 0.5 M x 20 mL = 10 mmol acid, 1:2 ratio -> 20 mmol base in 40 mL = 0.5 M.
    out = _ask("titration 0.5 20 1 2 40")
    assert "the base is 0.5 M" in out


def test_titrate_two_acid_one_base():
    # 0.1 M x 50 mL = 5 mmol acid, 2:1 ratio -> 2.5 mmol base in 25 mL = 0.1 M.
    out = _ask("titrate 0.1 50 2 1 25")
    assert "the base is 0.1 M" in out


def test_titrate_bad():
    assert "Usage" in _ask("titrate")
    assert "Usage" in _ask("titrate 0.1 25 1 1")
    assert "must all be positive" in _ask("titrate 0.1 25 1 1 0")
    assert "whole numbers" in _ask("titrate 0.1 25 1.5 1 10")


# ---------------------------------------------------------------- halflife
def test_halflife_n():
    # 100 / 2^3 = 12.5 left, 87.5 decayed.
    out = _ask("halflife 100 n 3")
    assert "After 3 half-lives, 12.5 is left" in out
    assert "87.5 decayed" in out


def test_halflife_after_time():
    # 10 / 5.27 = 1.898 half-lives; 100 / 2^1.898 = 26.87 left.
    out = _ask("halflife 100 after 10 hl 5.27")
    assert "After 1.898 half-lives" in out
    assert "26.84 is left" in out


def test_halflife_two_and_alias():
    # 80 / 2^2 = 20 left.
    out = _ask("decay 80 n 2")
    assert "After 2 half-lives, 20 is left" in out


def test_halflife_zero():
    out = _ask("halflife 100 n 0")
    assert "100 is left" in out
    assert "Nothing has decayed yet" in out


def test_halflife_bad():
    assert "Usage" in _ask("halflife")
    assert "Usage" in _ask("halflife 100 after 10")
    assert "Usage" in _ask("halflife 100 x 3")


# ---------------------------------------------------------------- non-finite input
def test_non_finite_numbers_are_usage_not_a_crash():
    # float("nan") and float("1e999") (= inf) both parse, and used to
    # crash callers: _fmt(inf) raises OverflowError out of int(inf),
    # round(nan) raises ValueError in the empirical multiplier loop.
    # Every skill answers with its usage text instead now.
    assert "Usage" in _ask("empirical C nan H 50")
    assert "Usage" in _ask("empirical C 1e999 H 50")
    assert "Usage" in _ask("gaslaw P nan V 5 n 0.5 T ?")
    assert "Usage" in _ask("gaslaw P 1e999 V 5 n 0.5 T ?")
    assert "Usage" in _ask("dilute M1 nan V1 100 M2 0.5 V2 ?")
    assert "Usage" in _ask("titrate nan 25 1 1 10")
    assert "Usage" in _ask("halflife nan n 3")
    assert "Usage" in _ask("halflife 100 n inf")
