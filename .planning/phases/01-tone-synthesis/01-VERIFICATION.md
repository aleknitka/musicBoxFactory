---
phase: 01-tone-synthesis
verified: 2026-03-31T21:00:00Z
status: human_needed
score: 9/10 must-haves verified
re_verification: false
human_verification:
  - test: "Install libfluidsynth3 and fluid-soundfont-gm, then run: uv run pytest tests/test_synth.py -v"
    expected: "4 passed, 4 skipped becomes 7 passed (or 8 passed if sf2 path is set). Specifically test_render_returns_correct_shape, test_render_buffer_range, test_missing_sf2_raises, and test_unknown_preset_raises_with_sf2 should all pass."
    why_human: "Integration tests require a physical .sf2 soundfont file and libfluidsynth3 system library. Cannot verify offline rendering, buffer shape, buffer range, or real FileNotFoundError behavior without the C library installed."
  - test: "Render a note and write to WAV, then listen: python -c \"from musicboxfactory import Synth; import scipy.io.wavfile as wv; import numpy as np; s=Synth('/usr/share/sounds/sf2/FluidR3_GM.sf2'); buf=s.render('c4',2.0); wv.write('/tmp/test_tone.wav', 44100, buf); print('written')\""
    expected: "WAV file plays back with a perceptibly warm, decaying music-box timbre — not a flat sine wave (Roadmap Success Criteria #3)"
    why_human: "Tone quality and timbral character cannot be verified programmatically — requires human listening."
---

# Phase 1: Tone Synthesis Verification Report

