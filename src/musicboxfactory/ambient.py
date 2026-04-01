"""Ambient noise generation: white, pink, brown, and womb/heartbeat buffers.

Public API:
    AmbientGenerator(seed=None) — stateless generator with optional reproducible seed
    generator.white(duration) -> np.ndarray   (AMBI-01)
    generator.pink(duration) -> np.ndarray    (AMBI-02)
    generator.brown(duration) -> np.ndarray   (AMBI-03)
    generator.womb(duration, bpm=60.0) -> np.ndarray  (AMBI-04)
"""
from __future__ import annotations

import numpy as np
from scipy.signal import detrend  # type: ignore[import-untyped]  # noqa: F401

from musicboxfactory.synth import SAMPLE_RATE  # noqa: F401


class AmbientGenerator:
    """Generates ambient noise buffers.

    All methods return float32 mono ndarrays at 44100 Hz with values in [-1.0, 1.0].

    Args:
        seed: Optional integer seed for reproducible output. None = non-deterministic.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)

    def white(self, duration: float) -> np.ndarray:
        """Return float32 mono white noise buffer of the given duration in seconds."""
        raise NotImplementedError

    def pink(self, duration: float) -> np.ndarray:
        """Return float32 mono pink noise buffer (-3 dB/oct) of the given duration."""
        raise NotImplementedError

    def brown(self, duration: float) -> np.ndarray:
        """Return float32 mono brown noise buffer (-6 dB/oct) of the given duration."""
        raise NotImplementedError

    def womb(self, duration: float, bpm: float = 60.0) -> np.ndarray:
        """Return float32 mono womb/heartbeat buffer (brown + ~60 BPM lub-dub pulse)."""
        raise NotImplementedError
