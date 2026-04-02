---
created: 2026-04-01T21:26:30.135Z
title: Add container function
area: general
files: []
---

## Problem

The library currently requires callers to instantiate and chain multiple objects (`Synth` → `MelodyPipeline` → `AmbientGenerator` → `Mixer`) to produce a WAV file. There is no single top-level convenience function for the common case.

## Solution

Add a container/façade function (e.g. `create_sleep_audio(...)`) to the public API that wires all four phases together in one call. Callers who want the full pipeline without managing individual objects should be able to call a single function with the key parameters (sf2_path, preset, melody, ambient type, duration, output path) and get a WAV file back. Low-level classes remain available for callers who want fine-grained control.
