---
phase: 03
slug: ambient-generation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already configured) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_ambient.py -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_ambient.py -q`
- **After every plan wave:** Run `uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | AMBI-01..04 | unit (stubs) | `uv run pytest tests/test_ambient.py -q` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | AMBI-01..04 | unit (stubs) | `uv run pytest tests/test_ambient.py -q` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | AMBI-01 | unit | `uv run pytest tests/test_ambient.py -k "white" -q` | ✅ | ⬜ pending |
| 03-02-02 | 02 | 2 | AMBI-02 | unit | `uv run pytest tests/test_ambient.py -k "pink" -q` | ✅ | ⬜ pending |
| 03-02-03 | 02 | 2 | AMBI-03 | unit | `uv run pytest tests/test_ambient.py -k "brown" -q` | ✅ | ⬜ pending |
| 03-02-04 | 02 | 2 | AMBI-04 | unit | `uv run pytest tests/test_ambient.py -k "womb" -q` | ✅ | ⬜ pending |
| 03-02-05 | 02 | 2 | AMBI-01..04 | unit | `uv run pytest tests/test_ambient.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_ambient.py` — stubs for AMBI-01, AMBI-02, AMBI-03, AMBI-04
- [ ] `src/musicboxfactory/ambient.py` — module scaffold (empty or stub class)
- [ ] `uv add scipy` — move scipy from dev to runtime dependency

*Wave 0 uses existing test infrastructure (conftest.py, pytest, uv).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Womb heartbeat audibility | AMBI-04 | Rhythmic LFO pulse requires listening | Render 10s womb buffer to WAV, play — confirm ~60 BPM low-frequency thump is audible |
| Pink/brown spectral character | AMBI-02, AMBI-03 | Spectral slope requires audio judgment | Render and compare: pink should sound "warmer" than white, brown "deeper" than pink |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
