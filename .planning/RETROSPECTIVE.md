# Retrospective: Music Box Factory

## Milestone: v1.0 — MVP

**Shipped:** 2026-04-02
**Phases:** 4 | **Plans:** 8 | **Timeline:** 3 days (2026-03-30 → 2026-04-02)

### What Was Built

1. `Synth` — FluidSynth soundfont rendering, lazy import for headless CI, named presets
2. `MelodyPipeline` — built-in lullabies, custom note sequences, procedural circle-of-fifths traversal
3. `AmbientGenerator` — FFT-shaped white/pink/brown noise + lub-dub womb/heartbeat LFO envelope
4. `Mixer` — volume-scaled mixing, peak-normalized loop-safe tiling, optional fade-in, WAV output

631 LOC source + 603 LOC tests. 38 tests pass; 8 FluidSynth integration tests skip cleanly without live soundfont.

### What Worked

- **TDD scaffold before implementation** — scaffolding each phase with RED stubs before implementing caught the module-level import / collection issue in Phase 4 early. Clear contract defined upfront.
- **Phase isolation** — each phase delivers one independently verifiable capability. No phase needed to be partially re-done due to a prior phase's API changing.
- **Wave-based parallel execution** — Wave 1 (scaffold) → Wave 2 (implement) pattern worked cleanly across all 4 phases. No dependency conflicts.
- **Peak normalization after fade-in** — correct ordering preserved the fade envelope in the final WAV.
- **`_trim_to_zero_crossing` before tiling** — zero-crossing boundary enforcement eliminated loop clicks in all numerical tests.

### What Was Inefficient

- Melody pipeline (Phase 2) SUMMARY one-liners were not captured cleanly — "One-liner:" blank entries appeared in milestone extract. Minor formatting issue in plan metadata.
- The worktree merge step for Wave 2 of Phase 4 was manual — the orchestrator needed to `git merge worktree-agent-aaaf2ec1` explicitly after the subagent completed in isolation.

### Patterns Established

- **TDD scaffold plan (Wave 1) → implementation plan (Wave 2)**: Every phase used this two-plan structure. Consistent and reliable.
- **Lazy FluidSynth import**: `try/except ImportError` at call site rather than module level — keeps the package importable for testing without the C library installed.
- **Operation order in `write()`**: fade_out guard → zero-crossing trim → tile → fade-in → normalize → int16 → write. Locked in as the correct sequence.
- **Module-level import inside test body**: When a top-level package import raises `ImportError`, placing it inside the test function body prevents pytest collection failure for sibling tests.

### Key Lessons

- Normalization threshold (1e-9, not 0) is required to handle all-zero (silent) buffers gracefully — otherwise division by zero on the peak.
- `× 32767` for int16 conversion (not 32768) — signed int16 max is 32767; using 32768 would produce values outside range.
- `fade_out` as a hard `ValueError` is the right API choice for a loop-safe library — callers need to be told explicitly, not silently ignored.
- FluidSynth integration tests should be skipped via `pytest.mark.skip` with an explicit reason when the C library isn't available — this pattern makes CI green without soundfonts.

### Cost Observations

- Model: Claude Sonnet 4.6 throughout
- Sessions: ~4 (one per phase + planning)
- Notable: Subagent-per-plan execution stayed lean (~50k tokens per executor agent). Orchestrator context stayed well under 15%.

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Timeline | Source LOC | Test LOC |
|-----------|--------|-------|----------|------------|----------|
| v1.0 MVP | 4 | 8 | 3 days | 631 | 603 |
