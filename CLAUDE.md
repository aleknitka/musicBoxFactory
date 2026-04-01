# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`musicboxfactory` — a pure-Python library that generates baby sleep audio as WAV files. Combines soundfont-rendered music box melodies (via FluidSynth) with generated ambient noise (white/pink/brown/womb) and writes a seamlessly loopable WAV file.

Python >=3.13. Managed with `uv`.

## Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/path/to/test_file.py::test_name

# Type check
uv run mypy src/

# Lint
uv run ruff check src/
```

## Architecture

The library is structured as four phases, each a discrete capability:

1. **Tone Synthesis** (`musicboxfactory/synth.py`) — `Synth` class wraps FluidSynth to load a `.sf2` soundfont and render individual notes. Returns `numpy.ndarray` (float32, mono, 44100 Hz). Named presets (`"music_box"`, `"celesta"`, `"bells"`) map to General MIDI patch numbers via a hardcoded `PRESETS` dict. Unknown preset raises `ValueError`.

2. **Melody Pipeline** (`musicboxfactory/melody.py`) — Sequences notes from the `Synth` into a melody buffer. Supports built-in lullaby presets, custom `(note, duration)` tuples, and procedural circle-of-fifths generation.

3. **Ambient Generation** (`musicboxfactory/ambient.py`) — Generates white, pink (FFT-shaped, −3 dB/oct), brown (−6 dB/oct), and womb/heartbeat (brown + ~60 BPM LFO pulse) noise as numpy buffers.

4. **Mixer / WAV Output** (`musicboxfactory/mixer.py`) — Combines melody and ambient at caller-specified volumes, normalizes to prevent int16 clipping, and writes a loop-safe WAV (zero-crossing boundary, optional fade-in/out).

## Buffer Contract

All inter-module audio buffers are `numpy.ndarray`, dtype `float32`, shape `(N,)` (mono), sample rate **44100 Hz**, values in `[-1.0, 1.0]`.

## Dependencies

- `numpy` 2.x — signal generation and buffer arithmetic
- `scipy` — WAV output and noise filtering
- `fluidsynth` (C library) + `pyfluidsynth` Python bindings — soundfont rendering (system dependency)

## Out of Scope (v1)

No CLI, no MIDI file input, no audio playback, no streaming, no MP3/OGG output, no bundled soundfont.
