"""Music Box Factory — soundfont-based baby sleep audio library.

Public API::

    from musicboxfactory import Synth, PRESETS
    from musicboxfactory import MelodyPipeline, LULLABY_PRESETS

    synth = Synth("path/to/soundfont.sf2", preset="music_box")
    buf = synth.render("c4", duration=2.0)
    # buf: np.ndarray, dtype=float32, shape=(88200,), values in [-1.0, 1.0]

    pipeline = MelodyPipeline(synth)
    melody_buf = pipeline.from_preset("twinkle")
    melody_buf = pipeline.from_notes([("c4", 0.5), ("g4", 0.5)])
    melody_buf = pipeline.from_procedural(num_notes=16, seed=42)
"""
from __future__ import annotations

from musicboxfactory.synth import PRESETS, Synth
from musicboxfactory.melody import LULLABY_PRESETS, MelodyPipeline

__all__ = ["Synth", "PRESETS", "MelodyPipeline", "LULLABY_PRESETS"]
