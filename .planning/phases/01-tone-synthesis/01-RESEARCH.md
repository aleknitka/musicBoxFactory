# Phase 1: Tone Synthesis - Research

**Researched:** 2026-03-31
**Domain:** FluidSynth soundfont rendering via pyfluidsynth; offline audio buffer extraction; General MIDI patch selection
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01: API Shape**
Stateful `Synth` object — caller constructs with `sf2_path` and `preset`, then calls `synth.render(note, duration)` for each note. Soundfont loads once at construction; render calls are cheap.

**D-02: Audio Buffer Contract**
Buffer format is `numpy.ndarray`, dtype `float32`, shape `(N,)` (mono), sample rate **44100 Hz**. Values in `[-1.0, 1.0]`. `N = int(44100 * duration_seconds)`.

**D-03: Inter-Phase Standard**
This buffer contract is the inter-phase standard — melody (Phase 2), ambient (Phase 3), and mixer (Phase 4) all operate on this buffer type.

**D-04: Note Duration**
Caller-specified duration in seconds: `synth.render('c4', duration=2.0)`. FluidSynth renders note-on then note-off at the boundary. No fixed default; melody pipeline controls note lengths.

**D-05: Preset-to-Patch Mapping**
Hardcoded `PRESETS` dict in library: `{'music_box': 10, 'celesta': 8, 'bells': 14}`. Names map to General MIDI patch numbers (0-indexed). Simple, predictable, no configuration required.

**D-06: Unknown Preset Behavior**
Unknown preset name raises `ValueError` immediately with a clear message listing valid preset names. Fail fast — no silent fallback.

### Claude's Discretion

- Exact MIDI patch numbers for each preset (music_box, celesta, bells) — choose values that produce the warmest, most sleep-appropriate timbre from a standard General MIDI soundfont.
- Whether to expose a `bank` parameter or keep it implicit (bank 0 default).
- FluidSynth initialization details (driver, audio backend settings for offline rendering).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TONE-01 | Caller can render music box tones from a caller-provided `.sf2` soundfont file | pyfluidsynth `Synth` + `sfload()` + `get_samples()` pipeline; offline rendering without calling `start()`; see Architecture Patterns section |
| TONE-02 | Library exposes named instrument presets (`"music_box"`, `"celesta"`, `"bells"`) that map to General MIDI patch numbers in the soundfont | GM patch numbers verified: music_box=10, celesta=8, bells=14 (0-indexed); `program_select(chan, sfid, bank, preset)` API confirmed; see Standard Stack and Code Examples sections |
</phase_requirements>

---

## Summary

Phase 1 delivers `musicboxfactory/synth.py` — a stateful `Synth` class that wraps pyfluidsynth to load a caller-provided `.sf2` soundfont and render individual notes as float32 numpy arrays. The design is locked: `Synth(sf2_path, preset)` at construction, then `synth.render(note, duration)` per note, returning `ndarray(float32, mono, 44100 Hz, [-1, 1])`. This buffer contract is the integration interface for all downstream phases.

The critical technical challenge for this phase is **offline rendering**: pyfluidsynth renders audio by calling `get_samples(len)` in a loop, which returns interleaved stereo int16 arrays. Callers must not invoke `synth.start()` (which would open a live audio driver). Instead, they call `noteon`, advance the synthesizer state with `get_samples`, then call `noteoff` and drain the tail. The resulting int16 stereo buffer must be converted to float32 mono. The FluidSynth C library must be installed on the system (`libfluidsynth3`); pyfluidsynth is the Python ctypes wrapper. The C library is available via `apt` (version 2.3.4) but not currently installed on this machine.

The MIDI patch numbers in D-05 (`music_box: 10, celesta: 8, bells: 14`) are confirmed correct against the General MIDI Level 1 specification (0-indexed program numbers). Bank 0 is the correct GM bank; no bank parameter needs to be exposed to callers. The `render` method maps note names (e.g. `"c4"`) to MIDI note numbers using 12-TET formula, which is the only correct approach — a hardcoded dict is fragile and incorrect.

