"""Music theory helpers: chord notes, scale notes, tempo math, transposition.

All local, keyless, no network — same contract as the rest of skills/.
Plain pitch arithmetic for the everyday music questions: which notes are
in a chord or a scale, how long a beat or a bar lasts at a tempo, and
what notes you get when you move a line up or down by an interval.

Pitch classes and rules used:
- The chromatic scale has 12 pitch classes. A note is a letter A-G plus
  an optional sharp (#) or flat (b): C, C#, D, Eb, F#, and so on.
- A chord is a root plus intervals in semitones: major (0, 4, 7), minor
  (0, 3, 7), diminished (0, 3, 6), augmented (0, 4, 8), sus2 (0, 2, 7),
  sus4 (0, 5, 7), dominant 7 (0, 4, 7, 10), major 7 (0, 4, 7, 11),
  minor 7 (0, 3, 7, 10), half-diminished (0, 3, 6, 10), diminished 7
  (0, 3, 6, 9), 6 (0, 4, 7, 9), minor 6 (0, 3, 7, 9), 9 (0, 4, 7, 10,
  14), minor 9 (0, 3, 7, 10, 14), add9 (0, 4, 7, 14).
- A scale is a root plus a step pattern in semitones: major (0, 2, 4,
  5, 7, 9, 11), natural minor (0, 2, 3, 5, 7, 8, 10), harmonic minor
  (0, 2, 3, 5, 7, 8, 11), melodic minor (0, 2, 3, 5, 7, 9, 11),
  dorian (0, 2, 3, 5, 7, 9, 10), mixolydian (0, 2, 4, 5, 7, 9, 10),
  major pentatonic (0, 2, 4, 7, 9), minor pentatonic (0, 3, 5, 7, 10),
  blues (0, 3, 5, 6, 7, 10).
- Tempo: one beat lasts 60,000 / BPM milliseconds. A bar lasts beats
  per bar x that. A duration holds BPM x seconds / 60 beats.
- Transposition moves every note by the same number of semitones:
  minor 2nd = 1, major 2nd = 2, minor 3rd = 3, major 3rd = 4, perfect
  4th = 5, tritone = 6, perfect 5th = 7, minor 6th = 8, major 6th = 9,
  minor 7th = 10, major 7th = 11, octave = 12.

Conventions and explicit caveats:
- Notes are pitch names, not letter-perfect spellings: the flat fifth
  of D blues shows as G# (the same pitch as Ab), and a Bbdim chord
  shows its fifth as E (the same pitch as Fb). If the spelling matters
  for sheet music, use the note letters of the key.
- Rare roots are shown in their common enharmonic form: D# reads as
  Eb and A# reads as Bb, the keys players actually use.
- A chord or scale names pitches only — it does not tell you which
  voicing or fingering to play, and it knows nothing about the song
  you are playing.
- Tempo math assumes a steady beat; a human player speeding up or a
  ritardando at the end of a piece makes the real bar lengths differ.
"""
from __future__ import annotations

from .base import Skill, SkillRegistry

_SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F",
                "F#", "G", "G#", "A", "A#", "B"]
_FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F",
               "Gb", "G", "Ab", "A", "Bb", "B"]
_LETTER_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def _parse_note(token: str) -> int | None:
    """Parse a note token (C, F#, Eb) to a pitch class 0-11, or None."""
    raw = token.strip()
    if len(raw) not in (1, 2):
        return None
    letter = raw[0].upper()
    if letter not in _LETTER_PC:
        return None
    pc = _LETTER_PC[letter]
    if len(raw) == 2:
        if raw[1] == "#":
            pc += 1
        elif raw[1] in ("b", "B"):
            pc -= 1
        else:
            return None
    return pc % 12


def _note_name(pc: int, flats: bool) -> str:
    return (_FLAT_NAMES if flats else _SHARP_NAMES)[pc % 12]


def _canonical_root(token: str, flats_default: bool = False) -> tuple[int, bool] | None:
    """Parse a root token, returning (pitch class, use-flats).

    Rare sharp roots D# and A# are normalised to Eb and Bb, the keys
    players actually use. A root with its own accidental keeps it; a
    natural root follows flats_default, so minor keys spell Eb/Ab/Bb
    the way sheet music does instead of D#/G#/A#.
    """
    pc = _parse_note(token)
    if pc is None:
        return None
    if "b" in token or "B" in token[1:]:
        return pc, True
    if pc == 3:  # D# -> Eb
        return pc, True
    if pc == 10:  # A# -> Bb
        return pc, True
    if "#" in token:
        return pc, False
    return pc, flats_default


# ---------------------------------------------------------------- chord

