"""Arrangement and track-level commands.

Aligned with TECHNICAL.md 5.12 - Phase 5 Command 清单.
"""

from datetime import datetime, timezone

from composer_engine.commands.base import Command
from composer_engine.generators.arrangement_engine import ArrangementEngine
from composer_engine.models.enums import InstrumentType
from composer_engine.models.song import Song


def _get_track(song: Song, track_id: str):
    for t in song.tracks:
        if t.id == track_id:
            return t
    return None


class IncreaseEnergyCommand(Command):
    def __init__(self, section_id: str, amount: float = 0.5):
        self.section_id = section_id
        self.amount = amount

    @property
    def description(self) -> str:
        return f"Increase energy by {self.amount}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = ArrangementEngine()
        song = engine.increase_energy(song, self.section_id, self.amount)
        song.updated_at = datetime.now(timezone.utc)
        return song


class DecreaseEnergyCommand(Command):
    def __init__(self, section_id: str, amount: float = 0.5):
        self.section_id = section_id
        self.amount = amount

    @property
    def description(self) -> str:
        return f"Decrease energy by {self.amount}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = ArrangementEngine()
        song = engine.decrease_energy(song, self.section_id, self.amount)
        song.updated_at = datetime.now(timezone.utc)
        return song


class IncreaseDensityCommand(Command):
    def __init__(self, section_id: str, amount: float = 0.5):
        self.section_id = section_id
        self.amount = amount

    @property
    def description(self) -> str:
        return f"Increase density by {self.amount}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = ArrangementEngine()
        song = engine.increase_density(song, self.section_id, self.amount)
        song.updated_at = datetime.now(timezone.utc)
        return song


class DecreaseDensityCommand(Command):
    def __init__(self, section_id: str, amount: float = 0.5):
        self.section_id = section_id
        self.amount = amount

    @property
    def description(self) -> str:
        return f"Decrease density by {self.amount}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = ArrangementEngine()
        song = engine.decrease_density(song, self.section_id, self.amount)
        song.updated_at = datetime.now(timezone.utc)
        return song


class AddLayerCommand(Command):
    def __init__(self, section_id: str, instrument_type: str | None = None):
        self.section_id = section_id
        self.instrument_type = InstrumentType(instrument_type) if instrument_type else None

    @property
    def description(self) -> str:
        name = self.instrument_type.value if self.instrument_type else "auto"
        return f"Add layer ({name})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = ArrangementEngine()
        song = engine.add_layer(song, self.section_id, self.instrument_type)
        song.updated_at = datetime.now(timezone.utc)
        return song


class RemoveLayerCommand(Command):
    def __init__(self, section_id: str, track_id: str):
        self.section_id = section_id
        self.track_id = track_id

    @property
    def description(self) -> str:
        return f"Remove layer {self.track_id}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = ArrangementEngine()
        song = engine.remove_layer(song, self.section_id, self.track_id)
        song.updated_at = datetime.now(timezone.utc)
        return song


class BuildUpCommand(Command):
    def __init__(self, target_beat: float, build_beats: float = 4.0):
        self.target_beat = target_beat
        self.build_beats = build_beats

    @property
    def description(self) -> str:
        return f"Build up to beat {self.target_beat}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = ArrangementEngine()
        song = engine.build_up(song, self.target_beat, self.build_beats)
        song.updated_at = datetime.now(timezone.utc)
        return song


class BreakDownCommand(Command):
    def __init__(self, section_id: str):
        self.section_id = section_id

    @property
    def description(self) -> str:
        return "Break down section"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = ArrangementEngine()
        song = engine.break_down(song, self.section_id)
        song.updated_at = datetime.now(timezone.utc)
        return song


class AddTransitionCommand(Command):
    def __init__(self, from_section_id: str, to_section_id: str):
        self.from_section_id = from_section_id
        self.to_section_id = to_section_id

    @property
    def description(self) -> str:
        return "Add transition between sections"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = ArrangementEngine()
        song = engine.add_transition(song, self.from_section_id, self.to_section_id)
        song.updated_at = datetime.now(timezone.utc)
        return song


class AddFillCommand(Command):
    def __init__(self, section_id: str, beat_position: float):
        self.section_id = section_id
        self.beat_position = beat_position

    @property
    def description(self) -> str:
        return f"Add fill at beat {self.beat_position}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = ArrangementEngine()
        song = engine.add_fill(song, self.section_id, self.beat_position)
        song.updated_at = datetime.now(timezone.utc)
        return song


class AddSilenceCommand(Command):
    def __init__(self, section_id: str, track_id: str | None = None):
        self.section_id = section_id
        self.track_id = track_id

    @property
    def description(self) -> str:
        return "Add silence"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = ArrangementEngine()
        song = engine.add_silence(song, self.section_id, self.track_id)
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTrackOctaveCommand(Command):
    def __init__(self, track_id: str, octave_offset: int):
        self.track_id = track_id
        self.octave_offset = octave_offset

    @property
    def description(self) -> str:
        return f"Set track octave offset to {self.octave_offset}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            track.octave_offset = max(-3, min(3, self.octave_offset))
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTrackDensityCommand(Command):
    def __init__(self, track_id: str, density: float):
        self.track_id = track_id
        self.density = density

    @property
    def description(self) -> str:
        return f"Set track density to {self.density}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            track.density = max(0.0, min(1.0, self.density))
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTrackEnergyCommand(Command):
    def __init__(self, track_id: str, energy: float):
        self.track_id = track_id
        self.energy = energy

    @property
    def description(self) -> str:
        return f"Set track energy to {self.energy}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            track.energy = max(0.0, min(1.0, self.energy))
        song.updated_at = datetime.now(timezone.utc)
        return song
