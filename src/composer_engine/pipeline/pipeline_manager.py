"""PipelineManager - orchestration layer above Commands.

Rules:
1. Auto-advance: when exit conditions are met, advance to next stage
2. Free go-back: can go back to any previous stage
3. Guidance, not enforcement: does not block any operation
4. Auto-evaluate: called after every Composer.execute()

Aligned with TECHNICAL.md 5.7.
"""

from pydantic import BaseModel

from composer_engine.models.enums import Stage
from composer_engine.models.song import Song
from composer_engine.pipeline.evaluation import EXIT_CHECKERS
from composer_engine.pipeline.stages import STAGE_DEFINITIONS, STAGE_ORDER


class StageEvaluation(BaseModel):
    """Result of evaluating the current stage."""

    current_stage: Stage
    progress: int
    completed_conditions: list[str]
    missing_conditions: list[str]
    can_advance: bool
    next_stage: Stage | None


class StageGuide(BaseModel):
    """AI guidance for the current stage."""

    stage: str
    stage_description: str
    progress: int
    what_to_do: list[str]
    what_is_missing: list[str]
    recommended_tools: list[str]
    can_advance: bool
    next_stage: str | None


class PipelineManager:
    """Manages the song creation pipeline."""

    def __init__(self):
        self.current_stage: Stage = Stage.EMPTY
        self.stage_history: list[dict] = []

    def evaluate(self, song: Song | None) -> StageEvaluation:
        """Evaluate current song state. Auto-advance if exit conditions are met."""
        if song is None or not song.name:
            self.current_stage = Stage.EMPTY
            return StageEvaluation(
                current_stage=Stage.EMPTY,
                progress=0,
                completed_conditions=[],
                missing_conditions=["No song created"],
                can_advance=False,
                next_stage=Stage.INSPIRATION,
            )

        if self.current_stage == Stage.EMPTY:
            self.current_stage = Stage.INSPIRATION

        checker = EXIT_CHECKERS.get(self.current_stage)
        if checker:
            completed, missing = checker(song)
        else:
            completed, missing = [], []

        total = len(completed) + len(missing)
        progress = int(len(completed) / total * 100) if total > 0 else 100

        can_advance = len(missing) == 0
        next_stage = self._get_next_stage()

        if can_advance and next_stage and self.current_stage != Stage.EXPORT:
            self._record_transition(self.current_stage, next_stage)
            self.current_stage = next_stage
            return self.evaluate(song)

        return StageEvaluation(
            current_stage=self.current_stage,
            progress=progress,
            completed_conditions=completed,
            missing_conditions=missing,
            can_advance=can_advance,
            next_stage=next_stage,
        )

    def get_guide(self, song: Song | None) -> StageGuide:
        """Get AI guidance for the current stage."""
        evaluation = self.evaluate(song)
        definition = STAGE_DEFINITIONS.get(self.current_stage)

        if definition is None:
            return StageGuide(
                stage="empty",
                stage_description="No song created yet. Use create_song to begin.",
                progress=0,
                what_to_do=["Create a new song with create_song"],
                what_is_missing=["A song must be created"],
                recommended_tools=["create_song"],
                can_advance=False,
                next_stage="inspiration",
            )

        return StageGuide(
            stage=definition.name,
            stage_description=definition.description,
            progress=evaluation.progress,
            what_to_do=definition.suggested_actions,
            what_is_missing=evaluation.missing_conditions,
            recommended_tools=definition.primary_tools,
            can_advance=evaluation.can_advance,
            next_stage=evaluation.next_stage.value if evaluation.next_stage else None,
        )

    def advance(self) -> Stage:
        """Manually advance to the next stage."""
        next_stage = self._get_next_stage()
        if next_stage is None:
            return self.current_stage
        self._record_transition(self.current_stage, next_stage)
        self.current_stage = next_stage
        return self.current_stage

    def go_back(self, target_stage: Stage) -> Stage:
        """Go back to a previous stage."""
        self._record_transition(self.current_stage, target_stage)
        self.current_stage = target_stage
        return self.current_stage

    def _get_next_stage(self) -> Stage | None:
        """Get the next stage in order."""
        try:
            idx = STAGE_ORDER.index(self.current_stage)
            if idx + 1 < len(STAGE_ORDER):
                return STAGE_ORDER[idx + 1]
        except ValueError:
            pass
        return None

    def _record_transition(self, from_stage: Stage, to_stage: Stage) -> None:
        """Record a stage transition."""
        self.stage_history.append({"from": from_stage.value, "to": to_stage.value})
