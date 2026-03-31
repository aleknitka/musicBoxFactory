# musicBoxFactory

A pure-Python library that generates baby sleep audio as WAV files. Combines soundfont-rendered music box melodies (via FluidSynth) with generated ambient noise and writes a seamlessly loopable WAV file.

**Python >=3.13 · Managed with [uv](https://github.com/astral-sh/uv)**

---

## System requirements

```bash
sudo apt install -y libfluidsynth3 libfluidsynth-dev
```

A caller-provided `.sf2` soundfont is required. The library does not bundle one.

---

## Installation

```bash
uv add musicboxfactory
```

---

## Quickstart

```python
from musicboxfactory import Synth, PRESETS

synth = Synth("path/to/soundfont.sf2", preset="music_box")

# Render middle C for 2 seconds
buf = synth.render("c4", duration=2.0)
# buf: np.ndarray, dtype=float32, shape=(88200,), values in [-1.0, 1.0]
```

---

## API

### `Synth(sf2_path, preset="music_box")`

Loads a soundfont and selects an instrument preset. Rendering is offline — no audio driver is opened.

| Parameter | Type | Description |
|-----------|------|-------------|
| `sf2_path` | `str` | Path to a `.sf2` soundfont file |
| `preset` | `str` | Instrument preset name (see `PRESETS`) |

Raises `ValueError` for unknown presets, `FileNotFoundError` if the soundfont cannot be loaded, `OSError` if `libfluidsynth3` is not installed.

### `synth.render(note, duration) -> np.ndarray`

Renders a single note to a float32 mono buffer.

| Parameter | Type | Description |
|-----------|------|-------------|
| `note` | `str` | Note name: `"c4"`, `"g#3"`, `"bb5"`, etc. |
| `duration` | `float` | Buffer length in seconds |

Returns `np.ndarray` — dtype `float32`, shape `(N,)`, values in `[-1.0, 1.0]`, where `N = int(44100 * duration)`.

### `PRESETS`

```python
{
    "music_box": 10,  # GM program 11: Music Box
    "celesta":    8,  # GM program  9: Celesta
    "bells":     14,  # GM program 15: Tubular Bells
}
```

---

## Buffer contract

All audio buffers are `np.ndarray`, dtype `float32`, shape `(N,)` (mono), sample rate **44100 Hz**, values in `[-1.0, 1.0]`.

---

## Development

```bash
uv sync

uv run pytest          # 4 unit tests pass without libfluidsynth3; 4 integration tests skip
uv run mypy src/
uv run ruff check src/
```

---

## Architecture

The library is structured as four phases:

| Phase | Module | Responsibility |
|-------|--------|----------------|
| 1 | `synth.py` | Soundfont-rendered note synthesis via FluidSynth |
| 2 | `melody.py` | Sequence notes into melody buffers; built-in lullaby presets |
| 3 | `ambient.py` | White / pink / brown / womb noise generation |
| 4 | `mixer.py` | Mix melody + ambient, normalize, write loopable WAV |

Phases 2–4 are not yet implemented.
