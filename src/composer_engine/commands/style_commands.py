"""Style commands for genre presets and mood settings.

Aligned with TECHNICAL.md 5.13 - Phase 6 Style Commands.
"""

from datetime import datetime, timezone

from composer_engine.commands.base import Command
from composer_engine.generators.style_engine import StyleEngine
from composer_engine.models.song import Song


class SetStyleCommand(Command):
    def __init__(self, style_name: str):
        self.style_name = style_name
        self._result: dict = {}

    @property
    def description(self) -> str:
        return f"Set style to {self.style_name}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = StyleEngine()
        self._result = engine.set_style(song, self.style_name)
        song.updated_at = datetime.now(timezone.utc)
        return song


class MixStylesCommand(Command):
    def __init__(self, style_a: str, style_b: str, weight_a: float = 0.5):
        self.style_a = style_a
        self.style_b = style_b
        self.weight_a = weight_a
        self._result: dict = {}

    @property
    def description(self) -> str:
        return f"Mix styles {self.style_a} + {self.style_b}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = StyleEngine()
        self._result = engine.mix_styles(
            song, self.style_a, self.style_b, self.weight_a
        )
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetMoodCommand(Command):
    def __init__(self, mood: str):
        self.mood = mood

    @property
    def description(self) -> str:
        return f"Set mood to {self.mood}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.global_settings.mood = self.mood
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetSwingCommand(Command):
    def __init__(self, swing_amount: float):
        self.swing_amount = swing_amount

    @property
    def description(self) -> str:
        return f"Set swing to {self.swing_amount}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.global_settings.swing = max(0.0, min(1.0, self.swing_amount))
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetGrooveCommand(Command):
    def __init__(self, groove_name: str):
        self.groove_name = groove_name

    @property
    def description(self) -> str:
        return f"Set groove to {self.groove_name}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.global_settings.groove = self.groove_name
        song.updated_at = datetime.now(timezone.utc)
        return song