**Primary recommendation:** Use pyfluidsynth's `get_samples()` loop for offline rendering. Do not call `Synth.start()`. Convert stereo int16 output to float32 mono by reshaping, averaging channels, and dividing by 32768.0.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pyfluidsynth | 1.3.4 | Python ctypes bindings for FluidSynth C library | Only maintained Python wrapper for FluidSynth; required for soundfont rendering per D-01 through D-04 |
| numpy | 2.4.x | Buffer arithmetic — int16→float32 conversion, mono downmix, sample indexing | Universal array foundation; buffer contract (D-02) is a numpy ndarray; no alternative |
| libfluidsynth3 | 2.3.4 (apt) | FluidSynth C shared library — actual soundfont synthesis engine | System dependency; pyfluidsynth is a ctypes wrapper around this C library; must be installed separately from pip |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scipy | 1.17.x | `scipy.io.wavfile.write` for dev/test WAV output (success criterion 4) | Use only for the dev utility that writes a single note to WAV for manual listening verification; not part of the `Synth` public API |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pyfluidsynth + libfluidsynth | Pure additive synthesis (sin * exp decay) | The project explicitly chose soundfont rendering (D-01 through D-04); additive synthesis is out of scope per CONTEXT.md. Do not implement. |
| pyfluidsynth `get_samples()` loop | `midi2audio()` file renderer | `midi2audio` requires a MIDI file on disk; `get_samples()` works fully in-memory. Use `get_samples()`. |
| pyfluidsynth `get_samples()` loop | `Synth.start()` + audio callback | `start()` opens a live audio driver (ALSA/PulseAudio); breaks on headless systems; unnecessary for batch rendering. Do not call `start()`. |

**Installation:**

```bash
# System dependency (must be installed once, not via uv)
sudo apt install libfluidsynth3 libfluidsynth-dev

# Python dependencies via uv
uv add pyfluidsynth numpy

# Dev dependencies
uv add --dev pytest ruff mypy scipy
```

**Version verification (confirmed 2026-03-31):**
- `pyfluidsynth`: 1.3.4 (latest on PyPI)
- `numpy`: 2.4.4 (latest on PyPI, released 2026-03-29)
- `libfluidsynth3`: 2.3.4-1build3 (available via apt on this machine; not yet installed)
- `scipy`: 1.17.1 (latest on PyPI; dev-only)

---

## Architecture Patterns

### Recommended Project Structure

Phase 1 creates the following files. Later phases add more modules; this is the Phase 1 footprint only.

```
src/
└── musicboxfactory/
    ├── __init__.py          # Package init — exports Synth and PRESETS
    └── synth.py             # Synth class — soundfont loading + note rendering
tests/
└── test_synth.py            # Unit tests for Synth (Wave 0 gap — must create)
pyproject.toml               # Add pyfluidsynth, numpy to dependencies
```

The `src/` layout is standard for uv-managed packages and ensures the installed package is used during tests rather than the local directory. CLAUDE.md architecture calls the module `musicboxfactory/synth.py`; that path is under `src/`.

### Pattern 1: Offline Rendering with get_samples()

**What:** Render a note to a buffer without opening a live audio driver. Call `noteon`, collect samples in a loop, call `noteoff`, drain the tail.

**When to use:** Always for batch/file rendering. Never call `Synth.start()` unless live playback is explicitly needed (it is not, per REQUIREMENTS.md).

**Example:**

```python
# Source: pyfluidsynth source (github.com/nwhitehead/pyfluidsynth) + FluidSynth docs
import numpy as np
import fluidsynth

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024  # FluidSynth renders in blocks; this is the conventional chunk size

def _render_note(fs: fluidsynth.Synth, midi_note: int, duration: float) -> np.ndarray:
    """Render a single MIDI note to a float32 mono buffer."""
    n_samples = int(SAMPLE_RATE * duration)

    fs.noteon(0, midi_note, 100)  # channel=0, note, velocity=100

    # Collect samples in blocks
    chunks = []
    collected = 0
    while collected < n_samples:
        block = min(BLOCK_SIZE, n_samples - collected)
        raw = fs.get_samples(block)           # returns int16 stereo: shape (2*block,)
        stereo = raw.reshape(-1, 2)           # shape (block, 2)
        mono = stereo.mean(axis=1)            # downmix to mono
        chunks.append(mono)
        collected += block

    fs.noteoff(0, midi_note)

    # Drain tail (note decay continues after noteoff)
    tail_seconds = 3.0  # conservatively drain up to 3s of decay
    tail_samples = int(SAMPLE_RATE * tail_seconds)
    tail_chunks = []
    drained = 0
    while drained < tail_samples:
        block = min(BLOCK_SIZE, tail_samples - drained)
        raw = fs.get_samples(block)
        stereo = raw.reshape(-1, 2)
        mono = stereo.mean(axis=1)
        tail_chunks.append(mono)
        drained += block

    body = np.concatenate(chunks)
    tail = np.concatenate(tail_chunks)
    full = np.concatenate([body, tail])

    # Truncate to requested duration + tail; normalize int16 to float32 [-1, 1]
    result = full[:n_samples + len(tail)].astype(np.float32) / 32768.0
    return result[:n_samples]  # return only the requested duration
```

