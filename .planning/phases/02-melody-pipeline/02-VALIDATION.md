---
phase: 02
slug: melody-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already configured) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_melody.py -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_melody.py -q`
- **After every plan wave:** Run `uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | MELO-01, MELO-02, MELO-03 | unit (stubs) | `uv run pytest tests/test_melody.py -q` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | MELO-02 | unit | `uv run pytest tests/test_melody.py::test_custom_sequence -q` | ✅ | ⬜ pending |
| 02-02-02 | 02 | 2 | MELO-01 | unit | `uv run pytest tests/test_melody.py::test_preset_sequences -q` | ✅ | ⬜ pending |
| 02-02-03 | 02 | 2 | MELO-03 | unit | `uv run pytest tests/test_melody.py::test_procedural_generation -q` | ✅ | ⬜ pending |
| 02-02-04 | 02 | 2 | MELO-01, MELO-02, MELO-03 | unit | `uv run pytest tests/test_melody.py::test_loop_boundary -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_melody.py` — stubs for MELO-01, MELO-02, MELO-03
- [ ] `src/musicboxfactory/melody.py` — module scaffold (empty or stub class)

*Wave 0 uses existing test infrastructure (conftest.py, pytest, uv).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Loop click test | MELO-01 | Audio quality requires listening | Render a 30s melody WAV with scipy, play it in a loop, confirm no click at boundary |
| Procedural melody musicality | MELO-03 | Subjective musical quality | Render 3 procedural melodies, confirm they sound musically coherent (not random noise) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
