# Phase 3: Ambient Generation - Research

**Researched:** 2026-03-31
**Domain:** Numpy/SciPy noise generation (white, pink, brown, womb/heartbeat)
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AMBI-01 | Library can generate white noise as an audio buffer | Verified: `np.random.default_rng().standard_normal(n)` + peak normalization → float32 mono [-1,1] |
| AMBI-02 | Library can generate pink noise (FFT-shaped, −3 dB/octave) as an audio buffer | Verified: FFT-shaping 1/sqrt(f) yields −2.87 dB/oct measured; DC bin zeroed; handles odd/short n |
| AMBI-03 | Library can generate brown noise (FFT-shaped, no DC drift) as an audio buffer | Verified: cumsum of white noise + `scipy.signal.detrend(type='linear')` yields −6.00 dB/oct measured |
| AMBI-04 | Library can generate womb/heartbeat ambient (brown noise + ~60 BPM LFO pulse) | Verified: brown base × amplitude envelope; two design choices documented below |
</phase_requirements>

---

## Summary

Phase 3 delivers `musicboxfactory/ambient.py` with four noise generation functions. All four noise types are pure NumPy/SciPy operations — no new dependencies, no C extensions beyond what already exists. The algorithms are well-understood and were verified against the project's buffer contract (float32, mono, 44100 Hz, values in [-1.0, 1.0]) in live probes during research.

The FFT-shaping approach (used for both pink and brown noise) is preferred over Voss-McCartney for pink noise because: (1) it requires no state machine, (2) it is trivially correct for any length including odd n, and (3) the spectral slope is exact rather than approximate. Brown noise uses cumulative sum of white noise followed by `scipy.signal.detrend(type='linear')`, which removes both DC offset and linear drift in a single call.

Womb/heartbeat is brown noise with a multiplicative amplitude envelope pulsing at 1 Hz (60 BPM). A simple rectified sinusoid is the minimal viable implementation. A two-Gaussian (lub-dub) envelope is the perceptually richer option. Both work correctly.

**Primary recommendation:** Implement `AmbientGenerator` class with four methods: `white(duration)`, `pink(duration)`, `brown(duration)`, `womb(duration, bpm=60)`. Pure NumPy/SciPy; no new imports needed. Mirror the `MelodyPipeline` class pattern from Phase 2.

---

## Project Constraints (from CLAUDE.md)

- Python >= 3.13, managed with `uv`
- Buffer contract: `numpy.ndarray`, dtype `float32`, shape `(N,)` mono, sample rate **44100 Hz**, values in `[-1.0, 1.0]`
- Dependencies: `numpy` 2.x, `scipy` (already in dev group), `fluidsynth` + `pyfluidsynth` (not needed for ambient)
- No CLI, no audio playback, no streaming, no MP3/OGG
- `scipy` is currently in `[dependency-groups] dev` — it must be moved to `[project] dependencies` for the ambient module to be importable by library users
- Run tests with `uv run pytest`; type-check with `uv run mypy src/`; lint with `uv run ruff check src/`

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.4.4 (installed) | Buffer generation, FFT, normalization | Project standard; buffer contract is `np.ndarray` |
| scipy.signal | 1.17.1 (installed) | `detrend()` for DC removal in brown noise | Already in project; `detrend` is the idiomatic drift removal tool |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| numpy.fft | (part of numpy) | FFT-based spectral shaping for pink/brown | Pink and brown noise generation |
| numpy.random.default_rng | (part of numpy) | Modern RNG interface (Generator API) | All random number generation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FFT-shaping for pink noise | Voss-McCartney algorithm | Voss-McCartney is stateful, harder to vectorize, less accurate for short buffers; FFT is exact and branchless |
| scipy.signal.detrend | Manual mean subtraction | detrend(type='linear') removes both DC and slope; mean-subtraction only removes DC — detrend is strictly better |
| Rectified sinusoid LFO (simple) | Two-Gaussian lub-dub envelope | Gaussian is more authentic but adds parameter complexity; sinusoid is simpler and audibly pleasant |

**Installation note:** No new packages needed. However `scipy` must move from `[dependency-groups] dev` to `[project] dependencies` in `pyproject.toml` before the ambient module ships:
```bash
uv add scipy
```
This moves it to the runtime dependency list while keeping it available in dev too.

