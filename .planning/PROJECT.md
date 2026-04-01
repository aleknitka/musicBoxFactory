# Music Box Factory

## What This Is

A Python library that programmatically generates baby sleep audio as WAV files — combining a music box melody rendered from a caller-provided `.sf2` soundfont layered over generated ambient sound (white/pink/brown noise, womb/heartbeat). Ships with built-in lullaby presets, accepts custom note sequences, and can procedurally generate melodies via circle-of-fifths traversal.

## Core Value

Given a melody (preset or custom) and an ambient type, produce a seamlessly loopable WAV file that sounds warm and sleep-inducing for babies.

## Requirements

### Validated

- [x] Music box tone synthesis — soundfont rendering via FluidSynth, `Synth` class, named presets (Validated in Phase 1: Tone Synthesis)
- [x] Built-in lullaby presets (Twinkle Twinkle, Brahms' Lullaby, Mary Had a Little Lamb) (Validated in Phase 2: Melody Pipeline)
- [x] Custom melody input via note sequences (pitch + duration) (Validated in Phase 2: Melody Pipeline)
- [x] Procedural melody generation via circle-of-fifths traversal (Validated in Phase 2: Melody Pipeline)
- [x] Loop-safe melody buffer with zero-crossing trim (Validated in Phase 2: Melody Pipeline)

### Active

- [x] Ambient sound generation — white/pink/brown noise, womb/heartbeat pulse (Validated in Phase 3: Ambient Generation)
- [ ] Layering — mix melody and ambient at configurable relative volumes
- [ ] WAV output — generates a loopable WAV file of configurable duration
- [ ] Clean Python library API — callable functions, no CLI required

### Out of Scope

- CLI interface — library-first; a CLI wrapper can be added later by users
- MIDI file input — out of scope for v1; note sequences are sufficient
- Rain/water ambient — not requested; keep ambient set focused
- Audio playback — library generates files only, does not play them
- Streaming / real-time audio — output is always a rendered WAV

## Context

- Blank-slate Python package (`musicboxfactory`, Python >=3.13, no deps yet)
- Pure Python synthesis preferred — no heavy DSP frameworks needed for this scope
- `numpy` for signal generation, `scipy` or stdlib `wave` for WAV output are the natural choices
- Music box character comes from a decaying sinusoidal tone per note (attack + exponential envelope)
- Ambient layers are generated noise signals shaped to the target spectrum (pink/brown via filtering)
- Womb/heartbeat: low rumble + rhythmic low-frequency pulse (~60 BPM)

## Constraints

- **Language**: Python >=3.13 — set in pyproject.toml
- **Dependencies**: NumPy 2.x + SciPy for WAV output; FluidSynth (C library + python bindings) for soundfont rendering — system dep is acceptable given the soundfont requirement
- **Output format**: WAV only (no MP3, OGG, etc.) for v1
- **Loopability**: Generated audio must loop seamlessly (no click at loop point)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Soundfont rendering (not pure synthesis) | Richer, configurable timbre; caller provides .sf2 | — Pending |
| Library API, not CLI | User specified reusable Python library as primary artifact | — Pending |
| numpy + stdlib wave | Minimal deps; sufficient for synthesis and WAV writing | — Pending |

---
*Last updated: 2026-04-01 — Phase 3 complete (Ambient Generation)*
