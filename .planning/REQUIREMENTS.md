# Requirements: Music Box Factory

**Defined:** 2026-03-30
**Core Value:** Given a melody (preset, custom, or procedurally generated) and an ambient type, produce a seamlessly loopable WAV file that sounds warm and sleep-inducing for babies.

## v1 Requirements

### Tone Synthesis

- [x] **TONE-01**: Caller can render music box tones from a caller-provided `.sf2` soundfont file
- [x] **TONE-02**: Library exposes named instrument presets (e.g. `"music_box"`, `"celesta"`, `"bells"`) that map to General MIDI patch numbers in the soundfont

### Melody

- [x] **MELO-01**: Library ships with built-in lullaby presets (Twinkle Twinkle, Brahms' Lullaby, and others) as note sequences
- [x] **MELO-02**: Caller can provide a custom note sequence as a list of `(note, duration)` tuples (e.g. `[("c4", 4), ("g4", 8)]`)
- [x] **MELO-03**: Library can procedurally generate a novel melody loop by traversing the circle of fifths (Western scales; non-Western deferred to v2)

### Ambient

- [x] **AMBI-01**: Library can generate white noise as an audio buffer
- [x] **AMBI-02**: Library can generate pink noise (FFT-shaped, −3 dB/octave) as an audio buffer
- [x] **AMBI-03**: Library can generate brown noise (FFT-shaped, no DC drift) as an audio buffer
- [x] **AMBI-04**: Library can generate womb/heartbeat ambient (brown noise + ~60 BPM LFO pulse)

### Mixing & Output

- [x] **OUT-01**: Caller can mix a melody layer and an ambient layer at configurable relative volumes
- [x] **OUT-02**: Mixed output is normalized to prevent int16 clipping/overflow before WAV write
- [x] **OUT-03**: Caller can render the mixed output to a WAV file at a specified duration
- [x] **OUT-04**: Generated WAV loops seamlessly — crossfade + zero-crossing boundary enforcement, no audible click at loop point
- [x] **OUT-05**: Caller can specify fade-in and fade-out duration at file boundaries

## v2 Requirements

### Melody

- **MELO-04**: Non-Western scale support for procedural melody generation
- **MELO-05**: Configurable BPM for melody playback

### Tone Synthesis

- **TONE-03**: Configurable decay rate / envelope shape for soundfont-rendered tones

### Output

- **OUT-06**: Library ships with a recommended free soundfont bundle for zero-config use

## Out of Scope

| Feature | Reason |
|---------|--------|
| Bundled .sf2 soundfont | Licensing complexity; caller provides their own free soundfont |
| Pure synthesis fallback (decaying sinusoid) | Soundfont rendering is the primary path; synthesis fallback adds complexity for v1 |
| CLI interface | Library-first; a CLI wrapper can be added later by users |
| MIDI file input | Note sequences are sufficient for v1; MIDI adds a parsing dependency |
| Audio playback | Library generates files only — playback is the caller's concern |
| Streaming / real-time audio | Output is always a rendered WAV file |
| MP3 / OGG output | WAV only for v1; encoding adds dependencies |
| Rain / ocean ambient | Not requested; keep ambient set focused |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TONE-01 | Phase 1 | Complete |
| TONE-02 | Phase 1 | Complete |
| MELO-01 | Phase 2 | Complete |
| MELO-02 | Phase 2 | Complete |
| MELO-03 | Phase 2 | Complete |
| AMBI-01 | Phase 3 | Complete |
| AMBI-02 | Phase 3 | Complete |
| AMBI-03 | Phase 3 | Complete |
| AMBI-04 | Phase 3 | Complete |
| OUT-01 | Phase 4 | Complete |
| OUT-02 | Phase 4 | Complete |
| OUT-03 | Phase 4 | Complete |
| OUT-04 | Phase 4 | Complete |
| OUT-05 | Phase 4 | Complete |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-30*
*Last updated: 2026-03-30 — traceability populated during roadmap creation*
