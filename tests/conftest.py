"""Shared test fixtures for musicboxfactory tests."""
from __future__ import annotations

import os
import pytest

# Path to a real .sf2 soundfont for integration tests.
# Set MBF_SF2_PATH env var, or install fluid-soundfont-gm (apt) which places it here.
_DEFAULT_SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
SF2_PATH = os.environ.get("MBF_SF2_PATH", _DEFAULT_SF2)

requires_sf2 = pytest.mark.skipif(
    not os.path.exists(SF2_PATH),
    reason=f"No soundfont at {SF2_PATH}. Install fluid-soundfont-gm or set MBF_SF2_PATH.",
)


@pytest.fixture
def sf2_path() -> str:
    """Return path to the test soundfont. Skip test if file is absent."""
    if not os.path.exists(SF2_PATH):
        pytest.skip(f"No soundfont at {SF2_PATH}. Install fluid-soundfont-gm or set MBF_SF2_PATH.")
    return SF2_PATH
