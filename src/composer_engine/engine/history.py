"""History manager for undo/redo and event log.

Aligned with TECHNICAL.md 5.3 - History 管理器.
"""

from datetime import datetime, timezone

from pydantic import BaseModel

from composer_engine.commands.base import Command
from composer_engine.models.song import Song


class CommandEvent(BaseModel):
    """Event Sourcing record for a command execution."""

    timestamp: datetime
    command_type: str
    description: str


class History:
    """Manages undo/redo stacks and event log.

    Uses Snapshot strategy: stores Song deep copy before each command.
    Max undo defaults to 100.
    """

    def __init__(self, max_undo: int = 100):
        self.undo_stack: list[tuple[Command, Song]] = []
        self.redo_stack: list[tuple[Command, Song]] = []
        self.event_log: list[CommandEvent] = []
        self.max_undo = max_undo

    def push(self, command: Command, before_state: Song) -> None:
        """Record an operation. Clears redo stack."""
        self.undo_stack.append((command, before_state))
        self.redo_stack.clear()
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)
        self.event_log.append(
            CommandEvent(
                timestamp=datetime.now(timezone.utc),
                command_type=type(command).__name__,
                description=command.description,
            )
        )

    def pop_undo(self) -> tuple[Command, Song] | None:
        """Pop the most recent operation for undo."""
        if not self.undo_stack:
            return None
        return self.undo_stack.pop()

    def pop_redo(self) -> tuple[Command, Song] | None:
        """Pop the most recent undone operation for redo."""
        if not self.redo_stack:
            return None
        return self.redo_stack.pop()

    def push_redo(self, command: Command, before_state: Song) -> None:
        """Push to redo stack (used during undo)."""
        self.redo_stack.append((command, before_state))

    def clear(self) -> None:
        """Clear all history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.event_log.clear()
