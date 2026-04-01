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

import random  # noqa: F401  -- used in generate_circle_of_fifths (Task 2)

import numpy as np

from musicboxfactory.synth import SAMPLE_RATE, Synth

# Type alias
NoteSequence = list[tuple[str, float]]

# --- Lullaby preset note tables (stubs — empty lists until Plan 02) ---
TWINKLE_TWINKLE: NoteSequence = []
BRAHMS_LULLABY: NoteSequence = []
MARY_HAD_A_LITTLE_LAMB: NoteSequence = []

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
    raise NotImplementedError


class MelodyPipeline:
    def __init__(self, synth: Synth, gap_seconds: float = 0.05) -> None:
        self._synth = synth
        self._gap_seconds = gap_seconds

    def from_preset(self, name: str) -> np.ndarray:
        raise NotImplementedError

    def from_notes(self, notes: NoteSequence) -> np.ndarray:
        raise NotImplementedError

    def from_procedural(
        self,
        num_notes: int = 16,
        num_fifths: int = 2,
        seed: int | None = None,
    ) -> np.ndarray:
        raise NotImplementedError
