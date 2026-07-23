"""Snapshot manager for named Song snapshots.

Aligned with TECHNICAL.md 5.3 - Snapshot 管理器.
"""

from composer_engine.models.song import Song


class SnapshotManager:
    """Manages named Song snapshots (deep copies)."""

    def __init__(self):
        self._snapshots: dict[str, Song] = {}

    def save(self, name: str, song: Song) -> None:
        """Save a named snapshot (deep copy of Song)."""
        self._snapshots[name] = song.model_copy(deep=True)

    def load(self, name: str) -> Song:
        """Load a named snapshot. Raises KeyError if not found."""
        if name not in self._snapshots:
            raise KeyError(f"Snapshot '{name}' not found")
        return self._snapshots[name].model_copy(deep=True)

    def list(self) -> list[str]:
        """List all snapshot names."""
        return list(self._snapshots.keys())

    def delete(self, name: str) -> None:
        """Delete a named snapshot."""
        self._snapshots.pop(name, None)
