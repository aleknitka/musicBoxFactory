"""Mixer: combine melody and ambient buffers, normalize, and write a loop-safe WAV file.

Public API:
    Mixer(melody_vol=0.8, ambient_vol=0.3) — configure volume levels
    mixer.mix(melody, ambient) -> np.ndarray  (OUT-01)
    mixer.write(buf, path, duration, fade_in=0.0, fade_out=0.0) -> None  (OUT-02–OUT-05)
"""
from __future__ import annotations

import numpy as np
from scipy.io import wavfile  # type: ignore[import-untyped]

from musicboxfactory.synth import SAMPLE_RATE
from musicboxfactory.melody import _trim_to_zero_crossing


def _tile_to_length(buf: np.ndarray, n_samples: int) -> np.ndarray:
    """Tile buf to exactly n_samples. Zero-pad if buf is empty."""
    if len(buf) == 0:
        return np.zeros(n_samples, dtype=np.float32)
    n_tiles = int(np.ceil(n_samples / len(buf)))
    return np.tile(buf, n_tiles)[:n_samples]


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
        self._melody_vol = melody_vol
        self._ambient_vol = ambient_vol

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
        if melody.shape != ambient.shape:
            raise ValueError(
                f"melody and ambient must have the same shape; "
                f"got {melody.shape} and {ambient.shape}."
            )
        return (melody * self._melody_vol + ambient * self._ambient_vol).astype(np.float32)

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
        if fade_out > 0:
            raise ValueError(
                "fade_out breaks loop safety: a faded-out tail cannot tile seamlessly. "
                "Omit fade_out (keep it at 0.0) for loop-safe WAV files. "
                "Non-looping export with fade_out is a v2 feature."
            )

        target_n = int(duration * SAMPLE_RATE)
        buf_safe = _trim_to_zero_crossing(buf)
        tiled = _tile_to_length(buf_safe, target_n)

        # Fade-in applied to full-duration tiled buffer (not input buf)
        if fade_in > 0.0:
            fade_samples = min(int(fade_in * SAMPLE_RATE), len(tiled))
            if fade_samples > 0:
                ramp = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
                tiled[:fade_samples] *= ramp

        # Peak normalization before int16 conversion (D-09)
        peak = float(np.abs(tiled).max())
        if peak > 1e-9:
            tiled = tiled / peak

        # int16 conversion — use 32767 (not 32768) to stay inside int16 range
        as_int16 = (tiled * 32767).astype(np.int16)
        wavfile.write(path, SAMPLE_RATE, as_int16)
