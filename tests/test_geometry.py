"""Tests for skills/geometry.py: circle, triangle, trig, coord."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


def test_skill_count():
    assert len(agent.list_skills()) == 176


# ---------------------------------------------------------------- circle
def test_circle_radius():
    # r = 5: d = 10, C = 2 pi x 5 = 31.4159 -> 31.42,
    # A = pi x 25 = 78.5398 -> 78.54.
    out = _ask("circle r5")
    assert "Circle with radius 5: diameter 10, circumference 31.42, area 78.54." in out


def test_circle_diameter():
    # d = 10 -> r = 5, same circle as above.
    out = _ask("circle d10")
    assert "Circle with radius 5: diameter 10, circumference 31.42, area 78.54." in out


def test_circle_circumference():
    # C = 31.42 -> r = 31.42 / (2 pi) = 5.0006 -> 5.001,
    # A = pi x 5.0006^2 = 78.56; C recomputed = 31.42.
    out = _ask("circle c31.42")
    assert "Circle with radius 5.001: diameter 10, circumference 31.42, area 78.56." in out


def test_circle_area():
    # A = 78.54 -> r = sqrt(78.54 / pi) = 5.00006 -> 5.
    out = _ask("circle a78.54")
    assert "Circle with radius 5: diameter 10, circumference 31.42, area 78.54." in out


def test_circle_bad():
    assert "Usage" in _ask("circle")
    assert "Usage" in _ask("circle 5")
    assert "Usage" in _ask("circle r")
    assert "Usage" in _ask("circle x5")
    assert "above 0" in _ask("circle r0")


# ---------------------------------------------------------------- triangle
def test_triangle_right_legs():
    # Legs 3 and 4: hyp = 5, area = 6, perimeter = 12.
    out = _ask("triangle 3 4")
    assert "Right triangle with legs 3 and 4: hypotenuse 5, area 6, perimeter 12." in out


def test_triangle_three_sides():
    # 3, 4, 5: s = 6, area = sqrt(6 x 3 x 2 x 1) = 6; 9 + 16 = 25, right.
    out = _ask("triangle 3 4 5")
    assert "Triangle with sides 3, 4, 5: perimeter 12, area 6, right triangle (3^2 + 4^2 = 5^2), scalene." in out


def test_triangle_isosceles():
    # 5, 5, 6: s = 8, area = sqrt(8 x 3 x 3 x 2) = 12; 25 + 25 != 36.
    out = _ask("triangle 5 5 6")
    assert "Triangle with sides 5, 5, 6: perimeter 16, area 12, not right-angled, isosceles." in out


def test_triangle_bad():
    assert "Usage" in _ask("triangle")
    assert "Usage" in _ask("triangle 3")
    assert "Usage" in _ask("triangle 3 4 5 6")
    assert "Usage" in _ask("triangle a b")
    assert "above 0" in _ask("triangle 0 4")
    assert "can't make a triangle" in _ask("triangle 2 3 10")


# ---------------------------------------------------------------- trig
def test_trig_forward():
    # sin 30 = 0.5, cos 60 = 0.5, tan 45 = 1, sin 90 = 1.
    assert "sin(30°) = 0.5." in _ask("trig sin 30")
    assert "cos(60°) = 0.5." in _ask("trig cos 60")
    assert "tan(45°) = 1." in _ask("trig tan 45")
    assert "sin(90°) = 1." in _ask("trig sin 90")


def test_trig_inverse():
    # asin 0.5 = 30, acos 0 = 90, atan 1 = 45.
    assert "asin(0.5) = 30°." in _ask("trig asin 0.5")
    assert "acos(0) = 90°." in _ask("trig acos 0")
    assert "atan(1) = 45°." in _ask("trig atan 1")


def test_trig_bad():
    assert "Usage" in _ask("trig")
    assert "Usage" in _ask("trig sin")
    assert "Usage" in _ask("trig sec 30")
    assert "Usage" in _ask("trig sin x")
    assert "undefined" in _ask("trig tan 90")
    assert "only takes -1 to 1" in _ask("trig asin 2")


# ---------------------------------------------------------------- coord
def test_coord_basic():
    # (0,0) to (3,4): distance 5, midpoint (1.5, 2), slope 4/3 = 1.333.
    out = _ask("coord 0 0 3 4")
    assert "From (0, 0) to (3, 4): distance 5, midpoint (1.5, 2), slope 1.333." in out


def test_coord_negative():
    # (-1,-1) to (2,3): dx 3, dy 4, distance 5, midpoint (0.5, 1).
    out = _ask("coord -1 -1 2 3")
    assert "From (-1, -1) to (2, 3): distance 5, midpoint (0.5, 1), slope 1.333." in out


def test_coord_vertical():
    # Same x: distance 3, midpoint (1, 3.5), slope undefined.
    out = _ask("coord 1 2 1 5")
    assert "From (1, 2) to (1, 5): distance 3, midpoint (1, 3.5), slope undefined (vertical line)." in out


def test_coord_bad():
    assert "Usage" in _ask("coord")
    assert "Usage" in _ask("coord 0 0 3")
    assert "Usage" in _ask("coord 0 0 3 x")
