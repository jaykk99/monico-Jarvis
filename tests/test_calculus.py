"""Tests for skills/calculus.py: deriv, integral, limit, tangent."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


def test_skill_count():
    assert len(agent.list_skills()) == 183


# ---------------------------------------------------------------- deriv
def test_deriv_quadratic():
    # f = x^2 - 3x + 2, f' = 2x - 3, f'(4) = 5, rising.
    out = _ask("deriv 1 -3 2 at 4")
    assert "f(x) = x^2 - 3x + 2, so f'(x) = 2x - 3." in out
    assert "f'(4) = 5" in out
    assert "rising" in out


def test_deriv_cubic():
    # f = 3x^3 - 2x + 5, f' = 9x^2 - 2, f'(1) = 7.
    out = _ask("deriv 3 0 -2 5 at 1")
    assert "f(x) = 3x^3 - 2x + 5, so f'(x) = 9x^2 - 2." in out
    assert "f'(1) = 7" in out


def test_deriv_linear_and_alias():
    # f = 2x + 1, f' = 2 everywhere; `derivative` is an alias trigger.
    out = _ask("derivative 2 1 at 3")
    assert "f'(x) = 2." in out
    assert "f'(3) = 2" in out


def test_deriv_constant():
    # A constant has derivative 0 and is flat everywhere.
    out = _ask("deriv 5 at 2")
    assert "f(x) = 5, so f'(x) = 0." in out
    assert "f'(2) = 0" in out
    assert "flat" in out


def test_deriv_falling():
    # f = x^2, f' = 2x, f'(-1) = -2, falling.
    out = _ask("deriv 1 0 0 at -1")
    assert "f'(-1) = -2" in out
    assert "falling" in out


def test_deriv_bad():
    assert "Usage" in _ask("deriv")
    assert "Usage" in _ask("deriv 1 2")
    assert "Usage" in _ask("deriv 1 2 3 4")
    assert "Usage" in _ask("deriv a b at 1")


# ---------------------------------------------------------------- integral
def test_integral_quadratic():
    # F = x^3/3; F(3) - F(0) = 9.
    out = _ask("integral 1 0 0 from 0 to 3")
    assert "The integral of x^2 from 0 to 3 is 9" in out
    assert "F(x) = x^3/3" in out


def test_integral_linear_and_alias():
    # f = 2x, F = x^2; F(4) - F(0) = 16; `integrate` is an alias trigger.
    out = _ask("integrate 2 0 from 0 to 4")
    assert "The integral of 2x from 0 to 4 is 16" in out
    assert "F(x) = x^2" in out


def test_integral_cancels():
    # f = x from -1 to 1: F = x^2/2, equal halves cancel to 0.
    out = _ask("integral 1 0 from -1 to 1")
    assert "The integral of x from -1 to 1 is 0" in out
    assert "F(x) = x^2/2" in out
    assert "cancel exactly" in out


def test_integral_reversed_bounds():
    # Backwards bounds flip the sign: -9, and the note says so.
    out = _ask("integral 1 0 0 from 3 to 0")
    assert "The integral of x^2 from 3 to 0 is -9" in out
    assert "run backwards" in out


def test_integral_negative_area():
    # f = -1 from 0 to 2: signed area -2, below the axis.
    out = _ask("integral 0 -1 from 0 to 2")
    assert "The integral of -1 from 0 to 2 is -2" in out
    assert "F(x) = -x" in out
    assert "signed area" in out


def test_integral_bad():
    assert "Usage" in _ask("integral")
    assert "Usage" in _ask("integral 1 0 0 from 0")
    assert "Usage" in _ask("integral 1 0 0 0 to 3")
    assert "Usage" in _ask("integral a from 0 to 1")


# ---------------------------------------------------------------- limit
def test_limit_polynomial():
    # f(4) = 16 - 12 + 2 = 6; polynomials are continuous.
    out = _ask("limit 1 -3 2 at 4")
    assert "The limit of x^2 - 3x + 2 as x approaches 4 is 6" in out
    assert "continuous" in out


def test_limit_hole():
    # (x^2 - 1)/(x - 1): both 0 at 1, (x - 1) cancels once, limit 2.
    out = _ask("limit 1 0 -1 / 1 -1 at 1")
    assert "is 2" in out
    assert "cancels once" in out
    assert "hole at x = 1" in out


def test_limit_hole_two():
    # (x^2 - 4)/(x - 2): hole at 2, limit 4.
    out = _ask("limit 1 0 -4 / 1 -2 at 2")
    assert "is 4" in out
    assert "hole at x = 2" in out


def test_limit_cancel_to_number():
    # (2x)/x: both 0 at 0, x cancels, limit 2.
    out = _ask("limit 2 0 / 1 0 at 0")
    assert "is 2" in out


def test_limit_no_finite():
    # x/(x - 1) at 1: numerator 1, denominator 0, blows up.
    out = _ask("limit 1 0 / 1 -1 at 1")
    assert "no finite limit" in out
    assert "grows without bound" in out


def test_limit_no_finite_after_cancel():
    # x/x^2 at 0: x cancels once, still 1/0, blows up.
    out = _ask("limit 1 0 / 1 0 0 at 0")
    assert "no finite limit" in out
    assert "after cancelling" in out


def test_limit_direct():
    # (x^2 + 1)/(x + 1) at 1: denominator 2, direct substitution, 1.
    out = _ask("limit 1 0 1 / 1 1 at 1")
    assert "is 1" in out
    assert "direct substitution" in out


def test_limit_bad():
    assert "Usage" in _ask("limit")
    assert "Usage" in _ask("limit 1 2 at")
    assert "Usage" in _ask("limit 1 / 2 at x")


# ---------------------------------------------------------------- tangent
def test_tangent_quadratic():
    # f = x^2 at 2: point (2, 4), slope 4, y = 4x - 4.
    out = _ask("tangent 1 0 0 at 2")
    assert "passes through (2, 4) with slope 4" in out
    assert "tangent line is y = 4x - 4." in out


def test_tangent_horizontal():
    # f = x^2 - 3x + 2 at 1.5: slope 0, point (1.5, -0.25).
    out = _ask("tangent 1 -3 2 at 1.5")
    assert "passes through (1.5, -0.25) with slope 0" in out
    assert "tangent line is y = -0.25." in out
    assert "horizontal" in out


def test_tangent_linear_and_alias():
    # f = 2x + 1 is its own tangent; `tangentline` is an alias trigger.
    out = _ask("tangentline 2 1 at 3")
    assert "passes through (3, 7) with slope 2" in out
    assert "tangent line is y = 2x + 1." in out
    assert "its own tangent" in out


def test_tangent_bad():
    assert "Usage" in _ask("tangent")
    assert "Usage" in _ask("tangent 1 2 3")
    assert "Usage" in _ask("tangent a at 1")
