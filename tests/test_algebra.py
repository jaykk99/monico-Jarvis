"""Tests for skills/algebra.py: linear, quadratic, simul, line."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


def test_skill_count():
    assert len(agent.list_skills()) == 150


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