**Key facts confirmed from pyfluidsynth source:**
- `get_samples(len)` returns `np.ndarray` of dtype int16, shape `(2 * len,)` — interleaved stereo
- No `start()` call required for `get_samples()` to work
- `program_select(chan, sfid, bank, preset)` selects instrument

### Pattern 2: Synth Construction and Soundfont Loading

**What:** Load a soundfont once at construction; reuse the Synth object for all subsequent `render()` calls.

**When to use:** Always. Loading a soundfont is expensive (~milliseconds to seconds for large sf2 files). Cache it.

```python
# Source: pyfluidsynth source (github.com/nwhitehead/pyfluidsynth)
import fluidsynth
import numpy as np

PRESETS = {'music_box': 10, 'celesta': 8, 'bells': 14}

class Synth:
    def __init__(self, sf2_path: str, preset: str = 'music_box') -> None:
        if preset not in PRESETS:
            raise ValueError(
                f"Unknown preset {preset!r}. Valid presets: {list(PRESETS)}"
            )
        self._preset = preset
        self._patch = PRESETS[preset]

        # No audio driver: do not call self._fs.start()
        self._fs = fluidsynth.Synth(gain=0.5, samplerate=44100)
        self._sfid = self._fs.sfload(sf2_path)
        if self._sfid == -1:
            raise FileNotFoundError(f"Could not load soundfont: {sf2_path}")

        # Select instrument: channel=0, bank=0 (GM bank), patch=PRESETS[preset]
        self._fs.program_select(0, self._sfid, 0, self._patch)

    def render(self, note: str, duration: float) -> np.ndarray:
        """Render a named note to a float32 mono buffer at 44100 Hz."""
        midi_note = _note_name_to_midi(note)
        return _render_note(self._fs, midi_note, duration)
```

### Pattern 3: Note Name to MIDI Number Conversion

**What:** Convert note names like `"c4"`, `"g#3"`, `"bb5"` to MIDI note numbers using 12-TET math.

**When to use:** Inside `render()`. Do not hard-code a dict of note → MIDI number; use the formula.

```python
# 12-TET formula: MIDI 69 = A4 = 440 Hz
# Note names: c, d, e, f, g, a, b with optional # or b suffix, followed by octave number

_PITCH_CLASS = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}

def _note_name_to_midi(note: str) -> int:
    """Convert note name string to MIDI note number.

    Supports: 'c4', 'g#3', 'bb5', 'f#2' etc.
    Middle C (c4) = MIDI 60.
    """
    note = note.strip().lower()
    if len(note) < 2:
        raise ValueError(f"Invalid note: {note!r}")

    # Parse accidental
    if note[1] in ('#', 'b') and len(note) >= 3:
        pitch_name = note[0]
        accidental = 1 if note[1] == '#' else -1
        octave = int(note[2:])
    else:
        pitch_name = note[0]
        accidental = 0
        octave = int(note[1:])

    pitch_class = _PITCH_CLASS[pitch_name] + accidental
    return (octave + 1) * 12 + pitch_class  # MIDI 60 = C4 = (4+1)*12 + 0
```

**Verification:** C4 → (4+1)*12 + 0 = 60. A4 → (4+1)*12 + 9 = 69. Both are correct per MIDI standard.

### Anti-Patterns to Avoid

