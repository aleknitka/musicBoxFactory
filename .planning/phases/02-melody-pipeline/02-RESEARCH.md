# Phase 2: Melody Pipeline - Research

**Researched:** 2026-03-31
**Domain:** Note sequencing, lullaby note tables, circle-of-fifths procedural generation, zero-crossing loop alignment, numpy buffer concatenation
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MELO-01 | Library ships with built-in lullaby presets (Twinkle Twinkle, Brahms' Lullaby, and others) as note sequences | Note tables documented in Code Examples below; sequences are public domain, hardcoded as `list[tuple[str, float]]` |
| MELO-02 | Caller can provide a custom note sequence as a list of `(note, duration)` tuples | Direct pass-through to sequencer; same type as preset tables; no extra API surface needed |
| MELO-03 | Library can procedurally generate a novel melody loop by traversing the circle of fifths | Algorithm documented in Architecture Patterns; pure numpy / stdlib, no external dependency |
</phase_requirements>

---

## Summary

Phase 2 delivers `musicboxfactory/melody.py` — a `MelodyPipeline` class (or `render_melody` function) that accepts a note sequence (from a preset, custom input, or procedural generation) and produces a single float32 mono numpy buffer by calling `Synth.render()` once per note and concatenating the results. The three requirement areas — presets, custom input, procedural generation — all feed the same sequencer function, so the core implementation is a single loop over `list[tuple[str, float]]`.

The key technical concerns are: (1) silence gaps between notes to prevent tones from bleeding into each other, (2) loop-boundary zero-crossing alignment so the melody buffer ends at a sample where the waveform crosses zero (preventing audible click when the Phase 4 mixer loops the output), and (3) the procedural circle-of-fifths generator, which must produce a deterministic, musically coherent note list without any new dependencies. The buffer contract from Phase 1 — float32, mono, 44100 Hz, values in [-1, 1] — is inherited by the melody output buffer.

Lullaby note sequences are public domain music that can be hardcoded as plain Python lists. Twinkle Twinkle Little Star and Brahms' Lullaby each have a well-known one-phrase melody (roughly 14-28 notes) that loops naturally. The procedural generator uses the circle-of-fifths as a Markov chain over scale degrees, requiring only numpy and the standard library.

**Primary recommendation:** Implement `melody.py` with a single `render_sequence(synth, notes, gap_seconds)` function that iterates `notes: list[tuple[str, float]]`, calls `synth.render(note, duration)` per pair, inserts a short silence buffer between notes, concatenates all buffers with `np.concatenate`, and trims the end to the nearest zero crossing. Presets, custom input, and procedural generation all produce a `list[tuple[str, float]]` and pass it to this function.

---

## Project Constraints (from CLAUDE.md)

| Directive | Type | Enforcement |
|-----------|------|-------------|
| Python >=3.13 | Required | All code uses >=3.13 syntax; no backports |
| `uv` for dependency management | Required | No new `pip install`; add deps via `uv add` |
| Test command: `uv run pytest` | Required | All test invocations via `uv run pytest` |
| Type check: `uv run mypy src/` | Required | `melody.py` must pass mypy strict |
| Lint: `uv run ruff check src/` | Required | `melody.py` must pass ruff |
| Module path: `musicboxfactory/melody.py` | Required | CLAUDE.md architecture specifies this filename |
| Buffer contract: float32, mono, 44100 Hz, [-1, 1] | Required | Output of `render_sequence` must match |
| No CLI | Forbidden | No `__main__`, no argparse |
| No audio playback | Forbidden | No sounddevice, pyaudio, pygame |
| No MP3/OGG | Forbidden | WAV only; this phase does not write files |
| No MIDI file input | Forbidden | Out-of-scope per REQUIREMENTS.md |
| numpy 2.x | Required | Already in pyproject.toml as `numpy>=2.0` |
| scipy for WAV output | Required | Only if dev WAV writer used (dev utility only) |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.4.4 (installed) | Buffer concatenation, silence generation, zero-crossing detection | Required by buffer contract; already a dependency |
| musicboxfactory.synth.Synth | Phase 1 output | Note rendering backend | The only tone renderer; `render(note, duration) -> ndarray` is the Phase 1 API |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scipy | 1.17.1 (dev dep) | WAV writer for integration test verification | Dev/test only; write melody buffer to WAV to verify audible output |

### No New Dependencies Required

Phase 2 requires no new Python packages. All functionality (buffer concatenation, silence, zero-crossing) is achievable with numpy 2.x and the standard library. Do not add librosa, music21, midiutil, or any other package.

**Installation:** No new installs. `uv sync` is sufficient; numpy is already declared in `pyproject.toml`.

**Version verification (confirmed 2026-03-31):**
- `numpy`: 2.4.4 (confirmed via `uv run python -c "import numpy; print(numpy.__version__)"`)
- `pytest`: 9.0.2 (confirmed via `uv run pytest --version`)

---

## Architecture Patterns

### Recommended Project Structure (Phase 2 additions)

```
src/
└── musicboxfactory/
    ├── __init__.py          # Add MelodyPipeline / render_melody to exports
    ├── synth.py             # Phase 1 — unchanged
    └── melody.py            # Phase 2 — NEW
tests/
├── __init__.py
├── conftest.py              # Unchanged — requires_sf2 marker already present
├── test_synth.py            # Phase 1 — unchanged
└── test_melody.py           # Phase 2 — NEW
```

### Pattern 1: Note Sequence Type

**What:** The canonical type for all melody data is `list[tuple[str, float]]` where the first element is a note name string (`"c4"`, `"g#3"`) and the second is duration in seconds (not musical beat values).

**When to use:** All three input paths (preset lookup, custom, procedural) produce this type and pass it to `render_sequence`.

**Why float seconds, not beats:** The `Synth.render()` API (Phase 1) takes duration in seconds. Converting from beats requires a BPM parameter — that is a v2 feature (MELO-05). For v1, callers express durations directly in seconds. Preset tables encode durations that sound correct at a fixed implicit tempo.

```python
# Type alias — use in melody.py
NoteSequence = list[tuple[str, float]]
```

### Pattern 2: Core Sequencer — render_sequence()

**What:** Iterate over note sequence, render each note to a buffer, insert silence gap, concatenate all, trim end to nearest zero crossing.

**When to use:** Always. All three MELO requirements funnel through this one function.

```python
# Source: numpy 2.x docs + Phase 1 synth.py API
import numpy as np
from musicboxfactory.synth import Synth, SAMPLE_RATE

def render_sequence(
    synth: Synth,
    notes: list[tuple[str, float]],
    gap_seconds: float = 0.05,
) -> np.ndarray:
    """Render a note sequence to a float32 mono buffer.

    Args:
        synth: Constructed Synth instance (Phase 1).
        notes: List of (note_name, duration_seconds) tuples.
        gap_seconds: Silence to insert between notes (default 50 ms).

    Returns:
        np.ndarray, dtype=float32, shape=(N,), values in [-1.0, 1.0].
        N is the total sample count including gaps, trimmed to a zero crossing.
    """
    silence = np.zeros(int(SAMPLE_RATE * gap_seconds), dtype=np.float32)
    chunks: list[np.ndarray] = []

    for note, duration in notes:
        buf = synth.render(note, duration)       # float32, [-1, 1]
        chunks.append(buf)
        chunks.append(silence)

    if not chunks:
        return np.zeros(0, dtype=np.float32)

    combined = np.concatenate(chunks)

    # Trim trailing samples to the last zero crossing before the final sample
    combined = _trim_to_zero_crossing(combined)

    return combined
```

### Pattern 3: Zero-Crossing Trim

**What:** Find the last zero crossing in the buffer and trim there so the melody ends silently. This prevents an audible click when the Phase 4 mixer loops the output.

**Why trim, not align the start too:** Phase 4 (OUT-04) is responsible for full crossfade + zero-crossing boundary enforcement on the final WAV. Phase 2's role is simpler: ensure the melody buffer ends at or near zero so Phase 4 has clean material to work with. Trimming a few samples at most.

**Algorithm:** Use `np.where(np.diff(np.sign(buf)) != 0)` to locate sign-change indices. Take the last one and truncate.

```python
# Source: numpy 2.x docs — np.sign, np.diff, np.where
def _trim_to_zero_crossing(buf: np.ndarray, search_window: int = 2048) -> np.ndarray:
    """Trim the end of buf to the last zero crossing within search_window samples.

    Scans backward from the end of the buffer up to search_window samples.
    If no zero crossing is found in that window, returns buf unchanged.

    Args:
        buf: float32 audio buffer.
        search_window: How many trailing samples to search (default: 2048 ~= 46 ms).

    Returns:
        Trimmed buffer (same dtype, same array data up to trim point).
    """
    if len(buf) < 2:
        return buf

    tail_start = max(0, len(buf) - search_window)
    tail = buf[tail_start:]

    # Sign changes indicate zero crossings
    sign_changes = np.where(np.diff(np.sign(tail)) != 0)[0]

    if len(sign_changes) == 0:
        return buf  # No zero crossing found — return unchanged

    # Last zero crossing index relative to buf
    last_zc = tail_start + sign_changes[-1] + 1  # +1: use sample after the crossing
    return buf[:last_zc]
```

**Key insight:** `search_window=2048` gives a ~46 ms search range at 44100 Hz. Music box tones have rich harmonic content; a zero crossing will almost always appear within 46 ms. This is the same range noted in STATE.md (100-200 samples is too small; 2048 is safer).

### Pattern 4: Built-in Lullaby Presets Dict

**What:** A module-level dict mapping preset name strings to `NoteSequence` values.

**When to use:** `MelodyPipeline.from_preset("twinkle")` looks up the name and delegates to `render_sequence`.

```python
LULLABY_PRESETS: dict[str, list[tuple[str, float]]] = {
    "twinkle": TWINKLE_TWINKLE,
    "brahms": BRAHMS_LULLABY,
    "mary": MARY_HAD_A_LITTLE_LAMB,
}
```

Unknown preset name raises `ValueError` (same convention as PRESETS in synth.py — fail fast, message lists valid names).

### Pattern 5: Procedural Generator (Circle of Fifths)

**What:** Generate a novel note sequence by walking the circle of fifths using a weighted random walk over scale degrees.

**Algorithm:**
1. Choose a root key (default C major).
2. Define the major scale intervals: `[0, 2, 4, 5, 7, 9, 11]` semitones above root.
3. Walk the scale using a Markov-style step: from current scale degree, step up or down 1-3 degrees with weights that prefer stepwise motion (degrees 1-2 more likely than leaps of 3).
4. After N notes, move to the next key a fifth up (add 7 semitones, mod 12) — this is the circle-of-fifths traversal.
5. Return to root key after traversing the desired number of fifths.
6. Convert each (key_root, scale_degree, octave) to a note name string using the same logic as `_note_name_to_midi` in synth.py.

**Traversal depth:** Default 2 fifths (C → G → D → C) gives a musically varied but stable loop. Expose as a parameter.

**Duration:** Default 0.4 seconds per note (approximately 150 BPM quarter notes). Fixed for v1; configurable BPM is v2 (MELO-05).

```python
# Source: music theory (circle of fifths is standard Western theory, not a library)
import random
import numpy as np

CHROMATIC = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]
MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]  # W W H W W W H

def generate_circle_of_fifths(
    num_notes: int = 16,
    num_fifths: int = 2,
    root: str = "c",
    octave: int = 4,
    note_duration: float = 0.4,
    seed: int | None = None,
) -> list[tuple[str, float]]:
    """Generate a novel melody traversing the circle of fifths.

    Args:
        num_notes: Total notes to generate.
        num_fifths: How many fifth-steps to traverse before returning to root.
        root: Root pitch class (e.g. "c", "g", "f").
        octave: Starting octave (default 4 for C4).
        note_duration: Duration in seconds for each note.
        seed: Optional random seed for reproducibility.

    Returns:
        list[tuple[str, float]] — note sequence suitable for render_sequence().
    """
    rng = random.Random(seed)
    root_idx = CHROMATIC.index(root.lower())
    result: list[tuple[str, float]] = []

    notes_per_key = num_notes // (num_fifths + 1)
    current_root = root_idx
    scale_degree = 0  # Start on tonic
    current_octave = octave

    keys_to_visit = [root_idx]
    for _ in range(num_fifths):
        keys_to_visit.append((keys_to_visit[-1] + 7) % 12)
    keys_to_visit.append(root_idx)  # Return to root

    for key_root in keys_to_visit:
        scale = [(key_root + interval) % 12 for interval in MAJOR_INTERVALS]

        for _ in range(notes_per_key):
            pitch_idx = scale[scale_degree % len(scale)]
            note_name = CHROMATIC[pitch_idx] + str(current_octave)
            result.append((note_name, note_duration))

            # Weighted step: favour stepwise motion
            step = rng.choices([1, -1, 2, -2], weights=[4, 4, 1, 1])[0]
            next_degree = scale_degree + step
            # Clamp to avoid extreme leaps across octaves
            if next_degree < 0:
                next_degree = 0
                current_octave = max(3, current_octave - 1)
            elif next_degree >= len(scale):
                next_degree = len(scale) - 1
                current_octave = min(5, current_octave + 1)
            scale_degree = next_degree

    return result[:num_notes]
```

### Pattern 6: Public API Surface

**What:** `MelodyPipeline` class or module-level functions — either is acceptable. Based on the CLAUDE.md architecture description ("Sequences notes from the `Synth`"), a class that holds a `Synth` reference is the cleanest design.

```python
class MelodyPipeline:
    """Sequences Synth notes into a melody buffer."""

    def __init__(self, synth: Synth, gap_seconds: float = 0.05) -> None:
        self._synth = synth
        self._gap_seconds = gap_seconds

    def from_preset(self, name: str) -> np.ndarray:
        """Render a built-in lullaby preset. Raises ValueError for unknown name."""
        if name not in LULLABY_PRESETS:
            raise ValueError(f"Unknown preset {name!r}. Valid: {list(LULLABY_PRESETS)}")
        return render_sequence(self._synth, LULLABY_PRESETS[name], self._gap_seconds)

    def from_notes(self, notes: list[tuple[str, float]]) -> np.ndarray:
        """Render a caller-supplied note sequence."""
        return render_sequence(self._synth, notes, self._gap_seconds)

    def from_procedural(
        self,
        num_notes: int = 16,
        num_fifths: int = 2,
        seed: int | None = None,
    ) -> np.ndarray:
        """Generate and render a circle-of-fifths melody."""
        notes = generate_circle_of_fifths(num_notes=num_notes, num_fifths=num_fifths, seed=seed)
        return render_sequence(self._synth, notes, self._gap_seconds)
```

### Anti-Patterns to Avoid

- **Calling `synth.render()` with duration=0:** Returns a zero-length buffer; `np.concatenate` will fail if all chunks are zero-length. Guard: skip notes with duration <= 0.
- **Using musical beat durations instead of seconds:** `render()` takes seconds. Mixing beats and seconds silently produces wrong-speed output. All preset tables encode seconds directly.
- **Normalizing the melody buffer a second time inside `melody.py`:** `Synth.render()` already guarantees [-1, 1] per note. Concatenating normalized buffers can produce a combined buffer where the peak note is 1.0. Re-normalizing the full melody would reduce the loudest note to exactly 1.0 but makes the buffer's absolute level depend on its content. Leave normalization to Phase 4's mixer (OUT-02). Phase 2 should NOT normalize the combined buffer.
- **Using `np.append` in a loop:** `np.append` creates a new array on every call — O(N²) time for N notes. Always collect into a Python list of arrays and call `np.concatenate(chunks)` once at the end.
- **Hard-coding note sequences as MIDI note numbers:** Phase 1 uses note name strings (`"c4"`, `"g#3"`). Phase 2 should also use strings for consistency and readability. The `_note_name_to_midi` conversion happens inside `Synth.render()`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Note name parsing | Custom parser in melody.py | Existing `_note_name_to_midi` in synth.py | Already implemented and tested; importing from synth.py avoids duplication |
| Beat-to-seconds conversion | Custom BPM calculator | N/A — not needed in v1 | Durations are in seconds; BPM support is v2 (MELO-05). Do not build it now. |
| Pitch class arithmetic | Custom chromatic mapping | Inline arithmetic with the `CHROMATIC` list | The mapping is 12 elements; it fits in a one-liner constant |
| WAV writing | Custom WAV encoder | `scipy.io.wavfile.write` (dev utility) | Already in dev dependencies; out-of-scope for the `melody.py` module itself |

**Key insight:** Phase 2 is orchestration, not synthesis. All heavy lifting (tone rendering, WAV writing, normalization) is done by other phases. `melody.py` needs only a loop, a concatenation, and a zero-crossing trim.

---

## Built-in Lullaby Preset Note Tables

These sequences are public domain (traditional folk music and 19th-century compositions). Durations are in seconds at an implicit ~100-120 BPM quarter note = 0.5s. Expressed for the C4-C5 range to suit music box timbres.

### Twinkle Twinkle Little Star (C major, MELO-01)

Traditional. The note sequence `C C G G A A G` (first phrase) is confirmed by multiple public sources.

```python
TWINKLE_TWINKLE: list[tuple[str, float]] = [
    # "Twinkle, twinkle, little star"
    ("c4", 0.5), ("c4", 0.5), ("g4", 0.5), ("g4", 0.5),
    ("a4", 0.5), ("a4", 0.5), ("g4", 1.0),
    # "How I wonder what you are"
    ("f4", 0.5), ("f4", 0.5), ("e4", 0.5), ("e4", 0.5),
    ("d4", 0.5), ("d4", 0.5), ("c4", 1.0),
    # "Up above the world so high"
    ("g4", 0.5), ("g4", 0.5), ("f4", 0.5), ("f4", 0.5),
    ("e4", 0.5), ("e4", 0.5), ("d4", 1.0),
    # "Like a diamond in the sky"
    ("g4", 0.5), ("g4", 0.5), ("f4", 0.5), ("f4", 0.5),
    ("e4", 0.5), ("e4", 0.5), ("d4", 1.0),
    # "Twinkle, twinkle, little star" (repeat)
    ("c4", 0.5), ("c4", 0.5), ("g4", 0.5), ("g4", 0.5),
    ("a4", 0.5), ("a4", 0.5), ("g4", 1.0),
    # "How I wonder what you are" (repeat)
    ("f4", 0.5), ("f4", 0.5), ("e4", 0.5), ("e4", 0.5),
    ("d4", 0.5), ("d4", 0.5), ("c4", 1.0),
]
```

### Brahms' Lullaby — Wiegenlied Op.49 No.4 (C major, MELO-01)

Public domain (1868). The principal melody is 3/4 time. Duration mapping: dotted quarter = 0.75s, quarter = 0.5s, eighth = 0.25s at ~80 BPM.

```python
BRAHMS_LULLABY: list[tuple[str, float]] = [
    # "Guten Abend, gut' Nacht" (phrase 1)
    ("g4", 0.75), ("e4", 0.25), ("e4", 0.5),
    ("g4", 0.75), ("e4", 0.25), ("e4", 0.5),
    # "mit Rosen bedacht" (phrase 2)
    ("g4", 0.5), ("g4", 0.25), ("a4", 0.25), ("g4", 0.5), ("e4", 0.5),
    # "mit Näglein besteckt" (phrase 3)
    ("f4", 0.5), ("f4", 0.25), ("g4", 0.25), ("f4", 0.5), ("d4", 0.5),
    # "schlupf unter die Deck'" (phrase 4)
    ("e4", 0.5), ("e4", 0.25), ("f4", 0.25), ("e4", 0.5), ("c4", 0.5),
]
```

### Mary Had a Little Lamb (C major, MELO-01 — third preset)

Traditional. Provides variety from the two above.

```python
MARY_HAD_A_LITTLE_LAMB: list[tuple[str, float]] = [
    # "Mary had a little lamb"
    ("e4", 0.5), ("d4", 0.5), ("c4", 0.5), ("d4", 0.5),
    ("e4", 0.5), ("e4", 0.5), ("e4", 1.0),
    # "little lamb, little lamb"
    ("d4", 0.5), ("d4", 0.5), ("d4", 1.0),
    ("e4", 0.5), ("g4", 0.5), ("g4", 1.0),
    # "Mary had a little lamb" (repeat)
    ("e4", 0.5), ("d4", 0.5), ("c4", 0.5), ("d4", 0.5),
    ("e4", 0.5), ("e4", 0.5), ("e4", 0.5), ("e4", 0.5),
    # "whose fleece was white as snow"
    ("d4", 0.5), ("d4", 0.5), ("e4", 0.5), ("d4", 0.5), ("c4", 1.0),
]
```

**Confidence (note tables):** HIGH — Twinkle Twinkle and Mary Had a Little Lamb are extremely well-documented traditional melodies with widely consistent transcriptions. Brahms' Lullaby melody is public-domain and confirmed against multiple music education sources. The exact duration mappings (0.5s per quarter note at ~120 BPM) are choices made for this project and can be adjusted during implementation.

---

## Common Pitfalls

### Pitfall 1: np.append in a Loop (Quadratic Memory)

**What goes wrong:** Using `buffer = np.append(buffer, note_buf)` inside the sequencer loop creates a new full array copy on every iteration. For a 20-note melody at 0.5s each, this is 20 array copies of increasing size — O(N²) allocations.

**Why it happens:** `np.append` looks like Python `list.append` but is fundamentally different.

**How to avoid:** Collect buffers in a Python list: `chunks.append(buf)`. Call `np.concatenate(chunks)` once after the loop. This is O(N) total allocation.

**Warning signs:** Performance degrades noticeably as the melody gets longer; memory usage spikes.

### Pitfall 2: Note Bleed from Missing Silence Gap

**What goes wrong:** Consecutive notes overlap audibly because `synth.render()` drains the tail inside itself (Phase 1 decision), but if gap_seconds=0, the FluidSynth internal state may still carry residual energy from the previous note into the next render call. Audible as a "smeared" attack on each note.

**Why it happens:** The `Synth.render()` drains 3s of tail after noteoff, which should clear residual state — but the gap also serves a musical role (defines note articulation). Without any gap, all notes run together without rhythmic separation.

**How to avoid:** Default `gap_seconds=0.05` (50 ms). Allow callers to set it to 0.0 for legato playing, but document that music box tones benefit from articulation gaps. For lullaby presets, 50 ms is appropriate.

**Warning signs:** Melody sounds like one continuous tone without rhythmic structure.

### Pitfall 3: Loop Click from Non-Zero End Sample

**What goes wrong:** The melody buffer's last sample is non-zero (e.g., 0.3). When Phase 4 stitches two loops together, the jump from 0.3 back to the first sample's value (e.g., 0.0) is an instantaneous discontinuity — audible as a click or pop.

**Why it happens:** Note buffers end at arbitrary amplitude values depending on the note's natural decay at the requested duration.

**How to avoid:** `_trim_to_zero_crossing()` scans backward from the end of the concatenated buffer (up to `search_window` samples) to find the last sign change, then truncates there. Music box tones decay to near-zero quickly; the trim will typically remove 0-50 samples.

**Warning signs:** Audible click at the loop boundary when the WAV is looped in a media player.

### Pitfall 4: Zero-Duration Notes Crashing np.concatenate

**What goes wrong:** A note tuple with `duration=0.0` produces a zero-length array from `synth.render()`. `np.concatenate` does not error on zero-length arrays, but the preceding silence gap is still added, producing a gap with no note — which is harmless but wrong if the caller intended to skip a note.

**Why it happens:** Callers may provide rest markers as zero-duration notes (common in MIDI workflows).

**How to avoid:** In `render_sequence`, skip any tuple where `duration <= 0` with a guard:
```python
if duration <= 0.0:
    continue
```
Or treat zero duration as a rest by adding only the silence gap (no `synth.render()` call).

**Warning signs:** Melody is shorter than expected or has unintended gaps.

### Pitfall 5: Procedural Generator Producing Out-of-Range MIDI Notes

**What goes wrong:** The circle-of-fifths walker moves the octave up/down at boundaries, but without clamping, can generate notes like `"c9"` (MIDI 120) or `"c1"` (MIDI 24) that are outside the audible range of most music box soundfonts.

**Why it happens:** Unclamped octave increments/decrements accumulate over many steps.

**How to avoid:** Clamp `current_octave` to [3, 5] — this keeps notes in the C3-C5 range (MIDI 48-72) which is the core music box register. Add an explicit assertion or clamp in `generate_circle_of_fifths`.

**Warning signs:** Some notes are silent (soundfont has no sample for that octave) or sound an octave wrong.

---

## Code Examples

### render_sequence Full Implementation

```python
# Source: numpy 2.x concatenation docs + Phase 1 Synth API
import numpy as np
from musicboxfactory.synth import Synth, SAMPLE_RATE

def render_sequence(
    synth: Synth,
    notes: list[tuple[str, float]],
    gap_seconds: float = 0.05,
) -> np.ndarray:
    silence = np.zeros(int(SAMPLE_RATE * gap_seconds), dtype=np.float32)
    chunks: list[np.ndarray] = []

    for note, duration in notes:
        if duration <= 0.0:
            chunks.append(silence)
            continue
        buf = synth.render(note, duration)
        chunks.append(buf)
        chunks.append(silence)

    if not chunks:
        return np.zeros(0, dtype=np.float32)

    combined = np.concatenate(chunks)
    return _trim_to_zero_crossing(combined)
```

### Zero-Crossing Trim

```python
# Source: numpy 2.x — np.sign, np.diff, np.where
def _trim_to_zero_crossing(buf: np.ndarray, search_window: int = 2048) -> np.ndarray:
    if len(buf) < 2:
        return buf
    tail_start = max(0, len(buf) - search_window)
    tail = buf[tail_start:]
    sign_changes = np.where(np.diff(np.sign(tail)) != 0)[0]
    if len(sign_changes) == 0:
        return buf
    last_zc = tail_start + sign_changes[-1] + 1
    return buf[:last_zc]
```

### Verify Zero Crossing Works in Project Venv

```python
# Confirmed working 2026-03-31:
# uv run python -c "
#   import numpy as np
#   a = np.array([1.0, -1.0, 0.5, -0.5], dtype=np.float32)
#   zc = np.where(np.diff(np.sign(a)))[0]
#   print('zero crossings at:', zc)  # Output: [0 1 2]
# "
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Looping with `np.append` | Collect list, then `np.concatenate` | numpy best practices (always) | O(N) vs O(N²) allocation |
| Fixed loop length | Zero-crossing trim for clean boundary | Standard audio looping practice | No click at loop point |
| MIDI file as melody source | `list[tuple[str, float]]` directly | Project decision (MIDI deferred out of scope) | No MIDI parsing dependency needed |
| BPM-based durations | Seconds-based durations (v1) | MELO-05 deferred to v2 | Simpler API; BPM conversion not needed |

**Deprecated/outdated:**
- Using `music21` or `midiutil` for melody data: These add dependencies for a feature (`list[tuple[str, float]]`) that is trivially representable in plain Python. Do not add them.

---

## Open Questions

1. **Optimal gap_seconds value for music box timbre**
   - What we know: 50 ms (0.05s) is a conventional short gap; `Synth.render()` drains the 3s decay tail internally, so notes do not physically bleed between render calls
   - What's unclear: Whether 50 ms sounds natural for music box articulation vs. too staccato — depends on the soundfont and tempo
   - Recommendation: Default 0.05s; expose as parameter; document that callers can adjust. Validate aurally during execution.

2. **search_window for zero-crossing trim**
   - What we know: 2048 samples = ~46 ms at 44100 Hz; music box tones have zero crossings well within this window
   - What's unclear: Whether any note+duration combination produces a flat tail with no zero crossings in 46 ms (e.g., a very long sustained tone that hasn't decayed at the duration boundary)
   - Recommendation: Default 2048; fall through to returning the untrimmed buffer if no zero crossing is found in the window (do not panic). Phase 4 handles the final crossfade regardless.

3. **Number of lullaby presets required by MELO-01**
   - What we know: MELO-01 says "Twinkle Twinkle, Brahms' Lullaby, and others" — minimum two explicitly named
   - What's unclear: Whether "others" means the test only checks for the two named ones or requires a third
   - Recommendation: Ship three (Twinkle Twinkle, Brahms' Lullaby, Mary Had a Little Lamb) — enough to satisfy "and others" without over-engineering. All three are public domain.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| numpy | Buffer concatenation, zero-crossing | ✓ | 2.4.4 | — |
| pytest | Tests | ✓ | 9.0.2 | — |
| libfluidsynth3 | `Synth()` integration tests | Unknown (was missing in Phase 1) | — | Integration tests skip if absent (requires_sf2 marker) |
| fluid-soundfont-gm | Integration tests | Unknown | — | Tests skip if no .sf2 (requires_sf2 marker already in conftest.py) |

**Missing dependencies with no fallback:** None for Phase 2 unit tests.

**Missing dependencies with fallback:**
- `libfluidsynth3` + soundfont: Required only for integration tests; unit tests (preset lookup, sequence structure, zero-crossing logic) pass without it using the `requires_sf2` marker pattern from Phase 1.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` `testpaths = ["tests"]` |
| Quick run command | `uv run pytest tests/test_melody.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MELO-01 | `from_preset("twinkle")` returns ndarray float32 with correct shape | integration (requires .sf2) | `uv run pytest tests/test_melody.py::test_preset_twinkle_returns_buffer -x` | ❌ Wave 0 |
| MELO-01 | `from_preset("brahms")` returns ndarray float32 | integration (requires .sf2) | `uv run pytest tests/test_melody.py::test_preset_brahms_returns_buffer -x` | ❌ Wave 0 |
| MELO-01 | Unknown preset name raises `ValueError` | unit (no .sf2) | `uv run pytest tests/test_melody.py::test_unknown_preset_raises -x` | ❌ Wave 0 |
| MELO-01 | `LULLABY_PRESETS` dict contains at least "twinkle" and "brahms" keys | unit (no .sf2) | `uv run pytest tests/test_melody.py::test_preset_dict_keys -x` | ❌ Wave 0 |
| MELO-02 | `from_notes([("c4", 0.5), ("g4", 0.5)])` returns float32 ndarray | integration (requires .sf2) | `uv run pytest tests/test_melody.py::test_custom_notes_returns_buffer -x` | ❌ Wave 0 |
| MELO-02 | Output buffer dtype is float32, shape is (N,), values in [-1, 1] | integration (requires .sf2) | `uv run pytest tests/test_melody.py::test_buffer_contract -x` | ❌ Wave 0 |
| MELO-02 | Empty note list returns zero-length float32 buffer (no crash) | unit (no .sf2) | `uv run pytest tests/test_melody.py::test_empty_notes -x` | ❌ Wave 0 |
| MELO-03 | `from_procedural()` returns non-empty float32 ndarray | integration (requires .sf2) | `uv run pytest tests/test_melody.py::test_procedural_returns_buffer -x` | ❌ Wave 0 |
| MELO-03 | `generate_circle_of_fifths(seed=42)` returns deterministic sequence | unit (no .sf2) | `uv run pytest tests/test_melody.py::test_procedural_deterministic -x` | ❌ Wave 0 |
| MELO-03 | Generated notes are valid note name strings (parseable by `_note_name_to_midi`) | unit (no .sf2) | `uv run pytest tests/test_melody.py::test_procedural_valid_note_names -x` | ❌ Wave 0 |
| All | Loop boundary: last sample of buffer is near zero (|val| < 0.01 after trim) | integration (requires .sf2) | `uv run pytest tests/test_melody.py::test_loop_boundary_near_zero -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_melody.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_melody.py` — covers all rows above (MELO-01, MELO-02, MELO-03 + loop boundary)
- [ ] `src/musicboxfactory/melody.py` — module does not yet exist

*(No new framework config needed — `pyproject.toml` `testpaths` and `conftest.py` `requires_sf2` marker are already in place from Phase 1.)*

---

## Sources

### Primary (HIGH confidence)

- numpy 2.4.4 (installed, confirmed) — `np.concatenate`, `np.zeros`, `np.sign`, `np.diff`, `np.where`; all patterns verified to work in project venv
- musicboxfactory/synth.py (Phase 1 implementation) — `Synth.render(note, duration) -> ndarray float32`, `SAMPLE_RATE = 44100`; directly readable
- General music theory (circle of fifths, major scale intervals) — static knowledge; confirmed by multiple references; not library-specific

### Secondary (MEDIUM confidence)

- WebSearch result: `np.where(np.sign(a[1:]) != np.sign(a[:-1]))` as zero-crossing detection pattern — confirmed to work in venv
- WebSearch — Twinkle Twinkle note sequence `C C G G A A G F F E E D D C` confirmed by multiple independent sources (glowscotland.org.uk PDF, MuseScore, 8notes.com)
- Brahms Lullaby melody outline — confirmed from 8notes.com, mfiles.co.uk, ViolinSchool.com; exact duration encoding is a project choice

### Tertiary (LOW confidence)

- Specific duration values in preset tables (0.5s per quarter note at ~120 BPM) — chosen by research author based on music box characteristics; should be validated aurally during execution
- `gap_seconds=0.05` default — reasonable estimate; needs empirical tuning against real soundfont

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; numpy confirmed installed
- Architecture: HIGH — sequencer pattern is straightforward numpy; API shape follows Phase 1 conventions exactly
- Preset note tables: HIGH (melody notes) / LOW (exact duration values) — note sequences are public domain and well-documented; durations are implementation choices that need aural validation
- Zero-crossing algorithm: HIGH — numpy sign/diff/where pattern confirmed working in project venv
- Procedural generator: MEDIUM — circle-of-fifths traversal algorithm is correct music theory; the specific Markov weights and octave clamping values need tuning during execution
- Pitfalls: HIGH — all grounded in numpy behavior and Phase 1 Synth API semantics

**Research date:** 2026-03-31
**Valid until:** 2026-09-30 (numpy API is stable; Phase 1 API is fixed; music theory is static)
