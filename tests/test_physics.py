"""Tests for skills/physics.py: force, speed, pressure, wave."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


def test_skill_count():
    assert len(agent.list_skills()) == 162


# ---------------------------------------------------------------- force
def test_force_basic():
    # F = 10 kg x 5 m/s^2 = 50 N.
    out = _ask("force 10kg 5")
    assert "Force of 10 kg at 5 m/s^2: 50 N." in out
    # 500 g is 0.5 kg: F = 0.5 x 10 = 5 N.
    out = _ask("force 500g 10")
    assert "Force of 0.5 kg at 10 m/s^2: 5 N." in out
    # 10 kg x 200 m/s^2 = 2000 N = 2 kN.
    out = _ask("force 10kg 200")
    assert "Force of 10 kg at 200 m/s^2: 2,000 N (2 kN)." in out


def test_force_weight():
    # W = 80 kg x 9.81 = 784.8 N.
    out = _ask("force weight 80kg")
    assert "Weight of 80 kg: 784.8 N." in out
    # W = 1 kg x 9.81 = 9.81 N.
    out = _ask("force weight 1kg")
    assert "Weight of 1 kg: 9.81 N." in out


def test_force_rearranged():
    # a = 100 N / 20 kg = 5 m/s^2.
    out = _ask("force accel 100N 20kg")
    assert "Acceleration from 100 N on 20 kg: 5 m/s^2." in out
    # m = 50 N / 5 m/s^2 = 10 kg.
    out = _ask("force mass 50N 5")
    assert "Mass from 50 N at 5 m/s^2: 10 kg." in out


def test_force_bad():
    assert "Usage" in _ask("force")
    assert "Usage" in _ask("force zzz 5")
    assert "Usage" in _ask("force 10kg")
    assert "Usage" in _ask("force weight")
    assert "Usage" in _ask("force accel 100N")
    assert "Usage" in _ask("force mass 50N 0")


# ---------------------------------------------------------------- speed
def test_speed_basic():
    # 100 km / 2 h = 50 km/h = 13.89 m/s (50 / 3.6).
    out = _ask("speed 100km 2h")
    assert "Speed for 100 km in 2 h: 50 km/h (13.89 m/s)." in out
    # 100 m / 10 s = 10 m/s = 36 km/h.
    out = _ask("speed 100m 10s")
    assert "36 km/h (10 m/s)" in out
    # 26 mi = 41.84 km, in 30 min = 0.5 h: 83.69 km/h.
    out = _ask("speed 26mi 30min")
    assert "83.69 km/h" in out


def test_speed_rearranged():
    # 60 km/h x 2 h = 120 km = 120,000 m.
    out = _ask("speed dist 60kmh 2h")
    assert "Distance at 60 km/h (16.67 m/s) for 2 h: 120 km (120,000 m)." in out
    # 120 km / 60 km/h = 2 h = 120 min.
    out = _ask("speed time 120km 60kmh")
    assert "Time for 120 km at 60 km/h (16.67 m/s): 2 h (120 min)." in out


def test_speed_bad():
    assert "Usage" in _ask("speed")
    assert "Usage" in _ask("speed 100km")
    assert "Usage" in _ask("speed zzz 2h")
    assert "Usage" in _ask("speed dist 60kmh")
    assert "Usage" in _ask("speed time 120km 0kmh")


# ---------------------------------------------------------------- pressure
def test_pressure_basic():
    # 100 N / 2 m^2 = 50 Pa = 0.05 kPa.
    out = _ask("pressure 100N 2m2")
    assert "Pressure of 100 N over 2 m^2: 50 Pa (0.05 kPa)." in out
    # 200 N / 200 cm^2 (0.02 m^2) = 10,000 Pa = 10 kPa.
    out = _ask("pressure 200N 200cm2")
    assert "Pressure of 200 N over 0.02 m^2: 10,000 Pa (10 kPa)." in out


def test_pressure_convert():
    # 1 atm = 101,325 Pa = 14.7 psi (101325 / 6894.76).
    out = _ask("pressure 1 atm to psi")
    assert "1 atm = 14.7 psi (101,325 Pa)." in out
    # 100 kPa = 100,000 Pa.
    assert "100 kPa = 100,000 Pa." in _ask("pressure 100 kPa to Pa")
    # 1 bar = 100,000 Pa = 0.9869 atm (100000 / 101325).
    out = _ask("pressure 1 bar to atm")
    assert "1 bar = 0.9869 atm (100,000 Pa)." in out


def test_pressure_bad():
    assert "Usage" in _ask("pressure")
    assert "Usage" in _ask("pressure 100N")
    assert "Usage" in _ask("pressure zzz 2m2")
    assert "Unknown pressure unit" in _ask("pressure 1 atm to parsecs")
    assert "Pressure must be 0 or more" in _ask("pressure -1 atm to psi")


# ---------------------------------------------------------------- wave
def test_wave_wavelength():
    # lambda = 343 / 440 = 0.7795 m = 77.95 cm (A4 in air at 20 C).
    out = _ask("wave 440Hz 343")
    assert "Wavelength of 440 Hz at 343 m/s: 0.7795 m (77.95 cm)." in out


def test_wave_freq():
    # f = 343 / 2 = 171.5 Hz.
    out = _ask("wave freq 2m 343")
    assert "Frequency for 2 m at 343 m/s: 171.5 Hz." in out


def test_wave_period():
    # T = 1 / 440 = 0.002273 s = 2.273 ms.
    out = _ask("wave period 440Hz")
    assert "Period of 440 Hz: 0.002273 s (2.273 ms)." in out


def test_wave_light():
    # f = c / lambda = 299792458 / 5e-7 = 5.996e14 Hz = 599.6 THz.
    out = _ask("wave light 500nm")
    assert "Light of 5e-07 m: 5.996e+14 Hz (599.6 THz)." in out


def test_wave_bad():
    assert "Usage" in _ask("wave")
    assert "Usage" in _ask("wave zzz 343")
    assert "Usage" in _ask("wave 440Hz")
    assert "Usage" in _ask("wave freq 2m")
    assert "Usage" in _ask("wave period 0Hz")
    assert "Usage" in _ask("wave light 0nm")
