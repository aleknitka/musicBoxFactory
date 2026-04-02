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

## Generate a file

```python
from musicboxfactory import Synth, MelodyPipeline, AmbientGenerator, Mixer

# 1. Load your soundfont
synth = Synth("path/to/soundfont.sf2", preset="music_box")

# 2. Build a melody — pick one approach:
pipeline = MelodyPipeline(synth)
melody = pipeline.from_preset("twinkle")          # built-in lullaby
# melody = pipeline.from_preset("brahms")         # Brahms' lullaby
# melody = pipeline.from_preset("mary")           # Mary Had a Little Lamb
# melody = pipeline.from_notes([("c4", 0.5), ("g4", 0.5)])  # custom notes
# melody = pipeline.from_procedural(num_notes=16, seed=42)   # procedural

# 3. Generate ambient noise — pick one:
gen = AmbientGenerator(seed=42)
ambient = gen.pink(duration=len(melody) / 44100)   # pink noise (most popular)
# ambient = gen.white(...)   # white noise
# ambient = gen.brown(...)   # brown noise
# ambient = gen.womb(...)    # womb/heartbeat (brown + ~60 BPM pulse)

# 4. Mix and write a 10-minute loopable WAV
mixer = Mixer(melody_vol=0.8, ambient_vol=0.3)
buf = mixer.mix(melody, ambient)
mixer.write(buf, "sleep.wav", duration=600.0, fade_in=2.0)
```

The output is a seamlessly loopable 44100 Hz / 16-bit mono WAV. Tiling is handled automatically — the one-pass melody buffer is tiled to fill the requested duration.

---

## API

### `Synth(sf2_path, preset="music_box")`

Loads a soundfont and selects an instrument preset. Rendering is offline — no audio driver is opened.

| Parameter | Type | Description |
|-----------|------|-------------|
| `sf2_path` | `str` | Path to a `.sf2` soundfont file |
| `preset` | `str` | Instrument preset name (see `PRESETS`) |

Raises `ValueError` for unknown presets, `FileNotFoundError` if the soundfont cannot be loaded, `OSError` if `libfluidsynth3` is not installed.

#### `synth.render(note, duration) -> np.ndarray`

Renders a single note to a float32 mono buffer.

| Parameter | Type | Description |
|-----------|------|-------------|
| `note` | `str` | Note name: `"c4"`, `"g#3"`, `"bb5"`, etc. |
| `duration` | `float` | Buffer length in seconds |

#### `PRESETS`

```python
{
    "music_box": 10,  # GM program 11: Music Box
    "celesta":    8,  # GM program  9: Celesta
    "bells":     14,  # GM program 15: Tubular Bells
}
```

---

### `MelodyPipeline(synth, gap_seconds=0.05)`

Sequences notes into a melody buffer. Inserts 50 ms silence between notes by default and trims the end to the nearest zero crossing for clean looping.

| Method | Description |
|--------|-------------|
| `from_preset(name)` | Render a built-in lullaby. Names: `"twinkle"`, `"brahms"`, `"mary"` |
| `from_notes(notes)` | Render a caller-supplied `list[tuple[str, float]]` (note, duration) |
| `from_procedural(num_notes, num_fifths, seed)` | Generate a circle-of-fifths melody |

---

### `AmbientGenerator(seed=None)`

Generates ambient noise buffers. All methods return float32 mono at 44100 Hz.

| Method | Description |
|--------|-------------|
| `white(duration)` | White noise |
| `pink(duration)` | Pink noise (−3 dB/oct) |
| `brown(duration)` | Brown noise (−6 dB/oct) |
| `womb(duration, bpm=60.0)` | Brown noise + ~60 BPM lub-dub heartbeat envelope |

---

### `Mixer(melody_vol=0.8, ambient_vol=0.3)`

Combines audio layers and writes the output WAV.

#### `mixer.mix(melody, ambient) -> np.ndarray`

Scales and sums two same-length float32 buffers. Raises `ValueError` if shapes differ.

#### `mixer.write(buf, path, duration, fade_in=0.0, fade_out=0.0)`

Tiles `buf` to `duration` seconds, normalizes, applies fade-in, and writes a 16-bit mono WAV.

| Parameter | Type | Description |
|-----------|------|-------------|
| `buf` | `np.ndarray` | Mixed buffer from `mix()` |
| `path` | `str` | Output file path |
| `duration` | `float` | Total WAV length in seconds |
| `fade_in` | `float` | Fade-in duration in seconds (default 0.0) |
| `fade_out` | `float` | Must be 0.0 — loop safety constraint |

---

## Buffer contract

All audio buffers are `np.ndarray`, dtype `float32`, shape `(N,)` (mono), sample rate **44100 Hz**, values in `[-1.0, 1.0]`.

---

## Development

```bash
uv sync

uv run pytest          # unit tests pass without libfluidsynth3; integration tests skip
uv run mypy src/
uv run ruff check src/
```

---

## Architecture

| Module | Responsibility |
|--------|----------------|
| `synth.py` | Soundfont-rendered note synthesis via FluidSynth |
| `melody.py` | Sequence notes into melody buffers; built-in lullaby presets |
| `ambient.py` | White / pink / brown / womb noise generation |
| `mixer.py` | Mix melody + ambient, normalize, write loopable WAV |