- **Calling `Synth.start()`:** Opens a live ALSA/PulseAudio audio driver. Will fail on headless CI machines. Not needed for batch rendering with `get_samples()`. Never call it.
- **Hard-coding a note-name dict:** Fragile, verbose, and error-prone. Use the 12-TET formula above.
- **Closing the FluidSynth object between render calls:** Defeats the soundfont caching purpose of D-01. Keep one `Synth` instance and reuse it.
- **Not draining the note tail after `noteoff`:** FluidSynth continues rendering the note decay after `noteoff`. If you stop collecting samples immediately after `noteoff`, the buffer will be abruptly silent mid-decay — the hallmark symptom is notes that sound cut off.
- **Returning the full render+tail buffer:** The `render()` method contract (D-02, D-04) is `N = int(44100 * duration_seconds)`. Callers expect exactly that many samples. Truncate to `N` after collecting the decay tail.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Soundfont sample rendering | Custom SF2 parser + sample interpolation | pyfluidsynth + libfluidsynth | SF2 format has complex modulator routing, envelope generators, sample interpolation, and tuning. FluidSynth is a full reference implementation. Hand-rolling SF2 rendering is months of work. |
| MIDI note scheduling | Custom MIDI sequencer | `fluidsynth.Synth.noteon()` / `noteoff()` directly | pyfluidsynth exposes direct note control at the sample level; no scheduler needed for single-note rendering |
| Audio driver management | Custom ALSA/PulseAudio binding | Don't start a driver at all — use `get_samples()` offline | Offline rendering needs no audio driver; the C library renders internally and returns samples on demand |

**Key insight:** The entire SF2 rendering domain — sample playback, envelope ADSR, tuning, LFO modulation — is handled by the C library. Python only needs to invoke `noteon`, collect blocks via `get_samples`, then `noteoff`. Do not try to recreate any of this.

---

## Common Pitfalls

### Pitfall 1: Note Tail Abruptly Cut Off

**What goes wrong:** The note sounds like it ends abruptly mid-decay. Caller hears a clipped tone rather than a natural ring-out.

**Why it happens:** After `noteoff`, FluidSynth continues rendering the note's release/decay phase internally. Stopping `get_samples()` collection immediately after calling `noteoff` cuts the buffer before the decay completes.

**How to avoid:** After `noteoff`, continue collecting samples for up to `tail_duration` seconds (3.0s is conservative; music box tines can ring for 2-4 seconds). Then truncate the final buffer to the requested `duration` using array slicing. See Pattern 1 code above.

**Warning signs:** Individual notes sound clipped when `duration` is shorter than the natural decay time (e.g. `render('c4', 0.5)` sounds cut off but `render('c4', 4.0)` sounds fine).

### Pitfall 2: Interleaved Stereo int16 Not Converted Correctly

**What goes wrong:** `get_samples(1024)` returns an array of shape `(2048,)` — interleaved L/R int16 samples. Treating it as `(1024,)` float32 mono without reshaping produces audio that plays at double speed with alternating channels as amplitude values.

**Why it happens:** pyfluidsynth returns stereo interleaved by default. The `2 * len` return size is documented but easy to miss.

**How to avoid:** Always reshape: `stereo = raw.reshape(-1, 2)`, then `mono = stereo.mean(axis=1)`. Then convert: `mono.astype(np.float32) / 32768.0`.

**Warning signs:** Rendered buffer plays back at double speed or sounds like noise with the wrong pitch.

### Pitfall 3: Calling `Synth.start()` Crashes on Headless Systems

**What goes wrong:** `fluidsynth.Synth.start()` attempts to open an ALSA (Linux) or CoreAudio (macOS) audio device. In CI environments, Docker containers, or WSL without audio, this raises an exception or silently fails, making the library untestable in automation.

**Why it happens:** Developers copy examples from pyfluidsynth README that show `start()` for live playback — those examples are for interactive use.

**How to avoid:** Never call `start()`. Call only `sfload()`, `program_select()`, `noteon()`, `get_samples()`, `noteoff()`. The offline rendering path works without any audio driver.

**Warning signs:** `fluidsynth: error: Couldn't open the device: default` error on test runs. Tests pass locally but fail in CI.

### Pitfall 4: FluidSynth C Library Not Installed

**What goes wrong:** `import fluidsynth` succeeds (pyfluidsynth is pure Python + ctypes), but the first call to `Synth()` raises `OSError: FluidSynth library not found`. The Python package and the C library are separate installation steps.

**Why it happens:** `pip install pyfluidsynth` installs the Python bindings but NOT `libfluidsynth.so`. The C library must be installed via the system package manager.

**How to avoid:** Document install order clearly. `sudo apt install libfluidsynth3` must precede `uv add pyfluidsynth`. Add a graceful `ImportError` or `OSError` in `synth.py` that tells callers exactly what is missing and how to install it.

**Warning signs:** `OSError: FluidSynth library not found` or `libfluidsynth.so.3: cannot open shared object file` on first `Synth()` instantiation.

### Pitfall 5: Wrong MIDI Patch Number Indexing

