# Architecture Research

**Domain:** Python audio synthesis library (music box tones + ambient noise, WAV output)
**Researched:** 2026-03-30
**Confidence:** HIGH (core signal pipeline patterns), MEDIUM (loopability details)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Public API Layer                          │
│   generate(melody, ambient, duration, ...)  → WAV bytes/path    │
│   Preset registry (TWINKLE_TWINKLE, BRAHMS, ...)                │
└────────────────────────────┬────────────────────────────────────┘
                             │
             ┌───────────────┴───────────────┐
             ↓                               ↓
┌────────────────────────┐     ┌─────────────────────────────┐
│   Melody Layer         │     │   Ambient Layer             │
│                        │     │                             │
│  ┌──────────────────┐  │     │  ┌──────────────────────┐  │
│  │  NoteSequencer   │  │     │  │  NoiseGenerator       │  │
│  │  (note → freq,   │  │     │  │  (white/pink/brown)   │  │
│  │   duration)      │  │     │  └──────────┬───────────┘  │
│  └────────┬─────────┘  │     │             │               │
│           ↓            │     │  ┌──────────┴───────────┐  │
│  ┌──────────────────┐  │     │  │  AmbientShaper        │  │
│  │  ToneSynthesizer │  │     │  │  (heartbeat pulse,    │  │
│  │  (decaying sine  │  │     │  │   spectral shaping)   │  │
│  │   + envelope)    │  │     │  └──────────────────────┘  │
│  └────────┬─────────┘  │     └──────────────┬──────────────┘
└───────────┼────────────┘                    │
            └──────────────┬──────────────────┘
                           ↓
            ┌─────────────────────────────┐
            │       Mixer                 │
            │  (volume balance, summing,  │
            │   normalization)            │
            └──────────────┬──────────────┘
                           ↓
            ┌─────────────────────────────┐
            │       LoopRenderer          │
            │  (repeat to duration,       │
            │   seamless loop endpoints)  │
            └──────────────┬──────────────┘
                           ↓
            ┌─────────────────────────────┐
            │       WAVWriter             │
            │  (float→int16, wave module) │
            └─────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Public API | Entry point — accepts user parameters, returns WAV | Module-level functions; no classes required at call site |
| Preset Registry | Stores named note sequences as plain data | Dict mapping preset name → list of `(note_str, duration)` tuples |
| NoteSequencer | Resolves note names to Hz frequencies; assigns sample counts per note | Pure function; 12-TET formula `f = 440 * 2^((n-69)/12)` |
| ToneSynthesizer | Generates one decaying sinusoidal tone per note | numpy: `sin * exp(-decay_rate * t)` with short linear attack |
| NoiseGenerator | Generates white/pink/brown noise buffers | FFT spectral shaping in frequency domain; `np.fft.irfft` |
| AmbientShaper | Applies character to noise (heartbeat rhythm, low-pass for womb) | Low-frequency sinusoidal AM envelope (~1 Hz) for heartbeat pulse |
| Mixer | Sums melody + ambient arrays; scales by volume weights; normalizes | Element-wise `numpy` operations; peak normalization to prevent clipping |
| LoopRenderer | Tiles or fades audio to target duration; ensures clean loop endpoints | Repeat + crossfade tail-to-head using `np.linspace` fade |
| WAVWriter | Converts float32 `[-1, 1]` → int16; writes stdlib `wave` file | `(arr * 32767).astype(np.int16)` then `wave.open().writeframes()` |

## Recommended Project Structure

```
src/
└── musicboxfactory/
    ├── __init__.py          # Public API: generate(), list_presets(), list_ambients()
    ├── presets.py           # Named note sequences (lullaby data as plain tuples)
    ├── notes.py             # Note-name → Hz conversion; duration → sample count
    ├── tone.py              # ToneSynthesizer: decaying sine + envelope per note
    ├── noise.py             # NoiseGenerator: white / pink / brown via FFT shaping
    ├── ambient.py           # AmbientShaper: noise → ambient character (womb, heartbeat, fan)
    ├── mixer.py             # Mix melody array + ambient array; normalize
    ├── loop.py              # Tile + crossfade to target duration; loop endpoint fix
    └── wav.py               # Write float buffer → WAV file via stdlib wave
```

