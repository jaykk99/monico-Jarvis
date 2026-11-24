"""Tests for skills/algebra.py: linear, quadratic, simul, line, ineq, seq,
gcd, ratio, exponent, logarithm, scientific, factorquad."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


def test_skill_count():
    assert len(agent.list_skills()) == 176


# ---------------------------------------------------------------- linear
def test_linear_basic():
    # 2x + 3 = 0 -> x = -3/2 = -1.5.
    out = _ask("linear 2 3")
    assert "2x + 3 = 0 has x = -1.5." in out


def test_linear_negative():
    # -4x + 8 = 0 -> x = 2; 3x - 9 = 0 -> x = 3.
    out = _ask("linear -4 8")
    assert "-4x + 8 = 0 has x = 2." in out
    out = _ask("linear 3 -9")
    assert "3x - 9 = 0 has x = 3." in out


def test_linear_equation_form():
    # 2x + 3 = 7 -> 2x = 4 -> x = 2; x + 1 = 2 -> x = 1.
    out = _ask("linear 2x+3=7")
    assert "2x + 3 = 7 has x = 2." in out
    out = _ask("linear x+1=2")
    assert "x + 1 = 2 has x = 1." in out


def test_linear_no_solution():
    # 0x + 5 = 0 is never true.
    out = _ask("linear 0 5")
    assert "5 = 0 has no solution" in out


def test_linear_every_x():
    # 0x + 0 = 0 is true for every x.
    out = _ask("linear 0 0")
    assert "0 = 0 is true for every x" in out


def test_linear_bad():
    assert "Usage" in _ask("linear")
    assert "Usage" in _ask("linear 2")
    assert "Usage" in _ask("linear abc 3")
    assert "Usage" in _ask("linear 2x+3")


# ---------------------------------------------------------------- quadratic
def test_quadratic_two_roots():
    # D = 9 - 8 = 1; roots (3 +- 1)/2 = 2, 1; vertex x = 1.5,
    # y = 2.25 - 4.5 + 2 = -0.25.
    out = _ask("quadratic 1 -3 2")
    assert "x^2 - 3x + 2 = 0 has two roots, x = 2 and x = 1 (discriminant 1); vertex (1.5, -0.25)." in out


def test_quadratic_two_roots_negative():
    # D = 0 + 16 = 16; roots (0 +- 4)/2 = 2, -2; vertex (0, -4).
    out = _ask("quadratic 1 0 -4")
    assert "x^2 - 4 = 0 has two roots, x = 2 and x = -2 (discriminant 16); vertex (0, -4)." in out
    # D = 16 + 48 = 64; roots (4 +- 8)/4 = 3, -1; vertex (1, -8).
    out = _ask("quadratic 2 -4 -6")
    assert "2x^2 - 4x - 6 = 0 has two roots, x = 3 and x = -1 (discriminant 64); vertex (1, -8)." in out


def test_quadratic_repeated_root():
    # D = 4 - 4 = 0; single root -2/2 = -1; vertex (-1, 0).
    out = _ask("quadratic 1 2 1")
    assert "x^2 + 2x + 1 = 0 has one repeated root, x = -1 (discriminant 0); vertex (-1, 0)." in out


def test_quadratic_complex():
    # D = 0 - 4 = -4; roots 0 +- 1i; vertex (0, 1).
    out = _ask("quadratic 1 0 1")
    assert "x^2 + 1 = 0 has no real roots (discriminant -4); complex roots x = 0 + 1i and x = 0 - 1i; vertex (0, 1)." in out
    # D = 4 - 20 = -16; roots 1 +- 2i; vertex (1, 4).
    out = _ask("quadratic 1 -2 5")
    assert "x^2 - 2x + 5 = 0 has no real roots (discriminant -16); complex roots x = 1 + 2i and x = 1 - 2i; vertex (1, 4)." in out


def test_quadratic_not_quadratic():
    assert "not a quadratic" in _ask("quadratic 0 2 1")


def test_quadratic_bad():
    assert "Usage" in _ask("quadratic")
    assert "Usage" in _ask("quadratic 1 2")
    assert "Usage" in _ask("quadratic 1 2 x")


# ---------------------------------------------------------------- simul
def test_simul_basic():
    # det = -2; x = (-5 - 1)/-2 = 3, y = (1 - 5)/-2 = 2.
    out = _ask("simul 1 1 5 1 -1 1")
    assert "x + y = 5 and x - y = 1 meet at x = 3, y = 2." in out


def test_simul_second():
    # 2x + 3y = 8, x - y = -1: det = -5; x = (-8 + 3)/-5 = 1,
    # y = (-2 - 8)/-5 = 2.
    out = _ask("simul 2 3 8 1 -1 -1")
    assert "2x + 3y = 8 and x - y = -1 meet at x = 1, y = 2." in out


def test_simul_third():
    # 3x + 2y = 7, x + 4y = 9: det = 10; x = (28 - 18)/10 = 1,
    # y = (27 - 7)/10 = 2.
    out = _ask("simul 3 2 7 1 4 9")
    assert "3x + 2y = 7 and x + 4y = 9 meet at x = 1, y = 2." in out


def test_simul_same_line():
    # Second equation is twice the first: det = 0, same line.
    out = _ask("simul 1 1 2 2 2 4")
    assert "are the same line" in out


def test_simul_parallel():
    # Same left sides, different right sides: det = 0, no solution.
    out = _ask("simul 1 1 2 1 1 3")
    assert "parallel lines that never meet" in out


def test_simul_bad():
    assert "Usage" in _ask("simul")
    assert "Usage" in _ask("simul 1 1 5")
    assert "Usage" in _ask("simul 1 1 5 1 -1")


# ---------------------------------------------------------------- line
def test_line_basic():
    # Slope (4 - 0)/(2 - 0) = 2, intercept 0, x-intercept 0.
    out = _ask("line 0 0 2 4")
    assert "Line through (0, 0) and (2, 4): y = 2x, slope 2, y-intercept 0, x-intercept 0." in out


def test_line_intercept():
    # Slope (5 - 1)/2 = 2, intercept 1, x-intercept -1/2 = -0.5.
    out = _ask("line 0 1 2 5")
    assert "Line through (0, 1) and (2, 5): y = 2x + 1, slope 2, y-intercept 1, x-intercept -0.5." in out


def test_line_fractional():
    # Slope (2 - 1)/2 = 0.5, intercept 0.5, x-intercept -1.
    out = _ask("line 1 1 3 2")
    assert "Line through (1, 1) and (3, 2): y = 0.5x + 0.5, slope 0.5, y-intercept 0.5, x-intercept -1." in out


def test_line_horizontal():
    # Slope 0: y = 3, never crosses the x-axis.
    out = _ask("line 0 3 4 3")
    assert "Line through (0, 3) and (4, 3): y = 3, slope 0, y-intercept 3, no x-intercept (it never crosses the x-axis)." in out


def test_line_vertical():
    # x1 = x2: x = 1, no slope, no y-intercept.
    out = _ask("line 1 2 1 5")
    assert "Line through (1, 2) and (1, 5): x = 1 (vertical line), slope undefined, no y-intercept." in out


def test_line_bad():
    assert "Usage" in _ask("line")
    assert "Usage" in _ask("line 0 0 3")
    assert "same point" in _ask("line 1 1 1 1")


# ---------------------------------------------------------------- ineq
def test_ineq_basic():
    # 2x > 4 -> x > 2, boundary value 7.
    out = _ask("ineq 2x+3>7")
    assert "x > 2. At x = 2 both sides equal 7." in out


def test_ineq_flip():
    # -2x + 4 < 10 -> -2x < 6, dividing by -2 flips it: x > -3.
    out = _ask("ineq -2x+4<10")
    assert "x > -3. At x = -3 both sides equal 10." in out


def test_ineq_closed_and_both_sides():
    # 3x >= 15 -> x >= 5; 2x <= 10 -> x <= 5, boundary 27.
    assert "x >= 5. At x = 5 both sides equal 10." in _ask("ineq 3x-5>=10")
    assert "x <= 5. At x = 5 both sides equal 27." in _ask("ineq 5x+2<=3x+12")


def test_ineq_none_or_every():
    # x cancels, 3 > 5 never holds; 3 < 5 always holds.
    assert "No solution" in _ask("ineq 2x+3>2x+5")
    assert "Every value of x works" in _ask("ineq 2x+3<2x+5")


def test_ineq_bad():
    assert "Usage" in _ask("ineq")
    assert "Usage" in _ask("ineq 2x+3=7")
    assert "Usage" in _ask("ineq 2x+3")


# ---------------------------------------------------------------- seq
def test_seq_arith():
    # Term 10 = 3 + 9 x 5 = 48; sum = 10/2 x (6 + 45) = 255.
    out = _ask("seq arith 3 5 10")
    assert "Arithmetic: term 10 = 48 (first 3, difference 5), sum of the first 10 = 255." in out
    # Terms 10, 8, 6, 4, 2: term 5 = 2, sum 30.
    out = _ask("seq arith 10 -2 5")
    assert "Arithmetic: term 5 = 2 (first 10, difference -2), sum of the first 5 = 30." in out


def test_seq_geo():
    # Term 5 = 2 x 3^4 = 162; sum = 2 x (243 - 1) / 2 = 242.
    out = _ask("seq geo 2 3 5")
    assert "Geometric: term 5 = 162 (first 2, ratio 3), sum of the first 5 = 242." in out
    # Ratio 1: every term is 5, sum of 7 is 35.
    out = _ask("seq geo 5 1 7")
    assert "Geometric: term 7 = 5 (first 5, ratio 1), sum of the first 7 = 35." in out
    # Terms 3, 1.5, 0.75, 0.375: term 4 = 0.375, sum 5.625.
    out = _ask("seq geo 3 0.5 4")
    assert "Geometric: term 4 = 0.375 (first 3, ratio 0.5), sum of the first 4 = 5.625." in out


def test_seq_bad():
    assert "Usage" in _ask("seq")
    assert "Usage" in _ask("seq arith 1 2")
    assert "whole number" in _ask("seq geo 1 2 0")
    assert "whole number" in _ask("seq arith 1 2 1.5")


# ---------------------------------------------------------------- gcd
def test_gcd_basic():
    # 12 = 2^2 x 3, 18 = 2 x 3^2: GCD 6, LCM 36.
    out = _ask("gcd 12 18")
    assert "GCD of 12 and 18 is 6. LCM is 36." in out


def test_gcd_coprime_and_large():
    # 7 and 13 share nothing: GCD 1, LCM 91. 100 and 80: GCD 20, LCM 400.
    assert "GCD of 7 and 13 is 1. LCM is 91." in _ask("gcd 7 13")
    assert "GCD of 100 and 80 is 20. LCM is 400." in _ask("gcd 100 80")


def test_gcd_zero_and_bad():
    assert "GCD of 0 and 5 is 5. LCM is 0." in _ask("gcd 0 5")
    assert "not defined" in _ask("gcd 0 0")
    assert "Usage" in _ask("gcd 12")
    assert "Usage" in _ask("gcd 1.5 2")


# ---------------------------------------------------------------- ratio
def test_ratio_simplify():
    # 12:18 -> 2:3; 1.5:2.5 -> 3:5.
    assert "12:18 simplifies to 2:3." in _ask("ratio 12 18")
    assert "1.5:2.5 simplifies to 3:5." in _ask("ratio 1.5 2.5")


def test_ratio_proportion():
    # 3:4 = 12:x -> x = 16; 2:5 = 10:x -> x = 25.
    assert "3:4 = 12:16, so the missing term is 16." in _ask("ratio 3 4 12")
    assert "2:5 = 10:25, so the missing term is 25." in _ask("ratio 2 5 10")


def test_ratio_bad():
    assert "Usage" in _ask("ratio")
    assert "Usage" in _ask("ratio 12")
    assert "not a ratio" in _ask("ratio 0 0")
    assert "No single answer" in _ask("ratio 0 4 12")


# ---------------------------------------------------------------- exponent
def test_exponent_basic():
    # 2^10 = 1024; 2^-3 = 1/8; 9^0.5 = 3.
    assert "2^10 = 1,024." in _ask("exponent 2 10")
    assert "2^-3 = 0.125." in _ask("exponent 2 -3")
    assert "9^0.5 = 3." in _ask("exponent 9 0.5")


def test_exponent_same_base_rules():
    # 2^3 x 2^4 = 2^7 = 128; 2^5 / 2^2 = 2^3 = 8.
    assert "2^3 x 2^4 = 2^7 = 128." in _ask("exponent 2 3 * 4")
    assert "2^5 / 2^2 = 2^3 = 8." in _ask("exponent 2 5 / 2")


def test_exponent_edge_and_bad():
    assert "not defined" in _ask("exponent 0 0")
    assert "not defined" in _ask("exponent 0 -2")
    assert "not a real number" in _ask("exponent -8 0.5")
    assert "too large" in _ask("exponent 10 400")
    assert "Usage" in _ask("exponent")
    assert "Usage" in _ask("exponent 2")
    assert "Usage" in _ask("exponent 2 x 3")


# ---------------------------------------------------------------- logarithm
def test_log_base10_and_any_base():
    # log10(100) = 2; log2(8) = 3; log3(81) = 4.
    assert "log10(100) = 2." in _ask("log 100")
    assert "log2(8) = 3." in _ask("log 8 2")
    assert "log3(81) = 4." in _ask("log 81 3")


def test_log_natural():
    # ln(10) = 2.302585... -> 2.303; `ln` works as its own trigger.
    assert "ln(10) = 2.303." in _ask("log ln 10")
    assert "ln(10) = 2.303." in _ask("ln 10")
    assert "ln(1) = 0." in _ask("log ln 1")


def test_log_edge_and_bad():
    assert "not defined" in _ask("log 0")
    assert "not defined" in _ask("log -5")
    assert "not 1" in _ask("log 8 1")
    assert "positive" in _ask("log 8 0")
    assert "Usage" in _ask("log")
    assert "Usage" in _ask("log abc")


# ---------------------------------------------------------------- scientific
def test_sci_to_notation():
    # 1234567 = 1.234567 x 10^6 -> 1.235 x 10^6; 0.00042 = 4.2 x 10^-4.
    assert "1,234,567 = 1.235 x 10^6." in _ask("sci 1234567")
    assert "0.00042 = 4.2 x 10^-4." in _ask("sci 0.00042")
    assert "0 in scientific notation is 0." in _ask("sci 0")


def test_sci_expand():
    # 1.5 x 10^6 = 1,500,000; 2.5 x 10^-3 = 0.0025.
    assert "1.5 x 10^6 = 1,500,000." in _ask("sci 1.5 6")
    assert "2.5 x 10^-3 = 0.0025." in _ask("sci 2.5 -3")


def test_sci_bad():
    assert "Usage" in _ask("sci")
    assert "Usage" in _ask("sci abc")
    assert "Usage" in _ask("sci 1.5 2.5")


# ---------------------------------------------------------------- factorquad
def test_factorquad_basic():
    # x^2 - 3x + 2 = (x - 1)(x - 2); 2x^2 + 7x + 3 = (x + 3)(2x + 1).
    assert "x^2 - 3x + 2 = (x - 1)(x - 2)." in _ask("factorquad 1 -3 2")
    assert "2x^2 + 7x + 3 = (x + 3)(2x + 1)." in _ask("factorquad 2 7 3")


def test_factorquad_difference_of_squares_and_negative():
    # x^2 - 9 = (x + 3)(x - 3); -x^2 + 5x - 6 = -(x - 2)(x - 3).
    assert "x^2 - 9 = (x + 3)(x - 3)." in _ask("factorquad 1 0 -9")
    assert "-x^2 + 5x - 6 = -(x - 2)(x - 3)." in _ask("factorquad -1 5 -6")


def test_factorquad_zero_constant():
    # 2x^2 + 5x = x(2x + 5).
    assert "2x^2 + 5x = x(2x + 5)." in _ask("factorquad 2 5 0")


def test_factorquad_no_integer_factors():
    # x^2 + 1 has discriminant -4: no integer factors, points at quadratic.
    out = _ask("factorquad 1 0 1")
    assert "does not factor over the integers" in out
    assert "discriminant -4" in out
    assert "quadratic 1 0 1" in out


def test_factorquad_bad():
    assert "not a quadratic" in _ask("factorquad 0 1 2")
    assert "Usage" in _ask("factorquad")
    assert "Usage" in _ask("factorquad 1 2")
    assert "Usage" in _ask("factorquad 1.5 2 3")
