"""Tests for skills/cook.py: recipe, bake, roast, serving."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- recipe
def test_recipe_metric():
    # 4 -> 8 servings doubles 200 g flour to 400 g
    out = _ask("recipe 4 8 200g flour")
    assert "4 servings → 8 servings (×2)" in out
    assert "200 g flour becomes 400 g flour" in out
    # Fractional amounts scale too: 4 -> 6 servings, 1.5 cups -> 2.25 cups
    out = _ask("recipe 4 6 1.5cups rice")
    assert "(×1.5)" in out and "1.5 cups rice becomes 2.25 cups rice" in out
    # Ingredient is optional
    out = _ask("recipe 2 6 100g")
    assert "100 g becomes 300 g" in out
    # The scale alias routes to the same skill
    out = _ask("scale 4 8 200g flour")
    assert "400 g flour" in out


def test_recipe_bad():
    assert "Usage" in _ask("recipe")
    assert "Usage" in _ask("recipe 4 8")  # needs an amount
    assert "Usage" in _ask("recipe 4 8 200")  # amount needs a unit
    assert "Usage" in _ask("recipe four 8 200g flour")
    assert "greater than 0" in _ask("recipe 0 8 200g flour")
    assert "greater than 0" in _ask("recipe 4 0 200g flour")
    assert "greater than 0" in _ask("recipe 4 8 0g flour")


# ---------------------------------------------------------------- bake
def test_bake_celsius():
    # 180 C = 356 F exactly; nearest gas mark is 4 (180 C / 350 F)
    out = _ask("bake 180C")
    assert "180°C = 356°F" in out
    assert "nearest gas mark 4 (180°C / 350°F)" in out
    # The oven alias routes to the same skill
    out = _ask("oven 200C")
    assert "200°C = 392°F" in out
    assert "nearest gas mark 6 (200°C / 400°F)" in out


def test_bake_fahrenheit():
    # 350 F = 177 C rounded; nearest gas mark is 4
    out = _ask("bake 350F")
    assert "350°F = 177°C" in out
    assert "nearest gas mark 4 (180°C / 350°F)" in out


def test_bake_gas():
    out = _ask("bake gas 4")
    assert "Gas mark 4 = 180°C / 350°F" in out
    # The compact form works too
    out = _ask("bake gas1")
    assert "Gas mark 1 = 140°C / 275°F" in out
    out = _ask("bake gas 9")
    assert "Gas mark 9 = 240°C / 475°F" in out


def test_bake_bad():
    assert "Usage" in _ask("bake")
    assert "Usage" in _ask("bake 180")  # needs a unit
    assert "Usage" in _ask("bake hot")
    assert "Gas mark must be 1 to 9" in _ask("bake gas 0")
    assert "Gas mark must be 1 to 9" in _ask("bake gas 10")
    assert "greater than 0" in _ask("bake 0C")


# ---------------------------------------------------------------- roast
def test_roast_beef_metric():
    # 1.5 kg beef medium-rare: 3 x 20 min = 60 min = 1 h, + 15 min rest
    out = _ask("roast beef 1.5kg")
    assert "1.5 kg beef, medium-rare" in out
    assert "about 1 h roasting at 200°C (400°F)" in out
    assert "plus 15 min rest" in out
    assert "63°C centre" in out
    # Rare is faster: 1 kg at 15 min per 500 g = 30 min
    out = _ask("roast beef 1kg rare")
    assert "about 30 min roasting" in out
    # Well done takes longest: 1 kg at 30 min per 500 g = 1 h
    out = _ask("roast beef 1kg well")
    assert "about 1 h roasting" in out


def test_roast_imperial():
    # 4 lb chicken = 1.81 kg: ceil(3.63 x 20) = 73 min + 20 extra
    # = 93 min = 1 h 33 min, at 190 C
    out = _ask("roast chicken 4lb")
    assert "4 lb (1.81 kg) chicken, well" in out
    assert "about 1 h 33 min roasting at 190°C (375°F)" in out
    assert "plus 20 min rest" in out
    assert "74°C in the thickest part" in out
    # 2 lb pork: 0.91 kg x 25 min per 500 g = 46 min
    out = _ask("roast pork 2lb")
    assert "2 lb (0.91 kg) pork, well" in out
    assert "about 46 min roasting" in out


def test_roast_lamb_turkey():
    # 2 kg lamb medium: 4 x 25 min = 100 min = 1 h 40 min
    out = _ask("roast lamb 2kg medium")
    assert "2 kg lamb, medium" in out
    assert "about 1 h 40 min roasting" in out
    # The roasting alias routes to the same skill
    out = _ask("roasting lamb 2kg medium")
    assert "about 1 h 40 min roasting" in out
    # 10 lb turkey: 4.54 kg -> ceil(9.07 x 20) = 182 min + 20 = 202 min
    out = _ask("roast turkey 10lb")
    assert "10 lb (4.54 kg) turkey, well" in out
    assert "about 3 h 22 min roasting" in out


def test_roast_bad():
    assert "Usage" in _ask("roast")
    assert "Usage" in _ask("roast beef")  # needs a weight
    assert "Usage" in _ask("roast beef 1.5")  # weight needs a unit
    assert "Usage" in _ask("roast fish 1kg")  # unknown meat
    assert "Doneness only applies to beef and lamb" in _ask(
        "roast chicken 2kg medium")
    assert "Doneness" in _ask("roast beef 1kg burnt")
    assert "greater than 0" in _ask("roast beef 0kg")


# ---------------------------------------------------------------- serving
def test_serving_metric():
    # 6 people x 100 g dry pasta = 600 g (21.2 oz)
    out = _ask("serving 6 pasta")
    assert "6 people, dry pasta (main course)" in out
    assert "600 g (21.2 oz)" in out
    # 4 people x 75 g dry rice = 300 g (10.6 oz)
    out = _ask("serving 4 rice")
    assert "300 g (10.6 oz)" in out
    # The servings and portions aliases route to the same skill
    out = _ask("servings 6 pasta")
    assert "600 g (21.2 oz)" in out
    out = _ask("portions 4 rice")
    assert "300 g (10.6 oz)" in out


def test_serving_soup():
    # 2 people x 300 ml soup = 600 ml (2.54 cups)
    out = _ask("serving 2 soup")
    assert "2 people, soup (main course)" in out
    assert "600 ml (2.54 cups)" in out


def test_serving_bad():
    assert "Usage" in _ask("serving")
    assert "Usage" in _ask("serving 6")  # needs a dish
    assert "Usage" in _ask("serving 6 pizza")  # unknown dish
    assert "Usage" in _ask("serving 2.5 pasta")  # people must be whole
    assert "greater than 0" in _ask("serving 0 pasta")


# ---------------------------------------------------------------- no trigger collisions
def test_no_existing_skill_lost_its_trigger():
    # `convert` (builtin) is the nearest neighbour; it must keep owning
    # its own trigger.
    out = _ask("convert 1 kg to lb")
    assert "1 kg = 2.20462 lb" in out
