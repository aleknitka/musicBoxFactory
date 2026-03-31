---
phase: 01-tone-synthesis
plan: 01
subsystem: testing
tags: [pytest, pyfluidsynth, numpy, scipy, fluidsynth, uv, hatchling]

# Dependency graph
requires: []
provides:
  - Importable musicboxfactory package skeleton with src/ layout
  - pytest infrastructure with testpaths configured
  - 8 failing test stubs covering TONE-01 and TONE-02 acceptance contract
  - requires_sf2 skip marker and sf2_path fixture for integration tests
affects: [01-tone-synthesis/01-02]

# Tech tracking
tech-stack:
  added:
    - pyfluidsynth==1.3.4 (runtime — Python ctypes bindings for FluidSynth C library)
    - numpy>=2.0 (runtime — buffer contract ndarray)
    - pytest==9.0.2 (dev)
    - ruff==0.15.8 (dev)
    - mypy==1.20.0 (dev)
    - scipy==1.17.1 (dev — WAV output utility)
    - hatchling (build system for src/ layout)
  patterns:
    - src/ layout with hatchling build backend
    - requires_sf2 marker pattern for graceful integration test skipping
    - TDD RED state: tests written before implementation module exists

key-files:
  created:
    - pyproject.toml (updated with build system, all deps, pytest/mypy config)
    - src/musicboxfactory/__init__.py
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_synth.py
  modified:
    - uv.lock (regenerated with all resolved packages)

key-decisions:
  - "hatchling build backend added to pyproject.toml to enable src/ layout package discovery"
  - "libfluidsynth3 system dep requires sudo — documented as manual prerequisite; does not block test collection or unit tests"
  - "Integration tests (requires_sf2) skip cleanly when no soundfont at /usr/share/sounds/sf2/FluidR3_GM.sf2"

patterns-established:
  - "Pattern: requires_sf2 pytest marker for conditional integration test skipping"
  - "Pattern: MBF_SF2_PATH env var override for soundfont path in CI"
  - "Pattern: noqa: PLC0415 for deferred imports inside test functions"

requirements-completed: [TONE-01, TONE-02]

# Metrics
duration: 12min
completed: 2026-03-31
---

# Phase 01 Plan 01: Tone Synthesis Scaffold Summary

**pytest infrastructure with 8 RED test stubs covering TONE-01/TONE-02 buffer contract, preset validation, and note-name conversion — package skeleton importable via uv**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-03-31T20:03:39Z
- **Completed:** 2026-03-31T20:15:30Z
- **Tasks:** 2
- **Files modified:** 5 created + 1 modified (pyproject.toml)

## Accomplishments
- Installed pyfluidsynth, numpy>=2.0, pytest, ruff, mypy, scipy via uv with lock file generated
- Created importable musicboxfactory package using src/ layout with hatchling build backend
- Wrote 8 test stubs (4 unit, 4 integration) covering TONE-01 and TONE-02 acceptance criteria
- Integration tests skip cleanly when libfluidsynth3/soundfont are absent

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies and create package skeleton** - `5177cb1` (chore)
2. **Task 2: Write test stubs for TONE-01 and TONE-02** - `ac6e754` (test)

**Plan metadata:** (see final commit)

_Note: TDD tasks — tests written before implementation (RED state confirmed)_

## Files Created/Modified
- `pyproject.toml` - Build system, all runtime/dev deps, pytest testpaths config, mypy strict mode
- `uv.lock` - Full resolved dependency lockfile
- `src/musicboxfactory/__init__.py` - Empty package init with `__all__ = []`
- `tests/__init__.py` - Empty package marker
- `tests/conftest.py` - `requires_sf2` skip marker + `sf2_path` fixture
- `tests/test_synth.py` - 8 test stubs: note-name MIDI conversion (2), PRESETS dict (2), render buffer contract (4 integration)

## Decisions Made
- Added hatchling build backend: uv with src/ layout requires an explicit build system to install the package in editable mode; hatchling is the standard uv-compatible choice
- libfluidsynth3 is a manual prerequisite: `sudo apt install libfluidsynth3 libfluidsynth-dev` requires a password; documented as a gate for integration tests, does not block unit test collection
- Integration tests skip via `requires_sf2` marker: checked at collection time against `os.path.exists(SF2_PATH)`; env var `MBF_SF2_PATH` allows override in CI

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added hatchling build-system to pyproject.toml**
- **Found during:** Task 1 (package skeleton creation)
- **Issue:** `uv sync` did not install the musicboxfactory package into the venv because pyproject.toml lacked a `[build-system]` table; `import musicboxfactory` failed with `ModuleNotFoundError`
- **Fix:** Added `[build-system]` with `requires = ["hatchling"]` and `[tool.hatch.build.targets.wheel] packages = ["src/musicboxfactory"]`
- **Files modified:** pyproject.toml
- **Verification:** `uv sync` rebuilt and installed musicboxfactory; `import musicboxfactory` succeeds
- **Committed in:** `5177cb1` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 3 — blocking)
**Impact on plan:** Required for package installation — no scope creep.

## Issues Encountered
- `sudo apt install libfluidsynth3` could not run non-interactively (password required). This is a known manual prerequisite; `import fluidsynth` fails at runtime but does not affect pytest collection or the 4 unit tests. Integration tests skip cleanly. Next plan (01-02) implements the Synth class and will re-test once the system dep is installed.

## User Setup Required
Before running integration tests, install the system dependency and soundfont:
```bash
sudo apt install -y libfluidsynth3 libfluidsynth-dev fluid-soundfont-gm
```
Then: `ldconfig -p | grep libfluidsynth` should show at least one line.
Set `MBF_SF2_PATH=/path/to/custom.sf2` to use a different soundfont.

## Next Phase Readiness
- Package skeleton importable: ready for Plan 02 to add `src/musicboxfactory/synth.py`
- Test suite RED: 4 unit tests fail on `ModuleNotFoundError: No module named 'musicboxfactory.synth'` — correct pre-implementation state
- 4 integration tests skip cleanly until libfluidsynth3 + soundfont installed
- Plan 02 will implement `synth.py` to turn this test suite GREEN

## Self-Check: PASSED

- FOUND: src/musicboxfactory/__init__.py
- FOUND: tests/__init__.py
- FOUND: tests/conftest.py
- FOUND: tests/test_synth.py
- FOUND: .planning/phases/01-tone-synthesis/01-01-SUMMARY.md
- FOUND commit 5177cb1 (Task 1 — chore: install dependencies and create package skeleton)
- FOUND commit ac6e754 (Task 2 — test: write failing test stubs for TONE-01 and TONE-02)

---
*Phase: 01-tone-synthesis*
*Completed: 2026-03-31*
