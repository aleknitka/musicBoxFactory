---
phase: 03-ambient-generation
plan: 01
subsystem: audio
tags: [numpy, scipy, ambient, noise, testing, tdd]

# Dependency graph
requires:
  - phase: 01-tone-synthesis
    provides: SAMPLE_RATE constant imported into ambient.py
provides:
  - AmbientGenerator class skeleton with NotImplementedError stubs
  - 12 failing test stubs covering AMBI-01 through AMBI-04
  - scipy as a runtime dependency in pyproject.toml
affects: [03-ambient-generation-plan-02, 04-mixer]

# Tech tracking
tech-stack:
  added: [scipy>=1.17.1 (moved to runtime)]
  patterns:
    - "NotImplementedError stubs for TDD red phase"
    - "numpy RNG via np.random.default_rng(seed) for reproducible noise"
    - "type: ignore[import-untyped] for scipy (no official stubs)"
    - "noqa: F401 for intentional stub-phase imports"

key-files:
  created:
    - src/musicboxfactory/ambient.py
    - tests/test_ambient.py
  modified:
    - pyproject.toml
    - uv.lock

key-decisions:
  - "scipy moved to runtime [project] dependencies (not dev-only) so users of the library get it"
  - "scipy duplicate removed from dev group after uv add placed it in both"
  - "type: ignore[import-untyped] applied to scipy import matching pyfluidsynth pattern in synth.py"
  - "noqa: F401 on stub imports (SAMPLE_RATE, detrend) to satisfy ruff while keeping plan-required imports"

patterns-established:
  - "AmbientGenerator takes optional seed via np.random.default_rng(seed) for reproducibility"
  - "All noise methods return float32 mono ndarray at SAMPLE_RATE Hz with values in [-1.0, 1.0]"

requirements-completed: [AMBI-01, AMBI-02, AMBI-03, AMBI-04]

# Metrics
duration: 8min
completed: 2026-04-01
---

# Phase 03 Plan 01: Ambient Generation Scaffold Summary

**AmbientGenerator class stub with scipy runtime dep and 12 TDD-red test contracts for white/pink/brown/womb noise**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-01T14:00:00Z
- **Completed:** 2026-04-01T14:08:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Moved scipy from dev-only to runtime dependency so library consumers receive it automatically
- Created AmbientGenerator class skeleton with properly documented NotImplementedError stubs for all 4 noise types
- Wrote 12 failing test stubs covering the full buffer contract (dtype, shape, range) and spectral/LFO behavior for AMBI-01 through AMBI-04
- No regressions in existing synth/melody tests (17 passing, 8 skipped as expected)

## Task Commits

Each task was committed atomically:

1. **Task 1: Move scipy to runtime dependencies** - `1985916` (chore)
2. **Task 2: Create ambient.py stub and failing tests** - `86a28ae` (test)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `src/musicboxfactory/ambient.py` - AmbientGenerator stub class with NotImplementedError on all noise methods
- `tests/test_ambient.py` - 12 test stubs for AMBI-01 through AMBI-04 (all fail red with NotImplementedError)
- `pyproject.toml` - scipy moved to [project] dependencies, removed from dev group
- `uv.lock` - Updated atomically by uv

## Decisions Made
- scipy was already in dev group; `uv add scipy` correctly placed it in [project] but left a duplicate in dev — the duplicate was cleaned up manually to avoid confusion
- scipy has no official type stubs; applied `type: ignore[import-untyped]` consistent with the existing `pyfluidsynth` pattern in synth.py
- `SAMPLE_RATE` and `detrend` imports are intentionally present in the stub for plan-link traceability; `noqa: F401` used to satisfy ruff during the stub phase
- test_import passes (1 passed) rather than failing because its purpose is to confirm import succeeds — the other 11 tests correctly fail red with NotImplementedError

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added type: ignore[import-untyped] for scipy import**
- **Found during:** Task 2 (create ambient.py stub)
- **Issue:** `uv run mypy src/musicboxfactory/ambient.py` exited 1 with "Library stubs not installed for scipy.signal" — mypy strict mode requires handling
- **Fix:** Added `# type: ignore[import-untyped]` matching the existing pyfluidsynth pattern in synth.py
- **Files modified:** src/musicboxfactory/ambient.py
- **Verification:** `uv run mypy src/musicboxfactory/ambient.py` exits 0
- **Committed in:** 86a28ae (Task 2 commit)

**2. [Rule 3 - Blocking] Added noqa: F401 for stub-phase unused imports**
- **Found during:** Task 2 (ruff lint check)
- **Issue:** `uv run ruff check src/musicboxfactory/ambient.py` exited 1 — SAMPLE_RATE and detrend are imported but unused in stub skeleton
- **Fix:** Added `# noqa: F401` to both imports; they remain for plan traceability and will be used in Plan 02 implementation
- **Files modified:** src/musicboxfactory/ambient.py
- **Verification:** `uv run ruff check src/musicboxfactory/ambient.py` exits 0
- **Committed in:** 86a28ae (Task 2 commit)

**3. [Rule 1 - Bug] Cleaned up scipy duplicate in pyproject.toml**
- **Found during:** Task 1 (post uv add verification)
- **Issue:** `uv add scipy` placed scipy in [project] dependencies but left the existing scipy entry in [dependency-groups] dev, creating a duplicate
- **Fix:** Removed scipy from dev group; ran `uv sync` to verify no breakage
- **Files modified:** pyproject.toml, uv.lock
- **Verification:** `grep -A 20 '[project]' pyproject.toml | grep scipy` shows exactly 1 entry; `uv run python -c "from scipy.signal import detrend; print('ok')"` exits 0
- **Committed in:** 1985916 (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (1 Rule 1 bug, 2 Rule 3 blocking)
**Impact on plan:** All auto-fixes necessary for correctness and clean tooling. No scope creep.

## Issues Encountered
None beyond the deviation fixes above.

## Known Stubs

- `src/musicboxfactory/ambient.py` lines 30-42: All four noise methods (`white`, `pink`, `brown`, `womb`) raise `NotImplementedError` — intentional for TDD red phase; Plan 02 implements them

## Next Phase Readiness
- Wave 1 scaffold complete: test contracts are established and failing red
- Plan 02 (Wave 2) can implement each noise method against the existing test suite
- scipy is available as a runtime dependency for implementation use

---
*Phase: 03-ambient-generation*
*Completed: 2026-04-01*
