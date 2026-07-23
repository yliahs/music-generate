"""Composer - the main engine.

The core of the entire system. All mutations go through execute().

Aligned with TECHNICAL.md 5.3.
"""

from composer_engine.commands.base import Command
from composer_engine.engine.history import History
from composer_engine.engine.snapshot import SnapshotManager
from composer_engine.models.song import Song
from composer_engine.observability.logger import log
from composer_engine.pipeline.pipeline_manager import PipelineManager


class ComposerError(Exception):
    """Raised when a Composer operation fails."""


class Composer:
    """Main engine - maintains Song state, executes Commands, manages history and pipeline.

    Responsibilities:
    1. Maintain current Song state
    2. Execute Commands (all mutations must go through Commands)
    3. Manage Undo/Redo history
    4. Manage Snapshots
    5. Manage Pipeline (stage tracking and evaluation)
    """

    def __init__(self):
        self.song: Song | None = None
        self.history: History = History()
        self.snapshots: SnapshotManager = SnapshotManager()
        self.pipeline: PipelineManager = PipelineManager()

    def execute(self, command: Command) -> Song:
        """Execute a command.

        Flow: save before_state → execute command → evaluate pipeline → return new state
        """
        before_state = self.song.model_copy(deep=True) if self.song else None
        self.song = command.execute(self.song)
        # Phase 7: Clear analysis cache after any command execution
        if (
            self.song is not None
            and hasattr(self.song, "analysis_cache")
            and self.song.analysis_cache
        ):
            self.song.analysis_cache.clear()
        if before_state is not None:
            self.history.push(command, before_state)
        else:
            self.history.push(command, Song(name=""))
        log(f"{command.__class__.__name__} → {command.description}", tag="CMD")
        self.pipeline.evaluate(self.song)
        return self.song

    def undo(self) -> Song:
        """Undo the most recent operation."""
        entry = self.history.pop_undo()
        if entry is None:
            raise ComposerError("Nothing to undo")
        command, before_state = entry
        log(f"Undo: {command.description}", tag="CMD")
        self.history.push_redo(command, self.song)
        self.song = before_state
        self.pipeline.evaluate(self.song)
        return self.song

    def redo(self) -> Song:
        """Redo the most recently undone operation."""
        entry = self.history.pop_redo()
        if entry is None:
            raise ComposerError("Nothing to redo")
        command, before_state = entry
        before_current = self.song.model_copy(deep=True)
        self.song = command.execute(self.song)
        if (
            self.song is not None
            and hasattr(self.song, "analysis_cache")
            and self.song.analysis_cache
        ):
            self.song.analysis_cache.clear()
        log(f"Redo: {command.description}", tag="CMD")
        self.history.undo_stack.append((command, before_current))
        self.pipeline.evaluate(self.song)
        return self.song

    def get_state(self) -> dict:
        """Return complete state including song, pipeline, and history summary."""
        evaluation = self.pipeline.evaluate(self.song)
        return {
            "song": self.song.model_dump(mode="json") if self.song else None,
            "pipeline": {
                "stage": self.pipeline.current_stage.value,
                "progress": evaluation.progress,
                "can_advance": evaluation.can_advance,
            },
            "history": {
                "undo_count": len(self.history.undo_stack),
                "redo_count": len(self.history.redo_stack),
            },
        }

    def get_stage_guide(self) -> dict:
        """Return pipeline stage guide for AI."""
        guide = self.pipeline.get_guide(self.song)
        return guide.model_dump()

    def save_snapshot(self, name: str) -> None:
        """Save current state as a named snapshot."""
        if self.song is None:
            raise ComposerError("No song to snapshot")
        self.snapshots.save(name, self.song)

    def load_snapshot(self, name: str) -> Song:
        """Load a named snapshot, replacing current state."""
        self.song = self.snapshots.load(name)
        self.pipeline.evaluate(self.song)
        return self.song
