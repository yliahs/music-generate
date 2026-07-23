"""Song model - the root aggregate.

Song is the core data, not MIDI. (Design Principle G4)
All data is accessed from Song. Serializing Song = saving all state.

Aligned with TECHNICAL.md 2.2.
"""

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from composer_engine.models.analysis import AnalysisResult
from composer_engine.models.automation import Marker
from composer_engine.models.chord import Chord
from composer_engine.models.enums import Stage
from composer_engine.models.global_settings import GlobalSettings
from composer_engine.models.section import Section
from composer_engine.models.track import Track


class Song(BaseModel):
    """Root aggregate - a complete song."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    stage: Stage = Stage.INSPIRATION
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    global_settings: GlobalSettings = Field(default_factory=GlobalSettings)
    sections: list[Section] = Field(default_factory=list)
    tracks: list[Track] = Field(default_factory=list)
    chord_progression: list[Chord] = Field(default_factory=list)
    analysis_cache: dict[str, AnalysisResult] = Field(default_factory=dict)
    markers: list[Marker] = Field(default_factory=list)
