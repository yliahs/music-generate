"""Chord data models.

Aligned with TECHNICAL.md 5.9.
"""

from enum import Enum

from pydantic import BaseModel, Field

from composer_engine.models.enums import Key


class ChordQuality(str, Enum):
    """Chord quality / type."""

    MAJOR = "major"
    MINOR = "minor"
    DIMINISHED = "diminished"
    AUGMENTED = "augmented"
    DOM7 = "dom7"
    MAJ7 = "maj7"
    MIN7 = "min7"
    HALF_DIM7 = "half_dim7"
    DIM7 = "dim7"
    SUS2 = "sus2"
    SUS4 = "sus4"
    ADD9 = "add9"
    ADD11 = "add11"
    DOM9 = "dom9"
    MAJ9 = "maj9"
    MIN9 = "min9"


class CadenceType(str, Enum):
    """Cadence type for section endings."""

    AUTHENTIC = "authentic"
    PLAGAL = "plagal"
    HALF = "half"
    DECEPTIVE = "deceptive"


class Chord(BaseModel):
    """A single chord in the progression."""

    root: Key
    quality: ChordQuality = ChordQuality.MAJOR
    bass: Key | None = None
    start_beat: float = Field(ge=0)
    duration_beat: float = Field(gt=0)
    roman: str | None = None
