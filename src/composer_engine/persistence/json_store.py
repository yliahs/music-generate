"""JSON file persistence layer.

Uses Pydantic model_dump_json() / model_validate_json() for zero-cost serialization.
Default storage: ~/.composer-engine/songs/

Aligned with TECHNICAL.md 5.6.
"""

from pathlib import Path

from composer_engine.models.song import Song


class JsonStore:
    """JSON file-based persistence."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path.home() / ".composer-engine" / "songs"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_song(self, song: Song, filename: str | None = None) -> Path:
        """Save Song to JSON file."""
        filename = filename or f"{song.id}.json"
        path = self.base_dir / filename
        path.write_text(song.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load_song(self, filename: str) -> Song:
        """Load Song from JSON file."""
        path = self.base_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Song file not found: {path}")
        return Song.model_validate_json(path.read_text(encoding="utf-8"))

    def list_songs(self) -> list[dict]:
        """List all saved Song files."""
        songs = []
        for path in self.base_dir.glob("*.json"):
            try:
                song = Song.model_validate_json(path.read_text(encoding="utf-8"))
                songs.append({"filename": path.name, "name": song.name, "id": song.id})
            except Exception:
                continue
        return songs
