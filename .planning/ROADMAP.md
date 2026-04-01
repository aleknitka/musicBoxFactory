# Roadmap: Music Box Factory

## Overview

Build a pure-Python audio synthesis library that produces seamlessly loopable baby sleep WAV files. The pipeline flows from tone synthesis (soundfont rendering, named instruments) through melody construction (presets, custom sequences, procedural generation) to ambient noise generation (white/pink/brown/womb), culminating in a mixer that combines layers and writes a correctly normalized, loop-safe WAV file. Each phase delivers one independently verifiable capability before the next layer is added.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Tone Synthesis** - Render music box tones from a .sf2 soundfont with named instrument presets (completed 2026-03-31)
- [ ] **Phase 2: Melody Pipeline** - Sequence notes into loopable melodies using presets, custom input, or procedural generation
- [ ] **Phase 3: Ambient Generation** - Produce white, pink, brown, and womb/heartbeat noise buffers
- [ ] **Phase 4: Mixing & WAV Output** - Combine melody and ambient layers, normalize, and write a loop-safe WAV file

## Phase Details

### Phase 1: Tone Synthesis
**Goal**: Callers can render music box tones for any note from a caller-provided soundfont
**Depends on**: Nothing (first phase)
**Requirements**: TONE-01, TONE-02
**Success Criteria** (what must be TRUE):
  1. Caller can pass a path to a `.sf2` file and get back an audio buffer for a named note (e.g. `"c4"`)
  2. Caller can select a named instrument preset (`"music_box"`, `"celesta"`, `"bells"`) and have it map to the correct MIDI patch in the soundfont
  3. Rendered tone has a perceptibly warm, decaying timbre — not a flat sine wave
  4. A single rendered note can be written to a WAV file and heard to confirm tone quality
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Scaffold: install deps, create package skeleton, write failing test stubs (TONE-01, TONE-02)
- [x] 01-02-PLAN.md — Implement: Synth class in synth.py, turn test suite GREEN (TONE-01, TONE-02)

### Phase 2: Melody Pipeline
**Goal**: Callers can produce a full loopable melody from presets, custom note sequences, or procedural generation
**Depends on**: Phase 1
**Requirements**: MELO-01, MELO-02, MELO-03
**Success Criteria** (what must be TRUE):
  1. Caller can select a built-in lullaby preset (e.g. Twinkle Twinkle, Brahms' Lullaby) and receive a melody audio buffer
  2. Caller can supply a custom list of `(note, duration)` tuples and receive the corresponding melody buffer
  3. Caller can invoke procedural generation and receive a novel melody that traverses the circle of fifths
  4. A melody buffer rendered to WAV plays back without an audible click at the loop boundary
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md — Scaffold: write failing test stubs for MELO-01/02/03, create melody.py skeleton (MELO-01, MELO-02, MELO-03)
- [ ] 02-02-PLAN.md — Implement: render_sequence, presets, procedural generator, MelodyPipeline class, update __init__.py (MELO-01, MELO-02, MELO-03)

### Phase 3: Ambient Generation
**Goal**: Callers can generate any of the four ambient sound types as audio buffers
**Depends on**: Phase 1
**Requirements**: AMBI-01, AMBI-02, AMBI-03, AMBI-04
**Success Criteria** (what must be TRUE):
  1. Caller can generate a white noise buffer of a specified duration with flat spectral distribution
  2. Caller can generate a pink noise buffer with a −3 dB/octave rolloff (no DC drift)
  3. Caller can generate a brown noise buffer with a −6 dB/octave rolloff (no DC drift)
  4. Caller can generate a womb/heartbeat buffer: brown noise base with a rhythmic ~60 BPM low-frequency pulse audible on playback
**Plans**: TBD

### Phase 4: Mixing & WAV Output
**Goal**: Callers can mix melody and ambient layers and write a normalized, loop-safe WAV file
**Depends on**: Phase 2, Phase 3
**Requirements**: OUT-01, OUT-02, OUT-03, OUT-04, OUT-05
**Success Criteria** (what must be TRUE):
  1. Caller can mix a melody buffer and an ambient buffer at independently specified volume levels and receive a single combined buffer
  2. Mixed output is automatically normalized so no sample exceeds ±1.0 before WAV conversion — no clipping distortion audible at any volume combination
  3. Caller can specify output duration in seconds and receive a WAV file of exactly that length
  4. Generated WAV file plays back in a loop with no audible click at the boundary (zero-crossing enforced)
  5. Caller can specify fade-in and fade-out durations applied at the file boundaries
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Tone Synthesis | 2/2 | Complete   | 2026-03-31 |
| 2. Melody Pipeline | 0/2 | Not started | - |
| 3. Ambient Generation | 0/? | Not started | - |
| 4. Mixing & WAV Output | 0/? | Not started | - |
