# Phase 4: Mixing & WAV Output - Research

**Researched:** 2026-04-02
**Domain:** NumPy buffer mixing, peak normalization, zero-crossing tiling, scipy WAV output
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `Mixer` class — `Mixer(melody_vol=0.8, ambient_vol=0.3)`. Caller constructs with volume config, then calls `.mix()` and `.write()`. Consistent with `Synth`, `MelodyPipeline`, `AmbientGenerator`.
- **D-02:** `Mixer` is exported from the top-level package (`from musicboxfactory import Mixer`).
- **D-03:** Two independent `0.0–1.0` float parameters: `melody_vol` and `ambient_vol`. Linear scale. Values do not need to sum to 1.0 — normalization (OUT-02) prevents clipping at any combination.
- **D-04:** Mixer tiles buffers automatically. The caller passes the raw melody and ambient buffers (which may be short) plus a `duration` in seconds to `write()`. The mixer tiles each buffer independently to fill the requested duration, then trims to exactly `int(duration * 44100)` samples.
- **D-05:** Tiling must preserve the zero-crossing loop safety of each input buffer — tile at the natural buffer boundary, not mid-sample.
- **D-06:** Fade-in (`fade_in` seconds) is always permitted — applied at the file start, does not affect loop safety at the end.
- **D-07:** Fade-out (`fade_out` seconds) is mutually exclusive with loop-safe output. If `fade_out > 0` is passed, `write()` raises `ValueError` with a clear message explaining the conflict.
- **D-08:** A non-looping export path is NOT in scope for Phase 4. `fade_out` raises `ValueError`.
- **D-09:** Normalization is applied to the mixed buffer before WAV conversion. Peak normalization: scale so the maximum absolute sample value is ≤ 1.0, then convert to int16.

### Claude's Discretion

- Exact zero-crossing boundary enforcement implementation (e.g., trim to nearest zero crossing before tiling, or after).
- Whether `mix()` returns a normalized buffer or raw mixed buffer (normalization may happen only in `write()`).
- Default values for `melody_vol` and `ambient_vol` if caller omits them.
- Whether `fade_in` defaults to 0.0 or is a required parameter.

### Deferred Ideas (OUT OF SCOPE)

- Non-looping export path (fade-out without loop safety) — v2 feature, not in Phase 4 scope
- Crossfade at loop seam — mentioned during discussion; decided against for Phase 4 complexity
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OUT-01 | Caller can mix a melody layer and an ambient layer at configurable relative volumes | Verified: linear multiply + add on float32 ndarrays; normalization prevents overflow at any combination |
| OUT-02 | Mixed output is normalized to prevent int16 clipping/overflow before WAV write | Verified: peak normalization (`buf / np.abs(buf).max()`) guarantees peak ≤ 1.0 before `* 32767` int16 conversion |
| OUT-03 | Caller can render the mixed output to a WAV file at a specified duration | Verified: `scipy.io.wavfile.write(path, 44100, int16_buf)`; tiling gives exact sample count `int(duration * 44100)` |
| OUT-04 | Generated WAV loops seamlessly — zero-crossing boundary enforcement, no audible click at loop point | Verified: melody.py already ships `_trim_to_zero_crossing`; apply before tiling so boundary is click-free at each tile join |
| OUT-05 | Caller can specify fade-in and fade-out duration at file boundaries | Verified: `np.linspace` ramp on leading samples; fade-out raises ValueError per D-07/D-08 |
</phase_requirements>

---

## Summary

Phase 4 is a pure NumPy / SciPy operation with no new system dependencies. The full pipeline is: receive two float32 mono buffers → scale by independent volumes → sum → peak-normalize → tile each source buffer independently to reach the requested duration → trim to exact sample count → apply optional fade-in → convert to int16 → write with `scipy.io.wavfile.write`.

