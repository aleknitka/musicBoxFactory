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

import numpy as np

from musicboxfactory.synth import SAMPLE_RATE, Synth  # noqa: F401

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


def _trim_to_zero_crossing(buf: np.ndarray, search_window: int = 2048) -> np.ndarray:
    raise NotImplementedError


def render_sequence(
    synth: Synth,
    notes: NoteSequence,
    gap_seconds: float = 0.05,
) -> np.ndarray:
    raise NotImplementedError


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
