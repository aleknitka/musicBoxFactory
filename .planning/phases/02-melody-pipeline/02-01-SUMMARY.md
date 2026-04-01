---
phase: 02-melody-pipeline
plan: "01"
subsystem: melody
tags: [tdd, scaffold, melody, red-state]
dependency_graph:
  requires: [01-tone-synthesis/01-02]
  provides: [melody-test-scaffold, melody-module-stub]
  affects: [02-02]
tech_stack:
  added: []
  patterns: [tdd-red-state, mock-spec-fixture, notimplementederror-stubs]
key_files:
  created:
    - tests/test_melody.py
    - src/musicboxfactory/melody.py
  modified: []
decisions:
  - LULLABY_PRESETS stubs use empty lists (not None) to allow imports to succeed and keep the dict structure ready for Plan 02
  - SAMPLE_RATE imported with noqa F401 to preserve the import for Plan 02 implementation
  - test_lullaby_presets_contains_expected_keys passes in RED state (constant check only) — acceptable as it verifies the dict structure, not behavior
metrics:
  duration_seconds: 116
  completed_date: "2026-03-31"
  tasks_completed: 2
  files_created: 2
  files_modified: 0
---

# Phase 02 Plan 01: Melody Pipeline TDD Scaffold Summary

**One-liner:** TDD red-state scaffold with 16 test stubs and a NotImplementedError melody.py skeleton establishing the MelodyPipeline/render_sequence/generate_circle_of_fifths contract.

## What Was Built

Two files were created to establish the TDD contract before any production logic is written:

1. **tests/test_melody.py** — 16 test functions covering all three melody requirements:
   - 11 unit tests (no soundfont needed, using `synth_mock` fixture with `Mock(spec=Synth)`)
   - 4 integration tests decorated with `@requires_sf2` (skip without soundfont)
   - 1 constant check test (`test_lullaby_presets_contains_expected_keys`)
   - All behavior tests FAIL with `NotImplementedError` (RED state)

2. **src/musicboxfactory/melody.py** — Module skeleton that makes imports succeed:
   - `MelodyPipeline` class with `from_preset`, `from_notes`, `from_procedural` methods
   - `render_sequence` module-level function
   - `generate_circle_of_fifths` module-level function
   - `_trim_to_zero_crossing` helper function
   - `LULLABY_PRESETS` dict with `twinkle`, `brahms`, `mary` keys (empty list stubs)
   - `NoteSequence` type alias (`list[tuple[str, float]]`)
   - All functions/methods raise `NotImplementedError`

## Test Results (RED State)

```
16 tests collected
11 failed (NotImplementedError)
1 passed (LULLABY_PRESETS constant check — expected)
4 skipped (integration tests — no soundfont on this machine)
```

## Deviations from Plan

None — plan executed exactly as written.

The `noqa: F401` comment was added to the `SAMPLE_RATE` import in melody.py (auto-fix Rule 1) since ruff flagged it as unused in stub state. This is intentional: SAMPLE_RATE will be used in Plan 02 implementation.

## Known Stubs

All stubs are intentional for this TDD RED-state plan:

| File | Symbol | Reason |
|------|--------|--------|
| `src/musicboxfactory/melody.py` | `TWINKLE_TWINKLE = []` | Empty until Plan 02 implements lullaby note tables |
| `src/musicboxfactory/melody.py` | `BRAHMS_LULLABY = []` | Empty until Plan 02 implements lullaby note tables |
| `src/musicboxfactory/melody.py` | `MARY_HAD_A_LITTLE_LAMB = []` | Empty until Plan 02 implements lullaby note tables |
| `src/musicboxfactory/melody.py` | `render_sequence` raises `NotImplementedError` | Plan 02 will implement |
| `src/musicboxfactory/melody.py` | `generate_circle_of_fifths` raises `NotImplementedError` | Plan 02 will implement |
| `src/musicboxfactory/melody.py` | `_trim_to_zero_crossing` raises `NotImplementedError` | Plan 02 will implement |
| `src/musicboxfactory/melody.py` | `MelodyPipeline.*` raises `NotImplementedError` | Plan 02 will implement |

Plan 02 will resolve all stubs.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| Task 1: Write failing test stubs | 881e46d | test(02-01): add failing test stubs for MELO-01, MELO-02, MELO-03 |
| Task 2: Create melody.py skeleton | b1dba0e | feat(02-01): add melody.py module skeleton with stubs |

## Self-Check: PASSED