All primitives are already present in the installed environment: NumPy 2.4.4 for buffer arithmetic, SciPy 1.17.1 for WAV output, and a verified `_trim_to_zero_crossing` helper in `melody.py` that is importable and can be reused in `mixer.py`. The zero-crossing trimming should be applied to each input buffer before tiling, not to the full tiled output; this guarantees every tile boundary is click-free, satisfying OUT-04.

The primary discretion decision is whether `mix()` returns a raw or normalized buffer. Recommended: `mix()` returns a raw mixed buffer (enables the caller to inspect values before write), and normalization is applied inside `write()` immediately before int16 conversion. This mirrors the pattern from `synth.py`, where `render()` normalizes only its own output, not the caller's downstream use.

**Primary recommendation:** Implement `mixer.py` following the class pattern from `synth.py`. Reuse `_trim_to_zero_crossing` from `melody.py` directly. Use `scipy.io.wavfile.write` with int16 output. Keep `mix()` return type as raw float32 and normalize inside `write()`.

---

## Project Constraints (from CLAUDE.md)

| Directive | Detail |
|-----------|--------|
| Python version | >=3.13 |
| Package manager | `uv` |
| Test runner | `uv run pytest` |
| Type checker | `uv run mypy src/` (strict mode) |
| Linter | `uv run ruff check src/` |
| WAV output | `scipy.io.wavfile.write` — already in runtime deps |
| Buffer contract | float32, mono, 44100 Hz, shape `(N,)`, values in [-1.0, 1.0] |
| No CLI | Library only |
| No MP3/OGG | WAV output only |
| Module header | `from __future__ import annotations` at top of each module |
| Public API docstring | Module-level docstring block listing class + methods |
| Fail-fast | Raise `ValueError` immediately with descriptive message on invalid input |
| Export | `Mixer` must be added to `__init__.py` `__all__` and import line |
| Constant reuse | Import `SAMPLE_RATE = 44100` from `musicboxfactory.synth`, do not redefine |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.4.4 (installed) | Buffer arithmetic: scaling, summing, tiling, fade ramps | Project buffer contract; all existing modules use it |
| scipy | 1.17.1 (installed) | `scipy.io.wavfile.write` for WAV file output | Already a runtime dependency; confirmed in pyproject.toml |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| stdlib `pathlib` / `str` | — | WAV output path parameter | `scipy.io.wavfile.write` accepts string or open file handle |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| int16 output (D-09) | float32 WAV output | scipy supports float32 WAV; int16 is more universally playable by media players, matches D-09 |
| scipy.io.wavfile.write | stdlib `wave` module | PROJECT.md explicitly chose scipy over stdlib wave; do not change |

**Installation:** No new packages needed. All dependencies are already in `pyproject.toml`.

**Version verification (live):**
- numpy: 2.4.4 (confirmed via `uv run python -c "import numpy as np; print(np.__version__)"`)
- scipy: 1.17.1 (confirmed via `uv run python -c "import scipy; print(scipy.__version__)"`)

---

## Architecture Patterns

### Recommended Project Structure

No new directories needed. One new file:

```
src/musicboxfactory/
├── synth.py         # Phase 1 — SAMPLE_RATE lives here; import it
├── melody.py        # Phase 2 — _trim_to_zero_crossing lives here; reuse it
├── ambient.py       # Phase 3 — AmbientGenerator
├── mixer.py         # Phase 4 — NEW: Mixer class
└── __init__.py      # Add Mixer to __all__ and import line
```

Test file:

```
tests/
├── conftest.py      # existing — no changes needed
├── test_mixer.py    # Phase 4 — NEW: unit + integration tests
```

### Pattern 1: Class with constructor config + methods

All existing classes follow this pattern. `Mixer` continues it.

```python
# Source: src/musicboxfactory/synth.py (established pattern)
from __future__ import annotations

from musicboxfactory.synth import SAMPLE_RATE
from musicboxfactory.melody import _trim_to_zero_crossing

class Mixer:
    """..."""
    def __init__(self, melody_vol: float = 0.8, ambient_vol: float = 0.3) -> None:
        ...

    def mix(self, melody: np.ndarray, ambient: np.ndarray) -> np.ndarray:
        ...  # returns raw mixed float32 buffer

    def write(
        self,
        buf: np.ndarray,
        path: str,
        duration: float,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
    ) -> None:
        ...  # normalizes, tiles, writes WAV
```

