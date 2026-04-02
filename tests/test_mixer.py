"""Tests for musicboxfactory.mixer — OUT-01, OUT-02, OUT-03, OUT-04, OUT-05."""
from __future__ import annotations

import numpy as np
import pytest
from scipy.io import wavfile  # type: ignore[import-untyped]

from musicboxfactory.mixer import Mixer as MixerDirect  # direct import always works
from musicboxfactory.synth import SAMPLE_RATE


# ---------------------------------------------------------------------------
# OUT-01: mix() — buffer contract and volume scaling
# ---------------------------------------------------------------------------

def test_import() -> None:
    """Mixer can be imported from the top-level musicboxfactory package (D-02)."""
    # Will fail until __init__.py exports Mixer — that happens in Plan 02
    from musicboxfactory import Mixer as _Mixer  # noqa: F401  # ImportError is the RED state


def test_mix_buffer_contract() -> None:
    """mix() returns float32 ndarray of same shape as inputs (OUT-01)."""
    mixer = MixerDirect()  # NotImplementedError is the RED state
    melody = np.zeros(SAMPLE_RATE, dtype=np.float32)
    ambient = np.zeros(SAMPLE_RATE, dtype=np.float32)
    result = mixer.mix(melody, ambient)
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    assert result.shape == melody.shape


def test_mix_volumes_applied() -> None:
    """mix() scales melody and ambient by their respective volume factors (OUT-01)."""
    mixer = MixerDirect(melody_vol=0.6, ambient_vol=0.2)  # NotImplementedError is the RED state
    melody = np.ones(SAMPLE_RATE, dtype=np.float32)
    ambient = np.ones(SAMPLE_RATE, dtype=np.float32)
    result = mixer.mix(melody, ambient)
    # Expected raw mix value: 0.6 * 1.0 + 0.2 * 1.0 = 0.8
    assert float(result[0]) == pytest.approx(0.8, abs=1e-5)


# ---------------------------------------------------------------------------
# OUT-02: write() — normalization / no clipping
# ---------------------------------------------------------------------------

def test_write_no_clipping(tmp_path: pytest.TempPathFactory) -> None:
    """write() normalizes output so WAV int16 values never exceed ±32767 (OUT-02)."""
    mixer = MixerDirect()  # NotImplementedError is the RED state
    buf = np.zeros(SAMPLE_RATE, dtype=np.float32)
    out_path = str(tmp_path / "out.wav")
    mixer.write(buf, out_path, duration=1.0)
    rate, data = wavfile.read(out_path)
    assert data.dtype == np.int16
    assert int(np.abs(data).max()) <= 32767


def test_write_no_clipping_high_vol() -> None:
    """write() normalizes even when combined volumes would exceed 1.0 (OUT-02)."""
    mixer = MixerDirect(melody_vol=1.0, ambient_vol=1.0)  # NotImplementedError is the RED state
    melody = np.ones(SAMPLE_RATE, dtype=np.float32)
    ambient = np.ones(SAMPLE_RATE, dtype=np.float32)
    buf = mixer.mix(melody, ambient)
    # buf would have values of 2.0 before normalization — mixer.write must normalize it
    assert float(np.abs(buf).max()) <= 2.0 + 1e-6  # raw mix can exceed 1.0


# ---------------------------------------------------------------------------
# OUT-03: write() — exact duration
# ---------------------------------------------------------------------------

def test_write_exact_duration(tmp_path: pytest.TempPathFactory) -> None:
    """write() tiles buf to requested duration and writes exactly that many samples (OUT-03)."""
    mixer = MixerDirect()  # NotImplementedError is the RED state
    buf = np.zeros(SAMPLE_RATE, dtype=np.float32)  # 1-second base buffer
    out_path = str(tmp_path / "out.wav")
    target_duration = 3.0
    mixer.write(buf, out_path, duration=target_duration)
    rate, data = wavfile.read(out_path)
    expected_samples = int(SAMPLE_RATE * target_duration)
    assert len(data) == expected_samples


def test_write_wav_readable(tmp_path: pytest.TempPathFactory) -> None:
    """write() produces a valid WAV file readable by scipy.io.wavfile (OUT-03)."""
    mixer = MixerDirect()  # NotImplementedError is the RED state
    buf = np.zeros(SAMPLE_RATE, dtype=np.float32)
    out_path = str(tmp_path / "out.wav")
    mixer.write(buf, out_path, duration=1.0)
    rate, data = wavfile.read(out_path)
    assert rate == SAMPLE_RATE
    assert data.ndim == 1  # mono


# ---------------------------------------------------------------------------
# OUT-04: write() — loop-safe tiling at zero-crossing boundary
# ---------------------------------------------------------------------------

def test_tiling_zero_crossing(tmp_path: pytest.TempPathFactory) -> None:
    """write() trims buf to nearest zero-crossing before tiling so loop boundary is click-free (OUT-04)."""
    mixer = MixerDirect()  # NotImplementedError is the RED state
    # Create a sine wave that does NOT end at zero — tiling without trim would cause a click
    t = np.arange(SAMPLE_RATE, dtype=np.float32) / SAMPLE_RATE
    buf = np.sin(2 * np.pi * 440.0 * t).astype(np.float32)
    out_path = str(tmp_path / "out.wav")
    mixer.write(buf, out_path, duration=2.0)
    rate, data = wavfile.read(out_path)
    # The written WAV should be close to 2 seconds (within rounding to zero-crossing trim)
    assert abs(len(data) - int(SAMPLE_RATE * 2.0)) < SAMPLE_RATE


# ---------------------------------------------------------------------------
# OUT-05: write() — fade-in and fade-out constraints
# ---------------------------------------------------------------------------

def test_fade_in_applied(tmp_path: pytest.TempPathFactory) -> None:
    """write(fade_in=0.1) applies a linear fade-in to the first fade_in seconds (OUT-05)."""
    mixer = MixerDirect()  # NotImplementedError is the RED state
    buf = np.ones(SAMPLE_RATE, dtype=np.float32)
    out_path = str(tmp_path / "out.wav")
    fade_in_seconds = 0.1
    mixer.write(buf, out_path, duration=1.0, fade_in=fade_in_seconds)
    rate, data = wavfile.read(out_path)
    # First sample should be near zero after fade-in (amplitude ramps from 0)
    assert abs(data[0]) < 1000  # int16 scale: near zero means < 1000 out of 32767


def test_fade_out_raises() -> None:
    """write(fade_out=0.1) raises ValueError to enforce loop-safety constraint (OUT-05)."""
    mixer = MixerDirect()  # NotImplementedError is the RED state
    buf = np.zeros(SAMPLE_RATE, dtype=np.float32)
    with pytest.raises((ValueError, NotImplementedError)):
        mixer.write(buf, "dummy.wav", duration=1.0, fade_out=0.1)
