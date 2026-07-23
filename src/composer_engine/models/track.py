"""Track model.

Aligned with TECHNICAL.md 2.2 / REQUIREMENTS.md 3.4.
"""

from uuid import uuid4

from pydantic import BaseModel, Field

from composer_engine.models.enums import (
    DEFAULT_GM_PROGRAMS,
    DRUMS_CHANNEL,
    InstrumentType,
)
from composer_engine.models.automation import AutomationCurve
from composer_engine.models.note import Note


class Track(BaseModel):
    """A musical track containing logical notes and playback parameters."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    instrument: InstrumentType
    program: int = Field(default=0, ge=0, le=127, description="MIDI Program Number")
    channel: int = Field(default=0, ge=0, le=15, description="MIDI Channel (drums=9)")
    notes: list[Note] = Field(default_factory=list)
    mute: bool = False
    solo: bool = False
    volume: int = Field(default=100, ge=0, le=127)
    pan: int = Field(default=64, ge=0, le=127, description="Pan (0=left, 64=center, 127=right)")
    octave_offset: int = Field(default=0, ge=-3, le=3, description="Octave offset (-3 to +3)")
    density: float = Field(default=0.5, ge=0.0, le=1.0, description="Note density (0-1)")
    energy: float = Field(default=0.5, ge=0.0, le=1.0, description="Energy level (0-1)")
    automation: list[AutomationCurve] = Field(default_factory=list)
    # Phase 12
    track_register: str = Field(default="mid", description="Register: high / mid / low")
    complexity: float = Field(default=0.5, ge=0.0, le=1.0, description="Complexity (0-1)")
    velocity_offset: int = Field(default=0, ge=-127, le=127, description="Velocity offset")
    timing_offset: float = Field(default=0.0, description="Timing offset in beats")
    humanize: float = Field(default=0.0, ge=0.0, le=1.0, description="Track humanize amount")
    groove: str = Field(default="", description="Track groove template name")
    rhythm_pattern: str = Field(default="", description="Rhythm pattern name")
    pitch_range_low: int = Field(default=0, ge=0, le=127, description="Pitch range lower bound")
    pitch_range_high: int = Field(default=127, ge=0, le=127, description="Pitch range upper bound")

    @classmethod
    def create(cls, name: str, instrument: InstrumentType, **kwargs) -> "Track":
        """Factory method that auto-assigns GM program and channel."""
        defaults = {
            "program": DEFAULT_GM_PROGRAMS.get(instrument, 0),
            "channel": DRUMS_CHANNEL if instrument == InstrumentType.DRUMS else 0,
        }
        defaults.update(kwargs)
        return cls(name=name, instrument=instrument, **defaults)