### Pattern 2: Zero-crossing tiling (D-04, D-05, OUT-04)

Apply `_trim_to_zero_crossing` to each input buffer before tiling. This makes every tile boundary click-free.

```python
# Source: verified experimentally (2026-04-02)
import numpy as np
from musicboxfactory.melody import _trim_to_zero_crossing

def _tile_to_length(buf: np.ndarray, n_samples: int) -> np.ndarray:
    """Tile buf to at least n_samples, then trim to exactly n_samples."""
    if len(buf) == 0:
        return np.zeros(n_samples, dtype=np.float32)
    n_tiles = int(np.ceil(n_samples / len(buf)))
    return np.tile(buf, n_tiles)[:n_samples]

# Usage inside write():
target_n = int(duration * SAMPLE_RATE)
melody_safe = _trim_to_zero_crossing(melody_buf)
ambient_safe = _trim_to_zero_crossing(ambient_buf)
melody_tiled = _tile_to_length(melody_safe, target_n)
ambient_tiled = _tile_to_length(ambient_safe, target_n)
```

### Pattern 3: Peak normalization + int16 conversion (D-09, OUT-02)

```python
# Source: verified experimentally (2026-04-02)
import numpy as np

def _normalize(buf: np.ndarray) -> np.ndarray:
    peak = float(np.abs(buf).max())
    if peak > 1e-9:
        return buf / peak
    return buf

def _to_int16(buf: np.ndarray) -> np.ndarray:
    # Multiply by 32767 (not 32768) — 32768 causes overflow when value == +1.0
    return (buf * 32767).astype(np.int16)
```

**Critical:** Use `32767` as the multiplier, not `32768`. Multiplying `+1.0 * 32768` as int16 overflows to `-32768`.

### Pattern 4: Fade-in ramp (D-06, OUT-05)

```python
# Source: verified experimentally (2026-04-02)
def _apply_fade_in(buf: np.ndarray, fade_seconds: float) -> np.ndarray:
    fade_samples = min(int(fade_seconds * SAMPLE_RATE), len(buf))
    if fade_samples <= 0:
        return buf
    ramp = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
    result = buf.copy()
    result[:fade_samples] *= ramp
    return result
```

### Pattern 5: ValueError for fade_out (D-07, D-08)

```python
# Source: synth.py fail-fast pattern applied here
def write(self, buf, path, duration, fade_in=0.0, fade_out=0.0):
    if fade_out > 0:
        raise ValueError(
            "fade_out breaks loop safety: a faded-out tail cannot tile seamlessly. "
            "Omit fade_out (keep it at 0.0) for loop-safe WAV files. "
            "Non-looping export with fade_out is a v2 feature."
        )
```

### Anti-Patterns to Avoid

- **Applying `_trim_to_zero_crossing` after tiling the full buffer:** This changes the output length unpredictably and may trim a significant tail off the requested duration. Trim each source before tiling.
- **Using `* 32768` for int16 conversion:** `+1.0 * 32768` overflows int16 to `-32768`. Use `* 32767`.
- **Writing float32 WAV instead of int16:** scipy will write a float32 WAV if passed a float32 array; some media players (especially on mobile/embedded) do not support float32 WAV. Convert to int16 explicitly per D-09.
- **Normalizing inside `mix()` instead of `write()`:** Normalizing in `mix()` hides the true mixed amplitude from the caller and makes it impossible to mix multiple calls into a larger pipeline. Normalize only in `write()` immediately before int16 conversion.
- **Redefining `SAMPLE_RATE`:** It already lives in `synth.py`. Import it.
- **Importing `_trim_to_zero_crossing` as a private symbol:** It is documented as importable in `melody.py`'s module docstring ("Module-level helpers (also importable)"). Cross-module private import is acceptable in this codebase.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WAV file writing | Custom byte packing | `scipy.io.wavfile.write` | Handles RIFF header, chunk sizing, bit depth — 0 lines of custom I/O code |
| Buffer tiling | Manual loop with append | `np.tile` + `[:n]` slice | One line; numpy's tile is written in C |
| Zero-crossing detection | Custom sign-change scanner | `_trim_to_zero_crossing` from `melody.py` | Already tested and in the project |
| Fade ramp | Custom loop | `np.linspace` + in-place multiply | One line; no loop |
| Peak normalization | Custom abs/max loop | `np.abs(buf).max()` then divide | Vectorized; handles zero-signal guard identically to existing modules |