**What goes wrong:** FluidSynth `program_select` uses 0-indexed program numbers. The GM specification lists patch numbers 1-128. Using 1-indexed values (e.g. passing `11` for Music Box instead of `10`) selects the wrong instrument — Music Box becomes Vibraphone.

**Why it happens:** GM documentation shows patch numbers starting at 1. Code uses the documented number without subtracting 1.

**How to avoid:** The hardcoded PRESETS dict (D-05) already uses 0-indexed values: `{'music_box': 10, 'celesta': 8, 'bells': 14}`. These are confirmed correct. Do not add 1. Document this in the PRESETS dict comment.

**Verification:** music_box=10 (GM program 11), celesta=8 (GM program 9), bells=14 (GM program 15 = Tubular Bells). All confirmed against General MIDI Level 1 specification.

---

## Code Examples

### Full Synth Class Skeleton

```python
# Source: pyfluidsynth 1.3.4 source + GM Level 1 specification
# File: src/musicboxfactory/synth.py

from __future__ import annotations
import numpy as np
import fluidsynth

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024

# 0-indexed General MIDI program numbers
PRESETS: dict[str, int] = {
    'music_box': 10,   # GM program 11: Music Box
    'celesta': 8,      # GM program 9: Celesta
    'bells': 14,       # GM program 15: Tubular Bells
}

_PITCH_CLASS = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}


def _note_name_to_midi(note: str) -> int:
    note = note.strip().lower()
    if note[1] in ('#', 'b') and len(note) >= 3:
        pc = _PITCH_CLASS[note[0]] + (1 if note[1] == '#' else -1)
        octave = int(note[2:])
    else:
        pc = _PITCH_CLASS[note[0]]
        octave = int(note[1:])
    return (octave + 1) * 12 + pc  # C4 = 60


class Synth:
    def __init__(self, sf2_path: str, preset: str = 'music_box') -> None:
        if preset not in PRESETS:
            raise ValueError(
                f"Unknown preset {preset!r}. Valid presets: {list(PRESETS)}"
            )
        self._fs = fluidsynth.Synth(gain=0.5, samplerate=SAMPLE_RATE)
        # Do NOT call self._fs.start() — offline rendering only
        self._sfid = self._fs.sfload(sf2_path)
        if self._sfid == -1:
            raise FileNotFoundError(f"Could not load soundfont: {sf2_path!r}")
        self._fs.program_select(0, self._sfid, 0, PRESETS[preset])

    def render(self, note: str, duration: float) -> np.ndarray:
        """Render a named note to a float32 mono buffer.

        Returns: ndarray, dtype=float32, shape=(N,) where N=int(44100*duration),
                 values in [-1.0, 1.0].
        """
        midi_note = _note_name_to_midi(note)
        n_samples = int(SAMPLE_RATE * duration)
        tail_samples = int(SAMPLE_RATE * 3.0)  # drain up to 3s of natural decay

        self._fs.noteon(0, midi_note, 100)
        body = self._collect_samples(n_samples)
        self._fs.noteoff(0, midi_note)
        _ = self._collect_samples(tail_samples)  # drain decay tail

        return body  # already truncated to n_samples, dtype float32

    def _collect_samples(self, n_samples: int) -> np.ndarray:
        chunks = []
        collected = 0
        while collected < n_samples:
            block = min(BLOCK_SIZE, n_samples - collected)
            raw = self._fs.get_samples(block)        # int16, shape (2*block,)
            stereo = raw.reshape(-1, 2)              # shape (block, 2)
            mono = stereo.mean(axis=1)               # shape (block,)
            chunks.append(mono.astype(np.float32) / 32768.0)
            collected += block
        return np.concatenate(chunks)[:n_samples]
```

### Dev/Test WAV Writer (Success Criterion 4)

