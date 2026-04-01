"""Melody pipeline: sequence Synth notes into a loopable float32 buffer.

Public API:
    MelodyPipeline(synth, gap_seconds=0.05) — stateful pipeline holding a Synth
    pipeline.from_preset(name) -> np.ndarray  (MELO-01)
    pipeline.from_notes(notes) -> np.ndarray  (MELO-02)
    pipeline.from_procedural(num_notes, num_fifths, seed) -> np.ndarray  (MELO-03)

Module-level helpers (also importable):
    render_sequence(synth, notes, gap_seconds) -> np.ndarray
    generate_circle_of_fifths(num_notes, num_fifths, root, octave, note_duration, seed) -> list[tuple[str, float]]
    _trim_to_zero_crossing(buf, search_window) -> np.ndarray
    LULLABY_PRESETS: dict[str, list[tuple[str, float]]]
    NoteSequence: type alias = list[tuple[str, float]]
"""
from __future__ import annotations

import random

import numpy as np

from musicboxfactory.synth import SAMPLE_RATE, Synth

# Type alias
NoteSequence = list[tuple[str, float]]

# --- Lullaby preset note tables ---
TWINKLE_TWINKLE: NoteSequence = [
    ("c4", 0.5), ("c4", 0.5), ("g4", 0.5), ("g4", 0.5),
    ("a4", 0.5), ("a4", 0.5), ("g4", 1.0),
    ("f4", 0.5), ("f4", 0.5), ("e4", 0.5), ("e4", 0.5),
    ("d4", 0.5), ("d4", 0.5), ("c4", 1.0),
    ("g4", 0.5), ("g4", 0.5), ("f4", 0.5), ("f4", 0.5),
    ("e4", 0.5), ("e4", 0.5), ("d4", 1.0),
    ("g4", 0.5), ("g4", 0.5), ("f4", 0.5), ("f4", 0.5),
    ("e4", 0.5), ("e4", 0.5), ("d4", 1.0),
    ("c4", 0.5), ("c4", 0.5), ("g4", 0.5), ("g4", 0.5),
    ("a4", 0.5), ("a4", 0.5), ("g4", 1.0),
    ("f4", 0.5), ("f4", 0.5), ("e4", 0.5), ("e4", 0.5),
    ("d4", 0.5), ("d4", 0.5), ("c4", 1.0),
]

BRAHMS_LULLABY: NoteSequence = [
    ("g4", 0.75), ("e4", 0.25), ("e4", 0.5),
    ("g4", 0.75), ("e4", 0.25), ("e4", 0.5),
    ("g4", 0.5), ("g4", 0.25), ("a4", 0.25), ("g4", 0.5), ("e4", 0.5),
    ("f4", 0.5), ("f4", 0.25), ("g4", 0.25), ("f4", 0.5), ("d4", 0.5),
    ("e4", 0.5), ("e4", 0.25), ("f4", 0.25), ("e4", 0.5), ("c4", 0.5),
]

MARY_HAD_A_LITTLE_LAMB: NoteSequence = [
    ("e4", 0.5), ("d4", 0.5), ("c4", 0.5), ("d4", 0.5),
    ("e4", 0.5), ("e4", 0.5), ("e4", 1.0),
    ("d4", 0.5), ("d4", 0.5), ("d4", 1.0),
    ("e4", 0.5), ("g4", 0.5), ("g4", 1.0),
    ("e4", 0.5), ("d4", 0.5), ("c4", 0.5), ("d4", 0.5),
    ("e4", 0.5), ("e4", 0.5), ("e4", 0.5), ("e4", 0.5),
    ("d4", 0.5), ("d4", 0.5), ("e4", 0.5), ("d4", 0.5), ("c4", 1.0),
]

LULLABY_PRESETS: dict[str, NoteSequence] = {
    "twinkle": TWINKLE_TWINKLE,
    "brahms": BRAHMS_LULLABY,
    "mary": MARY_HAD_A_LITTLE_LAMB,
}

# Module-level constants for procedural generation
CHROMATIC: list[str] = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]
MAJOR_INTERVALS: list[int] = [0, 2, 4, 5, 7, 9, 11]


def _trim_to_zero_crossing(buf: np.ndarray, search_window: int = 2048) -> np.ndarray:
    """Trim buffer to the last zero crossing within search_window samples from end.

    Prevents audible click at loop boundary by ensuring the buffer ends at a
    zero crossing.

    Args:
        buf: float32 mono audio buffer.
        search_window: Number of tail samples to search for a zero crossing.

    Returns:
        Buffer trimmed to the last zero crossing, or the original buffer if
        none found or buffer is too short.
    """
    if len(buf) < 2:
        return buf
    tail_start = max(0, len(buf) - search_window)
    tail = buf[tail_start:]
    sign_changes = np.where(np.diff(np.sign(tail)) != 0)[0]
    if len(sign_changes) == 0:
        return buf
    last_zc = tail_start + sign_changes[-1] + 1
    return buf[:last_zc]