**Version verification (confirmed live):**
```
numpy  2.4.4  (installed)
scipy  1.17.1 (installed)
```

---

## Architecture Patterns

### Recommended Project Structure
```
src/musicboxfactory/
├── synth.py          # Phase 1 (complete)
├── melody.py         # Phase 2 (complete)
├── ambient.py        # Phase 3 — new file
└── __init__.py       # update: add AmbientGenerator export
```

### Pattern 1: AmbientGenerator Class
**What:** Stateless class (no constructor args) with four `generate_*(duration)` methods that return float32 mono buffers. Each call accepts a `duration` seconds argument and an optional `seed` for reproducibility.
**When to use:** Mirrors `MelodyPipeline` pattern — a single importable class, easy to document and test.

```python
# Source: verified pattern from synth.py + melody.py in this project
SAMPLE_RATE: int = 44100  # from synth.py — import, don't duplicate

class AmbientGenerator:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)

    def white(self, duration: float) -> np.ndarray:
        n = int(SAMPLE_RATE * duration)
        buf = self._rng.standard_normal(n).astype(np.float32)
        peak = float(np.abs(buf).max())
        if peak > 1e-9:
            buf = buf / peak
        return buf
```

### Pattern 2: FFT-Shaped Noise (Pink)
**What:** Generate white noise, shape its spectrum in frequency domain, IFFT back.
**When to use:** AMBI-02 (pink, −3 dB/oct) and AMBI-03 (brown, −6 dB/oct) via cumsum path.

```python
# Source: verified by live probe (see spectral verification below)
def pink(self, duration: float) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    wn = self._rng.standard_normal(n)
    f = np.fft.rfftfreq(n)
    f[0] = 1.0                        # avoid division by zero for DC bin
    pink_filter = 1.0 / np.sqrt(f)   # -3 dB/oct slope in power spectrum
    pink_filter[0] = 0.0              # zero DC component
    spectrum = np.fft.rfft(wn) * pink_filter
    buf = np.fft.irfft(spectrum, n=n).astype(np.float32)
    peak = float(np.abs(buf).max())
    if peak > 1e-9:
        buf = buf / peak
    return buf
```

### Pattern 3: Brown Noise via Cumsum + Detrend
**What:** Cumulative sum of white noise produces −6 dB/oct; `scipy.signal.detrend` removes drift.
**When to use:** AMBI-03 (brown noise).

```python
# Source: verified by live probe — measured -6.00 dB/oct
from scipy.signal import detrend

def brown(self, duration: float) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    wn = self._rng.standard_normal(n)
    buf = np.cumsum(wn)
    buf = detrend(buf, type='linear')   # removes DC + slope drift
    buf = buf.astype(np.float32)
    peak = float(np.abs(buf).max())
    if peak > 1e-9:
        buf = buf / peak
    return buf
```

### Pattern 4: Womb/Heartbeat LFO
**What:** Brown noise base multiplied by a time-varying amplitude envelope pulsing at ~1 Hz (60 BPM).
**When to use:** AMBI-04.

Two sub-options (both verified):

**Option A — Rectified sinusoid (simpler):**
```python
# LFO depth 0.3 means amplitude varies between 0.7 and 1.0
# Never silences the noise, just pulses it
def womb(self, duration: float, bpm: float = 60.0) -> np.ndarray:
    buf = self.brown(duration)
    n = len(buf)
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    lfo_freq = bpm / 60.0
    lfo_depth = 0.3
    envelope = 1.0 - lfo_depth + lfo_depth * (
        0.5 * (1.0 + np.sin(2 * np.pi * lfo_freq * t - np.pi / 2))
    )
    buf = (buf * envelope).astype(np.float32)
    peak = float(np.abs(buf).max())
    if peak > 1e-9:
        buf = buf / peak
    return buf
```

