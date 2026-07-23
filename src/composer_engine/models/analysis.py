"""Analysis result models for Phase 7.

Aligned with TECHNICAL.md 5.14.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """Generic analysis result container."""
    type: str
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    track_id: str | None = None


class Phrase(BaseModel):
    """Detected musical phrase."""
    start_beat: float
    end_beat: float
    note_count: int = 0


class Motif(BaseModel):
    """Detected musical motif."""
    pitches: list[int] = Field(default_factory=list)
    rhythm: list[float] = Field(default_factory=list)
    occurrences: list[float] = Field(default_factory=list)


class RhythmProfile(BaseModel):
    """Rhythm analysis result."""
    dominant_value: float = 1.0
    syncopation_ratio: float = 0.0
    complexity: float = 0.0


class VoiceLeadingIssue(BaseModel):
    """Voice leading problem."""
    beat: float
    type: str
    description: str
    track_a: str = ""
    track_b: str = ""


class CounterpointReport(BaseModel):
    """Counterpoint analysis result."""
    parallel_ratio: float = 0.0
    contrary_ratio: float = 0.0
    oblique_ratio: float = 0.0
    similar_ratio: float = 0.0
    issues: list[VoiceLeadingIssue] = Field(default_factory=list)


class StyleMatch(BaseModel):
    """Style detection result."""
    style: str = ""
    confidence: float = 0.0
    scores: dict[str, float] = Field(default_factory=dict)


class MoodProfile(BaseModel):
    """Mood detection result."""
    valence: float = 0.0
    arousal: float = 0.0
    tags: list[str] = Field(default_factory=list)


class DynamicProfile(BaseModel):
    """Dynamic analysis result."""
    velocity_range: tuple[int, int] = (0, 127)
    avg_velocity: float = 64.0
    contour: list[tuple[float, float]] = Field(default_factory=list)


class StructureSegment(BaseModel):
    """Structure analysis segment."""
    type: str
    start_beat: float
    end_beat: float
    similarity_to: list[str] = Field(default_factory=list)