**Key insight:** Every non-trivial operation in this phase has a one- or two-line numpy/scipy solution. The module is almost entirely "glue" code; the complexity is in sequencing the operations correctly.

---

## Common Pitfalls

### Pitfall 1: int16 overflow at boundary value +1.0
**What goes wrong:** `(np.array([1.0], dtype=np.float32) * 32768).astype(np.int16)` produces `-32768`, not `32768`.
**Why it happens:** int16 range is -32768 to +32767 — asymmetric. `+32768` is out of range and wraps.
**How to avoid:** Multiply by `np.iinfo(np.int16).max` = `32767`, not `32768`. After peak normalization the max value is ≤ 1.0, and `1.0 * 32767 = 32767`, which fits in int16.
**Warning signs:** WAV file starts with a loud pop or sounds inverted; int16 array contains `-32768` when input was `+1.0`.

### Pitfall 2: Tiling without zero-crossing trim causes click
**What goes wrong:** If a melody buffer ends at a non-zero sample value (e.g., 0.4), tiling creates a discontinuous jump from 0.4 back to the first sample's value on each loop iteration.
**Why it happens:** `np.tile` repeats the buffer byte-for-byte. It knows nothing about audio continuity.
**How to avoid:** Call `_trim_to_zero_crossing` on each input buffer before tiling. The existing implementation in `melody.py` searches the last 2048 samples for a zero crossing.
**Warning signs:** Audible click or pop every N seconds (where N is the source buffer length).

### Pitfall 3: Tiling after mixing instead of tiling independently
**What goes wrong:** Mixing then tiling produces a longer combined buffer, but if melody and ambient have different natural loop lengths, the combined loop length may not sound right.
**Why it happens:** If melody is 15 s and ambient is 60 s, tiling the combined 15 s buffer means the ambient also loops every 15 s — shorter than its natural period.
**How to avoid:** Tile each buffer independently to `target_n` before summing (D-04 design). This means: `melody_tiled + ambient_tiled`, not `tile(melody + ambient)`.

### Pitfall 4: Memory for long durations
**What goes wrong:** An 8-hour request allocates a 4.73 GB float32 array in memory.
**Why it happens:** `np.tile` returns a fully materialized ndarray.
**How to avoid:** For v1 this is acceptable (no streaming out of scope). Document the limitation. For typical use (10 min = ~100 MB, 30 min = ~300 MB) this is fine on modern hardware. The STATE.md concern about memory is noted but streaming/chunked output is a v2 concern.
**Warning signs:** `MemoryError` raised by `np.tile` for very long durations.

### Pitfall 5: Fade-in applied to pre-tile vs. post-tile buffer
**What goes wrong:** If fade-in is applied to the raw short buffer before tiling, the fade-in ramps up in the first few seconds of the first tile only — which is the correct behavior. But if the fade-in window is longer than the first tile, it gets tiled too, repeating the ramp on each loop.
**Why it happens:** Applying fade-in before `_tile_to_length`.
**How to avoid:** Apply fade-in to the final tiled buffer (after tiling and trimming to `target_n`), not to the input buffer.

---

## Code Examples

### Complete `write()` operation flow