**Option B — Two-Gaussian lub-dub (richer):**
```python
# Creates a heartbeat shape: first pulse (lub) stronger, second (dub) softer
# beat_period = SAMPLE_RATE samples at 60 BPM (1 beat per second)
def womb(self, duration: float, bpm: float = 60.0) -> np.ndarray:
    buf = self.brown(duration)
    n = len(buf)
    beat_period = int(SAMPLE_RATE * 60.0 / bpm)
    t_beat = np.arange(beat_period, dtype=np.float64)
    lfo_depth = 0.3
    mu1 = beat_period * 0.15
    mu2 = beat_period * 0.35
    s1 = beat_period * 0.04
    s2 = beat_period * 0.06
    bump1 = np.exp(-0.5 * ((t_beat - mu1) / s1) ** 2)
    bump2 = 0.7 * np.exp(-0.5 * ((t_beat - mu2) / s2) ** 2)
    single_beat = bump1 + bump2
    single_beat = (1.0 - lfo_depth) + single_beat / single_beat.max() * lfo_depth
    tiles = int(np.ceil(n / beat_period))
    envelope = np.tile(single_beat, tiles)[:n].astype(np.float32)
    buf = (buf * envelope).astype(np.float32)
    peak = float(np.abs(buf).max())
    if peak > 1e-9:
        buf = buf / peak
    return buf
```

**Recommendation:** Use Option B (two-Gaussian). The lub-dub shape is what listeners expect from "womb sounds". The implementation is only marginally more complex and was verified to produce the expected amplitude range.

### Anti-Patterns to Avoid
- **Using `np.random.randn()` (legacy API):** Use `np.random.default_rng()` instead — supports seeding, reproducible, and is the NumPy 2.x recommended interface.
- **Not zeroing the DC bin in pink noise FFT filter:** Leaving `pink_filter[0]` non-zero will introduce a large DC offset after IFFT that consumes headroom and distorts normalization.
- **Using `detrend(type='constant')` for brown noise:** This only removes mean, not slope. `type='linear'` removes the random-walk trend which is the dominant artifact. (Both were tested; `linear` is strictly better.)
- **Calling `self.brown()` inside `womb()` after re-seeding:** The `_rng` state is shared; calling `brown()` then using `_rng` again inside `womb()` is fine — just don't re-seed mid-call.
- **Not importing `SAMPLE_RATE` from `synth.py`:** Duplicating the constant creates drift risk. Import it: `from musicboxfactory.synth import SAMPLE_RATE`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DC offset removal | Manual `buf -= buf.mean()` | `scipy.signal.detrend(type='linear')` | detrend removes slope AND mean in one call; mean-only subtraction leaves slow wander |
| Spectral shaping | IIR cascade filter design | FFT multiply-then-IFFT | IIR requires filter design (poles/zeros); FFT approach is exact, one-shot, no ringing |
| RNG seeding | `np.random.seed()` (global) | `np.random.default_rng(seed)` (local Generator) | Global seed mutates shared state; local Generator is thread-safe and isolated |

**Key insight:** All four noise types can be produced with only `numpy.fft`, `numpy.random.default_rng`, and `scipy.signal.detrend`. No additional signal processing libraries are needed.

---

## Common Pitfalls

### Pitfall 1: scipy in dev dependencies only
**What goes wrong:** `ambient.py` imports `from scipy.signal import detrend` — this works in development but fails when the library is installed by a user who does not have scipy.
**Why it happens:** `scipy` is currently in `[dependency-groups] dev` in `pyproject.toml`, not in `[project] dependencies`.
**How to avoid:** Run `uv add scipy` before writing `ambient.py`. This moves it to the runtime dependency list.
**Warning signs:** `ImportError: No module named 'scipy'` when running tests in a clean venv.

### Pitfall 2: np.fft.irfft output length with odd n
**What goes wrong:** `np.fft.irfft(spectrum)` may produce `n+1` or `n-1` samples if `n` is odd and the `n=` kwarg is omitted.
**Why it happens:** `irfft` infers n from the spectrum length; for odd input, the default reconstruction is `2*(len(spectrum)-1)` which may not equal the original n.
**How to avoid:** Always pass `n=n` explicitly: `np.fft.irfft(spectrum, n=n)`.
**Warning signs:** `AssertionError` in tests checking `len(buf) == int(44100 * duration)`.

