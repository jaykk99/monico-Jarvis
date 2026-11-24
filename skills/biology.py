"""Biology helpers: DNA sequences, Punnett squares, Hardy-Weinberg
equilibrium, population growth, enzyme kinetics, blood-type
compatibility, and water potential.

All local, keyless, no network — same contract as the rest of skills/.
Plain textbook biology for everyday questions: what the complement
of a DNA strand is, what protein a coding sequence makes, what
offspring a cross produces, what genotype frequencies a population
should show, how fast a population grows, how fast an enzyme works,
who can give blood to whom, and how thirsty a cell is.

Rules used:
- DNA: A pairs with T, G pairs with C. The reverse complement is
  the complement read backwards. GC content is (G + C) / length.
  Transcription copies DNA to RNA with T replaced by U. Translation
  reads codons (triplets) from the standard genetic code, starting
  at the first base; TAA, TAG, and TGA are stop codons and end the
  protein. A trailing partial codon is ignored and reported.
- Punnett square: a monohybrid cross of two two-allele genotypes
  (AA, Aa, aa). Each parent contributes each of its two alleles
  with probability 1/2, so the four offspring boxes are equally
  likely. An offspring with at least one dominant (uppercase)
  allele shows the dominant trait.
- Hardy-Weinberg: with allele frequencies p + q = 1, genotype
  frequencies are p^2 (AA), 2pq (Aa), q^2 (aa) in a population at
  equilibrium. From genotype counts, p = (2 x AA + Aa) / (2 x total)
  and q = 1 - p.
- Population growth: exponential N(t) = N0 x e^(rt), doubling time
  ln 2 / r. Logistic growth N(t) = K / (1 + ((K - N0) / N0) x
  e^(-rt)) levels off at the carrying capacity K.
- Enzyme kinetics: Michaelis-Menten v = Vmax x [S] / (Km + [S]).
  At [S] = Km the rate is exactly half of Vmax. Solving for [S]
  from a rate: [S] = v x Km / (Vmax - v), which needs v < Vmax.
- Blood types: ABO antigens and Rh factor decide compatibility.
  O- has no antigens, so it can donate to anyone (universal
  donor); AB+ has no antibodies, so it can receive from anyone
  (universal recipient). Rh- blood can only go to Rh- recipients
  when the donor is Rh+... more precisely, an Rh+ donor can only
  give to an Rh+ recipient, while Rh- can give to either.
- Water potential: solute potential Psi_s = -iCRT, with i the
  van't Hoff factor (1 for a non-dissociating solute, about 2 for
  NaCl), C in mol/L, R = 0.00831 L MPa / (mol K), T in kelvin.
  Total water potential Psi = Psi_s + Psi_p (pressure potential).
  Water moves from higher (less negative) to lower Psi.

Conventions and explicit caveats:
- DNA input must be A, C, G, T only; U is refused for DNA input
  (use `transcribe` on the DNA strand instead) and any other
  letter is reported, not guessed.
- `punnett` is monohybrid only — one gene, two alleles. A
  dihybrid cross needs a 4x4 square, which this skill does not do.
- Hardy-Weinberg assumes random mating, no selection, no mutation,
  no migration, and a large population; real populations drift
  from it, and the answer says so.
- Exponential growth never levels off; if a carrying capacity is
  known, use the logistic form instead.
- Blood-type answers are the standard transfusion rules, not
  medical advice for a real transfusion — crossmatching still
  applies, and the answer says so.
- Huge values refuse to print rather than dumping a wall of digits.
"""
from __future__ import annotations

import math
import re

from .base import Skill, SkillRegistry

_R_GAS_MPA = 0.008314  # L MPa / (mol K), for water potential

_COMP = {"A": "T", "T": "A", "G": "C", "C": "G"}

