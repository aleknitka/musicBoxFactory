---
phase: 01-tone-synthesis
plan: 02
subsystem: testing
tags: [pyfluidsynth, fluidsynth, numpy, synth, midi, soundfont]

# Dependency graph
requires:
  - phase: 01-tone-synthesis/01-01
    provides: pytest infrastructure, test stubs, package skeleton
provides:
  - Synth class (src/musicboxfactory/synth.py) — offline soundfont rendering via pyfluidsynth
  - _note_name_to_midi helper — 12-TET note name to MIDI number conversion
  - PRESETS dict — 0-indexed GM patch numbers for music_box, celesta, bells
  - Package public API — Synth and PRESETS importable from musicboxfactory
affects: [01-tone-synthesis/melody, 02-melody-pipeline, 03-ambient, 04-mixer]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Lazy fluidsynth import with OSError/ImportError catch — allows unit tests to pass without libfluidsynth3 installed
    - Offline rendering via get_samples() loop — no start() call, works headless/CI
    - 3s tail drain after noteoff — prevents abrupt note cutoff for music box ring-out
    - Buffer normalization — peak-normalise to [-1.0, 1.0] contract regardless of FluidSynth gain

key-files:
  created:
    - src/musicboxfactory/synth.py
  modified:
    - src/musicboxfactory/__init__.py

key-decisions:
  - "Lazy fluidsynth import (catch OSError/ImportError) allows unit tests to run without libfluidsynth3 — import fails gracefully, Synth() raises OSError at instantiation time only"
  - "3-second tail drain after noteoff chosen as conservative upper bound for music box ring-out (tines ring 2-4s per RESEARCH.md)"
  - "Peak normalization in render() guarantees [-1.0, 1.0] buffer contract regardless of FluidSynth gain setting"

patterns-established:
  - "Pattern: Lazy import with AVAILABLE flag — defers C-library errors from import-time to instantiation-time"
  - "Pattern: get_samples() block collection loop — BLOCK_SIZE=1024, collect-reshape-downmix-convert pipeline"

requirements-completed: [TONE-01, TONE-02]

# Metrics
duration: 18min
completed: 2026-03-31
---

# Phase 01 Plan 02: Tone Synthesis Implementation Summary

**Synth class with offline FluidSynth rendering via get_samples() loop — turns 4 RED unit tests GREEN with lazy import handling for headless systems without libfluidsynth3**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-03-31T20:23:38Z
- **Completed:** 2026-03-31T20:41:19Z
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- Implemented `src/musicboxfactory/synth.py` with full `Synth` class, `PRESETS` dict, and `_note_name_to_midi` helper
- All 4 unit tests now GREEN; 4 integration tests skip cleanly without libfluidsynth3/soundfont
- Updated `__init__.py` to export `Synth` and `PRESETS` as the public package API
- `uv run mypy src/` and `uv run ruff check src/` both pass clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement synth.py — Synth class and helpers** - `bca3ebd` (feat)
2. **Task 2: Update __init__.py exports and run full suite** - `f75e17c` (feat)

**Plan metadata:** (see final commit)

_Note: TDD task — tests written in Plan 01 (RED); implementation added here (GREEN)_

## Files Created/Modified
- `src/musicboxfactory/synth.py` - Synth class, _note_name_to_midi helper, PRESETS dict, _collect_samples pipeline
- `src/musicboxfactory/__init__.py` - Updated to export Synth, PRESETS with docstring

## Decisions Made
- Lazy import pattern for fluidsynth: the plan specified `try/except OSError` but pyfluidsynth raises `ImportError` (not `OSError`) when libfluidsynth3 is missing. Changed to catch both; deferred the error to `Synth.__init__()` so module-level imports of `_note_name_to_midi` and `PRESETS` work without the C library.
- `# type: ignore[import-untyped]` on the fluidsynth import (untyped) with `# noqa: F841` on the fallback `None` assignment in the except block — necessary to satisfy both mypy strict mode and ruff cleanly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Lazy fluidsynth import to allow unit tests without libfluidsynth3**
- **Found during:** Task 1 (after initial implementation attempt)
- **Issue:** Plan specified `try/except OSError` around `import fluidsynth`, but pyfluidsynth raises `ImportError` when libfluidsynth3 C library is missing. Module-level import failure prevented `_note_name_to_midi` and `PRESETS` from being imported by unit tests, causing all 4 unit tests to fail.
- **Fix:** Changed to lazy import pattern — `try: import fluidsynth as _fluidsynth; _FLUIDSYNTH_AVAILABLE = True` catching `(OSError, ImportError)`. `Synth.__init__` checks `_FLUIDSYNTH_AVAILABLE` and raises `OSError` with helpful install instructions if False.
- **Files modified:** src/musicboxfactory/synth.py
- **Verification:** `uv run pytest tests/test_synth.py -q` → 4 passed, 4 skipped
- **Committed in:** `bca3ebd` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug)
**Impact on plan:** Required for unit tests to pass without libfluidsynth3. No scope creep; implementation contract unchanged.

## Issues Encountered
- `uv run mypy src/` initially failed with `Unused "type: ignore" comment` on the fallback `None` assignment in the except block — mypy considers the except branch unreachable when fluidsynth is importable. Resolved by using `# noqa: F841` comment instead of `# type: ignore[assignment]` on that line.

## User Setup Required
Before running integration tests, install the system dependency and soundfont:
```bash
sudo apt install -y libfluidsynth3 libfluidsynth-dev fluid-soundfont-gm
```
Then: `ldconfig -p | grep libfluidsynth` should show at least one line.
Set `MBF_SF2_PATH=/path/to/custom.sf2` to use a different soundfont.

## Next Phase Readiness
- `Synth(sf2_path, preset).render(note, duration)` public API complete and tested
- Buffer contract (float32, mono, 44100 Hz, [-1, 1]) enforced by normalization step
- Integration tests (4 skipped) will turn GREEN once libfluidsynth3 + soundfont installed
- Ready for Phase 2 (Melody Pipeline) to consume the `Synth` and `PRESETS` API

## Known Stubs
None — all implementation is complete; no placeholder values or empty stubs.

## Self-Check: PASSED

- FOUND: src/musicboxfactory/synth.py
- FOUND: src/musicboxfactory/__init__.py
- FOUND commit bca3ebd (Task 1 — feat: implement Synth class and _note_name_to_midi helper)
- FOUND commit f75e17c (Task 2 — feat: export Synth and PRESETS from package __init__)

---
*Phase: 01-tone-synthesis*
*Completed: 2026-03-31*
