# Project Research Summary

**Project:** musicboxfactory
**Domain:** Pure-Python audio synthesis library — music box melody tones + ambient sleep noise, WAV output
**Researched:** 2026-03-30
**Confidence:** HIGH

## Executive Summary

musicboxfactory is a greenfield Python library that synthesizes music-box-style lullaby melodies and ambient sleep sounds (white, pink, brown, womb/heartbeat noise), mixes them, and writes loopable WAV files. This is not a general-purpose audio framework — it is a narrow, focused generation library. The expert approach is a pure NumPy buffer pipeline: every component operates on float32 arrays in [-1.0, 1.0] and passes them downstream as plain function return values. The only external runtime dependencies needed are NumPy (2.x) and SciPy (for WAV output); all synthesis math is elementary array operations, not DSP frameworks. The architecture is flat and composable: eight small modules, each independently testable, wired together by a single public `generate()` entry point.

The recommended build is: Python 3.13, NumPy 2.4, SciPy 1.17, managed with uv, tested with pytest. Tone synthesis uses additive sinusoids with inharmonic partials (not Karplus-Strong, which introduces tuning error at high frequencies). Noise is generated via FFT spectral shaping in a single pass. WAV output uses `scipy.io.wavfile.write` (safer than the stdlib `wave` module). The library occupies a clear gap: consumer baby sleep apps use pre-recorded samples; existing Python audio libraries ignore sleep-specific timbre. This library synthesizes both from scratch with no system dependencies.

The two highest-risk areas are audio quality correctness and seamless loop integrity. A music box tone without inharmonic partials sounds like a test signal, not an instrument. A WAV that doesn't return cleanly to zero at its boundary produces an audible click on every loop repetition — disqualifying for sleep audio played overnight. Both must be addressed in the first implementation pass, not patched later. Secondary risk is silent int16 overflow when mixing layers: NumPy does not warn, it just produces extreme distortion. Normalization before WAV conversion is mandatory and must be covered by a unit test.

---

## Key Findings

### Recommended Stack

The stack is minimal by design. NumPy 2.4 is the single correct foundation — every synthesis operation (sinusoid generation, FFT noise shaping, envelope application, mixing, normalization) is a vectorized array operation. SciPy 1.17 is included for `scipy.io.wavfile.write`, which accepts NumPy arrays directly and handles WAV headers correctly — it is strictly safer than the stdlib `wave` module. Both are stable, actively maintained, and compatible with Python 3.13. No other runtime dependencies are required. The `colorednoise` package (PyPI) is an optional alternative for noise generation but can be replaced with 30 lines of NumPy FFT math; vendoring is preferred if zero additional dependencies is a goal.

**Core technologies:**
- Python 3.13: runtime — already pinned in pyproject.toml; keeps NumPy/SciPy version floors sensible
- NumPy 2.4.x: signal arrays — all waveform generation, envelope shaping, mixing, and normalization; the only correct choice for bulk float sample operations in Python
- SciPy 1.17.x: WAV output via `scipy.io.wavfile.write` — accepts NumPy arrays directly, handles headers automatically; also provides `scipy.signal` filters if IIR noise shaping is needed
- uv: dependency/environment management — 2025 standard; replaces pip + venv + pip-tools
- pytest + ruff: testing and lint — standard, zero-config for this scope

**Do not use:** audiolazy (unmaintained since 2014), pydub (requires ffmpeg; designed for file processing not generation), librosa (heavyweight ML-oriented analysis library), pyaudio/sounddevice/pygame (playback devices, out of scope).

### Expected Features

The feature set is well-defined by the domain. Consumer baby sleep apps prove what sounds are necessary; the library differentiates by synthesizing them programmatically rather than playing pre-recorded files.