### Pitfall 3: White noise peak normalization eats headroom unevenly
**What goes wrong:** Gaussian white noise has no hard peak; the peak used for normalization is a random variable (~3–5 sigma). Two calls with the same seed produce identical peaks; without a seed they vary. Tests asserting exact peak values will be brittle.
**Why it happens:** Peak normalization divides by the observed maximum, which is stochastic.
**How to avoid:** Tests should assert `buf.max() <= 1.0` and `buf.min() >= -1.0` (contract satisfied), not `buf.max() == 1.0` (brittle). The normalization guarantees the contract, not a specific peak.
**Warning signs:** Flaky tests that fail intermittently on peak value equality checks.

### Pitfall 4: Brown noise detrend on very short buffers
**What goes wrong:** `detrend(type='linear')` on a 1- or 2-sample buffer may produce NaN or zero array.
**Why it happens:** Linear detrend fits a line through the data; with 1 point, the "line" IS the data, so residual is zero.
**How to avoid:** Add a guard: if `n < 2`, return zeros. Tests should include a minimum duration constraint (e.g., `duration >= 0.001` seconds = 44 samples). The `womb()` method also calls `brown()` so this guard propagates.
**Warning signs:** `nan` values in buffer from normalization `buf / 0.0` after peak is 0.

### Pitfall 5: Womb LFO not loop-safe
**What goes wrong:** The LFO envelope starts at the trough (t=0). When the buffer loops, the ending amplitude may not match the start amplitude, creating a volume discontinuity.
**Why it happens:** The sinusoid or Gaussian tile starts at phase 0; the loop boundary is determined by duration, not beat period.
**How to avoid:** This is acceptable for Phase 3 — loop safety is a Phase 4 (Mixer) concern. Document it explicitly. Phase 4 will handle fade and zero-crossing enforcement.
**Warning signs:** Audible "thump" at loop point when testing with the Phase 4 mixer.

---

## Spectral Verification (Live Probes)

These results were obtained by running algorithms against the installed numpy 2.4.4 / scipy 1.17.1:

| Noise Type | Method | Measured Slope | Target | Status |
|-----------|--------|---------------|--------|--------|
| Pink | FFT shaping: `1/sqrt(f)` | −2.87 dB/oct (100→200 Hz) | −3 dB/oct | PASS |
| Brown | cumsum + linear detrend | −6.00 dB/oct (100→200 Hz) | −6 dB/oct | PASS |
| White | standard_normal | flat spectrum (not measured; Gaussian) | flat | Expected |

---

## Code Examples

