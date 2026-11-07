"""Tests for skills/health.py: calorie, heartrate, steps, workout."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- calorie
def test_calorie_metric():
    # 9.8 MET x 80 kg x 0.5 h = 392 kcal; 784 kcal per hour
    out = _ask("calorie run 30 80kg")
    assert "30 min of running at 80 kg burns about 392 kcal" in out
    assert "784 kcal per hour" in out
    assert "not a measured value" in out
    # The burn alias routes to the same skill
    out = _ask("burn run 30 80kg")
    assert "392 kcal" in out


def test_calorie_imperial():
    # 175 lb = 79.38 kg; 3.5 MET x 79.38 kg x 0.75 h = 208 kcal
    out = _ask("calorie walk 45 175lb")
    assert "45 min of walking at 175 lb burns about 208 kcal" in out
    assert "278 kcal per hour" in out


def test_calorie_other_activities():
    # 7.5 MET x 70 kg x 1 h = 525 kcal
    out = _ask("calorie cycle 60 70kg")
    assert "525 kcal" in out
    # 2.5 MET x 60 kg x 0.5 h = 75 kcal
    out = _ask("calorie yoga 30 60kg")
    assert "75 kcal" in out


def test_calorie_bad():
    assert "Usage" in _ask("calorie")
    assert "Usage" in _ask("calorie run 30")  # needs a weight
    assert "Usage" in _ask("calorie ski 30 80kg")  # unknown activity
    assert "Usage" in _ask("calorie run thirty 80kg")
    assert "Usage" in _ask("calorie run 30 80")  # weight needs a unit
    assert "greater than 0" in _ask("calorie run 0 80kg")
    assert "greater than 0" in _ask("calorie run -30 80kg")


# ---------------------------------------------------------------- heartrate
def test_heartrate_zones():
    # 220 - 40 = 180 max; Z3 is 70-80% = 126-144 bpm
    out = _ask("heartrate 40")
    assert "estimated max heart rate 180 bpm" in out
    assert "Z1 very light 90-108 bpm" in out
    assert "Z3 moderate 126-144 bpm" in out
    assert "Z5 maximum 162-180 bpm" in out
    assert "not medical advice" in out
    # The hr alias routes to the same skill
    out = _ask("hr 40")
    assert "180 bpm" in out


def test_heartrate_resting():
    # HRR = 180 - 60 = 120; moderate 108-131, vigorous 132-167 (Karvonen)
    out = _ask("heartrate 40 60")
    assert "moderate work is about 108-131 bpm" in out
    assert "vigorous work about 132-167 bpm" in out
    assert "Karvonen" in out


def test_heartrate_bad():
    assert "Usage" in _ask("heartrate")
    assert "Usage" in _ask("heartrate forty")
    assert "Usage" in _ask("heartrate 40 60 70")  # too many args
    assert "between 5 and 110" in _ask("heartrate 200")
    assert "between 5 and 110" in _ask("heartrate 3")
    assert "between 30 and 120" in _ask("heartrate 40 20")
    assert "between 30 and 120" in _ask("heartrate 40 200")


# ---------------------------------------------------------------- steps
def test_steps_default_stride():
    # 10,000 steps x 0.762 m = 7.62 km (4.73 mi), ~400 kcal
    out = _ask("steps 10000")
    assert "10,000 steps (default stride 0.76 m (2.5 ft))" in out
    assert "7.62 km (4.73 mi)" in out
    assert "400 kcal" in out


def test_steps_with_height():
    # 180 cm tall: stride 0.413 x 1.8 m = 0.74 m; 10,000 steps = 7.43 km
    out = _ask("steps 10000 180cm")
    assert "stride about 0.74 m from 180 cm" in out
    assert "7.43 km (4.62 mi)" in out
    # Imperial height works too: 5.9 ft tall, 8,000 steps = 5.94 km
    out = _ask("steps 8000 5.9ft")
    assert "stride about 0.74 m from 5.9 ft" in out
    assert "5.94 km (3.69 mi)" in out
    assert "320 kcal" in out


def test_steps_bad():
    assert "Usage" in _ask("steps")
    assert "Usage" in _ask("steps ten-thousand")
    assert "Usage" in _ask("steps 10000 tall")  # bad height
    assert "Usage" in _ask("steps 10000 180")  # height needs a unit
    assert "greater than 0" in _ask("steps 0")
    assert "greater than 0" in _ask("steps -500")


# ---------------------------------------------------------------- workout
def test_workout_metric():
    # 3 sets x 10 reps x 50 kg = 30 reps, 1,500 kg volume, 500 kg/set
    out = _ask("workout 3x10 50kg bench")
    assert "3 sets x 10 reps x 50 kg bench = 30 reps" in out
    assert "1,500 kg total volume (500 kg per set)" in out
    assert "not a training plan" in out
    # Exercise is optional
    out = _ask("workout 3x10 50kg")
    assert "1,500 kg total volume" in out
    # The lift alias routes to the same skill
    out = _ask("lift 3x10 50kg")
    assert "1,500 kg" in out


def test_workout_imperial():
    # 5x5 x 225 lb = 25 reps, 5,625 lb (2,551 kg), 1,125 lb per set
    out = _ask("workout 5x5 225lb squat")
    assert "5 sets x 5 reps x 225 lb squat = 25 reps" in out
    assert "2,551 kg (5,625 lb) total volume" in out
    assert "510 kg (1,125 lb) per set" in out


def test_workout_bad():
    assert "Usage" in _ask("workout")
    assert "Usage" in _ask("workout 3x10")  # needs a weight
    assert "Usage" in _ask("workout 3-10 50kg")  # sets x reps format
    assert "Usage" in _ask("workout 3x10 50")  # weight needs a unit
    assert "greater than 0" in _ask("workout 0x10 50kg")
    assert "greater than 0" in _ask("workout 3x0 50kg")


# ---------------------------------------------------------------- regression
def test_bmi_keeps_trigger():
    out = _ask("bmi 80kg 180cm")
    assert "BMI 24.7 (healthy weight)" in out
