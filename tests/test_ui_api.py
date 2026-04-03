from __future__ import annotations

import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from musicboxfactory.ui.app import app
from musicboxfactory.ui.models import AudioRequest

client = TestClient(app)

def test_root():
    """Verify that the root endpoint returns status 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Music Box Factory API is running" in response.json()["message"]

def test_generate_missing_sf2():
    """Verify that providing a non-existent soundfont returns 400."""
    data = {
        "sf2_path": "/tmp/non_existent.sf2",
        "instrument": "music_box",
        "melody_type": "preset",
        "melody_preset": "twinkle",
        "ambient_type": "white",
        "melody_vol": 0.5,
        "ambient_vol": 0.2,
        "duration": 5.0,
        "fade_in": 1.0
    }
    response = client.post("/api/v1/generate", json=data)
    assert response.status_code == 400
    assert "Soundfont file not found" in response.json()["detail"]

@patch("musicboxfactory.ui.app.generate_audio")
def test_generate_success_mock(mock_gen):
    """Verify success response structure when audio generation is mocked."""
    # Mock returning a dummy file path
    mock_gen.return_value = "/tmp/musicboxfactory_ui/gen_12345.wav"
    
    data = {
        "sf2_path": "/tmp/test.sf2",
        "instrument": "celesta",
        "melody_type": "procedural",
        "melody_preset": "brahms",
        "ambient_type": "pink",
        "melody_vol": 0.8,
        "ambient_vol": 0.4,
        "duration": 10.0,
        "fade_in": 2.0
    }
    
    # We must also mock os.path.exists or provide a fake file path that exists
    # but since we mocked generate_audio, we skip the logic that checks the file
    # unless logic.py checks it first. logic.py checks it.
    
    # Let's mock logic.os.path.exists too
    with patch("musicboxfactory.ui.logic.os.path.exists", return_value=True):
        response = client.post("/api/v1/generate", json=data)
    
    assert response.status_code == 200
    assert response.json()["file_path"] == "/static/gen_12345.wav"
    assert "successfully" in response.json()["message"]
    mock_gen.assert_called_once()

def test_generate_invalid_input():
    """Verify that invalid pydantic inputs return 422."""
    data = {
        "sf2_path": "/tmp/test.sf2",
        "melody_vol": 1.5,  # Out of range [0.0, 1.0]
    }
    response = client.post("/api/v1/generate", json=data)
    assert response.status_code == 422