**Phase Goal:** Implement the Synth class that wraps FluidSynth to load a .sf2 soundfont and render individual notes as float32 numpy arrays.
**Verified:** 2026-03-31T21:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | pytest discovers and runs tests/test_synth.py with zero collection errors | VERIFIED | `8 tests collected in 0.06s` — no collection errors |
| 2  | Unit tests for note-name conversion, preset validation, and buffer contract exist | VERIFIED | 4 unit tests present and PASS: test_note_name_to_midi, test_note_name_to_midi_invalid, test_preset_patch_numbers, test_unknown_preset_raises |
| 3  | Integration tests are skipped cleanly when no soundfont is present | VERIFIED | 4 integration tests show SKIPPED with reason "No soundfont at /usr/share/sounds/sf2/FluidR3_GM.sf2" |
| 4  | pyproject.toml declares pyfluidsynth, numpy as runtime deps and pytest, ruff, mypy, scipy as dev deps | VERIFIED | pyproject.toml confirms all 6 packages declared with correct version pins |
| 5  | Caller can construct Synth(sf2_path, preset) and call render(note, duration) | VERIFIED | Class and method exist with correct signatures; behavioral spot-check confirms ValueError raised before fluidsynth check |
| 6  | All three named presets map to correct 0-indexed GM patch numbers | VERIFIED | PRESETS = {"music_box": 10, "celesta": 8, "bells": 14} confirmed in code and via import test |
| 7  | Unknown preset name raises ValueError with message listing valid presets | VERIFIED | Code raises `ValueError(f"Unknown preset {preset!r}. Valid presets: {list(PRESETS)}")` before any fluidsynth call; spot-check confirmed |
| 8  | Rendered buffer is exactly int(44100 * duration) samples long with values in [-1.0, 1.0] | PARTIAL | Implementation verified in code (n_samples = int(SAMPLE_RATE * duration), peak normalization present); test coverage requires soundfont — SKIPPED |
| 9  | All unit tests pass; integration tests pass when a .sf2 soundfont is present | PARTIAL | 4/4 unit tests pass; 4/4 integration tests SKIPPED (no soundfont in environment) |
| 10 | Rendered tone has a perceptibly warm, decaying timbre (Roadmap Success Criterion #3) | NEEDS HUMAN | Timbral quality requires human listening |

**Score:** 9/10 truths verified (7 fully verified, 2 partial pending soundfont, 1 needs human)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pyproject.toml` | Project metadata with all required dependencies | VERIFIED | pyfluidsynth>=1.3.4, numpy>=2.0 runtime; pytest>=9.0.2, ruff>=0.15.8, mypy>=1.20.0, scipy>=1.17.1 dev; testpaths=["tests"]; strict mypy |
| `src/musicboxfactory/__init__.py` | Package init — importable as musicboxfactory | VERIFIED | Exports Synth and PRESETS; `from musicboxfactory.synth import PRESETS, Synth` present |
| `tests/test_synth.py` | Test stubs covering 6 behaviours | VERIFIED | 8 tests collected: test_note_name_to_midi, test_note_name_to_midi_invalid, test_preset_patch_numbers, test_unknown_preset_raises, test_render_returns_correct_shape, test_render_buffer_range, test_missing_sf2_raises, test_unknown_preset_raises_with_sf2 |
| `tests/conftest.py` | Shared fixture: sf2_path with skip marker | VERIFIED | requires_sf2 marker and sf2_path fixture both present and wired |
| `src/musicboxfactory/synth.py` | Synth class and PRESETS dict — public API for Phase 2 | VERIFIED | 171 lines (above 80-line minimum); exports Synth, PRESETS, _note_name_to_midi; all three present |
| `tests/__init__.py` | Empty package marker | VERIFIED | File exists, 0 bytes |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `tests/conftest.py` | `tests/test_synth.py` | `sf2_path` fixture | VERIFIED | `from .conftest import requires_sf2` at line 7; `sf2_path` used as parameter in 3 integration tests |
| `src/musicboxfactory/synth.py` | `fluidsynth` C library | `get_samples()` loop — no `start()` call | VERIFIED | `get_samples` at lines 158, 165; no actual `.start()` call (line 107 is comment only) |
| `src/musicboxfactory/synth.py` | `numpy ndarray` | stereo int16 -> float32 mono conversion | VERIFIED | `reshape(-1, 2)` at line 166; `.astype(np.float32) / 32768.0` at line 168 |
| `src/musicboxfactory/__init__.py` | `src/musicboxfactory/synth.py` | `from musicboxfactory.synth import PRESETS, Synth` | VERIFIED | Line 13 of `__init__.py` confirmed |

### Data-Flow Trace (Level 4)

Not applicable — `Synth` is a synthesis class, not a component rendering from a data store. The data flows from FluidSynth C library -> int16 buffer -> float32 mono ndarray -> caller. This pipeline is implemented in `_collect_samples()` and verified by key link checks above.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| PRESETS values correct | `python -c "from musicboxfactory.synth import PRESETS; assert PRESETS['music_box']==10..."` | All assertions pass | PASS |
| _note_name_to_midi values | `python -c "from musicboxfactory.synth import _note_name_to_midi; assert _note_name_to_midi('c4')==60..."` | All 5 assertions pass | PASS |
| ValueError before fluidsynth for bad preset | `Synth('dummy.sf2', preset='nonexistent_preset')` raises `ValueError: Unknown preset 'nonexistent_preset'` | ValueError raised correctly | PASS |
| Public imports work | `from musicboxfactory import Synth, PRESETS` | Import succeeds | PASS |
| Integration tests with soundfont | Requires libfluidsynth3 + .sf2 file | Cannot run — library not installed | SKIP |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| TONE-01 | 01-01-PLAN.md, 01-02-PLAN.md | Caller can render music box tones from a caller-provided .sf2 soundfont file | SATISFIED (unit) / PENDING (integration) | `Synth.render()` implemented with correct signature and buffer contract logic; integration tests SKIPPED pending soundfont install |
| TONE-02 | 01-01-PLAN.md, 01-02-PLAN.md | Library exposes named instrument presets mapping to GM patch numbers | SATISFIED | `PRESETS = {"music_box": 10, "celesta": 8, "bells": 14}` verified in code and via import; test_preset_patch_numbers PASSES |

No orphaned requirements — REQUIREMENTS.md traceability table maps only TONE-01 and TONE-02 to Phase 1. Both accounted for.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_synth.py` | 51-55 | `test_unknown_preset_raises` bypasses `Synth.__init__` and raises `ValueError` manually instead of calling `Synth(sf2_path, "bad_preset")` | WARNING | Test passes but does not exercise the actual validation code path in `Synth.__init__`. The integration counterpart `test_unknown_preset_raises_with_sf2` does test the real path but is SKIPPED without a soundfont. Behavioral spot-check confirms the actual code does raise `ValueError` correctly, so this is a test quality gap not a code gap. |

No blockers found. The anti-pattern is a test quality warning only — the implementation itself is correct (confirmed by behavioral spot-check).

### Human Verification Required

#### 1. Integration Test Suite with Soundfont

**Test:** Install libfluidsynth3 and fluid-soundfont-gm, then run `uv run pytest tests/test_synth.py -v`

**Expected:** All 4 integration tests pass — `test_render_returns_correct_shape` confirms shape `(44100,)` and dtype `float32`; `test_render_buffer_range` confirms values in `[-1.0, 1.0]`; `test_missing_sf2_raises` confirms `FileNotFoundError`; `test_unknown_preset_raises_with_sf2` confirms `ValueError`.

**Why human:** Requires `sudo apt install libfluidsynth3 libfluidsynth-dev fluid-soundfont-gm` and a running system that can load the C library.

#### 2. Tone Quality — Warm Decaying Timbre

**Test:** Run:
```bash
uv run python -c "
from musicboxfactory import Synth
import scipy.io.wavfile as wv
s = Synth('/usr/share/sounds/sf2/FluidR3_GM.sf2', preset='music_box')
buf = s.render('c4', 2.0)
wv.write('/tmp/test_tone.wav', 44100, buf)
print('Written to /tmp/test_tone.wav')
"
```
Then play `/tmp/test_tone.wav`.

**Expected:** Audio plays with a perceptibly warm, bell-like music box timbre with natural decay — not a flat or synthetic tone.

**Why human:** Timbral quality and perceptual warmth are subjective and cannot be verified programmatically. This is Roadmap Success Criterion #3.

### Gaps Summary

No blocking gaps. All implementation artifacts exist, are substantive, and are correctly wired.

Two items remain pending human verification:
1. Integration tests (4 tests SKIPPED) — require system library + soundfont install. The implementation logic is verified programmatically; only end-to-end soundfont rendering is untested.
2. Tone quality — perceptual assessment of the rendered audio timbre.

One test quality warning: `test_unknown_preset_raises` is a hollow unit test that raises `ValueError` manually. The behavior is covered by the integration counterpart and behavioral spot-check, but the unit test does not exercise `Synth.__init__` directly.

---

_Verified: 2026-03-31T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