```python
# Source: scipy.io.wavfile docs (not part of public API — dev utility only)
import scipy.io.wavfile
import numpy as np

def write_test_wav(buffer: np.ndarray, path: str, sample_rate: int = 44100) -> None:
    """Write a float32 buffer to WAV for manual listening verification."""
    pcm = (buffer * 32767).astype(np.int16)
    scipy.io.wavfile.write(path, sample_rate, pcm)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pure additive synthesis (sin * exp) | Soundfont rendering via FluidSynth | Project decision (CONTEXT.md) | Richer, configurable timbre with no DSP math in library code |
| `fluidsynth.Synth.start()` + live playback | Offline `get_samples()` loop, no driver | pyfluidsynth design | Works on headless systems, CI, WSL; no audio hardware needed |
| 1-indexed GM patch numbers | 0-indexed program numbers in `program_select()` | FluidSynth API design (always) | Off-by-one error source; confirmed: use 0-indexed values |

**Deprecated/outdated:**
- Pure Python sin/exp synthesis for music box: Still works but is out of scope for this project. FluidSynth path is the locked decision.

---

## Open Questions

1. **Optimal FluidSynth gain setting**
   - What we know: `Synth(gain=0.5)` is a reasonable default; gain controls output amplitude scaling before `get_samples()`
   - What's unclear: The gain value that maximizes dynamic range without clipping for typical GM soundfonts — depends on the soundfont itself
   - Recommendation: Default gain=0.5; normalize the output buffer to [-1, 1] after collection (`buf /= max(abs(buf.max()), 1e-9)`) to guarantee the buffer contract regardless of gain

2. **Caller provides .sf2 path — no bundled soundfont**
   - What we know: OUT-OF-SCOPE per REQUIREMENTS.md; caller is responsible
   - What's unclear: Tests need a real `.sf2` to exercise `Synth`; the test suite must either mark FluidSynth tests as requiring an external file or use a freely licensed minimal soundfont
   - Recommendation: Mark integration tests with `@pytest.mark.skipif(not os.path.exists(SF2_PATH), reason="no soundfont")` and document `fluid-soundfont-gm` (available via apt) as the recommended test soundfont

3. **Inharmonic partial ratios for music box tines**
   - What we know: This phase uses soundfont rendering — inharmonic partials come from the soundfont's sample data, not from synthesis code. This is NOT a Phase 1 concern.
   - What's unclear: Nothing — the soundfont provides the timbre; Phase 1 code does not synthesize partials
   - Recommendation: No action needed in Phase 1

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | Runtime | ✗ | 3.12.3 (system) | uv manages Python version via `.python-version` file |
| uv | Dependency mgmt | ✓ | 0.11.1 | — |
| libfluidsynth3 | `fluidsynth.Synth()` | ✗ (not installed) | 2.3.4 (apt-available) | No fallback — must install |
| pyfluidsynth | `import fluidsynth` | ✗ (not installed) | 1.3.4 (PyPI) | No fallback — must install |
| numpy | Buffer contract | ✗ (not in venv) | 2.4.4 (PyPI) | No fallback — must install |
| scipy | Dev WAV writer | ✗ (not in venv) | 1.17.1 (PyPI) | No fallback for dev utility |
| fluid-soundfont-gm | Integration tests | ✗ (not installed) | 3.1-5.3 (apt-available) | Tests skip if no .sf2 available |

**Missing dependencies with no fallback:**
- `libfluidsynth3` — required for any `Synth()` instantiation; install with `sudo apt install libfluidsynth3`
- `pyfluidsynth` — required for `import fluidsynth`; install with `uv add pyfluidsynth`
- `numpy` — required for buffer operations; install with `uv add numpy`

**Missing dependencies with fallback:**
- Python 3.13: uv will download and manage it automatically if `.python-version` contains `3.13`; the system Python 3.12.3 is not used by uv projects
- `fluid-soundfont-gm` soundfont: Integration tests can be skipped; unit tests for note-name conversion and buffer contracts do not require a soundfont

**Wave 0 must include:** `sudo apt install libfluidsynth3` as a prerequisite step before any Python code runs.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (to be installed as dev dependency) |
| Config file | None — Wave 0 adds `[tool.pytest.ini_options]` to `pyproject.toml` |
| Quick run command | `uv run pytest tests/test_synth.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TONE-01 | `Synth(sf2_path, preset)` loads soundfont; `render(note, duration)` returns ndarray float32 mono 44100 Hz shape `(N,)` where `N = int(44100 * duration)` | integration (requires .sf2) | `uv run pytest tests/test_synth.py::test_render_returns_correct_shape -x` | Wave 0 |
| TONE-01 | Buffer values are within `[-1.0, 1.0]` | integration (requires .sf2) | `uv run pytest tests/test_synth.py::test_render_buffer_range -x` | Wave 0 |
| TONE-01 | `FileNotFoundError` raised for missing sf2 path | unit (no .sf2 needed) | `uv run pytest tests/test_synth.py::test_missing_sf2_raises -x` | Wave 0 |
| TONE-02 | `ValueError` raised for unknown preset name | unit (no .sf2 needed) | `uv run pytest tests/test_synth.py::test_unknown_preset_raises -x` | Wave 0 |
| TONE-02 | All three named presets (`music_box`, `celesta`, `bells`) are in `PRESETS` dict with correct 0-indexed GM patch numbers | unit | `uv run pytest tests/test_synth.py::test_preset_patch_numbers -x` | Wave 0 |
| TONE-01 | Note name to MIDI conversion: C4=60, A4=69, G#3=56, Bb5=82 | unit | `uv run pytest tests/test_synth.py::test_note_name_to_midi -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_synth.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/__init__.py` — empty; marks tests as a package
- [ ] `tests/test_synth.py` — covers TONE-01 and TONE-02 (all rows above)
- [ ] `src/musicboxfactory/__init__.py` — package init
- [ ] `pyproject.toml` update: add pytest, ruff, mypy dev deps; add `[tool.pytest.ini_options]` with `testpaths = ["tests"]`
- [ ] Framework install: `uv add --dev pytest ruff mypy` and `uv add pyfluidsynth numpy`
- [ ] System install: `sudo apt install libfluidsynth3` — prerequisite before any test can import fluidsynth