_CHORDS = {
    "": (0, 4, 7),
    "maj": (0, 4, 7),
    "major": (0, 4, 7),
    "m": (0, 3, 7),
    "min": (0, 3, 7),
    "minor": (0, 3, 7),
    "dim": (0, 3, 6),
    "diminished": (0, 3, 6),
    "aug": (0, 4, 8),
    "augmented": (0, 4, 8),
    "+": (0, 4, 8),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
    "7": (0, 4, 7, 10),
    "dom7": (0, 4, 7, 10),
    "dominant 7": (0, 4, 7, 10),
    "dominant seventh": (0, 4, 7, 10),
    "maj7": (0, 4, 7, 11),
    "major 7": (0, 4, 7, 11),
    "major seventh": (0, 4, 7, 11),
    "m7": (0, 3, 7, 10),
    "min7": (0, 3, 7, 10),
    "minor 7": (0, 3, 7, 10),
    "minor seventh": (0, 3, 7, 10),
    "m7b5": (0, 3, 6, 10),
    "half diminished": (0, 3, 6, 10),
    "dim7": (0, 3, 6, 9),
    "diminished 7": (0, 3, 6, 9),
    "6": (0, 4, 7, 9),
    "m6": (0, 3, 7, 9),
    "min6": (0, 3, 7, 9),
    "minor 6": (0, 3, 7, 9),
    "9": (0, 4, 7, 10, 14),
    "m9": (0, 3, 7, 10, 14),
    "minor 9": (0, 3, 7, 10, 14),
    "add9": (0, 4, 7, 14),
    "add 9": (0, 4, 7, 14),
    "sus 2": (0, 2, 7),
    "sus 4": (0, 5, 7),
}

_USAGE_CHORD = (
    "Usage: `chord <root><type>` or `chord <root> <type>` — e.g. `chord C`, "
    "`chord Am`, `chord G7`, `chord F#m7`, `chord C major`. Types: major, "
    "minor, dim, aug, sus2, sus4, 7, maj7, m7, m7b5, dim7, 6, m6, 9, m9, add9."
)


_CHORD_LABELS = {
    "": "major", "maj": "major", "major": "major", "M": "major",
    "m": "minor", "min": "minor", "minor": "minor",
    "dim": "diminished", "diminished": "diminished",
    "aug": "augmented", "augmented": "augmented", "+": "augmented",
    "sus2": "sus2", "sus4": "sus4",
    "7": "dominant 7", "dom7": "dominant 7",
    "maj7": "major 7", "M7": "major 7",
    "m7": "minor 7", "min7": "minor 7",
    "m7b5": "half-diminished", "dim7": "diminished 7",
    "6": "6th", "m6": "minor 6th", "min6": "minor 6th",
    "9": "9th", "m9": "minor 9th", "add9": "add9",
}


def _chord_label(suffix: str) -> str:
    return _CHORD_LABELS.get(suffix) or _CHORD_LABELS.get(suffix.lower(), suffix)


_FLAT_CHORD_TYPES = {
    "m", "min", "minor", "dim", "diminished",
    "m7", "min7", "minor 7", "minor seventh",
    "m7b5", "half diminished", "dim7", "diminished 7",
    "m6", "min6", "minor 6", "m9", "minor 9",
    # Dominant 7th/9th chords carry a flat 7th: C7 is C E G Bb.
    "7", "dom7", "dominant 7", "dominant seventh", "9",
}


def _lookup_chord(suffix: str) -> tuple[int, ...] | None:
    # "M7" is major 7, "m7" is minor 7 — case matters, check first.
    if suffix in ("M", "M7"):
        return _CHORDS["maj"] if suffix == "M" else _CHORDS["maj7"]
    return _CHORDS.get(suffix.lower())


def _run_chord(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if not parts:
        return _USAGE_CHORD
    root_token = parts[0]
    if len(parts) == 1:
        # Split a glued token like "Am", "F#m7", "Bbdim" into root + type.
        if len(root_token) < 1 or root_token[0].upper() not in _LETTER_PC:
            return _USAGE_CHORD
        cut = 2 if len(root_token) > 1 and root_token[1] in ("#", "b", "B") else 1
        root_token, suffix = root_token[:cut], root_token[cut:]
        intervals = _lookup_chord(suffix)
        if intervals is None:
            return (f"Unknown chord type `{suffix}`. " + _USAGE_CHORD)
        label = _chord_label(suffix)
    else:
        suffix = " ".join(parts[1:])
        intervals = _lookup_chord(suffix)
        if intervals is None:
            return (f"Unknown chord type `{suffix}`. " + _USAGE_CHORD)
        label = _chord_label(suffix)
    root = _canonical_root(root_token, suffix.lower() in _FLAT_CHORD_TYPES)
    if root is None:
        return _USAGE_CHORD
    pc, flats = root
    root_name = _note_name(pc, flats)
    notes = [_note_name(pc + step, flats) for step in intervals]
    return (f"{root_name} {label}: {' '.join(notes)} — "
            f"{len(notes)} notes, root plus {', '.join(str(s) for s in intervals[1:])} "
            f"semitones. Pitch names only — the spelling on sheet music "
            f"follows the key.")


# ---------------------------------------------------------------- scale

_SCALES = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "natural minor": (0, 2, 3, 5, 7, 8, 10),
    "harmonic minor": (0, 2, 3, 5, 7, 8, 11),
    "melodic minor": (0, 2, 3, 5, 7, 9, 11),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "pentatonic": (0, 2, 4, 7, 9),
    "major pentatonic": (0, 2, 4, 7, 9),
    "minor pentatonic": (0, 3, 5, 7, 10),
    "blues": (0, 3, 5, 6, 7, 10),
}

