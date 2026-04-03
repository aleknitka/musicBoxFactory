from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

from musicboxfactory.ambient import AmbientGenerator
from musicboxfactory.melody import MelodyPipeline
from musicboxfactory.mixer import Mixer
from musicboxfactory.synth import Synth
from musicboxfactory.ui.models import AudioRequest

# Global storage for temporary directories
TEMP_DIR = Path(tempfile.gettempdir()) / "musicboxfactory_ui"
TEMP_DIR.mkdir(exist_ok=True, parents=True)


def generate_audio(request: AudioRequest) -> str:
    """Generate audio based on the request and return the path to the WAV file.

    Args:
        request: Validated AudioRequest object.

    Returns:
        Absolute path to the generated WAV file.

    Raises:
        FileNotFoundError: If the soundfont file is missing.
        ValueError: If parameters are invalid.
    """
    if not os.path.exists(request.sf2_path):
        raise FileNotFoundError(f"Soundfont file not found: {request.sf2_path}")

    # 1. Initialize Synth
    synth = Synth(request.sf2_path, preset=request.instrument)

    # 2. Generate Melody
    pipeline = MelodyPipeline(synth)
    if request.melody_type == "preset":
        melody_buf = pipeline.from_preset(request.melody_preset)
    else:
        # For procedural, we use some defaults: 32 notes, seed is time-based
        melody_buf = pipeline.from_procedural(num_notes=32, seed=int(time.time()))

    # 3. Generate Ambient
    generator = AmbientGenerator()
    ambient_method = getattr(generator, request.ambient_type)
    ambient_buf = ambient_method(duration=10.0)  # ambient loop base is 10s

    # 4. Mix and Write
    mixer = Mixer()
    mixed_buf = mixer.mix(
        melody_buf,
        ambient_buf,
        melody_vol=request.melody_vol,
        ambient_vol=request.ambient_vol,
    )

    # Create a unique filename
    output_filename = f"gen_{int(time.time() * 1000)}.wav"
    output_path = TEMP_DIR / output_filename

    mixer.write(
        mixed_buf,
        str(output_path),
        duration=request.duration,
        fade_in=request.fade_in,
    )

    return str(output_path)


def cleanup_old_files(max_age_seconds: int = 3600) -> None:
    """Delete temporary files older than max_age_seconds."""
    now = time.time()
    for file in TEMP_DIR.glob("*.wav"):
        if now - file.stat().st_mtime > max_age_seconds:
            try:
                file.unlink()
            except OSError:
                pass