# Standard genetic code: codon -> (one-letter amino acid, name).
# Stop codons map to ("*", "Stop").
CODONS: dict[str, tuple[str, str]] = {
    "TTT": ("F", "Phe"), "TTC": ("F", "Phe"),
    "TTA": ("L", "Leu"), "TTG": ("L", "Leu"),
    "CTT": ("L", "Leu"), "CTC": ("L", "Leu"),
    "CTA": ("L", "Leu"), "CTG": ("L", "Leu"),
    "ATT": ("I", "Ile"), "ATC": ("I", "Ile"), "ATA": ("I", "Ile"),
    "ATG": ("M", "Met"),
    "GTT": ("V", "Val"), "GTC": ("V", "Val"),
    "GTA": ("V", "Val"), "GTG": ("V", "Val"),
    "TCT": ("S", "Ser"), "TCC": ("S", "Ser"),
    "TCA": ("S", "Ser"), "TCG": ("S", "Ser"),
    "CCT": ("P", "Pro"), "CCC": ("P", "Pro"),
    "CCA": ("P", "Pro"), "CCG": ("P", "Pro"),
    "ACT": ("T", "Thr"), "ACC": ("T", "Thr"),
    "ACA": ("T", "Thr"), "ACG": ("T", "Thr"),
    "GCT": ("A", "Ala"), "GCC": ("A", "Ala"),
    "GCA": ("A", "Ala"), "GCG": ("A", "Ala"),
    "TAT": ("Y", "Tyr"), "TAC": ("Y", "Tyr"),
    "TAA": ("*", "Stop"), "TAG": ("*", "Stop"),
    "CAT": ("H", "His"), "CAC": ("H", "His"),
    "CAA": ("Q", "Gln"), "CAG": ("Q", "Gln"),
    "AAT": ("N", "Asn"), "AAC": ("N", "Asn"),
    "AAA": ("K", "Lys"), "AAG": ("K", "Lys"),
    "GAT": ("D", "Asp"), "GAC": ("D", "Asp"),
    "GAA": ("E", "Glu"), "GAG": ("E", "Glu"),
    "TGT": ("C", "Cys"), "TGC": ("C", "Cys"),
    "TGA": ("*", "Stop"), "TGG": ("W", "Trp"),
    "CGT": ("R", "Arg"), "CGC": ("R", "Arg"),
    "CGA": ("R", "Arg"), "CGG": ("R", "Arg"),
    "AGT": ("S", "Ser"), "AGC": ("S", "Ser"),
    "AGA": ("R", "Arg"), "AGG": ("R", "Arg"),
    "GGT": ("G", "Gly"), "GGC": ("G", "Gly"),
    "GGA": ("G", "Gly"), "GGG": ("G", "Gly"),
}

