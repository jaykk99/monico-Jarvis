"""Tests for skills/music.py: chord, scale, tempo, transpose."""
from agent import agent


def _ask(text: str) -> str:
    resp = agent.respond(text)
    assert resp["ok"], f"{text!r} failed: {resp['response']}"
    return resp["response"]


# ---------------------------------------------------------------- chord
def test_chord_basic():
    # C major: root + 4 + 7 semitones = C E G.
    out = _ask("chord C")
    assert "C major: C E G" in out
    assert "root plus 4, 7 semitones" in out
    # A minor: root + 3 + 7 = A C E.
    out = _ask("chord Am")
    assert "A minor: A C E" in out
    # C diminished: root + 3 + 6 = C Eb Gb.
    out = _ask("chord C dim")
    assert "C diminished: C Eb Gb" in out
    # Two-word form gives the same answer.
    assert "C major: C E G" in _ask("chord C major")


def test_chord_extensions():
    # G7: root + 4 + 7 + 10 = G B D F.
    out = _ask("chord G7")
    assert "G dominant 7: G B D F" in out
    # F#m7: root + 3 + 7 + 10 = F# A C# E.
    out = _ask("chord F#m7")
    assert "F# minor 7: F# A C# E" in out
    # C dominant 7, two-word form: C E G Bb.
    out = _ask("chord C dominant 7")
    assert "C dominant 7: C E G Bb" in out
    # Cmaj7: root + 4 + 7 + 11 = C E G B.
    out = _ask("chord Cmaj7")
    assert "C major 7: C E G B" in out


def test_chord_enharmonic_root():
    # D# is shown as Eb, the key players use: Eb G Bb.
    out = _ask("chord D#")
    assert "Eb major: Eb G Bb" in out
    # Bb major uses flats throughout: Bb D F.
    out = _ask("chord Bb")
    assert "Bb major: Bb D F" in out


def test_chord_bad():
    assert "Usage" in _ask("chord")
    assert "Usage" in _ask("chord H")
    assert "Unknown chord type" in _ask("chord C zzz")
    assert "Unknown chord type" in _ask("chord C major extra")


# ---------------------------------------------------------------- scale
def test_scale_basic():
    # C major: C D E F G A B.
    out = _ask("musicscale C")
    assert "C major: C D E F G A B" in out
    assert "7 notes" in out
    # A natural minor: A B C D E F G.
    out = _ask("musicscale A minor")
    assert "A minor: A B C D E F G" in out


def test_scale_other_types():
    # G major pentatonic: G A B D E (5 notes).
    out = _ask("musicscale G pentatonic")
    assert "G pentatonic: G A B D E" in out
    assert "5 notes" in out
    # D blues: D F G Ab A C.
    out = _ask("musicscale D blues")
    assert "D blues: D F G Ab A C" in out
    assert "6 notes" in out
    # Eb major uses flats: Eb F G Ab Bb C D.
    out = _ask("musicscale Eb major")
    assert "Eb major: Eb F G Ab Bb C D" in out
    # C harmonic minor: C D Eb F G Ab B.
    out = _ask("musicscale C harmonic minor")
    assert "C harmonic minor: C D Eb F G Ab B" in out


def test_scale_bad():
    assert "Usage" in _ask("musicscale")
    assert "Usage" in _ask("musicscale H major")
    assert "Unknown scale type" in _ask("musicscale C zzz")


# ---------------------------------------------------------------- tempo
def test_tempo_basic():
    # 120 BPM: beat 60000/120 = 500 ms, 4/4 bar 2000 ms = 2 s.
    out = _ask("tempo 120")
    assert "At 120 BPM: one beat is 500 ms" in out
    assert "a 4/4 bar is 2 s" in out
    assert "120 beats in a minute" in out
    # 60 BPM: beat 1000 ms, 4/4 bar 4 s.
    out = _ask("tempo 60")
    assert "one beat is 1000 ms" in out
    assert "a 4/4 bar is 4 s" in out


def test_tempo_bar_and_duration():
    # 120 BPM in 3/4: bar 3 x 500 ms = 1500 ms = 1.50 s.
    out = _ask("tempo 120 3")
    assert "a 3/4 bar is 1.50 s" in out
    # 120 BPM x 90 s / 60 = 180 beats.
    out = _ask("tempo 120 90s")
    assert "90 seconds holds 180 beats" in out
    # 120 BPM x 3 min = 360 beats.
    out = _ask("tempo 120 3min")
    assert "3 minutes holds 360 beats" in out


def test_tempo_ms_to_bpm():
    # A 500 ms beat is 60000/500 = 120 BPM.
    out = _ask("tempo 500ms")
    assert "A 500 ms beat is 120.0 BPM" in out
    # A 250 ms beat is 240 BPM.
    out = _ask("tempo 250ms")
    assert "is 240.0 BPM" in out


def test_tempo_bad():
    assert "Usage" in _ask("tempo")
    assert "Usage" in _ask("tempo abc")
    assert "20-300" in _ask("tempo 10")
    assert "20-300" in _ask("tempo 400")
    assert "200-3000 ms" in _ask("tempo 50ms")
    assert "1-12" in _ask("tempo 120 13")
    assert "Usage" in _ask("tempo 120 5x")


# ---------------------------------------------------------------- transpose
def test_transpose_basic():
    # C E G up 2 semitones: D F# A.
    out = _ask("transpose C E G +2")
    assert "C E G shifted up 2 semitones is D F# A." in out
    # Bb Eb F down 2: Ab Db Eb (flats stay flats).
    out = _ask("transpose Bb Eb F -2")
    assert "Bb Eb F shifted down 2 semitones is Ab Db Eb." in out


def test_transpose_intervals():
    # A C# E up a perfect fifth (7 semitones): E G# B.
    out = _ask("transpose A C# E +P5")
    assert "A C# E shifted up 7 semitones is E G# B." in out
    # C up an octave is C again.
    out = _ask("transpose C +octave")
    assert "C shifted up 12 semitones is C." in out
    # A shift of 0 leaves the notes unchanged.
    out = _ask("transpose C E G 0")
    assert "shifted by 0 semitones is unchanged: C E G." in out


def test_transpose_bad():
    assert "Usage" in _ask("transpose")
    assert "Usage" in _ask("transpose C")
    assert "Usage" in _ask("transpose H +2")
    assert "Shift must be" in _ask("transpose C +13")
    assert "Shift must be" in _ask("transpose C +foo")
    assert "Shift must be" in _ask("transpose C E G +2 extra")


# ---------------------------------------------------------------- registry
def test_music_skills_registered():
    names = {s["name"] for s in agent.list_skills()}
    assert {"chord", "musicscale", "tempo", "transpose"} <= names
    assert len(agent.list_skills()) == 130
    # Plain `scale` still belongs to the recipe scaler (cook), not music.
    assert "400 g flour" in _ask("scale 4 8 200g flour")
