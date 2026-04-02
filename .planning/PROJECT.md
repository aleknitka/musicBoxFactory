# Music Box Factory

## What This Is

A Python library that programmatically generates baby sleep audio as WAV files — combining a music box melody rendered from a caller-provided `.sf2` soundfont layered over generated ambient sound (white/pink/brown noise, womb/heartbeat). Ships with built-in lullaby presets, accepts custom note sequences, and can procedurally generate melodies via circle-of-fifths traversal.

## Core Value

Given a melody (preset or custom) and an ambient type, produce a seamlessly loopable WAV file that sounds warm and sleep-inducing for babies.

## Current State

**v1.0 shipped 2026-04-02.** All 4 phases complete, 14/14 v1 requirements satisfied.

- `Synth` — FluidSynth soundfont rendering, named presets (music_box, celesta, bells)
- `MelodyPipeline` — built-in lullabies, custom note sequences, procedural circle-of-fifths
- `AmbientGenerator` — white/pink/brown noise, womb/heartbeat LFO
- `Mixer` — volume-scaled mixing, peak-normalized loop-safe WAV tiling with optional fade-in

631 LOC source Python + 603 LOC test Python. 38 tests pass (8 FluidSynth integration tests skipped without live soundfont).

## Requirements

### Validated (v1.0)

- ✓ Music box tone synthesis — soundfont rendering via FluidSynth, `Synth` class, named presets — v1.0
- ✓ Built-in lullaby presets (Twinkle Twinkle, Brahms' Lullaby, Mary Had a Little Lamb) — v1.0
- ✓ Custom melody input via note sequences (pitch + duration tuples) — v1.0
- ✓ Procedural melody generation via circle-of-fifths traversal — v1.0
- ✓ Loop-safe melody buffer with zero-crossing trim — v1.0
- ✓ Ambient sound generation — white/pink/brown noise, womb/heartbeat pulse — v1.0
- ✓ Layering — mix melody and ambient at configurable relative volumes — v1.0
- ✓ WAV output — generates a loopable WAV file of configurable duration — v1.0
- ✓ Clean Python library API — callable functions, no CLI required — v1.0

### Active (v2.0 candidates)

- [ ] Non-Western scale support for procedural melody generation (MELO-04)
- [ ] Configurable BPM for melody playback (MELO-05)
- [ ] Configurable decay rate / envelope shape for soundfont-rendered tones (TONE-03)
- [ ] Bundled recommended free soundfont for zero-config use (OUT-06)

### Out of Scope

- CLI interface — library-first; a CLI wrapper can be added later by users
- MIDI file input — note sequences are sufficient for v1
- Audio playback — library generates files only
- Streaming / real-time audio — output is always a rendered WAV
- MP3 / OGG output — WAV only for v1
- Rain/water ambient — not requested; keep ambient set focused

## Context

Shipped v1.0 with 631 LOC Python source + 603 LOC tests.
Tech stack: Python >=3.13, NumPy 2.x, SciPy, FluidSynth (C library) + pyfluidsynth.
TDD methodology used throughout — each phase scaffolded tests before implementation.
8 FluidSynth integration tests require live soundfont; they skip cleanly in CI without one.

## Constraints

- **Language**: Python >=3.13 — set in pyproject.toml
- **Dependencies**: NumPy 2.x + SciPy for WAV output; FluidSynth (C library + python bindings) for soundfont rendering — system dep is acceptable given the soundfont requirement
- **Output format**: WAV only (no MP3, OGG, etc.) for v1
- **Loopability**: Generated audio must loop seamlessly (no click at loop point)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Soundfont rendering (not pure synthesis) | Richer, configurable timbre; caller provides .sf2 | ✓ Good — clean API, avoids synthesis complexity |
| Library API, not CLI | User specified reusable Python library as primary artifact | ✓ Good — clean import surface |
| numpy + scipy for WAV | Minimal deps; sufficient for synthesis and WAV writing | ✓ Good — scipy.io.wavfile handles int16 WAV cleanly |
| TDD scaffold before implementation | RED → GREEN discipline per phase | ✓ Good — caught import/collection issues early in Phase 4 |
| Peak normalization after fade-in | Preserves fade envelope in final WAV | ✓ Good — no clipping even at max volume |
| `fade_out` raises ValueError | Loop safety is non-negotiable for v1 | ✓ Good — clear API contract |
| `_trim_to_zero_crossing` before tiling | Prevents click at loop boundary | ✓ Good — zero clicks in numerical tests |

---
*Last updated: 2026-04-02 — v1.0 milestone complete*
