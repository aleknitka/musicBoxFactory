from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AudioRequest(BaseModel):
    """Request model for audio generation."""
    
    sf2_path: str = Field(..., description="Path to the .sf2 soundfont file")
    instrument: Literal["music_box", "celesta", "bells"] = Field(
        "music_box", description="Instrument preset to use"
    )
    melody_type: Literal["preset", "procedural"] = Field(
        "preset", description="Type of melody to generate"
    )
    melody_preset: Literal["twinkle", "brahms", "mary"] = Field(
        "twinkle", description="Built-in lullaby preset (used if melody_type is 'preset')"
    )
    ambient_type: Literal["white", "pink", "brown", "womb"] = Field(
        "white", description="Type of ambient noise to generate"
    )
    melody_vol: float = Field(
        0.5, ge=0.0, le=1.0, description="Volume of the melody layer"
    )
    ambient_vol: float = Field(
        0.2, ge=0.0, le=1.0, description="Volume of the ambient layer"
    )
    duration: float = Field(
        30.0, ge=1.0, le=3600.0, description="Total duration in seconds"
    )
    fade_in: float = Field(
        2.0, ge=0.0, le=10.0, description="Fade-in duration in seconds"
    )


class AudioResponse(BaseModel):
    """Response model for audio generation."""
    
    file_path: str = Field(..., description="URL or path to the generated WAV file")
    message: str = Field("Success", description="Status message")
