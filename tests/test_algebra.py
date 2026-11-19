"""Tests for skills/algebra.py: linear, quadratic, simul, line, ineq, seq."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


def test_skill_count():
    assert len(agent.list_skills()) == 152


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
