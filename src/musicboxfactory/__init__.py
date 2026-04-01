"""Music Box Factory — soundfont-based baby sleep audio library.

Public API::

    from musicboxfactory import Synth, PRESETS

    synth = Synth("path/to/soundfont.sf2", preset="music_box")
    buf = synth.render("c4", duration=2.0)
    # buf: np.ndarray, dtype=float32, shape=(88200,), values in [-1.0, 1.0]
"""
from __future__ import annotations

from musicboxfactory.synth import PRESETS, Synth

__all__ = ["Synth", "PRESETS"]
