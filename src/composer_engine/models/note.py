"""Logical Note model.

Note is a logical musical note, NOT a MIDI event.
Time unit is beat (not seconds), decoupled from Tempo.
Renderer converts beats to seconds at render time.

Aligned with TECHNICAL.md 2.2 / 5.1.
"""

from pydantic import BaseModel, Field


class Note(BaseModel):
    """A logical musical note."""

    pitch: int = Field(ge=0, le=127, description="MIDI pitch (0-127)")
    start_beat: float = Field(ge=0, description="Start position in beats")
    duration_beat: float = Field(gt=0, description="Duration in beats")
    velocity: int = Field(default=100, ge=0, le=127, description="Velocity (0-127)")