### Structure Rationale

- **`__init__.py`:** Exposes `generate()` as the single entry point; imports from all modules. Users never need to touch internals.
- **`presets.py`:** Data-only module — easy to extend without touching synthesis logic.
- **`notes.py`:** Isolated frequency math keeps it testable and reusable in both melody and any future MIDI-adjacent use.
- **`tone.py` / `noise.py` / `ambient.py`:** Signal generators are separate so they can be tested with known inputs and outputs independently.
- **`mixer.py` / `loop.py` / `wav.py`:** Post-generation pipeline steps — each takes a numpy array and returns a numpy array (except `wav.py` which writes to disk). This keeps the pipeline composable.

## Architectural Patterns

### Pattern 1: Numpy Buffer Pipeline

**What:** Every component except the WAV writer operates on `numpy` float32 arrays in the range `[-1.0, 1.0]`. Components are plain functions: `generate_tone(freq, duration_samples, sr) → np.ndarray`. No streaming, no generators, no callbacks.

**When to use:** Always, for this scope. The output is finite-length WAV files, not a real-time audio stream. Batch buffer processing is simpler, easier to test, and sufficient for files up to tens of minutes.

**Trade-offs:** Holds the entire rendered buffer in RAM. At 44100 Hz × float32 × 60 seconds ≈ 10 MB — completely acceptable. Streaming would add complexity with zero benefit for this use case.

```python
# Example: every stage is a pure function returning ndarray
def synthesize_melody(notes: list[tuple], sample_rate: int) -> np.ndarray:
    buffers = [synthesize_tone(freq, n_samples, sample_rate) for freq, n_samples in notes]
    return np.concatenate(buffers)
```

### Pattern 2: Frequency-Domain Noise Shaping

**What:** Colored noise (pink, brown) is generated in the frequency domain: generate white noise, take FFT, multiply each bin by a spectral weight (`1/sqrt(f)` for pink, `1/f` for brown), apply inverse FFT.

**When to use:** For any noise color other than white. The FFT approach is clean and requires no IIR filter design — it produces the exact target spectral shape.

**Trade-offs:** Requires generating the full buffer length at once (fine for our use case). The alternative — IIR filtering of white noise — requires scipy.signal and careful filter design, which adds a dependency and complexity.

```python
def pink_noise(n_samples: int, sample_rate: int) -> np.ndarray:
    white = np.random.randn(n_samples)
    freqs = np.fft.rfftfreq(n_samples, d=1/sample_rate)
    freqs[0] = 1  # avoid divide-by-zero at DC
    spectrum = np.fft.rfft(white) / np.sqrt(freqs)
    return np.fft.irfft(spectrum, n=n_samples)
```

### Pattern 3: Decaying Sinusoid Tone Model

**What:** Each music box note is modeled as a sine wave at the note's frequency multiplied by an amplitude envelope: a short linear attack (≈2–5 ms) followed by an exponential decay. This captures the "plucked tine" character without Karplus-Strong complexity.

**When to use:** Preferred over Karplus-Strong for music box synthesis. The KS algorithm is better for guitar-like timbres; music box tines have a cleaner sinusoidal spectrum.

**Trade-offs:** Can add harmonic partials (2nd, 3rd harmonic at lower amplitudes) for more realistic tone. Start with single fundamental; harmonic stacking is an additive enhancement with no architectural change.

```python
def synthesize_tone(freq: float, n_samples: int, sample_rate: int,
                    decay_rate: float = 8.0, attack_samples: int = 100) -> np.ndarray:
    t = np.arange(n_samples) / sample_rate
    envelope = np.exp(-decay_rate * t)
    envelope[:attack_samples] *= np.linspace(0, 1, attack_samples)
    return np.sin(2 * np.pi * freq * t) * envelope
```

