"""Tests for skills/biology.py: dna, punnett, hardy, popgrowth,
enzyme, blood, osmosis."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


def test_skill_count():
    assert len(agent.list_skills()) == 176


# ---------------------------------------------------------------- dna
def test_dna_complement():
    # A<->T, G<->C, same order: ATGC -> TACG.
    out = _ask("dna complement ATGC")
    assert "complement of ATGC is TACG" in out


def test_dna_complement_not_reversed():
    # The complement is NOT the reverse: GATTACA -> CTAATGT,
    # not TGTAATC.
    out = _ask("dna complement GATTACA")
    assert "complement of GATTACA is CTAATGT" in out
    assert "TGTAATC" not in out


def test_dna_revcomp():
    # ATGC reversed is CGTA, complemented is GCAT.
    out = _ask("dna revcomp ATGC")
    assert "reverse complement of ATGC is GCAT" in out


def test_dna_revcomp_palindrome_check():
    # GAATTC is an EcoRI site: its reverse complement is itself.
    out = _ask("dna revcomp GAATTC")
    assert "reverse complement of GAATTC is GAATTC" in out


def test_dna_gc():
    # ATGC: 2 of 4 are G/C.
    out = _ask("dna gc ATGC")
    assert "GC content is 50%" in out
    # ATAT has no G or C at all.
    out = _ask("dna gc ATAT")
    assert "GC content is 0%" in out
    # GCGC is all G/C.
    out = _ask("dna gc GCGC")
    assert "GC content is 100%" in out


def test_dna_transcribe():
    # T -> U, everything else unchanged.
    out = _ask("dna transcribe ATGC")
    assert "RNA strand AUGC" in out


def test_dna_translate_start_stop():
    # ATG = Met, GCT = Ala, TAA = stop.
    out = _ask("dna translate ATGGCTTAA")
    assert "translates to MA (Met-Ala)" in out
    assert "stopped at a stop codon" in out


def test_dna_translate_no_stop():
    out = _ask("dna translate ATGGCT")
    assert "translates to MA (Met-Ala)" in out
    assert "No stop codon" in out


def test_dna_translate_partial_codon():
    # 7 bases: ATG GCT + one trailing A, ignored.
    out = _ask("dna translate ATGGCTA")
    assert "translates to MA (Met-Ala)" in out
    assert "1 base does not form a complete codon" in out


def test_dna_translate_wrong_answer_traps():
    # ATG is Met (M), not Ala; GCT is Ala (A), not Gly.
    out = _ask("dna translate ATGGCT")
    assert "(Met-Ala)" in out
    assert "Gly" not in out
    # TGG is Trp, not a stop; TGA is a stop.
    out = _ask("dna translate ATGTGG")
    assert "translates to MW (Met-Trp)" in out
    out = _ask("dna translate ATGTGA")
    assert "translates to M (Met)" in out
    assert "stopped at a stop codon" in out


def test_dna_bad():
    assert "Usage" in _ask("dna")
    assert "Usage" in _ask("dna complement")
    assert "Usage" in _ask("dna bogus ATGC")
    assert "only A, C, G, T" in _ask("dna complement ATGX")
    assert "RNA, not DNA" in _ask("dna complement AUGC")
    assert "only A, C, G, T" in _ask("dna gc ATG1")


# ---------------------------------------------------------------- punnett
def test_punnett_heterozygote_cross():
    # Aa x Aa -> 1 AA : 2 Aa : 1 aa, 3 dominant : 1 recessive.
    out = _ask("punnett Aa x Aa")
    assert "1 AA : 2 Aa : 1 aa" in out
    assert "AA 25%" in out
    assert "Aa 50%" in out
    assert "aa 25%" in out
    assert "3 dominant : 1 recessive" in out
    assert "75% / 25%" in out


def test_punnett_homozygous_dominant_recessive():
    # AA x aa -> every child Aa, all dominant trait.
    out = _ask("punnett AA x aa")
    assert "4 Aa" in out
    assert "Every offspring shows the dominant trait" in out


def test_punnett_test_cross():
    # Aa x aa -> 2 Aa : 2 aa, 50/50 phenotype.
    out = _ask("punnett Aa x aa")
    assert "2 Aa : 2 aa" in out
    assert "2 dominant : 2 recessive" in out
    assert "50% / 50%" in out


def test_punnett_recessive_cross():
    # aa x aa -> every child aa, all recessive trait.
    out = _ask("punnett aa x aa")
    assert "4 aa" in out
    assert "Every offspring shows the recessive trait" in out


def test_punnett_no_x_needed_and_alias():
    out = _ask("punnett Aa Aa")
    assert "1 AA : 2 Aa : 1 aa" in out
    out = _ask("cross Aa x Aa")
    assert "1 AA : 2 Aa : 1 aa" in out


def test_punnett_bad():
    assert "Usage" in _ask("punnett")
    assert "Usage" in _ask("punnett Aa")
    # Two different gene letters is not a monohybrid cross.
    assert "same gene" in _ask("punnett Aa x Bb")
    assert "two-letter genotype" in _ask("punnett AAA x Aa")
    assert "two-letter genotype" in _ask("punnett A1 x Aa")


# ---------------------------------------------------------------- hardy
def test_hardy_from_p():
    # p = 0.6, q = 0.4: AA 0.36, Aa 0.48, aa 0.16.
    out = _ask("hardy p 0.6")
    assert "p = 0.6 and q = 0.4" in out
    assert "AA p^2 = 0.36" in out
    assert "Aa 2pq = 0.48" in out
    assert "aa q^2 = 0.16" in out


def test_hardy_from_q():
    # q = 0.3 -> p = 0.7: AA 0.49, Aa 0.42, aa 0.09.
    out = _ask("hardy q 0.3")
    assert "p = 0.7 and q = 0.3" in out
    assert "AA p^2 = 0.49" in out
    assert "Aa 2pq = 0.42" in out
    assert "aa q^2 = 0.09" in out


def test_hardy_from_counts():
    # 360/480/160 in 1000: p = (720+480)/2000 = 0.6, q = 0.4,
    # expected counts exactly 360/480/160 (equilibrium).
    out = _ask("hardy AA 360 Aa 480 aa 160")
    assert "p = 0.6 and q = 0.4" in out
    assert "expects AA 360, Aa 480, aa 160" in out
    assert "observed 360, 480, 160" in out


def test_hardy_from_counts_not_equilibrium():
    # 500/300/200 in 1000: p = 0.65, q = 0.35, expected
    # AA 422.5, Aa 455, aa 122.5 — not the observed counts.
    out = _ask("hardy AA 500 Aa 300 aa 200")
    assert "p = 0.65 and q = 0.35" in out
    assert "expects AA 422.5, Aa 455, aa 122.5" in out


def test_hardy_alias_and_bad():
    out = _ask("hardyweinberg p 0.5")
    assert "AA p^2 = 0.25" in out
    assert "between 0 and 1" in _ask("hardy p 1.5")
    assert "between 0 and 1" in _ask("hardy p 0")
    assert "between 0 and 1" in _ask("hardy q -0.2")
    assert "Usage" in _ask("hardy p")
    assert "Usage" in _ask("hardy AA 10 Aa 20")
    assert "whole numbers" in _ask("hardy AA 10.5 Aa 20 aa 30")
    assert "add up to zero" in _ask("hardy AA 0 Aa 0 aa 0")
    assert "fixed in this sample" in _ask("hardy AA 100 Aa 0 aa 0")


# ---------------------------------------------------------------- popgrowth
def test_popgrowth_exponential():
    # 100 x e^(0.05 x 10) = 100 x e^0.5 = 164.87.
    out = _ask("popgrowth 100 r 0.05 t 10")
    assert "164.9" in out
    # Doubling time ln 2 / 0.05 = 13.86.
    assert "13.86" in out


def test_popgrowth_doubling():
    out = _ask("popgrowth double r 0.05")
    assert "13.86" in out
    out = _ask("popgrowth double r 0.1")
    assert "6.931" in out


def test_popgrowth_logistic():
    # K=1000, N0=100, r=0.1, t=20: 1000/(1+9 e^-2) = 450.9,
    # well below K and above N0.
    out = _ask("popgrowth logistic 100 1000 r 0.1 t 20")
    assert "450.9" in out
    assert "carrying capacity 1,000" in out


def test_popgrowth_logistic_long_time_approaches_k():
    # After a long time the logistic curve is near K, never above it.
    out = _ask("popgrowth logistic 100 1000 r 0.1 t 200")
    assert "carrying capacity 1,000" in out
    assert "= 1000 after 200 time units" in out


def test_popgrowth_alias_and_bad():
    out = _ask("population 100 r 0.05 t 10")
    assert "164.9" in out
    assert "Usage" in _ask("popgrowth 100 r 0.05")
    assert "must be positive" in _ask("popgrowth 0 r 0.05 t 10")
    assert "cannot be negative" in _ask("popgrowth 100 r 0.05 t -1")
    assert "positive for a doubling time" in _ask("popgrowth double r 0")
    assert "already at or above" in _ask("popgrowth logistic 1000 1000 r 0.1 t 5")
    out = _ask("popgrowth 100 r 0 t 10")
    assert "stays at 100" in out


# ---------------------------------------------------------------- enzyme
def test_enzyme_rate():
    # v = 100 x 2 / (2 + 2) = 50.
    out = _ask("enzyme vmax 100 km 2 s 2")
    assert "= 50." in out
    assert "exactly half of Vmax" in out


def test_enzyme_rate_below_km():
    # v = 100 x 0.5 / (2 + 0.5) = 20, not 25 (not linear in [S]).
    out = _ask("enzyme vmax 100 km 2 s 0.5")
    assert "= 20." in out


def test_enzyme_solve_substrate():
    # v = 50, Vmax = 100, Km = 2 -> [S] = 50 x 2 / 50 = 2.
    out = _ask("enzyme vmax 100 km 2 v 50")
    assert "[S] = v x Km / (Vmax - v) = 2." in out
    # v = 25 -> [S] = 25 x 2 / 75 = 0.6667.
    out = _ask("enzyme vmax 100 km 2 v 25")
    assert "= 0.6667." in out


def test_enzyme_alias_and_bad():
    out = _ask("michaelis vmax 100 km 2 s 2")
    assert "= 50." in out
    assert "Usage" in _ask("enzyme vmax 100 km 2")
    assert "must both be positive" in _ask("enzyme vmax 0 km 2 s 2")
    assert "cannot be negative" in _ask("enzyme vmax 100 km 2 s -1")
    assert "stay below Vmax" in _ask("enzyme vmax 100 km 2 v 100")
    assert "stay below Vmax" in _ask("enzyme vmax 100 km 2 v 120")


# ---------------------------------------------------------------- blood
def test_blood_a_positive():
    out = _ask("blood A+")
    assert "can donate to A+, AB+" in out
    assert "can receive from" in out
    for donor in ("O-", "O+", "A-", "A+"):
        assert donor in out


def test_blood_o_negative_universal_donor():
    out = _ask("blood O-")
    assert "universal donor" in out
    assert "can donate to O-, O+, A-, A+, B-, B+, AB-, AB+" in out
    assert "can receive from O-" in out


def test_blood_ab_positive_universal_recipient():
    out = _ask("blood AB+")
    assert "universal recipient" in out
    assert "can donate to AB+" in out
    assert "can receive from O-, O+, A-, A+, B-, B+, AB-, AB+" in out


def test_blood_b_negative():
    out = _ask("blood B-")
    assert "can donate to B-, B+, AB-, AB+" in out


def test_blood_transfusion_checks():
    assert "Yes" in _ask("blood O- to AB+")
    assert "Yes" in _ask("blood B- to AB-")
    assert "Yes" in _ask("blood A- to A+")
    # A antigens meet anti-A antibodies in a B recipient.
    assert "No" in _ask("blood A+ to B+")
    # Rh+ donor to an Rh- recipient is not allowed.
    assert "No" in _ask("blood O+ to O-")
    assert "No" in _ask("blood AB+ to O-")


def test_blood_alias_and_bad():
    out = _ask("bloodtype AB-")
    assert "can donate to AB-, AB+" in out
    assert "Usage" in _ask("blood")
    assert "Usage" in _ask("blood X+")
    assert "Usage" in _ask("blood A++")
    assert "Usage" in _ask("blood A+ to X")


# ---------------------------------------------------------------- osmosis
def test_osmosis_solute_potential():
    # Psi_s = -1 x 0.3 x 0.008314 x 298.15 = -0.7436 MPa.
    out = _ask("osmosis 0.3M")
    assert "-0.7436 MPa" in out
    assert "25 C" in out


def test_osmosis_vant_hoff_factor():
    # NaCl, i = 2, doubles the (negative) potential: -1.487 MPa.
    out = _ask("osmosis 0.3M i 2")
    assert "-1.487 MPa" in out


def test_osmosis_temperature():
    # At 20 C (293.15 K): -0.3 x 0.008314 x 293.15 = -0.7312 MPa.
    out = _ask("osmosis 0.3M 20C")
    assert "-0.7312 MPa" in out


def test_osmosis_total():
    out = _ask("osmosis total -0.7 -0.3")
    assert "= -1 MPa" in out
    assert "Water moves in" in out
    out = _ask("osmosis total 0.5 -0.5")
    assert "= 0 MPa" in out
    assert "No net water movement" in out


def test_osmosis_alias_and_bad():
    out = _ask("waterpotential 0.3M")
    assert "-0.7436 MPa" in out
    assert "Usage" in _ask("osmosis")
    assert "Usage" in _ask("osmosis 0.3")
    assert "must be a positive number" in _ask("osmosis -0.3M")
    assert "must be positive" in _ask("osmosis 0.3M i 0")
    assert "Usage" in _ask("osmosis 0.3M bogus 2")


# ---------------------------------------------------------------- cross-skill guards
def test_biology_rejects_nan_inf():
    # NaN/inf must be usage errors, never crashes or nonsense.
    for text in ("hardy p nan", "hardy p inf", "enzyme vmax 100 km 2 s nan",
                 "popgrowth 100 r inf t 10", "osmosis total nan -0.3"):
        resp = agent.respond(text)
        assert resp["ok"], f"{text!r} failed: {resp['response']}"
        assert "nan" not in resp["response"].lower()
        assert "inf" not in resp["response"].lower()
