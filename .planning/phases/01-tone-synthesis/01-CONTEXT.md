# Phase 1: Tone Synthesis - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a Python library component that loads a caller-provided `.sf2` soundfont via FluidSynth and renders individual notes as numpy audio buffers. Callers get back float32 numpy arrays they can pass to the melody pipeline (Phase 2) or write directly to a WAV for inspection. No melody sequencing, no ambient generation, no WAV file writing in this phase — those belong to later phases.

</domain>

<decisions>
## Implementation Decisions

### API Shape
- **D-01:** Stateful `Synth` object — caller constructs with `sf2_path` and `preset`, then calls `synth.render(note, duration)` for each note. Soundfont loads once at construction; render calls are cheap.

### Audio Buffer Contract
- **D-02:** Buffer format is `numpy.ndarray`, dtype `float32`, shape `(N,)` (mono), sample rate **44100 Hz**. Values in `[-1.0, 1.0]`. `N = int(44100 * duration_seconds)`.
- **D-03:** This contract is the inter-phase standard — melody (Phase 2), ambient (Phase 3), and mixer (Phase 4) all operate on this buffer type.

### Note Duration
- **D-04:** Caller-specified duration in seconds: `synth.render('c4', duration=2.0)`. FluidSynth renders note-on then note-off at the boundary. No fixed default; melody pipeline controls note lengths.

### Preset-to-Patch Mapping
- **D-05:** Hardcoded `PRESETS` dict in library: `{'music_box': 10, 'celesta': 8, 'bells': 14}`. Names map to General MIDI patch numbers. Simple, predictable, no configuration required.
- **D-06:** Unknown preset name raises `ValueError` immediately with a clear message listing valid preset names. Fail fast — no silent fallback.

### Claude's Discretion
- Exact MIDI patch numbers for each preset (music_box, celesta, bells) — choose values that produce the warmest, most sleep-appropriate timbre from a standard General MIDI soundfont.
- Whether to expose a `bank` parameter or keep it implicit (bank 0 default).
- FluidSynth initialization details (driver, audio backend settings for offline rendering).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — TONE-01, TONE-02 define the acceptance criteria for this phase
- `.planning/ROADMAP.md` §Phase 1 — success criteria and phase goal

### Project Constraints
- `.planning/PROJECT.md` §Constraints — Python >=3.13, numpy 2.x, FluidSynth (C library + python bindings), WAV-only output, no CLI

No external ADRs or specs — all decisions captured in this context file.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — codebase is a blank stub (`main.py` placeholder only)

### Established Patterns
- None established yet — Phase 1 sets the patterns for all subsequent phases

### Integration Points
- `Synth` object and the float32 mono 44100 Hz buffer contract are the integration surface that Phase 2 (melody) and Phase 4 (mixer) will consume

</code_context>

<specifics>
## Specific Ideas

- Single rendered note should be writable to WAV for manual listening confirmation (per ROADMAP.md success criterion 4 for Phase 1) — not a public API feature, just a dev/test utility
- "Warm, decaying timbre — not a flat sine wave" is the quality bar (ROADMAP.md success criterion 3)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-tone-synthesis*
*Context gathered: 2026-03-30*
