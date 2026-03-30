# Stack Research

**Domain:** Pure-Python audio synthesis library (music box tones + noise generation → WAV output)
**Researched:** 2026-03-30
**Confidence:** HIGH (core stack), MEDIUM (noise helper library decision)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | >=3.13 | Runtime | Already pinned in pyproject.toml; 3.13 brings free-threaded GIL experiments but irrelevant here — the constraint keeps numpy/scipy version floors sensible |
| NumPy | 2.4.x (current: 2.4.4) | Signal arrays — waveform generation, envelope shaping, noise filtering, mixing | The single correct choice for bulk floating-point sample arrays in Python. Every synthesis operation (sinusoid generation, Karplus-Strong ring buffer, pink-noise shaping) is a vectorised array op. `np.linspace`, `np.exp`, `np.convolve` cover 90% of the synthesis math. NumPy 2.x is now stable (released June 2024, patch releases through March 2026). |
| SciPy | 1.17.x (current: 1.17.1) | WAV output (`scipy.io.wavfile.write`) and optional signal-processing filters | `scipy.io.wavfile.write` is the cleanest path from a NumPy array to a WAV file — one call, accepts int16/int32/float32 arrays, no external C library required. `scipy.signal.lfilter` or `scipy.signal.sosfilt` are used for IIR-based pink/brown noise colouring if you choose the filter approach over FFT. |

### Supporting Libraries (conditional)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| colorednoise | 2.2.0 | Spectral-domain pink/brown noise generation (Timmer-Koenig algorithm) | Use **only if** you want a single-line call for coloured noise and don't mind a third dependency. It generates correct 1/f^beta noise; beta=1 = pink, beta=2 = brown. Downside: last release October 2023, no explicit NumPy 2.x CI. Since its internals are pure NumPy FFT maths with no C extensions or deprecated APIs, it works on NumPy 2.x in practice. Vendor the 60-line core if you want zero external risk. |
| stdlib `wave` | built-in | Alternative WAV writer when SciPy is not wanted | Use only if you want to keep SciPy out of the dependency list. Accepts raw bytes (16-bit PCM only — you must pack with `struct` or `numpy.tobytes()`). More ceremony, same result. Not recommended as primary path. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Dependency management, virtualenv, lockfile | The 2025 standard Python project tool. Replaces pip + venv + pip-tools. `uv add numpy scipy` updates pyproject.toml and writes uv.lock. 10-100x faster than pip. Already the de-facto recommendation in the Python packaging community. |
| pytest | Unit testing | Standard test runner. Use `numpy.testing.assert_allclose` for asserting sample arrays rather than raw `==` checks — handles floating-point tolerance correctly. |
| ruff | Linter + formatter | Replaces flake8 + black + isort in a single Rust-based tool. Zero config needed for a project this size. |

---

## Installation

