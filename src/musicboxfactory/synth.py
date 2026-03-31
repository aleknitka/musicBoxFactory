"""Tone synthesis via FluidSynth soundfont rendering.

Public API:
    Synth(sf2_path, preset='music_box') — load soundfont, select instrument
    synth.render(note, duration) -> np.ndarray (float32, mono, 44100 Hz, [-1, 1])

PRESETS — dict mapping preset names to 0-indexed GM program numbers.
"""
from __future__ import annotations

import numpy as np

try:
    import fluidsynth as _fluidsynth  # type: ignore[import-untyped]
    _FLUIDSYNTH_AVAILABLE = True
except (OSError, ImportError):
    _fluidsynth = None  # noqa: F841
    _FLUIDSYNTH_AVAILABLE = False

SAMPLE_RATE: int = 44100
BLOCK_SIZE: int = 1024

# 0-indexed General MIDI program numbers (FluidSynth program_select is 0-indexed;
# GM spec lists programs 1-128, so subtract 1).
PRESETS: dict[str, int] = {
    "music_box": 10,  # GM program 11: Music Box
    "celesta": 8,     # GM program 9:  Celesta
    "bells": 14,      # GM program 15: Tubular Bells
}

_PITCH_CLASS: dict[str, int] = {
    "c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11
}


def _note_name_to_midi(note: str) -> int:
    """Convert a note name string to a MIDI note number.

    Supports natural notes (c4), sharps (g#3, f#2), and flats (bb5, eb4).
    Middle C (c4) = MIDI 60. Concert A (a4) = MIDI 69.

    Args:
        note: Note name string, e.g. 'c4', 'g#3', 'bb5', 'F#2'.

    Returns:
        Integer MIDI note number.

    Raises:
        ValueError: If the note string is too short or has an invalid pitch letter.
    """
    note = note.strip().lower()
    if len(note) < 2:
        raise ValueError(f"Invalid note name: {note!r}. Expected format: 'c4', 'g#3', 'bb5'.")

    pitch_char = note[0]
    if pitch_char not in _PITCH_CLASS:
        raise ValueError(
            f"Invalid pitch letter {pitch_char!r} in note {note!r}. "
            f"Valid letters: {list(_PITCH_CLASS)}"
        )

    if len(note) >= 3 and note[1] in ("#", "b"):
        accidental = 1 if note[1] == "#" else -1
        octave = int(note[2:])
    else:
        accidental = 0
        octave = int(note[1:])

    pitch_class = _PITCH_CLASS[pitch_char] + accidental
    return (octave + 1) * 12 + pitch_class  # C4 = (4+1)*12 + 0 = 60


class Synth:
    """Stateful soundfont-based tone synthesizer.

    Loads a .sf2 soundfont once at construction; each render() call is cheap
    (no file I/O, no driver initialisation).

    Usage::

        synth = Synth("path/to/soundfont.sf2", preset="music_box")
        buf = synth.render("c4", duration=2.0)
        # buf: np.ndarray, dtype=float32, shape=(88200,), values in [-1.0, 1.0]

    Args:
        sf2_path: Path to the caller-provided .sf2 soundfont file.
        preset: Named instrument preset. One of: 'music_box', 'celesta', 'bells'.

    Raises:
        ValueError: If preset is not a recognised name.
        FileNotFoundError: If sf2_path does not exist or cannot be loaded by FluidSynth.
    """

    def __init__(self, sf2_path: str, preset: str = "music_box") -> None:
        if preset not in PRESETS:
            raise ValueError(
                f"Unknown preset {preset!r}. Valid presets: {list(PRESETS)}"
            )

        if not _FLUIDSYNTH_AVAILABLE or _fluidsynth is None:
            raise OSError(
                "FluidSynth C library not found. Install it with:\n"
                "    sudo apt install libfluidsynth3\n"
                "Then re-install pyfluidsynth: uv add pyfluidsynth"
            )

        # Do NOT call self._fs.start() — that opens a live ALSA/PulseAudio driver.
        # Offline rendering via get_samples() requires no audio driver.
        self._fs = _fluidsynth.Synth(gain=0.5, samplerate=float(SAMPLE_RATE))
        self._sfid: int = self._fs.sfload(sf2_path)
        if self._sfid == -1:
            raise FileNotFoundError(
                f"Could not load soundfont: {sf2_path!r}. "
                "Verify the file exists and is a valid .sf2 soundfont."
            )

        # Select instrument: channel=0, bank=0 (GM standard bank), patch=PRESETS[preset]
        self._fs.program_select(0, self._sfid, 0, PRESETS[preset])

    def render(self, note: str, duration: float) -> np.ndarray:
        """Render a note to a float32 mono buffer at 44100 Hz.

        The returned buffer is exactly int(44100 * duration) samples long.
        Natural note decay (ring-out) beyond `duration` is drained internally
        and discarded — the caller receives only the requested window.

        Args:
            note: Note name, e.g. 'c4', 'g#3', 'bb5'.
            duration: Desired buffer length in seconds.

        Returns:
            np.ndarray, dtype=float32, shape=(N,), values in [-1.0, 1.0],
            where N = int(44100 * duration).
        """
        midi_note = _note_name_to_midi(note)
        n_samples = int(SAMPLE_RATE * duration)

        # Render note body
        self._fs.noteon(0, midi_note, 100)
        body = self._collect_samples(n_samples)

        # Noteoff then drain decay tail (music box tines ring 2-4 seconds;
        # not draining causes abrupt silence — see RESEARCH.md Pitfall 1)
        self._fs.noteoff(0, midi_note)
        tail_samples = int(SAMPLE_RATE * 3.0)
        self._collect_samples(tail_samples)  # discard tail

        # Normalise to guarantee [-1.0, 1.0] contract regardless of FluidSynth gain
        peak = float(np.abs(body).max())
        if peak > 1e-9:
            body = body / peak

        return body

    def _collect_samples(self, n_samples: int) -> np.ndarray:
        """Collect exactly n_samples from the FluidSynth renderer.

        get_samples(n) returns int16 interleaved stereo of shape (2*n,).
        This method reshapes, downmixes to mono, and converts to float32.
        """
        chunks: list[np.ndarray] = []
        collected = 0
        while collected < n_samples:
            block = min(BLOCK_SIZE, n_samples - collected)
            raw = self._fs.get_samples(block)          # int16, shape (2*block,)
            stereo = raw.reshape(-1, 2)                # shape (block, 2)
            mono = stereo.mean(axis=1)                 # shape (block,)
            chunks.append(mono.astype(np.float32) / 32768.0)
            collected += block
        return np.concatenate(chunks)[:n_samples]
