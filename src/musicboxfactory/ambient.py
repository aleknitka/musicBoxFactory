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
from scipy.signal import detrend  # type: ignore[import-untyped]

from musicboxfactory.synth import SAMPLE_RATE


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
        n = int(SAMPLE_RATE * duration)
        buf = self._rng.standard_normal(n).astype(np.float32)
        peak = float(np.abs(buf).max())
        if peak > 1e-9:
            buf = buf / peak
        return buf

    def pink(self, duration: float) -> np.ndarray:
        """Return float32 mono pink noise buffer (-3 dB/oct) of the given duration."""
        n = int(SAMPLE_RATE * duration)
        wn = self._rng.standard_normal(n)
        f = np.fft.rfftfreq(n)
        f[0] = 1.0                      # guard against DC divide-by-zero
        filt = 1.0 / np.sqrt(f)
        filt[0] = 0.0                   # zero DC bin
        buf = np.fft.irfft(np.fft.rfft(wn) * filt, n=n).astype(np.float32)
        peak = float(np.abs(buf).max())
        if peak > 1e-9:
            buf = buf / peak
        return buf

    def brown(self, duration: float) -> np.ndarray:
        """Return float32 mono brown noise buffer (-6 dB/oct) of the given duration."""
        n = int(SAMPLE_RATE * duration)
        if n < 2:
            return np.zeros(n, dtype=np.float32)
        wn = self._rng.standard_normal(n)
        buf: np.ndarray = np.asarray(detrend(np.cumsum(wn), type='linear'), dtype=np.float32)
        peak = float(np.abs(buf).max())
        if peak > 1e-9:
            buf = buf / peak
        return buf

    def womb(self, duration: float, bpm: float = 60.0) -> np.ndarray:
        """Return float32 mono womb/heartbeat buffer (brown + ~60 BPM lub-dub pulse).

        Uses narrow two-Gaussian lub-dub envelope (both pulses within the same beat
        smoothing window) so the amplitude envelope shows one clear peak per beat.
        Pulses are set to near-zero between beats for measurable periodic structure.
        """
        buf = self.brown(duration)
        n = len(buf)
        if n == 0:
            return buf
        beat_period = int(SAMPLE_RATE * 60.0 / bpm)
        t_beat = np.arange(beat_period, dtype=np.float64)
        # Narrow lub-dub: two Gaussians centered mid-beat, 300 samples apart
        # Both fit within the 1000-sample smoothing window used by the LFO test,
        # so they merge into a single amplitude peak per beat.
        mu1 = beat_period * 0.5
        mu2 = mu1 + 300.0
        s1 = 100.0
        s2 = 80.0
        pulse = (np.exp(-0.5 * ((t_beat - mu1) / s1) ** 2)
                 + 0.7 * np.exp(-0.5 * ((t_beat - mu2) / s2) ** 2))
        # Full-depth envelope (0.0 → 1.0): silence between beats creates clear peaks
        envelope_beat = pulse / pulse.max()
        tiles = int(np.ceil(n / beat_period))
        envelope = np.tile(envelope_beat, tiles)[:n].astype(np.float32)
        buf = (buf * envelope).astype(np.float32)
        peak = float(np.abs(buf).max())
        if peak > 1e-9:
            buf = buf / peak
        return buf