## Data Flow

### Primary Generation Flow

```
User call: generate(preset="TWINKLE", ambient="pink", duration=60, melody_vol=0.6)
    │
    ▼
presets.py       → note sequence: [("c4", 4), ("c4", 4), ("g4", 4), ...]
    │
    ▼
notes.py         → (freq_hz, n_samples) pairs: [(261.63, 11025), ...]
    │
    ▼
tone.py          → melody_buffer: np.ndarray, shape (total_note_samples,)
    │                              dtype float32, range [-1, 1]
    ▼
noise.py         → raw_noise: np.ndarray, shape (duration_samples,)
    │
    ▼
ambient.py       → ambient_buffer: np.ndarray, same shape, spectrally shaped
    │
    ├── melody_buffer ──────────────────────────────┐
    ▼                                               ▼
loop.py          → melody_looped: tiled + crossfaded to duration_samples
    │
    ▼
mixer.py         → mixed: melody_vol * melody_looped + (1-melody_vol) * ambient_buffer
                →  normalized to [-1, 1] peak
    │
    ▼
wav.py           → writes int16 PCM to file; returns output path
```

### Key Data Contracts

1. **Note sequence format:** `list[tuple[str, int]]` — note name string (`"c4"`, `"g#3"`, `"r"` for rest) and duration denominator (4 = quarter, 8 = eighth). This mirrors PySynth conventions and is easy to write by hand.
2. **Audio buffer contract:** All internal buffers are `np.ndarray` of `float32` in `[-1.0, 1.0]`. Normalization happens in the mixer before WAV writing.
3. **Sample rate:** Single constant (`SAMPLE_RATE = 44100`) defined once, passed through or imported everywhere.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single file, short (≤5 min) | Current design is ideal — in-memory buffer, no streaming needed |
| Long files (30–60 min) | Loop a short master segment rather than generating full duration in memory; no architecture change needed |
| Batch generation (many files) | Public API is already stateless; trivial to parallelize with `concurrent.futures` |
| Adding new ambient types | Add a function to `ambient.py` and register it in a dict; no other changes |
| Adding new presets | Add a tuple to `presets.py`; zero architecture impact |

### Scaling Priorities

1. **First bottleneck (if any):** Memory usage for very long durations. Mitigation: generate one loop cycle (melody length), tile it via `np.tile` or by writing repeat frames — avoids holding 60-minute buffer. Can be implemented in `loop.py` transparently.
2. **Second bottleneck:** Noise generation for brown noise via FFT scales as O(n log n) — fine for our use, but if generation time matters, swap to a cumulative-sum method for brown noise (`np.cumsum(white_noise)`) which is O(n).

## Anti-Patterns

### Anti-Pattern 1: Interleaving Synthesis and I/O

**What people do:** Write samples directly to a WAV file frame-by-frame as they synthesize each note.

**Why it's wrong:** Makes it impossible to apply cross-buffer operations (normalization, mixing, crossfade loop points). Each operation needs the full buffer.

**Do this instead:** Synthesize everything into numpy arrays first; write to WAV as the final step only.

### Anti-Pattern 2: Reinventing Note-to-Frequency Mapping as a Giant Dict

**What people do:** Hard-code a dictionary mapping `"c4" → 261.63`, `"d4" → 293.66`, etc.

**Why it's wrong:** Fragile, error-prone, and verbose. There is a precise formula.

**Do this instead:** Use 12-TET math: `freq = 440.0 * (2 ** ((midi_note - 69) / 12))` where MIDI note is derived from the note name. Map note names to MIDI numbers with a small lookup for the 12 pitch classes; compute all octaves mathematically.

### Anti-Pattern 3: Shared Mutable State Between Components

**What people do:** Use a class with global `self.sample_rate`, `self.buffer`, etc. that all methods modify in place.

