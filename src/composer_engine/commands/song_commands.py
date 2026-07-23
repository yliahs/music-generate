"""Song-level commands.

Aligned with TECHNICAL.md 5.2 - Song Commands.
"""

from datetime import datetime, timezone

from composer_engine.commands.base import Command
from composer_engine.models.enums import Key, Mode, Stage
from composer_engine.models.global_settings import GlobalSettings
from composer_engine.models.song import Song


class CreateSongCommand(Command):
    """Create a new song."""

    def __init__(
        self,
        name: str,
        tempo: float = 120.0,
        key: Key = Key.C,
        mode: Mode = Mode.MAJOR,
        time_signature: tuple[int, int] = (4, 4),
    ):
        self.name = name
        self.tempo = tempo
        self.key = key
        self.mode = mode
        self.time_signature = time_signature

    @property
    def description(self) -> str:
        return f"Create song '{self.name}'"

    def execute(self, song: Song) -> Song:
        return Song(
            name=self.name,
            stage=Stage.INSPIRATION,
            global_settings=GlobalSettings(
                tempo=self.tempo,
                key=self.key,
                mode=self.mode,
                time_signature=self.time_signature,
            ),
        )


class DeleteSongCommand(Command):
    """Delete the current song."""

    @property
    def description(self) -> str:
        return "Delete song"

    def execute(self, song: Song) -> Song:
        return Song(name="", stage=Stage.EMPTY)


class CloneSongCommand(Command):
    """Clone the current song with a new name."""

    def __init__(self, new_name: str):
        self.new_name = new_name

    @property
    def description(self) -> str:
        return f"Clone song as '{self.new_name}'"

    def execute(self, song: Song) -> Song:
        from uuid import uuid4

        cloned = song.model_copy(deep=True)
        cloned.id = str(uuid4())
        cloned.name = self.new_name
        cloned.created_at = datetime.now(timezone.utc)
        cloned.updated_at = datetime.now(timezone.utc)
        return cloned