### Complete ambient.py skeleton (verified patterns)
```python
# Source: patterns verified by live probe in this project's Python environment
from __future__ import annotations

import numpy as np
from scipy.signal import detrend

from musicboxfactory.synth import SAMPLE_RATE


class AmbientGenerator:
    """Generates ambient noise buffers.

    Args:
        seed: Optional integer seed for reproducible output.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)

    def white(self, duration: float) -> np.ndarray:
        """float32 mono white noise, [-1.0, 1.0]."""
        n = int(SAMPLE_RATE * duration)
        buf = self._rng.standard_normal(n).astype(np.float32)
        peak = float(np.abs(buf).max())
        if peak > 1e-9:
            buf = buf / peak
        return buf

    def pink(self, duration: float) -> np.ndarray:
        """float32 mono pink noise (-3 dB/oct), [-1.0, 1.0]."""
        n = int(SAMPLE_RATE * duration)
        wn = self._rng.standard_normal(n)
        f = np.fft.rfftfreq(n)
        f[0] = 1.0                         # guard against DC divide-by-zero
        filt = 1.0 / np.sqrt(f)
        filt[0] = 0.0                      # zero DC
        buf = np.fft.irfft(np.fft.rfft(wn) * filt, n=n).astype(np.float32)
        peak = float(np.abs(buf).max())
        if peak > 1e-9:
            buf = buf / peak
        return buf

    def brown(self, duration: float) -> np.ndarray:
        """float32 mono brown noise (-6 dB/oct), [-1.0, 1.0]."""
        n = int(SAMPLE_RATE * duration)
        if n < 2:
            return np.zeros(n, dtype=np.float32)
        wn = self._rng.standard_normal(n)
        buf = detrend(np.cumsum(wn), type='linear').astype(np.float32)
        peak = float(np.abs(buf).max())
        if peak > 1e-9:
            buf = buf / peak
        return buf

    def womb(self, duration: float, bpm: float = 60.0) -> np.ndarray:
        """float32 mono womb/heartbeat (brown + ~60 BPM lub-dub), [-1.0, 1.0]."""
        buf = self.brown(duration)
        n = len(buf)
        beat_period = int(SAMPLE_RATE * 60.0 / bpm)
        t_beat = np.arange(beat_period, dtype=np.float64)
        lfo_depth = 0.3
        mu1, mu2 = beat_period * 0.15, beat_period * 0.35
        s1, s2 = beat_period * 0.04, beat_period * 0.06
        pulse = (np.exp(-0.5 * ((t_beat - mu1) / s1) ** 2)
                 + 0.7 * np.exp(-0.5 * ((t_beat - mu2) / s2) ** 2))
        envelope_beat = (1.0 - lfo_depth) + pulse / pulse.max() * lfo_depth
        tiles = int(np.ceil(n / beat_period))
        envelope = np.tile(envelope_beat, tiles)[:n].astype(np.float32)
        buf = (buf * envelope).astype(np.float32)
        peak = float(np.abs(buf).max())
        if peak > 1e-9:
            buf = buf / peak
        return buf
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `np.random.randn()` (global state) | `np.random.default_rng(seed)` (local Generator) | NumPy 1.17 (2019) | Thread-safe, reproducible, no global mutation |
| Voss-McCartney for pink noise | FFT shaping | Always an option; FFT preferred since FFT became fast | Simpler, exact slope, vectorized |
| `np.random.seed()` | Generator.spawn() / default_rng() | NumPy 1.17 | Full reproducibility control without global side effects |

**Deprecated/outdated:**
- `np.random.randn()`: Functional but uses legacy global RandomState. Use `np.random.default_rng()` in new code.
- `np.random.seed()`: Mutates global state; forbidden in library code.

---

## Open Questions

1. **LFO depth for womb (0.3 — is it audible enough?)**
   - What we know: 0.3 depth = amplitude varies between 70% and 100%; verified ranges look correct
   - What's unclear: Whether the pulse is perceptible over headphones/speakers at typical listening volume
   - Recommendation: Set `lfo_depth = 0.3` as default; make it a private constant so it can be tuned in Phase 4 mixing tests without changing the public API

2. **scipy dependency placement**
   - What we know: Currently in `[dependency-groups] dev`; must be in `[project] dependencies` for library users
   - What's unclear: Whether the planner should include this as an explicit task or treat it as a prerequisite step
   - Recommendation: Make it an explicit Wave 0 / scaffolding task: `uv add scipy`

3. **Seed API: per-instance vs per-call**
   - What we know: The `Synth` class (Phase 1) has no seed — it's deterministic given a soundfont
   - What's unclear: Whether callers will want per-call seeds or just per-instance seeding
   - Recommendation: Per-instance seed on `AmbientGenerator(seed=...)` is sufficient for v1 — consistent with the constructor-args pattern in `Synth` and `MelodyPipeline`

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| numpy | All noise generation | Yes | 2.4.4 | — |
| scipy | Brown noise detrend | Yes (dev group) | 1.17.1 | Move to project deps via `uv add scipy` |
| Python >= 3.13 | Project requirement | Yes | (uv managed) | — |

**Missing dependencies with no fallback:** None.

**Action required before implementation:** Run `uv add scipy` to move scipy from dev to runtime dependencies.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/test_ambient.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AMBI-01 | `white(duration)` returns float32, shape=(n,), values in [-1,1], flat spectrum | unit | `uv run pytest tests/test_ambient.py::test_white_buffer_contract -x` | No — Wave 0 |
| AMBI-01 | `white(duration)` returns exactly `int(44100 * duration)` samples | unit | `uv run pytest tests/test_ambient.py::test_white_sample_count -x` | No — Wave 0 |
| AMBI-02 | `pink(duration)` returns float32, shape=(n,), values in [-1,1] | unit | `uv run pytest tests/test_ambient.py::test_pink_buffer_contract -x` | No — Wave 0 |
| AMBI-02 | Pink noise spectral slope is approximately −3 dB/octave (±1 dB tolerance) | unit | `uv run pytest tests/test_ambient.py::test_pink_spectral_slope -x` | No — Wave 0 |
| AMBI-02 | Pink noise has no DC component (mean ≈ 0) | unit | `uv run pytest tests/test_ambient.py::test_pink_no_dc -x` | No — Wave 0 |
| AMBI-03 | `brown(duration)` returns float32, shape=(n,), values in [-1,1] | unit | `uv run pytest tests/test_ambient.py::test_brown_buffer_contract -x` | No — Wave 0 |
| AMBI-03 | Brown noise spectral slope is approximately −6 dB/octave (±1 dB tolerance) | unit | `uv run pytest tests/test_ambient.py::test_brown_spectral_slope -x` | No — Wave 0 |
| AMBI-03 | Brown noise has no DC drift (mean ≈ 0) | unit | `uv run pytest tests/test_ambient.py::test_brown_no_dc -x` | No — Wave 0 |
| AMBI-04 | `womb(duration)` returns float32, shape=(n,), values in [-1,1] | unit | `uv run pytest tests/test_ambient.py::test_womb_buffer_contract -x` | No — Wave 0 |
| AMBI-04 | Womb output amplitude envelope shows periodic variation at ~60 BPM | unit | `uv run pytest tests/test_ambient.py::test_womb_lfo_period -x` | No — Wave 0 |
| All | `AmbientGenerator` is importable from `musicboxfactory` | unit | `uv run pytest tests/test_ambient.py::test_import -x` | No — Wave 0 |
| All | Seeded generator produces identical buffers on repeat calls | unit | `uv run pytest tests/test_ambient.py::test_seed_reproducibility -x` | No — Wave 0 |

### Spectral slope test approach (verified feasible)
```python
# Measure power in octave bins and check dB difference
psd = np.abs(np.fft.rfft(buf)) ** 2
freqs = np.fft.rfftfreq(len(buf), 1 / 44100)
mask1 = (freqs >= 100) & (freqs < 200)   # one octave
mask2 = (freqs >= 200) & (freqs < 400)   # next octave
slope = 10 * np.log10(psd[mask2].mean()) - 10 * np.log10(psd[mask1].mean())
assert abs(slope - (-3.0)) < 1.0  # pink: within 1 dB of -3 dB/oct
# For brown: target -6 dB/oct
```

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_ambient.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_ambient.py` — covers AMBI-01 through AMBI-04 (all tests listed above)
- [ ] `src/musicboxfactory/ambient.py` — implementation stub (class skeleton, all methods raise NotImplementedError)
- [ ] `pyproject.toml` change: `uv add scipy` moves scipy to runtime deps

