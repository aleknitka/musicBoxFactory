# Phase 4: Mixing & WAV Output - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a `Mixer` class that combines a melody buffer and an ambient buffer at caller-specified volumes, tiles them to fill a requested duration, normalizes the result to prevent int16 clipping, and writes a loop-safe WAV file. Optional fade-in is supported; fade-out is supported only for non-looping exports (raises `ValueError` if used with loop-safe output).

</domain>

<decisions>
## Implementation Decisions

### API Shape
- **D-01:** `Mixer` class — `Mixer(melody_vol=0.8, ambient_vol=0.3)`. Caller constructs with volume config, then calls `.mix()` and `.write()`. Consistent with `Synth`, `MelodyPipeline`, `AmbientGenerator`.
- **D-02:** `Mixer` is exported from the top-level package (`from musicboxfactory import Mixer`).

### Volume Model
- **D-03:** Two independent `0.0–1.0` float parameters: `melody_vol` and `ambient_vol`. Linear scale. Values do not need to sum to 1.0 — normalization (OUT-02) prevents clipping at any combination.

### Duration + Tiling
- **D-04:** Mixer tiles buffers automatically. The caller passes the raw melody and ambient buffers (which may be short) plus a `duration` in seconds to `write()`. The mixer tiles each buffer independently to fill the requested duration, then trims to exactly `int(duration * 44100)` samples.
- **D-05:** Tiling must preserve the zero-crossing loop safety of each input buffer — tile at the natural buffer boundary, not mid-sample.

### Fade vs Loop Contract
- **D-06:** Fade-in (`fade_in` seconds) is always permitted — applied at the file start, does not affect loop safety at the end.
- **D-07:** Fade-out (`fade_out` seconds) is mutually exclusive with loop-safe output. If `fade_out > 0` is passed, `write()` raises `ValueError` with a clear message explaining the conflict and directing the caller to use fade-out only for non-looping exports. This is consistent with the library's fail-fast pattern (`ValueError` for invalid input, same as `Synth`).
- **D-08:** A non-looping export path is NOT in scope for Phase 4. `fade_out` raises `ValueError`. If a non-looping export is needed in future, it's a v2 feature.

### Normalization
- **D-09:** Normalization is applied to the mixed buffer before WAV conversion. Peak normalization: scale so the maximum absolute sample value is ≤ 1.0, then convert to int16. No clipping distortion at any volume combination.

### Claude's Discretion
- Exact zero-crossing boundary enforcement implementation (e.g., trim to nearest zero crossing before tiling, or after).
- Whether `mix()` returns a normalized buffer or raw mixed buffer (normalization may happen only in `write()`).
- Default values for `melody_vol` and `ambient_vol` if caller omits them.
- Whether `fade_in` defaults to 0.0 or is a required parameter.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §Mixing & Output — OUT-01 through OUT-05 define the acceptance criteria for this phase
- `.planning/ROADMAP.md` §Phase 4 — success criteria and phase goal

### Project Constraints
- `.planning/PROJECT.md` §Constraints — Python >=3.13, numpy 2.x, scipy for WAV output, WAV-only, no CLI
- `.planning/PROJECT.md` §Context — `scipy` or stdlib `wave` for WAV output

### Buffer Contract (locked from Phase 1)
- `.planning/phases/01-tone-synthesis/01-CONTEXT.md` §D-02, D-03 — float32, mono, 44100 Hz, [-1.0, 1.0]. All inter-module buffers follow this contract.

### Existing Module Patterns
- `src/musicboxfactory/synth.py` — class-based pattern, fail-fast ValueError, SAMPLE_RATE constant
- `src/musicboxfactory/__init__.py` — how public API is exported (Mixer must be added here)

No external ADRs or specs — all decisions captured in this context file.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SAMPLE_RATE = 44100` constant in `synth.py` — import and reuse, do not redefine
- `AmbientGenerator`, `MelodyPipeline`, `Synth` — all produce float32 mono 44100 Hz buffers; no conversion needed before mixing

### Established Patterns
- Class with `__init__` accepting config params, methods for operations
- `ValueError` raised immediately with descriptive message on invalid input
- `from __future__ import annotations` at top of each module
- Public API docstring block at module top listing class name, constructor, and method signatures

### Integration Points
- `Mixer` receives outputs from `MelodyPipeline` and `AmbientGenerator` — both already produce compliant buffers
- `mixer.py` is a new file; `Mixer` must be added to `__init__.py` `__all__` and import line

</code_context>

<specifics>
## Specific Ideas

- The canonical usage pattern (from `__init__.py` docstring style): `mixer = Mixer(melody_vol=0.8, ambient_vol=0.3)` → `buf = mixer.mix(melody_buf, ambient_buf)` → `mixer.write(buf, path, duration=600.0)`
- `ValueError` message for `fade_out` conflict should be actionable: explain that fade-out breaks loop safety and suggest omitting it for loop-safe files.

</specifics>

<deferred>
## Deferred Ideas

- Non-looping export path (fade-out without loop safety) — v2 feature, not in Phase 4 scope
- Crossfade at loop seam — mentioned during discussion; decided against for Phase 4 complexity

</deferred>

---

*Phase: 04-mixing-wav-output*
*Context gathered: 2026-04-01*