```python
# Source: verified experimentally (2026-04-02); patterns from synth.py
from __future__ import annotations

import numpy as np
from scipy.io import wavfile  # type: ignore[import-untyped]
from musicboxfactory.synth import SAMPLE_RATE
from musicboxfactory.melody import _trim_to_zero_crossing

def write(
    buf: np.ndarray,     # raw mixed float32 buffer from mix()
    path: str,
    duration: float,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
) -> None:
    if fade_out > 0:
        raise ValueError(
            "fade_out breaks loop safety: a faded-out tail cannot tile seamlessly. "
            "Omit fade_out for loop-safe WAV files. "
            "Non-looping export with fade_out is a v2 feature."
        )

    target_n = int(duration * SAMPLE_RATE)

    # Tile to requested duration preserving zero-crossing boundaries
    buf_safe = _trim_to_zero_crossing(buf)
    n_tiles = int(np.ceil(target_n / len(buf_safe))) if len(buf_safe) > 0 else 1
    tiled = np.tile(buf_safe, n_tiles)[:target_n]

    # Apply fade-in on the tiled, full-duration buffer
    if fade_in > 0:
        fade_samples = min(int(fade_in * SAMPLE_RATE), len(tiled))
        ramp = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
        tiled[:fade_samples] *= ramp

    # Normalize to prevent int16 clipping (D-09)
    peak = float(np.abs(tiled).max())
    if peak > 1e-9:
        tiled = tiled / peak

    # Convert to int16 — use 32767 to stay inside int16 range
    as_int16 = (tiled * 32767).astype(np.int16)
    wavfile.write(path, SAMPLE_RATE, as_int16)
```

### `mix()` method

```python
# Source: verified experimentally (2026-04-02)
def mix(self, melody: np.ndarray, ambient: np.ndarray) -> np.ndarray:
    """Combine melody and ambient at configured volumes. Returns raw float32 buffer."""
    return (melody * self._melody_vol + ambient * self._ambient_vol).astype(np.float32)
```

Note: `mix()` does NOT normalize. Normalization is deferred to `write()`.

### `__init__.py` export addition

```python
# Source: src/musicboxfactory/__init__.py pattern (established)
from musicboxfactory.mixer import Mixer

__all__ = ["Synth", "PRESETS", "MelodyPipeline", "LULLABY_PRESETS", "AmbientGenerator", "Mixer"]
```

The docstring should be extended with the `Mixer` usage example.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `wave` stdlib for WAV output | `scipy.io.wavfile.write` | PROJECT.md decision | Simpler API, direct ndarray support |
| float32 WAV files | int16 WAV files | D-09 (CONTEXT.md) | Broader media player compatibility |

**Deprecated/outdated:**
- `wave` stdlib module: Supported but not used in this project per PROJECT.md decision. Do not introduce it.

---

## Open Questions

1. **`mix()` output buffer length when melody and ambient differ in length**
   - What we know: D-04 specifies tiling happens in `write()`, not `mix()`. If `mix()` is called with buffers of unequal length, NumPy broadcasting will raise a shape mismatch error.
   - What's unclear: Should `mix()` silently tile the shorter buffer to match the longer? Or require equal-length inputs and document that the caller is responsible?
   - Recommendation: Require equal-length inputs in `mix()` (raise `ValueError` if shapes differ). Document that the caller should tile buffers themselves before calling `mix()`, OR have `write()` take melody and ambient buffers directly and tile internally before mixing. The second approach is cleaner and avoids the shape mismatch problem entirely. Recommend: `write()` accepts `melody_buf` and `ambient_buf` separately, tiles them independently to `target_n`, then mixes.

2. **Default values for `melody_vol` and `ambient_vol`**
   - What we know: D-01 shows `Mixer(melody_vol=0.8, ambient_vol=0.3)` as the canonical usage. Claude's discretion on defaults.
   - Recommendation: Default to `melody_vol=0.8, ambient_vol=0.3` — matches the canonical usage in CONTEXT.md and is a reasonable perceptual balance for the target use case.

3. **`fade_in` default: 0.0 vs required**
   - What we know: Claude's discretion.
   - Recommendation: Default to `0.0` (no fade). Makes `write()` callable without keyword arguments in the simple case.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| numpy | Buffer arithmetic | Yes | 2.4.4 | — |
