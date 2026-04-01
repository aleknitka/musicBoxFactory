"""Tests for musicboxfactory.ambient — AMBI-01, AMBI-02, AMBI-03, AMBI-04."""
from __future__ import annotations

import numpy as np
import pytest

from musicboxfactory.ambient import AmbientGenerator
from musicboxfactory.synth import SAMPLE_RATE


# ---------------------------------------------------------------------------
# AMBI-01: white noise
# ---------------------------------------------------------------------------

def test_import() -> None:
    """AmbientGenerator can be imported from musicboxfactory.ambient without error."""
    gen = AmbientGenerator()
    assert gen is not None


def test_white_buffer_contract() -> None:
    """white(1.0) returns float32 ndarray shape=(44100,), values in [-1.0, 1.0]."""
    gen = AmbientGenerator(seed=42)
    buf = gen.white(1.0)
    assert isinstance(buf, np.ndarray)
    assert buf.dtype == np.float32
    assert buf.shape == (SAMPLE_RATE,)
    assert float(np.min(buf)) >= -1.0
    assert float(np.max(buf)) <= 1.0


def test_white_sample_count() -> None:
    """white(2.5) returns exactly int(44100 * 2.5) = 110250 samples."""
    gen = AmbientGenerator(seed=42)
    buf = gen.white(2.5)
    assert len(buf) == int(SAMPLE_RATE * 2.5)


# ---------------------------------------------------------------------------
# AMBI-02: pink noise
# ---------------------------------------------------------------------------

def test_pink_buffer_contract() -> None:
    """pink(1.0) returns float32 ndarray shape=(44100,), values in [-1.0, 1.0]."""
    gen = AmbientGenerator(seed=42)
    buf = gen.pink(1.0)
    assert isinstance(buf, np.ndarray)
    assert buf.dtype == np.float32
    assert buf.shape == (SAMPLE_RATE,)
    assert float(np.min(buf)) >= -1.0
    assert float(np.max(buf)) <= 1.0


def test_pink_spectral_slope() -> None:
    """pink(5.0) spectral slope is in range [-4.0, -2.0] dB/octave (100-400 Hz bins)."""
    gen = AmbientGenerator(seed=42)
    buf = gen.pink(5.0)
    psd = np.abs(np.fft.rfft(buf)) ** 2
    freqs = np.fft.rfftfreq(len(buf), 1 / SAMPLE_RATE)
    mask1 = (freqs >= 100) & (freqs < 200)
    mask2 = (freqs >= 200) & (freqs < 400)
    slope = 10 * np.log10(psd[mask2].mean()) - 10 * np.log10(psd[mask1].mean())
    assert -4.0 <= slope <= -2.0, f"Pink spectral slope {slope:.2f} dB/oct outside [-4.0, -2.0]"


def test_pink_no_dc() -> None:
    """pink(5.0) absolute mean is < 0.01 (no DC bias)."""
    gen = AmbientGenerator(seed=42)
    buf = gen.pink(5.0)
    assert abs(float(buf.mean())) < 0.01


# ---------------------------------------------------------------------------
# AMBI-03: brown noise
# ---------------------------------------------------------------------------

def test_brown_buffer_contract() -> None:
    """brown(1.0) returns float32 ndarray shape=(44100,), values in [-1.0, 1.0]."""
    gen = AmbientGenerator(seed=42)
    buf = gen.brown(1.0)
    assert isinstance(buf, np.ndarray)
    assert buf.dtype == np.float32
    assert buf.shape == (SAMPLE_RATE,)
    assert float(np.min(buf)) >= -1.0
    assert float(np.max(buf)) <= 1.0


def test_brown_spectral_slope() -> None:
    """brown(5.0) spectral slope is in range [-7.0, -5.0] dB/octave (100-400 Hz bins)."""
    gen = AmbientGenerator(seed=42)
    buf = gen.brown(5.0)
    psd = np.abs(np.fft.rfft(buf)) ** 2
    freqs = np.fft.rfftfreq(len(buf), 1 / SAMPLE_RATE)
    mask1 = (freqs >= 100) & (freqs < 200)
    mask2 = (freqs >= 200) & (freqs < 400)
    slope = 10 * np.log10(psd[mask2].mean()) - 10 * np.log10(psd[mask1].mean())
    assert -7.0 <= slope <= -5.0, f"Brown spectral slope {slope:.2f} dB/oct outside [-7.0, -5.0]"


def test_brown_no_dc() -> None:
    """brown(5.0) absolute mean is < 0.01 (no DC bias)."""
    gen = AmbientGenerator(seed=42)
    buf = gen.brown(5.0)
    assert abs(float(buf.mean())) < 0.01


# ---------------------------------------------------------------------------
# AMBI-04: womb/heartbeat noise
# ---------------------------------------------------------------------------

def test_womb_buffer_contract() -> None:
    """womb(1.0) returns float32 ndarray shape=(44100,), values in [-1.0, 1.0]."""
    gen = AmbientGenerator(seed=42)
    buf = gen.womb(1.0)
    assert isinstance(buf, np.ndarray)
    assert buf.dtype == np.float32
    assert buf.shape == (SAMPLE_RATE,)
    assert float(np.min(buf)) >= -1.0
    assert float(np.max(buf)) <= 1.0


def test_womb_lfo_period() -> None:
    """womb(5.0, bpm=60) envelope shows periodic amplitude variation with period ~44100 samples."""
    gen = AmbientGenerator(seed=42)
    buf = gen.womb(5.0, bpm=60)
    # Compute envelope as abs(buf) smoothed with a 1000-sample window
    window_size = 1000
    kernel = np.ones(window_size) / window_size
    envelope = np.convolve(np.abs(buf), kernel, mode="valid")
    # Find local maxima (peaks in envelope)
    peak_indices = []
    for i in range(1, len(envelope) - 1):
        if envelope[i] > envelope[i - 1] and envelope[i] > envelope[i + 1]:
            peak_indices.append(i)
    assert len(peak_indices) >= 2, "Expected at least 2 peaks in womb envelope"
    spacings = np.diff(peak_indices)
    median_spacing = float(np.median(spacings))
    # 60 BPM => 1 beat per second => 44100 samples; allow 20% tolerance
    assert 35280 <= median_spacing <= 52920, (
        f"Womb LFO median peak spacing {median_spacing:.0f} outside [35280, 52920]"
    )


# ---------------------------------------------------------------------------
# All: seed reproducibility
# ---------------------------------------------------------------------------

def test_seed_reproducibility() -> None:
    """AmbientGenerator(seed=42).white(1.0) equals AmbientGenerator(seed=42).white(1.0)."""
    buf_a = AmbientGenerator(seed=42).white(1.0)
    buf_b = AmbientGenerator(seed=42).white(1.0)
    np.testing.assert_array_equal(buf_a, buf_b)
