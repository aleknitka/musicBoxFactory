---
phase: 02-melody-pipeline
plan: "02"
subsystem: melody
tags: [tdd, melody, lullaby-presets, circle-of-fifths, sequencer, green-state]
dependency_graph:
  requires: [02-melody-pipeline/02-01]
  provides: [melody-pipeline-implementation, lullaby-presets, procedural-generation]
  affects: [03-ambient-generation, 04-mixer-wav-output]
tech_stack:
  added: []
  patterns: [numpy-concatenate, zero-crossing-trim, seeded-rng, circle-of-fifths-markov]
key_files:
  created: []
  modified:
    - src/musicboxfactory/melody.py
    - src/musicboxfactory/__init__.py
decisions:
  - Pre-existing mypy unused-ignore in synth.py is out-of-scope; deferred to a future fix
  - noqa F401 not needed after Task 2 completed (random import is now actively used)
  - SAMPLE_RATE imported directly (noqa removed from synth import since it is now used in render_sequence)
metrics:
  duration_seconds: 245
  completed_date: "2026-04-01"
  tasks_completed: 3
  files_created: 0
  files_modified: 2
---

# Phase 02 Plan 02: Melody Pipeline Implementation Summary

**One-liner:** Full MelodyPipeline implementation with three lullaby preset tables, seeded circle-of-fifths procedural generator, and zero-crossing loop trimmer — turning all 12 RED unit tests GREEN.

## What Was Built

Two files were modified to complete the melody pipeline implementation:

### 1. `src/musicboxfactory/melody.py` (full implementation)

**`_trim_to_zero_crossing(buf, search_window=2048)`**
- Searches the last `search_window` samples for the last sign change
- Returns the buffer sliced to that point to prevent audible clicks at loop boundaries
- No-ops on buffers with fewer than 2 samples

**`render_sequence(synth, notes, gap_seconds=0.05)`**
- Iterates note list, calls `synth.render(note, duration)` per pair
- Inserts silence gap (default 50 ms) between notes via `np.concatenate`
- Skips zero/negative duration notes
- Trims combined buffer to last zero crossing
- Returns `np.zeros(0, dtype=np.float32)` for empty input

**Lullaby preset tables (hardcoded note sequences):**
- `TWINKLE_TWINKLE`: 42 notes — full two-verse Twinkle Twinkle Little Star
- `BRAHMS_LULLABY`: 21 notes — Brahms' Lullaby one phrase
- `MARY_HAD_A_LITTLE_LAMB`: 25 notes — Mary Had a Little Lamb

**`generate_circle_of_fifths(num_notes, num_fifths, root, octave, note_duration, seed)`**
- Uses `random.Random(seed)` for deterministic output
- Visits keys related by fifths (each +7 semitones) then returns to root
- Walks scale degrees with weighted random steps (forward/back, +1/+2)
- Clamps octave to [3, 5] range to prevent extreme notes
- Returns exactly `num_notes` (note_name, duration) tuples

**`MelodyPipeline` class:**
- `from_preset(name)`: validates name against LULLABY_PRESETS, raises `ValueError` for unknowns
- `from_notes(notes)`: direct pass-through to render_sequence
- `from_procedural(num_notes, num_fifths, seed)`: generates then renders circle-of-fifths melody

### 2. `src/musicboxfactory/__init__.py`

Added `MelodyPipeline` and `LULLABY_PRESETS` exports alongside existing `Synth` and `PRESETS`:
```python
from musicboxfactory.melody import LULLABY_PRESETS, MelodyPipeline
__all__ = ["Synth", "PRESETS", "MelodyPipeline", "LULLABY_PRESETS"]
```

## Test Results (GREEN State)

```
16 passed, 8 skipped in 0.16s
(12 unit tests pass; 4 integration tests skipped — no soundfont on this machine)
```

## Deviations from Plan

### Out-of-Scope Issues Deferred

**Pre-existing mypy warning in synth.py**
- `src/musicboxfactory/synth.py:14: error: Unused "type: ignore" comment [unused-ignore]`
- This existed before this plan and is not caused by any changes here
- Deferred to a future maintenance fix

## Known Stubs

None. All stubs from Plan 01 have been resolved. The melody pipeline is fully functional.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| Task 1: _trim_to_zero_crossing and render_sequence | def8ca8 | feat(02-02): implement _trim_to_zero_crossing and render_sequence |
| Task 2: lullaby presets, generate_circle_of_fifths, MelodyPipeline | e62e5a9 | feat(02-02): implement lullaby presets, generate_circle_of_fifths, and MelodyPipeline |
| Task 3: update __init__.py exports | ba631a5 | feat(02-02): export MelodyPipeline and LULLABY_PRESETS from package __init__.py |

## Self-Check: PASSED