| scipy | WAV output | Yes | 1.17.1 | — |
| pytest | Test runner | Yes | 9.0.2 | — |
| mypy | Type checking | Yes | 1.20.0 | — |
| ruff | Linting | Yes | 0.15.8 | — |

No missing dependencies. All Phase 4 requirements are satisfiable with currently installed packages.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_mixer.py -q` |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OUT-01 | `mix()` returns combined buffer scaled by volumes | unit | `uv run pytest tests/test_mixer.py::test_mix_buffer_contract -x` | No — Wave 0 |
| OUT-01 | `mix()` with different vol combos produces expected relative amplitudes | unit | `uv run pytest tests/test_mixer.py::test_mix_volumes_applied -x` | No — Wave 0 |
| OUT-02 | `write()` normalizes so no int16 sample exceeds 32767 | unit | `uv run pytest tests/test_mixer.py::test_write_no_clipping -x` | No — Wave 0 |
| OUT-02 | High vol combo (1.0+1.0) still produces no clipping | unit | `uv run pytest tests/test_mixer.py::test_write_no_clipping_high_vol -x` | No — Wave 0 |
| OUT-03 | `write()` produces WAV of exactly `int(duration * 44100)` samples | unit | `uv run pytest tests/test_mixer.py::test_write_exact_duration -x` | No — Wave 0 |
| OUT-03 | `write()` produces readable WAV at 44100 Hz | unit | `uv run pytest tests/test_mixer.py::test_write_wav_readable -x` | No — Wave 0 |
| OUT-04 | Tiled output does not have a large amplitude jump at tile boundaries | unit | `uv run pytest tests/test_mixer.py::test_tiling_zero_crossing -x` | No — Wave 0 |
| OUT-05 | fade_in ramp starts from 0 at sample 0 | unit | `uv run pytest tests/test_mixer.py::test_fade_in_applied -x` | No — Wave 0 |
| OUT-05 | fade_out > 0 raises ValueError | unit | `uv run pytest tests/test_mixer.py::test_fade_out_raises -x` | No — Wave 0 |
| OUT-02 | `Mixer` importable from top-level package | unit | `uv run pytest tests/test_mixer.py::test_import -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_mixer.py -q`
- **Per wave merge:** `uv run pytest -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_mixer.py` — covers OUT-01 through OUT-05 (all 10 tests above)
- [ ] `src/musicboxfactory/mixer.py` — module does not yet exist

*(Framework, conftest, and all other infrastructure already exist — no new fixtures or config needed.)*

---

## Sources

### Primary (HIGH confidence)
- Live environment: `uv run python` — scipy 1.17.1, numpy 2.4.4 confirmed installed
- `scipy.io.wavfile.write` — API verified via `help(wavfile.write)` in live environment
- `src/musicboxfactory/synth.py` — class pattern, SAMPLE_RATE, ValueError convention, normalization idiom
- `src/musicboxfactory/melody.py` — `_trim_to_zero_crossing` source confirmed importable and tested
- `src/musicboxfactory/ambient.py` — buffer contract confirmation, peak normalization pattern
- `pyproject.toml` — dependency versions and test infrastructure
- Experimental verification — int16 conversion overflow, tiling arithmetic, full pipeline correctness

### Secondary (MEDIUM confidence)
- scipy docs (in-process help text) — `wavfile.write` accepts string path, rate int, data ndarray; dtype determines bit depth

### Tertiary (LOW confidence)
- None required — all findings verified from live environment and source code

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — confirmed installed versions via live interpreter
- Architecture: HIGH — patterns directly copied from existing modules in the same codebase
- Pitfalls: HIGH — int16 overflow and tile discontinuity verified experimentally; memory numbers computed analytically
- Test map: HIGH — test names and commands designed to match existing project conventions

**Research date:** 2026-04-02
**Valid until:** 2026-06-01 (stable libraries; numpy/scipy APIs are long-lived)
