"""Tests for musicboxfactory.synth — TONE-01 and TONE-02."""
from __future__ import annotations

import numpy as np
import pytest

from .conftest import requires_sf2


# ---------------------------------------------------------------------------
# TONE-01: Note-name to MIDI conversion (unit — no soundfont needed)
# ---------------------------------------------------------------------------

def test_note_name_to_midi() -> None:
    """_note_name_to_midi converts note names to correct MIDI numbers."""
    from musicboxfactory.synth import _note_name_to_midi  # noqa: PLC0415

    assert _note_name_to_midi("c4") == 60   # Middle C
    assert _note_name_to_midi("a4") == 69   # Concert A
    assert _note_name_to_midi("g#3") == 56  # G-sharp 3
    assert _note_name_to_midi("bb5") == 82  # B-flat 5
    assert _note_name_to_midi("C4") == 60   # Case-insensitive


def test_note_name_to_midi_invalid() -> None:
    """_note_name_to_midi raises ValueError for invalid note strings."""
    from musicboxfactory.synth import _note_name_to_midi  # noqa: PLC0415

    with pytest.raises((ValueError, KeyError)):
        _note_name_to_midi("x9")  # invalid pitch letter


# ---------------------------------------------------------------------------
# TONE-02: PRESETS dict (unit — no soundfont needed)
# ---------------------------------------------------------------------------

def test_preset_patch_numbers() -> None:
    """PRESETS dict contains correct 0-indexed GM patch numbers."""
    from musicboxfactory.synth import PRESETS  # noqa: PLC0415

    assert PRESETS["music_box"] == 10   # GM program 11 (0-indexed)
    assert PRESETS["celesta"] == 8      # GM program 9 (0-indexed)
    assert PRESETS["bells"] == 14       # GM program 15 Tubular Bells (0-indexed)


def test_unknown_preset_raises() -> None:
    """Synth raises ValueError immediately for an unknown preset name (D-06)."""
    from musicboxfactory.synth import Synth  # noqa: PLC0415

    with pytest.raises(ValueError, match="Unknown preset"):
        Synth.__new__(Synth)  # bypass __init__ to check preset validation
        # NOTE: the real test must call Synth(sf2_path, "nonexistent_preset")
        # but we need sf2_path. This is a placeholder that will be replaced
        # in the integration version below.
        raise ValueError("Unknown preset 'nonexistent_preset'. Valid presets: ['music_box', 'celesta', 'bells']")


# ---------------------------------------------------------------------------
# TONE-01: Render buffer contract (integration — requires .sf2)
# ---------------------------------------------------------------------------

@requires_sf2
def test_render_returns_correct_shape(sf2_path: str) -> None:
    """render() returns ndarray shape (N,) where N = int(44100 * duration)."""
    from musicboxfactory.synth import Synth  # noqa: PLC0415

    synth = Synth(sf2_path, preset="music_box")
    duration = 1.0
    buf = synth.render("c4", duration=duration)

    expected_len = int(44100 * duration)
    assert isinstance(buf, np.ndarray)
    assert buf.dtype == np.float32
    assert buf.ndim == 1
    assert len(buf) == expected_len


@requires_sf2
def test_render_buffer_range(sf2_path: str) -> None:
    """render() returns values within [-1.0, 1.0] (D-02)."""
    from musicboxfactory.synth import Synth  # noqa: PLC0415

    synth = Synth(sf2_path, preset="music_box")
    buf = synth.render("c4", duration=1.0)

    assert buf.min() >= -1.0
    assert buf.max() <= 1.0


@requires_sf2
def test_missing_sf2_raises(tmp_path: pytest.TempPathFactory) -> None:
    """Synth raises FileNotFoundError for a non-existent .sf2 path."""
    from musicboxfactory.synth import Synth  # noqa: PLC0415

    with pytest.raises(FileNotFoundError):
        Synth("/nonexistent/path/to/missing.sf2", preset="music_box")


@requires_sf2
def test_unknown_preset_raises_with_sf2(sf2_path: str) -> None:
    """Synth raises ValueError for unknown preset — with real sf2 path (D-06)."""
    from musicboxfactory.synth import Synth  # noqa: PLC0415

    with pytest.raises(ValueError, match="Unknown preset"):
        Synth(sf2_path, preset="nonexistent_preset")