**Must have (table stakes — v1):**
- Music box tone synthesis with exponential decay envelope — the core timbre; absent = the library has no identity
- White noise generation — most common sleep ambient; trivial with NumPy
- Pink noise generation — second most common; requires FFT spectral shaping
- Brown noise generation — deeper rumble; enables womb/heartbeat type
- Built-in lullaby presets (minimum 3: Twinkle Twinkle, Brahms' Lullaby, You Are My Sunshine)
- Custom note sequence input — `list[tuple[str, int]]` format (note name, duration denominator)
- Melody + ambient layering with configurable relative volumes
- WAV file output with configurable duration
- Seamless loop at WAV boundary (zero-crossing guaranteed)

**Should have (v1.x — after validation):**
- Womb/heartbeat ambient type (brown noise base + 60 BPM LFO amplitude envelope)
- Fade-in/fade-out on output file (raised-cosine ramp, 1-2s)
- Per-note inharmonic partials / warmth control (2-4 additive partials at ~2.76x, ~5.4x fundamental)
- Melody tempo/BPM parameter (duration scaling)
- Preset metadata dataclass (for library consumers building UIs)
- Multiple simultaneous ambient layers

**Defer (v2+):**
- Note reverb/room tail — algorithmic Schroeder reverb in NumPy is feasible but high complexity; validate demand first
- Additional lullaby presets — accumulate from user requests rather than speculating
- Ambient volume pulse modulation — refinement of heartbeat type; only after basic heartbeat is shipped

**Anti-features (explicitly out of scope):** audio playback (`play()` function), MP3/OGG output, real-time streaming, MIDI file input, rain/ocean/nature sounds (require audio samples or complex physical modelling), CLI interface, LUFS loudness targeting, melody harmonisation.

### Architecture Approach

The architecture is a linear numpy buffer pipeline with eight small modules. `__init__.py` exposes `generate()` as the single public entry point and orchestrates all stages. Each module is a pure function: it takes NumPy arrays (and parameters) and returns NumPy arrays. No shared mutable state. No classes required at the call site. The WAV writer is the only component that touches the filesystem. This design makes every stage independently testable and the pipeline trivially composable.

**Major components:**
1. `notes.py` — note name → Hz conversion (12-TET formula); duration denominator → sample count
2. `presets.py` — named lullaby note sequences as plain data (dict of tuples); zero synthesis logic
3. `tone.py` (ToneSynthesizer) — per-note decaying sinusoid with short linear attack envelope; additive inharmonic partials for warmth
4. `noise.py` (NoiseGenerator) — white/pink/brown noise via FFT spectral shaping (`np.fft.rfft` → frequency mask → `np.fft.irfft`)
5. `ambient.py` (AmbientShaper) — applies character to noise: low-pass for womb, LFO amplitude envelope for heartbeat pulse
6. `loop.py` (LoopRenderer) — tiles melody to target duration; crossfades tail-to-head at loop boundary for seamless repeat
7. `mixer.py` (Mixer) — sums melody + ambient with volume weights; peak-normalizes to [-1, 1] before output
8. `wav.py` (WAVWriter) — converts float32 → int16; writes via `scipy.io.wavfile.write`

**Key data contracts:** all internal buffers are `np.ndarray` float32 in [-1.0, 1.0]; note format is `list[tuple[str, int]]`; single `SAMPLE_RATE = 44100` constant defined once.

### Critical Pitfalls

1. **Loop-point click at WAV boundary** — apply a short (2-10 ms) fade-out/fade-in at file boundaries so the signal reaches exactly 0.0; crossfade the noise tail onto the head (~100-200 samples); assert `abs(audio[-1]) < 1e-4` before writing. This is disqualifying for sleep audio and must be addressed in the first render pipeline pass, not retrofitted.

2. **Silent int16 overflow on mixed layers** — two layers each at 0.7 amplitude sum to 1.4, which NumPy silently wraps to extreme negative values on int16 cast (no warning). Always normalize or clip after mixing: `np.clip(mixed, -1.0, 1.0)` or divide by peak. Add a unit test: mix both layers at max configured amplitude, assert no sample exceeds ±1.0 before conversion.

3. **Brown noise DC drift from naive cumsum** — `np.cumsum(white_noise)` drifts over long durations; use FFT spectral shaping (power ∝ 1/f²) instead. Always remove DC offset after generation: `signal -= signal.mean()`. Never use raw cumsum for output > ~10 seconds.

4. **Music box tone sounds like a pure sine (too clinical)** — a single `sin * exp` envelope sounds like a test signal, not an instrument. Add 2-4 inharmonic partials at ~2.76x and ~5.4x the fundamental with shorter individual decay constants. Establish and verify target timbre in the first tone synthesis implementation pass.

5. **Note onset click from non-zero initial phase** — `np.sin(2π·f·t)` at t=0 is non-zero unless the frequency is an exact integer. A short (5-10 ms) linear attack ramp on the amplitude envelope masks this regardless of initial phase. Build the attack envelope into the first implementation; do not treat it as a later polish step.

---

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Core Tone Synthesis
**Rationale:** The note-to-frequency pipeline and tone synthesizer are the foundation everything else depends on. The architecture research defines a strict build order: `notes.py` first (no dependencies, pure math), then `tone.py`, then `wav.py`. Establishing correct timbre with inharmonic partials in Phase 1 avoids a costly retrofit later (PITFALLS: Pitfall 5 — "medium recovery cost" if partials are absent at first release).
**Delivers:** A playable music box tone for any note name; single-note WAV output for perceptual validation.
**Addresses:** Music box tone synthesis, exponential envelope per note (table stakes); per-note inharmonicity partially (start with 2 partials).
**Avoids:** Pure-sine timbre pitfall (Pitfall 5); note onset click (Pitfall 8); WAV header corruption (Pitfall 7 — use `scipy.io.wavfile.write` from day one).

### Phase 2: Melody Pipeline
**Rationale:** Once a single tone is correct, building the full melody pipeline (presets, note sequencing, tiling, loop boundary) is a natural next step. Loop seam correctness must be validated before the ambient layer is added — it is easier to hear and diagnose on melody-only output.
**Delivers:** Full lullaby rendered as a loopable WAV; 3 built-in presets; custom note sequence input.
**Addresses:** Built-in lullaby presets, custom note sequence input, configurable duration, seamless loop (all v1 table stakes).
**Avoids:** Loop-point click (Pitfall 1 — apply boundary fade here while the signal is still simple); note scheduling click (Pitfall 8 — confirmed working before adding noise complexity).

### Phase 3: Ambient Noise Generation
**Rationale:** Noise generation is isolated from melody synthesis (no shared state); ARCHITECTURE build order puts `noise.py` after `presets.py`. Pink and brown noise both require FFT spectral shaping — implement them together so the FFT pattern is written once. Brown noise DC drift must be prevented here, not patched later.
**Delivers:** White, pink, and brown noise buffers at target duration; spectral accuracy verified.
**Addresses:** White noise, pink noise, brown noise (all v1 table stakes).
**Avoids:** Brown noise DC drift (Pitfall 3 — use FFT shaping, not cumsum); pink noise low-frequency inaccuracy (Pitfall 4 — single-pass FFT, not chunked).

### Phase 4: Mixing and Final Output
**Rationale:** Mixing requires both melody (Phase 2) and ambient (Phase 3) to be complete. Normalization and int16 conversion happen here — the overflow pitfall must be addressed with a mandatory unit test at this phase. This phase closes the full v1 pipeline.
**Delivers:** Mixed melody + ambient WAV at configurable duration and relative volumes; the complete v1 product.
**Addresses:** Melody + ambient layering, WAV output, configurable duration (completing v1 table stakes).
**Avoids:** Silent int16 overflow (Pitfall 2 — normalization is a required pipeline step, covered by unit test); loop-point click revisited on mixed signal.

### Phase 5: Quality and Differentiators (v1.x)
**Rationale:** Once core is validated by real use, add the differentiating features that have medium value but no v1 blockers. Womb/heartbeat builds directly on brown noise (Phase 3). Fade-in/fade-out is a post-process on the final array (no architectural change). Inharmonicity refinement extends Phase 1 tone synthesis.
**Delivers:** Womb/heartbeat ambient type; fade-in/fade-out; BPM parameter; preset metadata; multiple simultaneous ambient layers.
**Addresses:** All v1.x "should have" features from FEATURES.md.

### Phase Ordering Rationale

- **Tone first:** The melody layer has more internal dependencies (notes → tone → loop) and is perceptually harder to validate than noise. Getting tone right early avoids re-work.
- **Loop boundary in Phase 2, not Phase 4:** Loop correctness is easier to validate on a melody-only signal. Adding noise first and discovering loop issues later means diagnosing a combined signal.
- **Noise as a dedicated phase:** Pink and brown noise share the FFT spectral shaping pattern. Implementing them together produces a clean, reusable `noise.py` module rather than ad-hoc implementations scattered across phases.
- **Mixing last among v1 phases:** Mixer requires both upstream buffers to exist and same-length arrays to be enforced. Placing mixing last keeps integration concerns isolated to a single phase.
- **No Karplus-Strong:** Research recommends additive sinusoid synthesis over Karplus-Strong throughout. KS introduces tuning inaccuracy at high frequencies (Pitfall 6, HIGH recovery cost if already shipped). Additive synthesis has exact frequency control and simpler implementation.

### Research Flags

Phases with well-documented patterns (skip `/gsd:research-phase`):
- **Phase 1 (Tone Synthesis):** Decaying sinusoid + additive inharmonic partials is a well-documented pattern with code examples in research. NumPy primitives are sufficient.
- **Phase 3 (Noise Generation):** FFT spectral shaping for pink/brown noise is fully documented with verified reference implementations (python-acoustics, colorednoise source, DSP Related article).
- **Phase 4 (Mixing/Output):** `scipy.io.wavfile.write` is documented; normalization pattern is straightforward; no unknowns.

Phases likely needing deeper investigation during planning:
- **Phase 2 (Melody Pipeline / Seamless Loop):** The crossfade approach for noise loop boundaries at the melody-level may need experimentation — the exact crossfade length and method affects both melody (note decay at boundary) and later noise (ambient texture). Worth a focused spike.
- **Phase 5 (Womb/Heartbeat):** The LFO amplitude envelope modulation for heartbeat pulse needs perceptual tuning (BPM, pulse shape, rumble balance). The mechanism is known but the parameters require listening tests. Plan for iteration.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | NumPy and SciPy versions verified on PyPI; uv as standard tool confirmed; all anti-use libraries confirmed as unsuitable via documented reasons |
| Features | MEDIUM | Consumer app ecosystem well-documented; synthesis library norms confirmed via open-source references; some perceptual quality specifics (partial ratios, decay constants) extrapolated from DSP literature rather than empirically measured |
| Architecture | HIGH | Core pipeline pattern (buffer-passing pure functions) confirmed across multiple reference implementations; build order derived from data-flow dependencies with no ambiguity |
| Pitfalls | HIGH | int16 overflow confirmed via NumPy issue tracker; loop-click, DC drift, and tuning inaccuracy are documented in DSP literature and audio developer forums with verified sources |

**Overall confidence:** HIGH

### Gaps to Address

- **Inharmonic partial ratios for music box tines:** Research cites marimba/xylophone physics as a proxy. Exact ratios for music box tines (~2.756x, ~5.4x) are approximations from secondary sources. Validate by comparing synthesized output against recordings of real music boxes during Phase 1. Adjustment is additive (no architecture impact).
- **Optimal crossfade length for seamless loop:** Research recommends 100-200 samples; the exact value affects perceptual smoothness. Determine empirically in Phase 2 with listening tests. Parameter should be tunable (not hardcoded).
- **colorednoise NumPy 2.x compatibility:** Package has no upper version cap and no C extensions; expected to work but not CI-verified against NumPy 2.4. Test on first install; fall back to vendored 30-line FFT implementation if needed (documented in STACK.md).
- **Memory footprint for 8-hour files:** At 44100 Hz × float32 × 28800 seconds ≈ 5 GB — too large for a single in-memory buffer. Phase 2 (LoopRenderer) should implement tile-from-short-master strategy rather than generating full duration upfront. This is a known scaling path from ARCHITECTURE.md.

---

## Sources

### Primary (HIGH confidence)
- PyPI numpy 2.4.4 page — verified current version and release date
- PyPI scipy 1.17.1 page — verified current version and compatibility with NumPy 2.x
- python-acoustics noise generator module (GitHub) — inspected source; confirms FFT spectral shaping pattern
- PySynth note sequence format (GitHub) — widely used reference; confirms `(note_str, duration_denominator)` tuple convention
- SciPy docs `wavfile.write` v1.17.0 — confirmed int16/float32 array support, header auto-generation
- NumPy 2.0 migration blog — confirmed ABI break June 2024; rationale for pinning `numpy>=2.0`
- NumPy issue #10782 — confirmed silent integer overflow behavior on array cast
- DSP Related: Generating pink noise (Allen Downey) — confirmed -3 dB/octave target for pink noise spectrum
- Karplus-Strong Wikipedia — confirmed tuning inaccuracy at high frequencies and allpass correction requirement

### Secondary (MEDIUM confidence)
- Soundverse AI baby sleep article (2026) — feature landscape for consumer sleep audio apps
- BabySnooze / Sound Sleeper App Store listings — confirmed white/pink/brown/womb as standard sleep sound categories
- colorednoise GitHub (217 stars) — confirmed Timmer-Koenig algorithm; NumPy 2.x works in practice
- Sound Synthesis in Python (Noah Hradek, Medium) — pattern confirmation; unverified credentials
- WolfSound wavetable synth tutorial — pipeline pattern confirmation
- Karplus-Strong Python (Frolian's Blog) — algorithm confirmation for KS alternative
- Synthesizing Bells (Sound On Sound) — partial ratio reference for tine-like synthesis
- Seamless loop techniques (FrontierSoundFX, Audacity docs) — crossfade approach confirmation

### Tertiary (LOW confidence)
- Generating white/pink/brown noise (smrati.katiyar, Medium) — cross-checked against python-acoustics source; consistent
- Inharmonic partials for tine sounds (North Coast Synthesis blog) — partial ratio approximations; needs empirical validation

---
*Research completed: 2026-03-30*
*Ready for roadmap: yes*
