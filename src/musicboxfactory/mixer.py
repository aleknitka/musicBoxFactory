"""Mixer: combine melody and ambient buffers, normalize, and write a loop-safe WAV file.

Public API:
    Mixer(melody_vol=0.8, ambient_vol=0.3) — configure volume levels
    mixer.mix(melody, ambient) -> np.ndarray  (OUT-01)
    mixer.write(buf, path, duration, fade_in, fade_out) -> None  (OUT-02, OUT-03, OUT-04, OUT-05)
"""
from __future__ import annotations

import numpy as np

from musicboxfactory.synth import SAMPLE_RATE as _SAMPLE_RATE  # noqa: F401


class Mixer:
    """Combine melody and ambient audio layers and write a normalized WAV file.

    Usage::

        mixer = Mixer(melody_vol=0.8, ambient_vol=0.3)
        buf = mixer.mix(melody_buf, ambient_buf)
        mixer.write(buf, "output.wav", duration=600.0)

    Args:
        melody_vol: Melody volume scale factor in [0.0, 1.0]. Default 0.8.
        ambient_vol: Ambient volume scale factor in [0.0, 1.0]. Default 0.3.
    """

    def __init__(self, melody_vol: float = 0.8, ambient_vol: float = 0.3) -> None:
        raise NotImplementedError

    def mix(self, melody: np.ndarray, ambient: np.ndarray) -> np.ndarray:
        """Scale melody and ambient by configured volumes and sum into a raw float32 buffer.

        Args:
            melody: float32 mono buffer, shape (N,), values in [-1.0, 1.0].
            ambient: float32 mono buffer, shape (N,), values in [-1.0, 1.0].
                     Must have the same length as melody.

        Returns:
            np.ndarray, dtype=float32, shape (N,). Raw (un-normalized) mixed buffer.

        Raises:
            ValueError: If melody and ambient shapes differ.
        """
        raise NotImplementedError

    def write(
        self,
        buf: np.ndarray,
        path: str,
        duration: float,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
    ) -> None:
        """Tile buf to duration, normalize, apply fade-in, and write a loop-safe WAV.

        Args:
            buf: Raw float32 mono buffer from mix().
            path: Output file path (string).
            duration: Desired WAV length in seconds.
            fade_in: Fade-in duration in seconds applied at file start. Default 0.0.
            fade_out: Must be 0.0 — raises ValueError if > 0 (loop safety constraint).

        Raises:
            ValueError: If fade_out > 0 (breaks loop safety).
        """
        raise NotImplementedError
