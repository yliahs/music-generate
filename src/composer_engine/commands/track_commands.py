"""Track-level commands.

Aligned with TECHNICAL.md 5.2 - Track Commands.
Phase 1: Add, Remove, Mute, Solo, Volume, Pan, AddNotes, RemoveNotes.
Phase 12: Register, Complexity, VelocityOffset, TimingOffset, Humanize, Groove, Rhythm, Range.
"""

from datetime import datetime, timezone

from composer_engine.commands.base import Command
from composer_engine.models.enums import InstrumentType
from composer_engine.models.note import Note
from composer_engine.models.song import Song
from composer_engine.models.track import Track


class AddTrackCommand(Command):
    """Add a new track to the song."""

    def __init__(
        self,
        name: str,
        instrument: InstrumentType,
        program: int | None = None,
        channel: int | None = None,
    ):
        self.name = name
        self.instrument = instrument
        self.program = program
        self.channel = channel

    @property
    def description(self) -> str:
        return f"Add track '{self.name}' ({self.instrument.value})"

    def execute(self, song: Song) -> Song:
        kwargs = {}
        if self.program is not None:
            kwargs["program"] = self.program
        if self.channel is not None:
            kwargs["channel"] = self.channel
        track = Track.create(name=self.name, instrument=self.instrument, **kwargs)
        song = song.model_copy(deep=True)
        song.tracks.append(track)
        song.updated_at = datetime.now(timezone.utc)
        return song


class RemoveTrackCommand(Command):
    """Remove a track from the song."""

    def __init__(self, track_id: str):
        self.track_id = track_id

    @property
    def description(self) -> str:
        return f"Remove track '{self.track_id}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.tracks = [t for t in song.tracks if t.id != self.track_id]
        song.updated_at = datetime.now(timezone.utc)
        return song


class MuteTrackCommand(Command):
    """Set track mute state."""

    def __init__(self, track_id: str, mute: bool):
        self.track_id = track_id
        self.mute = mute

    @property
    def description(self) -> str:
        action = "Mute" if self.mute else "Unmute"
        return f"{action} track '{self.track_id}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.mute = self.mute
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class SoloTrackCommand(Command):
    """Set track solo state."""

    def __init__(self, track_id: str, solo: bool):
        self.track_id = track_id
        self.solo = solo

    @property
    def description(self) -> str:
        action = "Solo" if self.solo else "Unsolo"
        return f"{action} track '{self.track_id}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.solo = self.solo
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTrackVolumeCommand(Command):
    """Set track volume."""

    def __init__(self, track_id: str, volume: int):
        self.track_id = track_id
        self.volume = volume

    @property
    def description(self) -> str:
        return f"Set track '{self.track_id}' volume to {self.volume}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.volume = self.volume
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTrackPanCommand(Command):
    """Set track pan."""

    def __init__(self, track_id: str, pan: int):
        self.track_id = track_id
        self.pan = pan

    @property
    def description(self) -> str:
        return f"Set track '{self.track_id}' pan to {self.pan}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.pan = self.pan
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class AddNotesCommand(Command):
    """Add notes to a track."""

    def __init__(self, track_id: str, notes: list[Note]):
        self.track_id = track_id
        self.notes = notes

    @property
    def description(self) -> str:
        return f"Add {len(self.notes)} note(s) to track '{self.track_id}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.notes.extend(self.notes)
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class RemoveNotesCommand(Command):
    """Remove notes from a track by indices."""

    def __init__(self, track_id: str, note_indices: list[int]):
        self.track_id = track_id
        self.note_indices = sorted(note_indices, reverse=True)

    @property
    def description(self) -> str:
        return f"Remove {len(self.note_indices)} note(s) from track '{self.track_id}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                for idx in self.note_indices:
                    if 0 <= idx < len(track.notes):
                        track.notes.pop(idx)
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


# ── Phase 12: Track property commands ─────────────────────────────────────


class SetTrackRegisterCommand(Command):
    """Set track register (high/mid/low)."""

    def __init__(self, track_id: str, register: str):
        self.track_id = track_id
        self.register = register if register in ("high", "mid", "low") else "mid"

    @property
    def description(self) -> str:
        return f"Set track '{self.track_id}' register to {self.register}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.track_register = self.register
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTrackComplexityCommand(Command):
    """Set track complexity."""

    def __init__(self, track_id: str, complexity: float):
        self.track_id = track_id
        self.complexity = max(0.0, min(1.0, complexity))

    @property
    def description(self) -> str:
        return f"Set track '{self.track_id}' complexity to {self.complexity}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.complexity = self.complexity
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTrackVelocityOffsetCommand(Command):
    """Set track velocity offset."""

    def __init__(self, track_id: str, offset: int):
        self.track_id = track_id
        self.offset = max(-127, min(127, offset))

    @property
    def description(self) -> str:
        return f"Set track '{self.track_id}' velocity offset to {self.offset}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.velocity_offset = self.offset
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTrackTimingOffsetCommand(Command):
    """Set track timing offset."""

    def __init__(self, track_id: str, offset: float):
        self.track_id = track_id
        self.offset = offset

    @property
    def description(self) -> str:
        return f"Set track '{self.track_id}' timing offset to {self.offset}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.timing_offset = self.offset
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTrackHumanizeCommand(Command):
    """Set track humanize amount."""

    def __init__(self, track_id: str, humanize: float):
        self.track_id = track_id
        self.humanize = max(0.0, min(1.0, humanize))

    @property
    def description(self) -> str:
        return f"Set track '{self.track_id}' humanize to {self.humanize}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.humanize = self.humanize
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTrackGrooveCommand(Command):
    """Set track groove template."""

    def __init__(self, track_id: str, groove: str):
        self.track_id = track_id
        self.groove = groove

    @property
    def description(self) -> str:
        return f"Set track '{self.track_id}' groove to '{self.groove}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.groove = self.groove
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTrackRhythmCommand(Command):
    """Set track rhythm pattern."""

    def __init__(self, track_id: str, rhythm_pattern: str):
        self.track_id = track_id
        self.rhythm_pattern = rhythm_pattern

    @property
    def description(self) -> str:
        return f"Set track '{self.track_id}' rhythm to '{self.rhythm_pattern}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.rhythm_pattern = self.rhythm_pattern
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetTrackRangeCommand(Command):
    """Set track pitch range."""

    def __init__(self, track_id: str, low: int, high: int):
        self.track_id = track_id
        self.low = max(0, min(127, low))
        self.high = max(0, min(127, high))

    @property
    def description(self) -> str:
        return f"Set track '{self.track_id}' range to {self.low}-{self.high}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for track in song.tracks:
            if track.id == self.track_id:
                track.pitch_range_low = self.low
                track.pitch_range_high = self.high
                break
        song.updated_at = datetime.now(timezone.utc)
        return song
