"""Tests for skills/science.py: ph, moles, energy, density."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


def test_skill_count():
    assert len(agent.list_skills()) == 130


# ---------------------------------------------------------------- ph
def test_ph_from_concentration():
    # [H+] = 0.01 mol/L: pH = -log10(0.01) = 2, pOH = 12,
    # [OH-] = 10^-12 mol/L, acidic.
    out = _ask("ph 0.01")
    assert "pH 2.00 (acidic)" in out
    assert "[H+] 0.01 mol/L" in out
    assert "pOH 12.00" in out
    assert "[OH-] 1.00e-12 mol/L" in out
    # [H+] = 1 mol/L is pH 0, not -0.00.
    out = _ask("ph 1")
    assert "pH 0.00 (acidic)" in out


def test_ph_from_value():
    # pH 7: neutral, both ions 10^-7 mol/L.
    out = _ask("ph value 7")
    assert "pH 7.00 (neutral)" in out
    assert "[H+] 1.00e-07 mol/L" in out
    assert "pOH 7.00" in out
    assert "[OH-] 1.00e-07 mol/L" in out
    # pH 3.5: [H+] = 10^-3.5 = 3.16e-04, pOH 10.50.
    out = _ask("ph value 3.5")
    assert "pH 3.50 (acidic)" in out
    assert "[H+] 3.16e-04 mol/L" in out
    assert "pOH 10.50" in out


def test_ph_from_hydroxide():
    # [OH-] = 0.001 mol/L: pOH = 3, pH = 11, [H+] = 10^-11, basic.
    out = _ask("ph oh 0.001")
    assert "pH 11.00 (basic (alkaline))" in out
    assert "pOH 3.00" in out
    assert "[H+] 1.00e-11 mol/L" in out


def test_ph_bad():
    assert "Usage" in _ask("ph")
    assert "Usage" in _ask("ph zzz")
    assert "Usage" in _ask("ph oh")
    assert "must be 10^-14 to 1" in _ask("ph 2")
    assert "must be 10^-14 to 1" in _ask("ph oh 5")
    assert "pH must be 0-14" in _ask("ph value 15")


# ---------------------------------------------------------------- moles
def test_moles_from_mass():
    # 36 g of water (18 g/mol) = 2 mol = 2 x 6.022e23 molecules.
    out = _ask("moles 36g 18")
    assert "36 g at 18 g/mol is 2 mol" in out
    assert "1.204e+24 molecules" in out
    # 0.036 kg is the same 36 g.
    out = _ask("moles 0.036kg 18")
    assert "36 g at 18 g/mol is 2 mol" in out


def test_moles_to_mass():
    # 2 mol at 18 g/mol = 36 g.
    out = _ask("moles 2mol 18")
    assert "2 mol at 18 g/mol is 36 g" in out


def test_moles_molarity():
    # 2 mol in 0.5 L = 4 mol/L.
    out = _ask("moles molarity 2mol 0.5L")
    assert "2 mol in 0.5 L is 4 mol/L (4 M)" in out
    # 36 g at 18 g/mol = 2 mol, in 2 L = 1 mol/L.
    out = _ask("moles molarity 36g 18 2L")
    assert "36 g at 18 g/mol is 2 mol" in out
    assert "in 2 L that is 1 mol/L (1 M)" in out


def test_moles_bad():
    assert "Usage" in _ask("moles")
    assert "Usage" in _ask("moles 36g")
    assert "Usage" in _ask("moles zzz 18")
    assert "Molar mass must be more than 0" in _ask("moles 36g 0")
    assert "Usage" in _ask("moles molarity 2mol")


# ---------------------------------------------------------------- energy
def test_energy_convert():
    # 1 kWh = 3.6 x 10^6 J.
    assert "1 kWh = 3,600,000 J." in _ask("energy 1 kWh to J")
    # 500 cal x 4.184 J/cal = 2092 J.
    assert "500 cal = 2,092 J." in _ask("energy 500 cal to J")
    # 1 kcal = 4184 J.
    assert "1 kcal = 4,184 J." in _ask("energy 1 kcal to J")
    # 1 eV = 1.602176634e-19 J.
    assert "1 eV = 1.602e-19 J." in _ask("energy 1 eV to J")
    # 1000 J = 0.2381 kcal (1000/4184).
    out = _ask("energy 1000 J to kcal")
    assert "1,000 J = 0.239 kcal (1,000 J)" in out


def test_energy_kinetic():
    # KE = 1/2 x 80 kg x (10 m/s)^2 = 4000 J = 4 kJ.
    out = _ask("energy ke 80kg 10")
    assert "Kinetic energy of 80 kg at 10 m/s: 4,000 J (4 kJ)" in out
    # 36 km/h is the same 10 m/s.
    out = _ask("energy ke 80kg 36kmh")
    assert "Kinetic energy of 80 kg at 10 m/s: 4,000 J (4 kJ)" in out


def test_energy_potential():
    # PE = 10 kg x 9.81 x 5 m = 490.5 J.
    out = _ask("energy pe 10kg 5m")
    assert "Potential energy of 10 kg at 5 m: 490.5 J" in out


def test_energy_bad():
    assert "Usage" in _ask("energy")
    assert "Usage" in _ask("energy 100 J")
    assert "Unknown energy unit" in _ask("energy 100 parsecs to J")
    assert "Energy must be 0 or more" in _ask("energy -5 J to kJ")
    assert "Usage" in _ask("energy ke 80kg")


# ---------------------------------------------------------------- density
def test_density_basic():
    # 100 g / 50 mL = 2 g/cm3 = 2000 kg/m3, denser than water, sinks.
    out = _ask("density 100g 50ml")
    assert "Density: 2 g/cm3 (2,000 kg/m3)" in out
    assert "it sinks" in out
    # 500 g / 1 L = 0.5 g/cm3 = 500 kg/m3, floats.
    out = _ask("density 500g 1L")
    assert "Density: 0.5 g/cm3 (500 kg/m3)" in out
    assert "it floats" in out
    # 1 kg / 1 L = 1 g/cm3, same as water.
    out = _ask("density 1kg 1L")
    assert "Density: 1 g/cm3 (1,000 kg/m3)" in out
    assert "hangs suspended" in out


def test_density_convert():
    # 2.7 g/cm3 = 2700 kg/m3 (aluminium).
    assert "2.7 g/cm3 = 2,700 kg/m3." in _ask("density 2.7 g/cm3 to kg/m3")
    # 1000 kg/m3 = 1 g/cm3 = 62.43 lb/ft3.
    out = _ask("density 1000 kg/m3 to lb/ft3")
    assert "1,000 kg/m3 = 62.43 lb/ft3 (1 g/cm3)" in out


def test_density_bad():
    assert "Usage" in _ask("density")
    assert "Usage" in _ask("density 100g")
    assert "Usage" in _ask("density zzz 50ml")
    assert "Unknown density unit" in _ask("density 2.7 g/cm3 to parsecs")
    assert "Density must be 0 or more" in _ask("density -1 g/cm3 to kg/m3")
