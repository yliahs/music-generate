"""Global settings commands.

Aligned with TECHNICAL.md 5.2 - Global Commands.
Phase 1: SetTempo, SetKey, SetMode, SetTimeSignature, SetMasterVelocity, SetMasterHumanize.
Phase 12: SetScale, SetMasterTiming, SetGlobalEnergy.
"""

from datetime import datetime, timezone
from typing import Optional

from composer_engine.commands.base import Command
from composer_engine.models.enums import Key, Mode
from composer_engine.models.song import Song


class SetTempoCommand(Command):
    """Set song tempo."""

    def __init__(self, tempo: float):
        self.tempo = tempo

    @property
    def description(self) -> str:
        return f"Set tempo to {self.tempo} BPM"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.global_settings.tempo = self.tempo
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetKeyCommand(Command):
    """Set song key."""

    def __init__(self, key: Key):
        self.key = key

    @property
    def description(self) -> str:
        return f"Set key to {self.key.value}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.global_settings.key = self.key
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetModeCommand(Command):
    """Set song mode."""

    def __init__(self, mode: Mode):
        self.mode = mode

    @property
    def description(self) -> str:
        return f"Set mode to {self.mode.value}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.global_settings.mode = self.mode
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTimeSignatureCommand(Command):
    """Set song time signature."""

    def __init__(self, numerator: int, denominator: int):
        self.numerator = numerator
        self.denominator = denominator

    @property
    def description(self) -> str:
        return f"Set time signature to {self.numerator}/{self.denominator}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.global_settings.time_signature = (self.numerator, self.denominator)
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetMasterVelocityCommand(Command):
    """Set master velocity baseline."""

    def __init__(self, velocity: int):
        self.velocity = max(0, min(127, velocity))

    @property
    def description(self) -> str:
        return f"Set master velocity to {self.velocity}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.global_settings.master_velocity = self.velocity
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetMasterHumanizeCommand(Command):
    """Set master humanize amount."""

    def __init__(self, amount: float):
        self.amount = max(0.0, min(1.0, amount))

    @property
    def description(self) -> str:
        return f"Set master humanize to {self.amount}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.global_settings.master_humanize = self.amount
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetScaleCommand(Command):
    """Set song scale (override Key+Mode default)."""

    def __init__(self, scale: Optional[str]):
        self.scale = scale

    @property
    def description(self) -> str:
        return f"Set scale to {self.scale or 'auto'}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.global_settings.scale = self.scale
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetMasterTimingCommand(Command):
    """Set master timing offset."""

    def __init__(self, timing: float):
        self.timing = timing

    @property
    def description(self) -> str:
        return f"Set master timing to {self.timing}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.global_settings.master_timing = self.timing
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetGlobalEnergyCommand(Command):
    """Set global energy level."""

    def __init__(self, energy: float):
        self.energy = max(0.0, min(1.0, energy))

    @property
    def description(self) -> str:
        return f"Set global energy to {self.energy}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.global_settings.global_energy = self.energy
        song.updated_at = datetime.now(timezone.utc)
        return song
