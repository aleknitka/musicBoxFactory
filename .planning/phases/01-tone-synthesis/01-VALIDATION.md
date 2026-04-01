---
phase: 1
slug: tone-synthesis
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | pyproject.toml (to be added in Wave 0) |
| **Quick run command** | `uv run pytest tests/test_synth.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_synth.py -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 0 | TONE-01 | unit stub | `uv run pytest tests/test_synth.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | TONE-01 | unit | `uv run pytest tests/test_synth.py::test_render_returns_buffer -x -q` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | TONE-01 | unit | `uv run pytest tests/test_synth.py::test_buffer_contract -x -q` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 1 | TONE-02 | unit | `uv run pytest tests/test_synth.py::test_preset_mapping -x -q` | ❌ W0 | ⬜ pending |
| 1-01-05 | 01 | 1 | TONE-02 | unit | `uv run pytest tests/test_synth.py::test_invalid_preset_raises -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_synth.py` — stubs for TONE-01, TONE-02
- [ ] `tests/conftest.py` — shared fixtures (sf2 path, skip marker for missing libfluidsynth3)
- [ ] `uv add --dev pytest` — add pytest to dev dependencies
- [ ] `sudo apt install libfluidsynth3` — system prerequisite (document in README)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Rendered tone sounds warm and decaying (not a flat sine) | TONE-01 | Subjective audio quality — not automatable | Run `python -c "from musicboxfactory.synth import Synth; s=Synth('test.sf2'); import scipy.io.wavfile; scipy.io.wavfile.write('out.wav', 44100, s.render('c4', duration=2.0))"` and listen to `out.wav` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
