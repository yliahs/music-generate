"""Automation and Marker models for Phase 8."""

from uuid import uuid4

from pydantic import BaseModel, Field

from composer_engine.models.enums import AutomationParam


class AutomationPoint(BaseModel):
    """Single control point on an automation curve."""

    beat: float
    value: int = Field(ge=0, le=127)


class AutomationCurve(BaseModel):
    """Automation curve for a single parameter."""

    param: AutomationParam
    points: list[AutomationPoint] = Field(default_factory=list)

    def get_value_at(self, beat: float) -> int | None:
        """Linear interpolation at given beat."""
        if not self.points:
            return None
        sorted_pts = sorted(self.points, key=lambda p: p.beat)
        if beat <= sorted_pts[0].beat:
            return sorted_pts[0].value
        if beat >= sorted_pts[-1].beat:
            return sorted_pts[-1].value
        for i in range(len(sorted_pts) - 1):
            if sorted_pts[i].beat <= beat <= sorted_pts[i + 1].beat:
                t = (beat - sorted_pts[i].beat) / (
                    sorted_pts[i + 1].beat - sorted_pts[i].beat
                )
                return round(
                    sorted_pts[i].value
                    + t * (sorted_pts[i + 1].value - sorted_pts[i].value)
                )
        return sorted_pts[-1].value


class Marker(BaseModel):
    """Timeline marker."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    beat: float
    label: str
    color: str = ""
