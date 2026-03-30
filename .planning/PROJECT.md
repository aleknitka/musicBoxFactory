# Music Box Factory

## What This Is

A Python library that programmatically generates baby sleep audio as WAV files — combining a music box melody rendered from a caller-provided `.sf2` soundfont layered over generated ambient sound (white/pink/brown noise, womb/heartbeat). Ships with built-in lullaby presets, accepts custom note sequences, and can procedurally generate melodies via circle-of-fifths traversal.

## Core Value

Given a melody (preset or custom) and an ambient type, produce a seamlessly loopable WAV file that sounds warm and sleep-inducing for babies.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Music box tone synthesis — plucked tine timbre with attack + exponential decay, warm and sleep-inducing
- [ ] Built-in lullaby presets (Twinkle Twinkle, Brahms' Lullaby, etc.)
- [ ] Custom melody input via note sequences (pitch + duration)
- [ ] Ambient sound generation — white/pink noise, womb/heartbeat pulse, fan/brown noise
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
*Last updated: 2026-03-30 after initial questioning*
