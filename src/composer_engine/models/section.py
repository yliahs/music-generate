"""Section model.

Aligned with TECHNICAL.md 2.2 / REQUIREMENTS.md 3.3.
"""

from uuid import uuid4

from pydantic import BaseModel, Field

from composer_engine.models.enums import SectionType


class Section(BaseModel):
    """A song section (e.g. Intro, Verse, Chorus)."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: SectionType
    start_beat: float = Field(ge=0, description="Start position in beats")
    length_beats: float = Field(gt=0, description="Length in beats")
    repeat: int = Field(default=1, ge=1, description="Repeat count")
