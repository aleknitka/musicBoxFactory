---
phase: 04-mixing-wav-output
plan: 01
subsystem: testing
tags: [mixer, wav, numpy, scipy, tdd, scaffold]

# Dependency graph
requires:
  - phase: 03-ambient-generation
    provides: AmbientGenerator producing float32 mono buffers at 44100 Hz
  - phase: 02-melody-pipeline
    provides: MelodyPipeline producing float32 mono buffers at 44100 Hz
  - phase: 01-tone-synthesis
    provides: SAMPLE_RATE constant and Synth class

provides:
  - src/musicboxfactory/mixer.py — importable Mixer stub with correct API signatures (D-01)
  - tests/test_mixer.py — 10 failing RED test stubs covering OUT-01 through OUT-05

affects: [04-02-implementation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TDD scaffold: stub raises NotImplementedError, tests fail RED before implementation
    - Module-level import of top-level export placed inside test body to avoid collection errors

key-files:
  created:
    - src/musicboxfactory/mixer.py
    - tests/test_mixer.py
  modified: []

key-decisions:
  - "Module-level from musicboxfactory import Mixer removed from test file header — moved inside test_import body to allow collection; ImportError is the RED state for that test"

patterns-established:
  - "Pattern: Top-level package export test uses local import inside test body to avoid blocking collection of sibling tests"

requirements-completed: [OUT-01, OUT-02, OUT-03, OUT-04, OUT-05]

# Metrics
duration: 2min
completed: 2026-04-02
---

# Phase 4 Plan 01: Mixer TDD Scaffold Summary

**Mixer stub (68 lines) and 10 RED test stubs established TDD contract for WAV mixing and output before implementation**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-02T20:47:16Z
- **Completed:** 2026-04-02T20:49:16Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `src/musicboxfactory/mixer.py` with correct `Mixer` API (D-01): `__init__`, `mix`, `write` all raising `NotImplementedError`
- Created `tests/test_mixer.py` with exactly 10 test stubs — all collected, all failing RED as required
- All 10 tests fail via `NotImplementedError` (or `ImportError` for `test_import`) — no skips, no errors at collection time
- Existing test suite unaffected: 28 passed, 8 skipped with `--ignore=tests/test_mixer.py`
- `mypy src/musicboxfactory/mixer.py` exits 0 — stub is type-clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Create mixer.py stub** - `6a42af4` (feat)
2. **Task 2: Write failing test stubs for test_mixer.py** - `02b2a13` (test)

## Files Created/Modified

- `src/musicboxfactory/mixer.py` — Mixer stub class with `__init__`, `mix`, `write` signatures; all raise NotImplementedError
- `tests/test_mixer.py` — 10 RED test stubs covering OUT-01 through OUT-05 (133 lines)

## Decisions Made

- Module-level `from musicboxfactory import Mixer` import removed from test file header and placed inside `test_import` body. Reason: a module-level import that raises `ImportError` at collection time blocks all 10 tests from being collected, turning them from FAIL into ERROR. Moving the import inside the test body allows collection to succeed and `test_import` to fail RED with `ImportError` as intended.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Moved top-level Mixer import inside test_import body**

- **Found during:** Task 2 (Write failing test stubs)
- **Issue:** Plan's example included `from musicboxfactory import Mixer` at module level. This caused `ImportError` at collection time, making pytest exit code 2 (ERROR) instead of 1 (FAIL). The done criteria required 10 failures and 0 errors.
- **Fix:** Removed the module-level import; placed `from musicboxfactory import Mixer as _Mixer` inside `test_import()` body. All other tests use `MixerDirect` (direct import from `musicboxfactory.mixer`) which always works.
- **Files modified:** `tests/test_mixer.py`
- **Verification:** `uv run pytest tests/test_mixer.py --collect-only -q` shows 10 tests collected; `uv run pytest tests/test_mixer.py -q` shows 10 failed, 0 passed, 0 errors.
- **Committed in:** `02b2a13` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug in plan's example import pattern)
**Impact on plan:** Essential fix for correct RED state. No scope creep.

## Issues Encountered

None beyond the deviation documented above.

## User Setup Required

None - no external service configuration required.

## Known Stubs

- `src/musicboxfactory/mixer.py` — entire class is a stub (all methods raise `NotImplementedError`). Intentional: this is the TDD scaffold plan. Plan 02 will implement all methods.

## Next Phase Readiness

- `mixer.py` stub is importable and type-clean — Plan 02 implementation can proceed
- All 10 test stubs are collected and RED — Plan 02 implementation will turn them GREEN
- No blockers

## Self-Check: PASSED

- FOUND: src/musicboxfactory/mixer.py
- FOUND: tests/test_mixer.py
- FOUND: .planning/phases/04-mixing-wav-output/04-01-SUMMARY.md
- FOUND commit: 6a42af4
- FOUND commit: 02b2a13

---
*Phase: 04-mixing-wav-output*
*Completed: 2026-04-02*