---

## Project Constraints (from CLAUDE.md)

All directives from `./CLAUDE.md` that the planner must enforce:

| Directive | Type | Enforcement |
|-----------|------|-------------|
| Python >=3.13 | Required | `requires-python = ">=3.13"` in pyproject.toml; uv manages version |
| `uv` for dependency management | Required | All installs via `uv add`; no `pip install` |
| Test command: `uv run pytest` | Required | Tests run with `uv run pytest`, not `python -m pytest` |
| Type check: `uv run mypy src/` | Required | mypy must pass on synth.py |
| Lint: `uv run ruff check src/` | Required | ruff must pass on synth.py |
| Module path: `musicboxfactory/synth.py` | Required | File lives at `src/musicboxfactory/synth.py` |
| `Synth` class with `PRESETS` dict | Required | Locked by CLAUDE.md architecture description |
| `ValueError` for unknown preset | Required | Locked by CLAUDE.md architecture description |
| Buffer contract: float32, mono, 44100 Hz, `[-1, 1]` | Required | All buffers must match; verified by tests |
| No CLI | Forbidden | Phase 1 has no entrypoint or `__main__` |
| No audio playback | Forbidden | No `sounddevice`, `pyaudio`, `pygame`; no `Synth.start()` |
| No MP3/OGG | Forbidden | Dev WAV writer uses `scipy.io.wavfile` only |
| numpy 2.x | Required | Pin `numpy>=2.0` in pyproject.toml |
| scipy for WAV output | Required | `scipy.io.wavfile.write` is the standard; no `wave` module |

---

## Sources

### Primary (HIGH confidence)

- pyfluidsynth 1.3.4 source (github.com/nwhitehead/pyfluidsynth) — `get_samples()` return type, `program_select()` signature, offline rendering pattern, `Synth.__init__` signature
- General MIDI Level 1 specification via soundprogramming.net — patch numbers verified: music_box=10, celesta=8, bells=14 (0-indexed)
- PyPI pyfluidsynth — confirmed version 1.3.4 as current
- PyPI numpy — confirmed version 2.4.4 (released 2026-03-29)
- PyPI scipy — confirmed version 1.17.1
- apt package libfluidsynth3 — confirmed version 2.3.4-1build3 available on this machine

### Secondary (MEDIUM confidence)

- pyfluidsynth GitHub README offline rendering note — confirms no `start()` needed for `get_samples()`
- General MIDI Wikipedia article — confirms patch numbering and GM Level 1 instrument list

### Tertiary (LOW confidence)

- None — all critical claims are verified against primary sources

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pyfluidsynth version and API confirmed from source; GM patch numbers confirmed from spec
- Architecture: HIGH — pyfluidsynth `get_samples()` loop pattern confirmed from source; Synth class shape locked by CONTEXT.md
- Pitfalls: HIGH — all pitfalls verified against documented pyfluidsynth behavior and FluidSynth C library semantics
- Environment: HIGH — direct machine probes performed (apt, pip3, command -v)

**Research date:** 2026-03-31
**Valid until:** 2026-09-30 (pyfluidsynth is stable; FluidSynth C library is stable; GM spec is static)