def render_sequence(
    synth: Synth,
    notes: NoteSequence,
    gap_seconds: float = 0.05,
) -> np.ndarray:
    """Render a sequence of notes into a single float32 buffer.

    Calls synth.render() once per note, inserts silence gaps between notes,
    concatenates all buffers, and trims the end to the nearest zero crossing.

    Args:
        synth: Constructed Synth instance.
        notes: List of (note_name, duration_seconds) tuples.
        gap_seconds: Silence duration between notes in seconds.

    Returns:
        np.ndarray, dtype=float32, shape=(N,), values in [-1.0, 1.0].
        Returns shape (0,) for an empty note list.
    """
    silence = np.zeros(int(SAMPLE_RATE * gap_seconds), dtype=np.float32)
    chunks: list[np.ndarray] = []
    for note, duration in notes:
        if duration <= 0.0:
            continue  # skip zero/negative duration notes
        buf = synth.render(note, duration)
        chunks.append(buf)
        chunks.append(silence)
    if not chunks:
        return np.zeros(0, dtype=np.float32)
    combined = np.concatenate(chunks)
    combined = _trim_to_zero_crossing(combined)
    return combined


def generate_circle_of_fifths(
    num_notes: int = 16,
    num_fifths: int = 2,
    root: str = "c",
    octave: int = 4,
    note_duration: float = 0.4,
    seed: int | None = None,
) -> NoteSequence:
    """Generate a procedural melody traversing the circle of fifths.

    Creates a deterministic (when seeded) melody by visiting keys related by
    fifths and walking scale degrees within each key.

    Args:
        num_notes: Total number of notes to generate.
        num_fifths: Number of fifth-related key changes to traverse.
        root: Root note name (e.g. 'c', 'g', 'd').
        octave: Starting octave (clamped to [3, 5] range during generation).
        note_duration: Duration in seconds for each generated note.
        seed: Random seed for deterministic output. None = non-deterministic.

    Returns:
        List of exactly num_notes (note_name, duration) tuples.
    """
    rng = random.Random(seed)
    root_idx = CHROMATIC.index(root.lower())
    result: NoteSequence = []

    notes_per_key = max(1, num_notes // (num_fifths + 1))
    scale_degree = 0
    current_octave = octave

    keys_to_visit: list[int] = [root_idx]
    for _ in range(num_fifths):
        keys_to_visit.append((keys_to_visit[-1] + 7) % 12)
    keys_to_visit.append(root_idx)  # return to root

    for key_root in keys_to_visit:
        scale = [(key_root + interval) % 12 for interval in MAJOR_INTERVALS]
        for _ in range(notes_per_key):
            if len(result) >= num_notes:
                break
            pitch_idx = scale[scale_degree % len(scale)]
            note_name = CHROMATIC[pitch_idx] + str(current_octave)
            result.append((note_name, note_duration))

            step = rng.choices([1, -1, 2, -2], weights=[4, 4, 1, 1])[0]
            next_degree = scale_degree + step
            if next_degree < 0:
                next_degree = 0
                current_octave = max(3, current_octave - 1)  # clamp low
            elif next_degree >= len(scale):
                next_degree = len(scale) - 1
                current_octave = min(5, current_octave + 1)  # clamp high
            scale_degree = next_degree

    return result[:num_notes]


class MelodyPipeline:
    """Sequences Synth notes into a melody buffer.

    Args:
        synth: Constructed Synth instance (Phase 1).
        gap_seconds: Silence between notes in seconds (default 50 ms).
    """

    def __init__(self, synth: Synth, gap_seconds: float = 0.05) -> None:
        self._synth = synth
        self._gap_seconds = gap_seconds

    def from_preset(self, name: str) -> np.ndarray:
        """Render a built-in lullaby preset. Raises ValueError for unknown name."""
        if name not in LULLABY_PRESETS:
            raise ValueError(
                f"Unknown preset {name!r}. Valid presets: {list(LULLABY_PRESETS)}"
            )
        return render_sequence(self._synth, LULLABY_PRESETS[name], self._gap_seconds)

    def from_notes(self, notes: NoteSequence) -> np.ndarray:
        """Render a caller-supplied note sequence."""
        return render_sequence(self._synth, notes, self._gap_seconds)

    def from_procedural(
        self,
        num_notes: int = 16,
        num_fifths: int = 2,
        seed: int | None = None,
    ) -> np.ndarray:
        """Generate and render a circle-of-fifths melody."""
        notes = generate_circle_of_fifths(
            num_notes=num_notes, num_fifths=num_fifths, seed=seed
        )
        return render_sequence(self._synth, notes, self._gap_seconds)