_USAGE_SCALE = (
    "Usage: `musicscale <root> [type]` — e.g. `musicscale C`, `musicscale A minor`, "
    "`musicscale G pentatonic`, `musicscale D blues`. Types: major, minor, harmonic "
    "minor, melodic minor, dorian, mixolydian, pentatonic, minor pentatonic, blues. "
    "(Plain `scale` is the recipe scaler.)"
)


_MINOR_SCALE_TYPES = {
    "minor", "natural minor", "harmonic minor", "melodic minor",
    "dorian", "minor pentatonic", "blues",
}


def _run_scale(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if not parts:
        return _USAGE_SCALE
    kind = " ".join(parts[1:]).lower() if len(parts) > 1 else "major"
    intervals = _SCALES.get(kind)
    if intervals is None:
        return f"Unknown scale type `{kind}`. " + _USAGE_SCALE
    root = _canonical_root(parts[0], kind in _MINOR_SCALE_TYPES)
    if root is None:
        return _USAGE_SCALE
    pc, flats = root
    root_name = _note_name(pc, flats)
    notes = [_note_name(pc + step, flats) for step in intervals]
    return (f"{root_name} {kind}: {' '.join(notes)} — {len(notes)} notes. "
            f"Pitch names only — the spelling on sheet music follows the key.")


# ---------------------------------------------------------------- tempo

_USAGE_TEMPO = (
    "Usage: `tempo <bpm> [beats-per-bar]` — e.g. `tempo 120`, `tempo 120 3` — "
    "or `tempo <bpm> <duration>` — e.g. `tempo 120 90s`, `tempo 120 3min` — "
    "or `tempo <ms>ms` to turn a beat length into BPM, e.g. `tempo 500ms`."
)


def _fmt_ms(ms: float) -> str:
    if ms == int(ms):
        return f"{int(ms)} ms"
    return f"{ms:.1f} ms"


def _fmt_seconds(seconds: float) -> str:
    if seconds == int(seconds):
        return f"{int(seconds)} s"
    return f"{seconds:.2f} s"


def _run_tempo(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if not parts:
        return _USAGE_TEMPO
    first = parts[0].lower()
    if first.endswith("ms"):
        try:
            ms = float(first[:-2])
        except ValueError:
            return _USAGE_TEMPO
        if not 200 <= ms <= 3000:
            return "Beat length must be 200-3000 ms (20-300 BPM)."
        bpm = 60000 / ms
        return (f"A {_fmt_ms(ms)} beat is {bpm:.1f} BPM — one beat every "
                f"{_fmt_ms(ms)}, {bpm:.1f} beats in a minute.")
    try:
        bpm = float(first)
    except ValueError:
        return _USAGE_TEMPO
    if bpm != int(bpm):
        return "BPM must be a whole number."
    bpm = int(bpm)
    if not 20 <= bpm <= 300:
        return f"BPM must be 20-300, got {bpm}."
    beat_ms = 60000 / bpm
    if len(parts) == 1:
        bar_ms = beat_ms * 4
        return (f"At {bpm} BPM: one beat is {_fmt_ms(beat_ms)}, a 4/4 bar "
                f"is {_fmt_seconds(bar_ms / 1000)}, {bpm} beats in a minute.")
    if len(parts) != 2:
        return _USAGE_TEMPO
    second = parts[1].lower()
    if second.endswith("min"):
        try:
            minutes = float(second[:-3])
        except ValueError:
            return _USAGE_TEMPO
        if minutes <= 0:
            return "Duration must be more than 0."
        beats = bpm * minutes
        beats_text = f"{int(beats)}" if beats == int(beats) else f"{beats:.1f}"
        return (f"At {bpm} BPM, {minutes:g} minute{'s' if minutes != 1 else ''} "
                f"holds {beats_text} beats.")
    if second.endswith("s"):
        try:
            seconds = float(second[:-1])
        except ValueError:
            return _USAGE_TEMPO
        if seconds <= 0:
            return "Duration must be more than 0."
        beats = bpm * seconds / 60
        beats_text = f"{int(beats)}" if beats == int(beats) else f"{beats:.1f}"
        return (f"At {bpm} BPM, {seconds:g} seconds holds {beats_text} beats.")
    try:
        per_bar = int(second)
    except ValueError:
        return _USAGE_TEMPO
    if not 1 <= per_bar <= 12:
        return f"Beats per bar must be 1-12, got `{parts[1]}`."
    bar_ms = beat_ms * per_bar
    return (f"At {bpm} BPM: one beat is {_fmt_ms(beat_ms)}, a {per_bar}/4 bar "
            f"is {_fmt_seconds(bar_ms / 1000)}.")


# ---------------------------------------------------------------- transpose

_INTERVALS = {
    "m2": 1, "min2": 1, "minor2": 1,
    "m3": 3, "min3": 3, "minor3": 3,
    "m6": 8, "min6": 8, "minor6": 8,
    "m7": 10, "min7": 10, "minor7": 10,
    "p4": 5, "perfect4": 5, "fourth": 5,
    "p5": 7, "perfect5": 7, "fifth": 7,
    "p8": 12, "perfect8": 12, "octave": 12,
    "tt": 6, "tritone": 6,
}

_USAGE_TRANSPOSE = (
    "Usage: `transpose <note> <note> ... <shift>` — e.g. `transpose C E G +2`, "
    "`transpose Bb Eb F -2`, `transpose A C# E +P5`. Shift is semitones "
    "(-12 to 12) or an interval: m2, M2, m3, M3, P4, TT, P5, m6, M6, m7, M7, octave."
)


def _parse_shift(token: str) -> int | None:
    raw = token.strip()
    sign = 1
    if raw.startswith(("+", "-")):
        sign = -1 if raw[0] == "-" else 1
        raw = raw[1:]
    if not raw:
        return None
    # Major intervals are case-sensitive (M2 is not m2) — check first.
    if raw in ("M2", "M3", "M6", "M7"):
        return sign * {"M2": 2, "M3": 4, "M6": 9, "M7": 11}[raw]
    if raw.lstrip("-").isdigit():
        return sign * int(raw)
    value = _INTERVALS.get(raw.lower())
    if value is None:
        return None
    return sign * value


def _run_transpose(trigger: str, args: str) -> str:
    parts = (args or "").split()
    if len(parts) < 2:
        return _USAGE_TRANSPOSE
    shift = _parse_shift(parts[-1])
    if shift is None or not -12 <= shift <= 12:
        return (f"Shift must be -12 to 12 semitones or an interval name, "
                f"got `{parts[-1]}`. " + _USAGE_TRANSPOSE)
    notes = [_parse_note(p) for p in parts[:-1]]
    if any(n is None for n in notes):
        return _USAGE_TRANSPOSE
    flats = any("b" in p or "B" in p[1:] for p in parts[:-1])
    before = [_note_name(n, flats) for n in notes]
    after = [_note_name(n + shift, flats) for n in notes]
    if shift == 0:
        return (f"{' '.join(before)} shifted by 0 semitones is unchanged: "
                f"{' '.join(after)}.")
    direction = "up" if shift > 0 else "down"
    return (f"{' '.join(before)} shifted {direction} {abs(shift)} "
            f"semitone{'s' if abs(shift) != 1 else ''} is "
            f"{' '.join(after)}.")


def register_all(registry: SkillRegistry) -> None:
    registry.register(Skill(
        name="chord", description="Notes in a chord from its root and type.",
        usage="chord <root><type> | chord <root> <type>",
        triggers=["chord", "chordnotes", "chord-notes"],
        run=_run_chord,
        examples=["chord C", "chord Am", "chord G7", "chord C major"]))
    registry.register(Skill(
        name="musicscale", description="Notes in a scale from its root and type.",
        usage="musicscale <root> [type]",
        triggers=["musicscale", "scalenotes", "scale-notes"],
        run=_run_scale,
        examples=["musicscale C", "musicscale A minor", "musicscale D blues"]))
    registry.register(Skill(
        name="tempo", description="Beat and bar lengths at a BPM, or BPM from a beat length.",
        usage="tempo <bpm> [beats-per-bar|duration] | tempo <ms>ms",
        triggers=["tempo", "bpm", "metronome"],
        run=_run_tempo,
        examples=["tempo 120", "tempo 120 3", "tempo 500ms"]))
    registry.register(Skill(
        name="transpose", description="Transpose notes up or down by semitones or an interval.",
        usage="transpose <note> <note> ... <shift>",
        triggers=["transpose", "transposenotes", "transpose-notes"],
        run=_run_transpose,
        examples=["transpose C E G +2", "transpose A C# E +P5"]))
