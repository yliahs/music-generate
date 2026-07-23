"""Command abstract base class.

All mutations go through Commands. (Design Principle G3, G5)
Undo uses Snapshot strategy - History saves Song deep copy before execute.

Aligned with TECHNICAL.md 5.2.
"""

from abc import ABC, abstractmethod

from composer_engine.models.song import Song


class Command(ABC):
    """Base class for all commands."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of this command."""
        ...

    @abstractmethod
    def execute(self, song: Song) -> Song:
        """Execute the command, return modified Song."""
        ...
