"""Tests for musicboxfactory.melody — MELO-01, MELO-02, MELO-03."""
from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import Mock

from musicboxfactory.melody import (
    MelodyPipeline,
    render_sequence,
    generate_circle_of_fifths,
    _trim_to_zero_crossing,
    LULLABY_PRESETS,
)
from musicboxfactory.synth import Synth
from .conftest import requires_sf2


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def synth_mock() -> Mock:
    mock = Mock(spec=Synth)
    mock.render.side_effect = lambda note, duration: np.zeros(
        int(44100 * duration), dtype=np.float32
    )
    return mock


# ---------------------------------------------------------------------------
# MELO-02: render_sequence — unit tests (no soundfont required)
# ---------------------------------------------------------------------------

def test_render_sequence_empty(synth_mock: Mock) -> None:
    """render_sequence with empty list returns float32 ndarray of shape (0,)."""
    result = render_sequence(synth_mock, [])
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    assert result.shape == (0,)


def test_render_sequence_single_note(synth_mock: Mock) -> None:
    """render_sequence with one note returns float32 ndarray with at least 1 sample."""
    result = render_sequence(synth_mock, [("c4", 0.5)])
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    assert result.shape[0] >= 1


def test_render_sequence_gap_inserted(synth_mock: Mock) -> None:
    """render_sequence with gap_seconds=0.1 produces buffer longer than note duration alone."""
    notes = [("c4", 0.5), ("g4", 0.5)]
    note_samples = int(44100 * 0.5) * 2  # samples from notes only
    result = render_sequence(synth_mock, notes, gap_seconds=0.1)
    assert result.shape[0] > note_samples


def test_render_sequence_skips_zero_duration(synth_mock: Mock) -> None:
    """render_sequence skips zero-duration notes; result matches [("g4", 0.5)] alone."""
    result_with_zero = render_sequence(synth_mock, [("c4", 0.0), ("g4", 0.5)], gap_seconds=0.0)
    result_without_zero = render_sequence(synth_mock, [("g4", 0.5)], gap_seconds=0.0)
    assert result_with_zero.shape == result_without_zero.shape


def test_render_sequence_buffer_contract(synth_mock: Mock) -> None:
    """Output of render_sequence has dtype float32 and is 1-dimensional (mono)."""
    result = render_sequence(synth_mock, [("c4", 0.3), ("e4", 0.3)])
    assert result.dtype == np.float32
    assert result.ndim == 1


# ---------------------------------------------------------------------------
# MELO-02: _trim_to_zero_crossing — unit test
# ---------------------------------------------------------------------------

def test_trim_to_zero_crossing_no_op_on_short() -> None:
    """_trim_to_zero_crossing on empty buffer returns same-length buffer."""
    buf = np.array([], dtype=np.float32)
    result = _trim_to_zero_crossing(buf)
    assert isinstance(result, np.ndarray)
    assert result.shape == (0,)


# ---------------------------------------------------------------------------
# MELO-02: MelodyPipeline.from_notes — unit tests
# ---------------------------------------------------------------------------

def test_melody_pipeline_custom_notes(synth_mock: Mock) -> None:
    """MelodyPipeline.from_notes returns float32 ndarray for a valid note list."""
    pipeline = MelodyPipeline(synth_mock)
    result = pipeline.from_notes([("c4", 0.5)])
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32


def test_melody_pipeline_unknown_preset(synth_mock: Mock) -> None:
    """MelodyPipeline.from_preset raises ValueError for unrecognised preset name."""
    pipeline = MelodyPipeline(synth_mock)
    with pytest.raises(ValueError):
        pipeline.from_preset("nonexistent")


# ---------------------------------------------------------------------------
# MELO-03: generate_circle_of_fifths — unit tests
# ---------------------------------------------------------------------------

def test_procedural_generator_returns_list() -> None:
    """generate_circle_of_fifths returns a list of exactly num_notes tuples."""
    result = generate_circle_of_fifths(num_notes=8, seed=42)
    assert isinstance(result, list)
    assert len(result) == 8
    for item in result:
        assert isinstance(item, tuple)
        assert len(item) == 2
        assert isinstance(item[0], str)
        assert isinstance(item[1], float)


def test_procedural_generator_deterministic() -> None:
    """Two calls with same seed return identical lists."""
    result_a = generate_circle_of_fifths(num_notes=8, seed=42)
    result_b = generate_circle_of_fifths(num_notes=8, seed=42)
    assert result_a == result_b


def test_procedural_generator_octave_range() -> None:
    """All notes from generate_circle_of_fifths have octave in [3, 4, 5]."""
    result = generate_circle_of_fifths(num_notes=16, seed=1)
    for note, _ in result:
        octave = int("".join(c for c in note if c.isdigit()))
        assert 3 <= octave <= 5, f"Note {note!r} has octave {octave} outside [3, 5]"


# ---------------------------------------------------------------------------
# MELO-01: built-in lullaby presets (unit — just check the constant exists)
# ---------------------------------------------------------------------------

def test_lullaby_presets_contains_expected_keys() -> None:
    """LULLABY_PRESETS contains at least 'twinkle' and 'brahms' keys."""
    assert "twinkle" in LULLABY_PRESETS
    assert "brahms" in LULLABY_PRESETS


# ---------------------------------------------------------------------------
# Integration tests (require a real .sf2 soundfont)
# ---------------------------------------------------------------------------

@requires_sf2
def test_preset_twinkle_integration(sf2_path: str) -> None:
    """from_preset('twinkle') returns ndarray longer than 1 second (> 44100 samples)."""
    from musicboxfactory.synth import Synth  # noqa: PLC0415

    pipeline = MelodyPipeline(Synth(sf2_path))
    result = pipeline.from_preset("twinkle")
    assert isinstance(result, np.ndarray)
    assert len(result) > 44100


@requires_sf2
def test_preset_brahms_integration(sf2_path: str) -> None:
    """from_preset('brahms') returns ndarray longer than 1 second (> 44100 samples)."""
    from musicboxfactory.synth import Synth  # noqa: PLC0415

    pipeline = MelodyPipeline(Synth(sf2_path))
    result = pipeline.from_preset("brahms")
    assert isinstance(result, np.ndarray)
    assert len(result) > 44100


@requires_sf2
def test_custom_sequence_integration(sf2_path: str) -> None:
    """from_notes with two notes returns non-empty ndarray."""
    from musicboxfactory.synth import Synth  # noqa: PLC0415

    pipeline = MelodyPipeline(Synth(sf2_path))
    result = pipeline.from_notes([("c4", 0.5), ("g4", 0.5)])
    assert isinstance(result, np.ndarray)
    assert len(result) > 0


@requires_sf2
def test_procedural_integration(sf2_path: str) -> None:
    """from_procedural returns a numpy ndarray for a short sequence."""
    from musicboxfactory.synth import Synth  # noqa: PLC0415

    pipeline = MelodyPipeline(Synth(sf2_path))
    result = pipeline.from_procedural(num_notes=4, seed=0)
    assert isinstance(result, np.ndarray)
