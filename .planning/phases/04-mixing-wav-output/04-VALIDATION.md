---
phase: 4
slug: mixing-wav-output
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-02
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/test_mixer.py -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_mixer.py -q`
- **After every plan wave:** Run `uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 0 | OUT-01 | unit | `uv run pytest tests/test_mixer.py::test_mix_buffer_contract -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 0 | OUT-01 | unit | `uv run pytest tests/test_mixer.py::test_mix_volumes_applied -x` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 0 | OUT-02 | unit | `uv run pytest tests/test_mixer.py::test_write_no_clipping -x` | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 0 | OUT-02 | unit | `uv run pytest tests/test_mixer.py::test_write_no_clipping_high_vol -x` | ❌ W0 | ⬜ pending |
| 04-01-05 | 01 | 0 | OUT-03 | unit | `uv run pytest tests/test_mixer.py::test_write_exact_duration -x` | ❌ W0 | ⬜ pending |
| 04-01-06 | 01 | 0 | OUT-03 | unit | `uv run pytest tests/test_mixer.py::test_write_wav_readable -x` | ❌ W0 | ⬜ pending |
| 04-01-07 | 01 | 0 | OUT-04 | unit | `uv run pytest tests/test_mixer.py::test_tiling_zero_crossing -x` | ❌ W0 | ⬜ pending |
| 04-01-08 | 01 | 0 | OUT-05 | unit | `uv run pytest tests/test_mixer.py::test_fade_in_applied -x` | ❌ W0 | ⬜ pending |
| 04-01-09 | 01 | 0 | OUT-05 | unit | `uv run pytest tests/test_mixer.py::test_fade_out_raises -x` | ❌ W0 | ⬜ pending |
| 04-01-10 | 01 | 0 | OUT-02 | unit | `uv run pytest tests/test_mixer.py::test_import -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_mixer.py` — stubs for OUT-01 through OUT-05 (all 10 tests above)
- [ ] `src/musicboxfactory/mixer.py` — module does not yet exist (stub needed for import test)

*Framework, conftest, and all other infrastructure already exist — no new fixtures or config needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| WAV plays back with no audible click at loop boundary | OUT-04 | Subjective audio quality | Load output WAV in Audacity, loop playback, verify no pop/click at boundary |
| WAV plays back with no audible distortion at max volumes | OUT-02 | Subjective audio quality | Load output WAV in Audacity, verify no distortion |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
