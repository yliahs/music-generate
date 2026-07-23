"""GlobalSettings model.

Aligned with TECHNICAL.md 2.2 / REQUIREMENTS.md 3.2.
Phase 1: tempo, time_signature, key, mode, swing, master_velocity, master_humanize.
Phase 12: scale, master_timing, global_energy.
"""

from typing import Optional

from pydantic import BaseModel, Field

from composer_engine.models.enums import Key, Mode


class GlobalSettings(BaseModel):
    """Global settings for a song."""

    tempo: float = Field(default=120.0, gt=0, le=300, description="Tempo in BPM")
    time_signature: tuple[int, int] = Field(
        default=(4, 4), description="Time signature (numerator, denominator)"
    )
    key: Key = Key.C
    mode: Mode = Mode.MAJOR
    swing: float = Field(default=0.0, ge=0.0, le=1.0, description="Swing amount")
    master_velocity: int = Field(default=100, ge=0, le=127, description="Master velocity")
    master_humanize: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Master humanize amount"
    )
    groove: str = Field(default="straight", description="Global groove template name")
    style: str = Field(default="", description="Current style preset")
    mood: str = Field(default="", description="Current mood tag")
    # Phase 12
    scale: Optional[str] = Field(default=None, description="Override scale name (None=auto from Key+Mode)")
    master_timing: float = Field(default=0.0, description="Global timing offset in beats")
    global_energy: float = Field(default=0.5, ge=0.0, le=1.0, description="Global energy level")
