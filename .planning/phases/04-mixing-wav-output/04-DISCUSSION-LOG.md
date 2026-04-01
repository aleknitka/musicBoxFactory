# Phase 4: Mixing & WAV Output — Discussion Log

**Date:** 2026-04-01
**Phase:** 04 — Mixing & WAV Output

---

## Areas Discussed

Four gray areas were presented; user selected all four.

---

### Area 1: API Shape

**Q:** How should the mixer be invoked?
**Options:** Mixer class / Module-level functions / Single write_wav function
**Selected:** Mixer class

**Rationale:** Consistent with existing `Synth`, `MelodyPipeline`, `AmbientGenerator` pattern. Constructor holds config; `.mix()` and `.write()` are methods.

---

### Area 2: Volume Model

**Q:** How should the caller specify volume for each layer?
**Options:** 0–1 float per layer / Single balance knob / You decide
**Selected:** 0–1 float per layer

**Rationale:** Simple linear scale. Normalization handles clipping, so values don't need to sum to 1.0. Consistent with numpy audio buffer conventions.

---

### Area 3: Duration + Tiling

**Q:** When buffers are shorter than the requested duration — what should happen?
**Options:** Mixer tiles automatically / Caller pre-fills buffers / mix() returns buffer, write() tiles
**Selected:** Mixer tiles automatically

**Rationale:** Expected workflow for sleep audio — caller just says `duration=600.0`. Mixer tiles each buffer independently and trims to exact length.

---

### Area 4: Fade vs Loop Contract

**Q (round 1):** OUT-04 (seamless loop) vs OUT-05 (fade-out) — how to resolve the conflict?
**Options:** Fades are for export only / Crossfade the loop point / No fade-out allowed with looping
**Selected:** No fade-out allowed with looping

**Q (round 2):** Should the mixer raise ValueError or silently apply fade-out with a warning?
**Options:** Raise ValueError / Apply fade with warning / You decide
**Selected:** Raise ValueError

**Rationale:** Fail fast — consistent with library's `ValueError` pattern. Caller must explicitly choose. Non-looping export path is deferred to v2.

---

*Log generated: 2026-04-01*