```bash
# Core runtime dependencies
uv add numpy scipy

# Dev dependencies
uv add --dev pytest ruff

# Optional: coloured noise helper (only if not vendoring)
uv add colorednoise
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `scipy.io.wavfile.write` | `soundfile` (libsndfile) | Only if you need non-WAV output formats (FLAC, OGG) or 24-bit PCM. soundfile requires a compiled C library (libsndfile), adding a system dependency. Unnecessary for WAV-only output. |
| `scipy.io.wavfile.write` | stdlib `wave` | If you need zero SciPy dependency and only need 16-bit PCM. Costs 10 lines of packing boilerplate instead of 1 call. Not worth it when SciPy is already in the stack for signal filters. |
| NumPy FFT-based pink noise (via `np.fft`) | `colorednoise` package | If you want no extra dependency. Generate white noise, shape the spectrum in frequency domain, IFFT. NumPy 2.x ships with all required primitives. Slightly more implementation work, but trivial (30 lines). |
| Karplus-Strong + decaying sinusoid blend | `audiolazy` | audiolazy is unmaintained (last PyPI release 2014). Do not use. |
| `uv` | `poetry` | poetry is fine for larger teams; uv is faster and simpler for a single-library project of this scope |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `audiolazy` | Unmaintained since 2014; Python 2 era codebase; no NumPy 2.x support | Implement synthesis primitives directly with NumPy — they are short |
| `pydub` | Designed for processing existing audio files (slicing, conversion, effects); not for programmatic signal generation from scratch. Adds ffmpeg/avconv as runtime system dependency. | NumPy array math directly |
| `librosa` | Heavyweight ML-oriented audio analysis library (loads sklearn, audioread, resampy etc.). Zero synthesis utilities. | Not relevant to generation-only library |
| `pyaudio` / `sounddevice` | Real-time audio playback devices. Out of scope — this library generates files, does not play them. | Not applicable |
| `pygame.mixer` | Game audio playback. Out of scope. | Not applicable |
| NumPy 1.x | NumPy 2.0 shipped June 2024 with breaking ABI + type-promotion changes. Starting a greenfield project on 1.x now means a forced migration later. | Pin `numpy>=2.0` |

---

## Synthesis Approach Notes (not a library choice, but informs architecture)

**Music box tones (per-note):**
- A music box tine produces a near-pure sinusoid with fast attack and long exponential decay.
- Implementation: `np.sin(2 * np.pi * freq * t) * np.exp(-decay_rate * t)` where `decay_rate` controls the tine's ring time (~3-8 seconds for realistic music box character).
- No external library needed beyond NumPy. This is 5 lines of code.

**Plucked variant (Karplus-Strong):**
- Fills a ring buffer with white noise, then averages neighbouring samples per output sample. Produces a richer, slightly inharmonic plucked timbre closer to a guitar or mbira tine.
- Implemented with a Python deque or a pre-allocated NumPy array. Pure NumPy, no library.
- More CPU-intensive but not relevant at these durations (minutes of audio, not real-time).

**Pink noise (1/f):**
- FFT approach: `white = np.random.randn(N)`, compute FFT, multiply by `1/sqrt(f)` frequency mask, IFFT. Correct and fast.
- Alternatively: IIR filter approximation via `scipy.signal.sosfilt` with a pre-designed pink-noise filter (Yule-Walker method). Slightly less accurate but sample-by-sample streamable.
- Recommendation: FFT approach for offline rendering (this project's use case).

**Brown/womb noise:**
- Brown noise = 1/f^2 spectrum, same FFT approach with steeper frequency mask.
- Womb ambient = brown noise + low-pass (cutoff ~300 Hz, via `scipy.signal.butter` + `sosfilt`).

**Heartbeat pulse:**
- Low-frequency bump: two-sided Gaussian envelope at ~1 Hz (60 BPM), applied to a 50-80 Hz sine. NumPy only.

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| numpy 2.4.x | Python 3.11-3.13 | Full support. NumPy 2.1+ added Python 3.13 support. |
| scipy 1.17.x | numpy >=1.23.5, Python 3.10-3.13 | scipy 1.17 was released Feb 2026; compatible with numpy 2.x |
| colorednoise 2.2.0 | numpy >=1.17 (no upper cap) | Works with numpy 2.x in practice; no C extensions to break. Test on first use. |
| pytest (latest) | Python 3.8+ | No constraints relevant here |

---

## Sources

- PyPI numpy page — verified current version 2.4.4, released 2026-03-29 [https://pypi.org/project/numpy/]
- PyPI scipy page — verified current version 1.17.1, released 2026-02-23 [https://pypi.org/project/scipy/]
- PyPI colorednoise page — verified version 2.2.0, released 2023-10-09 [https://pypi.org/project/colorednoise/]
- colorednoise GitHub — confirmed numpy >=1.17.0 dependency, no upper cap, 217 stars [https://github.com/felixpatzelt/colorednoise]
- Python docs wave module — confirmed PCM-only limitation, any setsampwidth [https://docs.python.org/3/library/wave.html]
- SciPy docs wavfile.write — v1.17.0 manual, confirmed int16/int32/float32/float64 support [https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.wavfile.write.html]
- NumPy 2.0 migration blog — breaking ABI change confirmed June 2024 [https://blog.scientific-python.org/numpy/numpy2/]
- uv Astral docs — confirmed 2025 standard tool for pyproject.toml projects [https://docs.astral.sh/uv/concepts/projects/dependencies/]
- WebSearch: colorednoise noise generation approach (Timmer-Koenig 1995) — MEDIUM confidence
- WebSearch: Karplus-Strong Python implementations — MEDIUM confidence (well-documented algorithm, multiple verified implementations)

---

*Stack research for: musicboxfactory — Python audio synthesis library*
*Researched: 2026-03-30*