**Why it's wrong:** Breaks testability and makes the call order matter. For a generation library, pure functions are always preferable.

**Do this instead:** Pass `sample_rate` as a parameter. Have each function return a new array. The public `generate()` function is the only stateful coordinator.

### Anti-Pattern 4: Using a Large Audio Framework

**What people do:** Pull in `pydub`, `librosa`, or `sounddevice` "to make it easier."

**Why it's wrong:** These libraries add heavyweight dependencies (ffmpeg binaries, heavy C extensions) inappropriate for a minimal synthesis library. `librosa` alone pulls in `scipy`, `scikit-learn`, `numba`, etc.

**Do this instead:** `numpy` for signal generation + `wave` (stdlib) for WAV output. Zero non-numpy dependencies for the core pipeline.

## Integration Points

### External Services

None. This library is fully self-contained with no network calls.

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Public API → all modules | Direct function calls | `__init__.py` orchestrates; modules do not call each other |
| `presets.py` → `notes.py` | Data (list of tuples) | Presets are pure data; `notes.py` does the frequency math |
| `tone.py` → `mixer.py` | numpy array (melody buffer) | No shared state |
| `noise.py` → `ambient.py` | numpy array (raw noise) | `ambient.py` shapes the noise from `noise.py` |
| `ambient.py` + `loop.py` → `mixer.py` | numpy arrays | Mixer receives two same-length arrays |
| `mixer.py` → `wav.py` | numpy float32 array | WAV writer is the only component that touches the filesystem |

## Suggested Build Order

Build order is determined by the data flow dependencies above. Each phase produces a tested, independently useful artifact.

1. **`notes.py`** — No dependencies. Pure math. Immediately testable.
2. **`tone.py`** — Depends only on numpy. Can generate a single tone WAV to verify timbre.
3. **`wav.py`** — Depends only on stdlib `wave`. Write a test buffer to disk.
4. **`presets.py`** — Pure data. Define the note tuple format and add first lullaby.
5. **`noise.py`** — Depends only on numpy. Generate and listen to each noise color.
6. **`ambient.py`** — Depends on `noise.py`. Apply heartbeat envelope; verify with ears.
7. **`loop.py`** — Depends on numpy. Test seamless loop with a simple melody buffer.
8. **`mixer.py`** — Depends on all generator components. Test stereo mix + normalization.
9. **`__init__.py`** — Wires all components. Integration test: full `generate()` call.

## Sources

- [Sound Synthesis in Python — Noah Hradek (Medium)](https://medium.com/@noahhradek/sound-synthesis-in-python-4e60614010da) — MEDIUM confidence (unverified author credentials; pattern is sound)
- [Wavetable Synth in Python Tutorial — WolfSound](https://thewolfsound.com/sound-synthesis/wavetable-synth-in-python/) — MEDIUM confidence
- [python-acoustics noise generator module (GitHub)](https://github.com/python-acoustics/python-acoustics/blob/master/acoustics/generator.py) — HIGH confidence (inspected source)
- [PySynth note sequence format (GitHub)](https://github.com/mdoege/PySynth) — HIGH confidence (widely used reference implementation)
- [Generate Audio with Python — Zach Denton](https://zach.se/generate-audio-with-python/) — MEDIUM confidence
- [colorednoise PyPI package](https://pypi.org/project/colorednoise/) — HIGH confidence (established library, confirms FFT approach)
- [Generating white, pink, brown noise — smrati katiyar (Medium)](https://medium.com/@smrati.katiyar/generating-white-ping-brown-blue-noise-using-python-and-save-in-a-audio-file-2db47220cf8e) — LOW confidence (unverified; cross-checked with python-acoustics source)
- [DSP Related: Generating pink noise — Allen Downey](https://www.dsprelated.com/showarticle/908.php) — HIGH confidence (known DSP author)

---
*Architecture research for: Python audio synthesis library (musicboxfactory)*
*Researched: 2026-03-30*