# ABO/Rh compatibility: donor -> set of recipients it can give to.
_BLOOD_ORDER = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
_DONATE_TO: dict[str, set[str]] = {
    "O-": {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"},
    "O+": {"O+", "A+", "B+", "AB+"},
    "A-": {"A-", "A+", "AB-", "AB+"},
    "A+": {"A+", "AB+"},
    "B-": {"B-", "B+", "AB-", "AB+"},
    "B+": {"B+", "AB+"},
    "AB-": {"AB-", "AB+"},
    "AB+": {"AB+"},
}

_BLOOD_RE = re.compile(r"^(O|A|B|AB)([+-])$", re.IGNORECASE)


def _fmt(x: float) -> str:
    """Short human number: integers plain, else up to 4 significant digits."""
    if x == int(x) and abs(x) < 1e15:
        return f"{int(x):,}"
    return f"{x:.4g}"


def _num(token: str) -> float | None:
    """Parse a plain number, tolerating thousands commas.

    Rejects non-finite values: float("nan") and float("1e999") (= inf)
    both parse, and a NaN/inf slipping through crashed callers in
    other skill families — a number the skills cannot use is a usage
    error, not a crash.
    """
    try:
        value = float(token.strip().replace(",", ""))
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def _too_big() -> str:
    return "That answer is too large to print — try smaller numbers."


def _check_dna(seq: str) -> str | None:
    """Validate a DNA string; returns an error string or None."""
    if not seq:
        return "Give a DNA sequence of A, C, G, T — e.g. `dna complement ATGC`."
    if not re.fullmatch(r"[ACGTacgt]+", seq):
        if "U" in seq.upper():
            return ("That has a U in it — RNA, not DNA. Give the DNA "
                    "strand (A, C, G, T) and I will transcribe it for you.")
        return ("DNA uses only A, C, G, T — that sequence has another "
                "letter in it.")
    return None


# ---------------------------------------------------------------- dna

_USAGE_DNA = (
    "Usage: `dna complement <seq>` / `dna revcomp <seq>` / "
    "`dna gc <seq>` / `dna transcribe <seq>` / `dna translate <seq>` "
    "— e.g. `dna complement ATGC`, `dna translate ATGGCTTAA`."
)


def _run_dna(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) != 2:
        return _USAGE_DNA
    mode, seq = tokens[0].lower(), tokens[1].upper()
    if mode not in ("complement", "revcomp", "gc", "transcribe", "translate"):
        return _USAGE_DNA
    err = _check_dna(seq)
    if err is not None:
        return err
    if mode == "complement":
        comp = "".join(_COMP[b] for b in seq)
        return f"The complement of {seq} is {comp} (A<->T, G<->C)."
    if mode == "revcomp":
        rev = "".join(_COMP[b] for b in reversed(seq))
        return (f"The reverse complement of {seq} is {rev} — the "
                f"strand that runs the other way.")
    if mode == "gc":
        gc = seq.count("G") + seq.count("C")
        pct = gc / len(seq) * 100
        return (f"{seq} is {len(seq)} bases with {gc} G/C, so GC "
                f"content is {_fmt(pct)}%.")
    if mode == "transcribe":
        rna = seq.replace("T", "U")
        return f"Transcribing {seq} gives the RNA strand {rna} (T -> U)."
    # translate
    codons = [seq[i:i + 3] for i in range(0, len(seq) - len(seq) % 3, 3)]
    leftover = len(seq) % 3
    letters: list[str] = []
    names: list[str] = []
    stopped = False
    for codon in codons:
        letter, name = CODONS[codon]
        if letter == "*":
            stopped = True
            break
        letters.append(letter)
        names.append(name)
    protein = "".join(letters) if letters else "(none)"
    names_str = "-".join(names) if names else "(none)"
    out = (f"{seq} translates to {protein} ({names_str}).")
    if stopped:
        out += " Translation stopped at a stop codon."
    elif codons and not stopped:
        out += " No stop codon in this sequence."
    if leftover:
        out += (f" The trailing {leftover} base"
                f"{'s' if leftover > 1 else ''} do{'es' if leftover == 1 else ''} "
                f"not form a complete codon and {'was' if leftover == 1 else 'were'} ignored.")
    return out


# ---------------------------------------------------------------- punnett

_USAGE_PUNNETT = (
    "Usage: `punnett <genotype> x <genotype>` for a monohybrid cross "
    "— e.g. `punnett Aa x Aa`, `punnett AA x aa`."
)


def _parse_genotype(token: str) -> tuple[str, str] | None:
    """A monohybrid genotype: two alleles of the same gene letter."""
    if len(token) != 2 or not token.isalpha():
        return None
    a, b = token[0], token[1]
    if a.upper() != b.upper():
        return None
    return (a, b)


def _run_punnett(trigger: str, args: str) -> str:
    tokens = [t for t in (args or "").split() if t.lower() != "x"]
    if len(tokens) != 2:
        return _USAGE_PUNNETT
    g1 = _parse_genotype(tokens[0])
    g2 = _parse_genotype(tokens[1])
    if g1 is None or g2 is None:
        return (_USAGE_PUNNETT + " Each parent needs a two-letter "
                "genotype for one gene, e.g. AA, Aa, or aa.")
    if g1[0].upper() != g2[0].upper():
        return (_USAGE_PUNNETT + " Both parents must be crossed for "
                "the same gene — Aa x Bb mixes two genes, and this "
                "skill does one gene at a time.")
    # Four equally likely offspring: each parent gives each allele.
    offspring: list[str] = []
    for a in g1:
        for b in g2:
            pair = "".join(sorted((a, b), key=lambda c: (c.upper(), c.islower())))
            offspring.append(pair)
    counts: dict[str, int] = {}
    for child in offspring:
        counts[child] = counts.get(child, 0) + 1
    # Order genotypes dominant-first: AA, then Aa, then aa.
    ordered = sorted(counts.items(),
                     key=lambda kv: (sum(1 for c in kv[0] if c.islower()), kv[0]))
    geno = " : ".join(f"{n} {g}" for g, n in ordered)
    geno_pct = ", ".join(f"{g} {_fmt(n / 4 * 100)}%" for g, n in ordered)
    dominant = sum(1 for c in offspring if any(a.isupper() for a in c))
    recessive = 4 - dominant
    out = (f"{tokens[0]} x {tokens[1]} gives {geno} "
           f"({geno_pct}).")
    if dominant == 4:
        out += (" Every offspring shows the dominant trait — no "
                "recessive offspring are possible here.")
    elif recessive == 4:
        out += (" Every offspring shows the recessive trait — no "
                "dominant offspring are possible here.")
    else:
        out += (f" Phenotype: {dominant} dominant : {recessive} "
                f"recessive ({_fmt(dominant / 4 * 100)}% / "
                f"{_fmt(recessive / 4 * 100)}%).")
    return out


# ---------------------------------------------------------------- hardy

_USAGE_HARDY = (
    "Usage: `hardy p <frequency>` / `hardy q <frequency>` gives the "
    "genotype frequencies, or `hardy AA <n> Aa <n> aa <n>` works them "
    "out from counts — e.g. `hardy p 0.6`, `hardy AA 360 Aa 480 aa 160`."
)


def _hardy_from_p(p: float) -> str:
    q = 1 - p
    return (f"With p = {_fmt(p)} and q = {_fmt(q)}, Hardy-Weinberg "
            f"gives AA p^2 = {_fmt(p * p)}, Aa 2pq = "
            f"{_fmt(2 * p * q)}, aa q^2 = {_fmt(q * q)}. "
            f"That assumes random mating, no selection, no mutation, "
            f"no migration, and a large population.")


def _run_hardy(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) == 2 and tokens[0].lower() in ("p", "q"):
        freq = _num(tokens[1])
        if freq is None or freq <= 0 or freq >= 1:
            return "An allele frequency must be between 0 and 1 (exclusive)."
        p = freq if tokens[0].lower() == "p" else 1 - freq
        return _hardy_from_p(p)
    if len(tokens) == 6:
        counts: dict[str, float] = {}
        for i in range(0, 6, 2):
            key = tokens[i]
            if key not in ("AA", "Aa", "aa"):
                return _USAGE_HARDY
            if key in counts:
                return _USAGE_HARDY
            value = _num(tokens[i + 1])
            if value is None or value < 0 or value != int(value):
                return "Genotype counts must be whole numbers, zero or more."
            counts[key] = value
        total = counts["AA"] + counts["Aa"] + counts["aa"]
        if total == 0:
            return "Those counts add up to zero — give real genotype counts."
        p = (2 * counts["AA"] + counts["Aa"]) / (2 * total)
        q = 1 - p
        if p <= 0 or p >= 1:
            return (f"Those counts give p = {_fmt(p)} — one allele is "
                    f"fixed in this sample, so there is no variation to "
                    f"work with.")
        exp_aa = p * p * total
        exp_a_het = 2 * p * q * total
        exp_aa_rec = q * q * total
        return (f"Out of {_fmt(total)} individuals, p = {_fmt(p)} and "
                f"q = {_fmt(q)}. Hardy-Weinberg expects AA "
                f"{_fmt(exp_aa)}, Aa {_fmt(exp_a_het)}, aa "
                f"{_fmt(exp_aa_rec)} — compare with the observed "
                f"{_fmt(counts['AA'])}, {_fmt(counts['Aa'])}, "
                f"{_fmt(counts['aa'])}.")
    return _USAGE_HARDY


# ---------------------------------------------------------------- popgrowth

_USAGE_POPGROWTH = (
    "Usage: `popgrowth <N0> r <rate> t <time>` for exponential growth, "
    "`popgrowth logistic <N0> <K> r <rate> t <time>`, or "
    "`popgrowth double r <rate>` for the doubling time — e.g. "
    "`popgrowth 100 r 0.05 t 10`."
)


def _run_popgrowth(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) == 3 and tokens[0].lower() == "double":
        if tokens[1].lower() != "r":
            return _USAGE_POPGROWTH
        rate = _num(tokens[2])
        if rate is None or rate <= 0:
            return "The growth rate must be positive for a doubling time."
        return (f"At a growth rate of {_fmt(rate)} per time unit, the "
                f"population doubles every {_fmt(math.log(2) / rate)} "
                f"time units (ln 2 / r).")
    if len(tokens) == 5 and tokens[1].lower() == "r" and tokens[3].lower() == "t":
        n0 = _num(tokens[0])
        rate = _num(tokens[2])
        t = _num(tokens[4])
        if n0 is None or rate is None or t is None:
            return _USAGE_POPGROWTH
        if n0 <= 0:
            return "The starting population must be positive."
        if t < 0:
            return "Time cannot be negative."
        if rate == 0:
            return (f"With a growth rate of 0 the population stays at "
                    f"{_fmt(n0)}.")
        try:
            n = n0 * math.exp(rate * t)
        except OverflowError:
            return _too_big()
        if n != n or n in (math.inf, -math.inf) or n > 1e15:
            return _too_big()
        out = (f"Exponential growth: N = {_fmt(n0)} x e^({_fmt(rate)} x "
               f"{_fmt(t)}) = {_fmt(n)} after {_fmt(t)} time units.")
        if rate > 0:
            out += (f" Doubling time is "
                    f"{_fmt(math.log(2) / rate)} time units.")
        else:
            out += (f" Halving time is "
                    f"{_fmt(math.log(2) / abs(rate))} time units.")
        out += " Exponential growth never levels off — use the logistic form if there is a carrying capacity."
        return out
    if (len(tokens) == 7 and tokens[0].lower() == "logistic"
            and tokens[3].lower() == "r" and tokens[5].lower() == "t"):
        n0 = _num(tokens[1])
        k = _num(tokens[2])
        rate = _num(tokens[4])
        t = _num(tokens[6])
        if n0 is None or k is None or rate is None or t is None:
            return _USAGE_POPGROWTH
        if n0 <= 0 or k <= 0:
            return "The starting population and carrying capacity must be positive."
        if n0 >= k:
            return (f"The starting population {_fmt(n0)} is already at "
                    f"or above the carrying capacity {_fmt(k)} — "
                    f"logistic growth starts below K.")
        if rate <= 0:
            return "The logistic growth rate must be positive."
        if t < 0:
            return "Time cannot be negative."
        try:
            n = k / (1 + ((k - n0) / n0) * math.exp(-rate * t))
        except OverflowError:
            return _too_big()
        if n != n or n in (math.inf, -math.inf) or n > 1e15:
            return _too_big()
        return (f"Logistic growth: N = {_fmt(k)} / (1 + "
                f"{_fmt((k - n0) / n0)} x e^(-{_fmt(rate)} x {_fmt(t)})) "
                f"= {_fmt(n)} after {_fmt(t)} time units, levelling off "
                f"at the carrying capacity {_fmt(k)}.")
    return _USAGE_POPGROWTH


# ---------------------------------------------------------------- enzyme

_USAGE_ENZYME = (
    "Usage: `enzyme vmax <Vmax> km <Km> s <substrate>` gives the "
    "reaction rate, or `enzyme vmax <Vmax> km <Km> v <rate>` solves "
    "for the substrate concentration — e.g. "
    "`enzyme vmax 100 km 2 s 2`."
)


def _run_enzyme(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) != 6:
        return _USAGE_ENZYME
    keys = [t.lower() for t in tokens[0::2]]
    if keys != ["vmax", "km", "s"] and keys != ["vmax", "km", "v"]:
        return _USAGE_ENZYME
    vmax = _num(tokens[1])
    km = _num(tokens[3])
    third = _num(tokens[5])
    if vmax is None or km is None or third is None:
        return _USAGE_ENZYME
    if vmax <= 0 or km <= 0:
        return "Vmax and Km must both be positive."
    if keys[2] == "s":
        s = third
        if s < 0:
            return "The substrate concentration cannot be negative."
        v = vmax * s / (km + s)
        if v != v or v in (math.inf, -math.inf) or v > 1e15:
            return _too_big()
        out = (f"Michaelis-Menten: v = {_fmt(vmax)} x {_fmt(s)} / "
               f"({_fmt(km)} + {_fmt(s)}) = {_fmt(v)}.")
        if s == km:
            out += " At [S] = Km the rate is exactly half of Vmax, as expected."
        return out
    v = third
    if v < 0:
        return "The reaction rate cannot be negative."
    if v >= vmax:
        return (f"A rate of {_fmt(v)} can never be reached — "
                f"Michaelis-Menten rates stay below Vmax "
                f"({_fmt(vmax)}).")
    s = v * km / (vmax - v)
    if s != s or s in (math.inf, -math.inf) or s > 1e15:
        return _too_big()
    return (f"For v = {_fmt(v)} with Vmax {_fmt(vmax)} and Km "
            f"{_fmt(km)}, [S] = v x Km / (Vmax - v) = {_fmt(s)}.")


# ---------------------------------------------------------------- blood

_USAGE_BLOOD = (
    "Usage: `blood <type>` lists who that type can give to and "
    "receive from, or `blood <donor> to <recipient>` checks one "
    "transfusion — e.g. `blood A+`, `blood O- to AB+`."
)


def _blood_type(token: str) -> str | None:
    m = _BLOOD_RE.fullmatch(token.strip())
    if not m:
        return None
    return m.group(1).upper() + m.group(2)


def _run_blood(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) == 1:
        btype = _blood_type(tokens[0])
        if btype is None:
            return _USAGE_BLOOD + " Blood types look like A+, O-, AB+."
        recipients = [t for t in _BLOOD_ORDER if t in _DONATE_TO[btype]]
        donors = [t for t in _BLOOD_ORDER
                  if btype in _DONATE_TO[t]]
        note = ""
        if btype == "O-":
            note = " O- is the universal donor — no A, B, or Rh antigens."
        elif btype == "AB+":
            note = " AB+ is the universal recipient — no anti-A or anti-B antibodies."
        return (f"Type {btype} can donate to {', '.join(recipients)} "
                f"and can receive from {', '.join(donors)}.{note} "
                f"These are the standard rules, not medical advice for "
                f"a real transfusion — crossmatching still applies.")
    if len(tokens) == 3 and tokens[1].lower() == "to":
        donor = _blood_type(tokens[0])
        recipient = _blood_type(tokens[2])
        if donor is None or recipient is None:
            return _USAGE_BLOOD + " Blood types look like A+, O-, AB+."
        if recipient in _DONATE_TO[donor]:
            return (f"Yes — {donor} blood can go to a {recipient} "
                    f"recipient. Crossmatching still applies for a real "
                    f"transfusion.")
        return (f"No — {donor} blood cannot go to a {recipient} "
                f"recipient. The recipient has antibodies against the "
                f"donor's antigens.")
    return _USAGE_BLOOD


# ---------------------------------------------------------------- osmosis

_USAGE_OSMOSIS = (
    "Usage: `osmosis <concentration>M [i <factor>] [<temp>C]` gives "
    "the solute potential, or `osmosis total <Psi_s> <Psi_p>` adds "
    "solute and pressure potentials — e.g. `osmosis 0.3M`, "
    "`osmosis 0.3M i 2`, `osmosis total -0.7 -0.3`."
)


def _run_osmosis(trigger: str, args: str) -> str:
    tokens = (args or "").split()
    if len(tokens) == 3 and tokens[0].lower() == "total":
        psis = _num(tokens[1])
        psip = _num(tokens[2])
        if psis is None or psip is None:
            return _USAGE_OSMOSIS
        total = psis + psip
        if total != total or total in (math.inf, -math.inf) or abs(total) > 1e15:
            return _too_big()
        direction = ("Water moves in — this total is below pure water "
                     "outside (0 MPa), so water flows towards it." if total < 0 else
                     "Water moves out — this total is above the outside "
                     "potential, so water flows away." if total > 0 else
                     "No net water movement — the potentials balance.")
        return (f"Psi = Psi_s + Psi_p = {_fmt(psis)} + {_fmt(psip)} = "
                f"{_fmt(total)} MPa. {direction}")
    # Solute potential: osmosis <conc>M [i <n>] [<temp>C]
    if not tokens:
        return _USAGE_OSMOSIS
    conc_token = tokens[0]
    if not conc_token.lower().endswith("m"):
        return _USAGE_OSMOSIS
    conc = _num(conc_token[:-1])
    if conc is None or conc < 0:
        return "The concentration must be a positive number of mol/L."
    i_factor = 1.0
    temp_c = 25.0
    rest = tokens[1:]
    j = 0
    while j < len(rest):
        key = rest[j].lower()
        if key == "i" and j + 1 < len(rest):
            value = _num(rest[j + 1])
            if value is None or value <= 0:
                return "The van't Hoff factor i must be positive."
            i_factor = value
            j += 2
        elif re.fullmatch(r"-?\d+(\.\d+)?c", key):
            temp_c = float(key[:-1])
            j += 1
        else:
            return _USAGE_OSMOSIS
    temp_k = temp_c + 273.15
    psis = -i_factor * conc * _R_GAS_MPA * temp_k
    if psis != psis or psis in (math.inf, -math.inf) or abs(psis) > 1e15:
        return _too_big()
    out = (f"Solute potential Psi_s = -iCRT = -{_fmt(i_factor)} x "
           f"{_fmt(conc)} x 0.00831 x {_fmt(temp_k)} = {_fmt(psis)} "
           f"MPa at {_fmt(temp_c)} C.")
    if i_factor == 1.0:
        out += " (i = 1, a solute that does not dissociate; NaCl is about i = 2.)"
    out += " Water moves from higher (less negative) to lower water potential."
    return out


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="dna", description="DNA complement, reverse complement, GC content, transcription, translation.",
        usage="dna complement|revcomp|gc|transcribe|translate <seq>",
        triggers=["dna", "genecode"],
        run=_run_dna,
        examples=["dna complement ATGC", "dna revcomp ATGC", "dna gc ATGC", "dna transcribe ATGC", "dna translate ATGGCTTAA"]))
    registry.register(Skill(
        name="punnett", description="Monohybrid Punnett square: offspring genotype and phenotype ratios.",
        usage="punnett <genotype> x <genotype>",
        triggers=["punnett", "cross"],
        run=_run_punnett,
        examples=["punnett Aa x Aa", "punnett AA x aa", "punnett Aa x aa"]))
    registry.register(Skill(
        name="hardy", description="Hardy-Weinberg allele and genotype frequencies, from p/q or from counts.",
        usage="hardy p <freq> | hardy AA <n> Aa <n> aa <n>",
        triggers=["hardy", "hardyweinberg"],
        run=_run_hardy,
        examples=["hardy p 0.6", "hardy q 0.3", "hardy AA 360 Aa 480 aa 160"]))
    registry.register(Skill(
        name="popgrowth", description="Exponential and logistic population growth, and doubling time.",
        usage="popgrowth <N0> r <rate> t <time> | popgrowth logistic <N0> <K> r <rate> t <time> | popgrowth double r <rate>",
        triggers=["popgrowth", "population"],
        run=_run_popgrowth,
        examples=["popgrowth 100 r 0.05 t 10", "popgrowth logistic 100 1000 r 0.1 t 20", "popgrowth double r 0.05"]))
    registry.register(Skill(
        name="enzyme", description="Michaelis-Menten enzyme rate, or the substrate concentration for a rate.",
        usage="enzyme vmax <Vmax> km <Km> s <substrate> | enzyme vmax <Vmax> km <Km> v <rate>",
        triggers=["enzyme", "michaelis"],
        run=_run_enzyme,
        examples=["enzyme vmax 100 km 2 s 2", "enzyme vmax 100 km 2 s 0.5", "enzyme vmax 100 km 2 v 50"]))
    registry.register(Skill(
        name="blood", description="Blood-type donation compatibility: who a type can give to and receive from.",
        usage="blood <type> | blood <donor> to <recipient>",
        triggers=["blood", "bloodtype"],
        run=_run_blood,
        examples=["blood A+", "blood O-", "blood O- to AB+", "blood A+ to B+"]))
    registry.register(Skill(
        name="osmosis", description="Solute and total water potential (Psi_s = -iCRT, Psi = Psi_s + Psi_p).",
        usage="osmosis <conc>M [i <factor>] [<temp>C] | osmosis total <Psi_s> <Psi_p>",
        triggers=["osmosis", "waterpotential"],
        run=_run_osmosis,
        examples=["osmosis 0.3M", "osmosis 0.3M i 2", "osmosis total -0.7 -0.3"]))