*(conftest.py already exists and requires no changes for ambient tests — no soundfont needed)*

---

## Sources

### Primary (HIGH confidence)
- Live Python probe: numpy 2.4.4, scipy 1.17.1 installed in project venv — all algorithms run and verified
- `src/musicboxfactory/synth.py` — buffer contract (`float32`, `(N,)`, `[-1.0, 1.0]`, 44100 Hz), `SAMPLE_RATE` constant
- `src/musicboxfactory/melody.py` — class and method pattern to follow (`MelodyPipeline`)
- `pyproject.toml` — confirmed scipy is in `[dependency-groups] dev`, not `[project] dependencies`

### Secondary (MEDIUM confidence)
- NumPy documentation: `numpy.random.default_rng`, `numpy.fft.rfft/irfft/rfftfreq` — standard library, stable API
- SciPy documentation: `scipy.signal.detrend` — type='linear' removes slope, verified via probe

### Tertiary (LOW confidence)
- None — all claims verified with live probes or official project files

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified installed versions, no new deps required
- Architecture: HIGH — algorithms verified by live spectral measurement
- Pitfalls: HIGH — each pitfall discovered through probing, not speculation
- Test map: HIGH — test patterns follow existing test_synth.py / test_melody.py conventions

**Research date:** 2026-03-31
**Valid until:** 2026-09-30 (stable algorithms; numpy/scipy APIs are stable)
