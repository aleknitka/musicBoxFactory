# Milestones

## v1.0 MVP (Shipped: 2026-04-02)

**Phases completed:** 4 phases, 8 plans, 12 tasks

**Key accomplishments:**

- pytest infrastructure with 8 RED test stubs covering TONE-01/TONE-02 buffer contract, preset validation, and note-name conversion — package skeleton importable via uv
- Synth class with offline FluidSynth rendering via get_samples() loop — turns 4 RED unit tests GREEN with lazy import handling for headless systems without libfluidsynth3
- One-liner:
- One-liner:
- AmbientGenerator class stub with scipy runtime dep and 12 TDD-red test contracts for white/pink/brown/womb noise
- Four noise generators implemented with FFT spectral shaping, cumsum detrend, and lub-dub LFO envelope — all 12 AMBI tests green, AmbientGenerator exported from package
- Mixer stub (68 lines) and 10 RED test stubs established TDD contract for WAV mixing and output before implementation
- Mixer class implemented with volume-scaled mixing, peak-normalized loop-safe tiling, and WAV output — all 10 tests GREEN, full suite clean

---
