"""Humanize commands for timing, velocity, and groove adjustments.

Aligned with TECHNICAL.md 5.13 - Phase 6 Humanize Commands.
"""

from datetime import datetime, timezone

from composer_engine.commands.base import Command
from composer_engine.generators.humanize_engine import HumanizeEngine
from composer_engine.models.note import Note
from composer_engine.models.song import Song


def _get_track(song: Song, track_id: str):
    for track in song.tracks:
        if track.id == track_id:
            return track
    return None


def _get_section_range(song: Song, section_id: str) -> tuple[float, float]:
    for section in song.sections:
        if section.id == section_id:
            return section.start_beat, section.start_beat + section.length_beats
    raise ValueError(f"Section not found: {section_id}")


def _filter_notes_in_range(
    notes: list[Note], start: float, end: float
) -> list[Note]:
    return [n for n in notes if start <= n.start_beat < end]


def _select_notes(
    track_notes: list[Note], section_id: str | None, song: Song
) -> list[Note]:
    if section_id is None:
        return track_notes
    start, end = _get_section_range(song, section_id)
    return _filter_notes_in_range(track_notes, start, end)


class HumanizeTimingCommand(Command):
    def __init__(
        self, track_id: str, amount: float = 0.5, section_id: str | None = None
    ):
        self.track_id = track_id
        self.amount = amount
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Humanize timing on track {self.track_id}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            raise ValueError(f"Track not found: {self.track_id}")
        notes = _select_notes(track.notes, self.section_id, song)
        HumanizeEngine().humanize_timing(notes, self.amount)
        song.updated_at = datetime.now(timezone.utc)
        return song


class HumanizeVelocityCommand(Command):
    def __init__(
        self, track_id: str, amount: float = 0.5, section_id: str | None = None
    ):
        self.track_id = track_id
        self.amount = amount
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Humanize velocity on track {self.track_id}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            raise ValueError(f"Track not found: {self.track_id}")
        notes = _select_notes(track.notes, self.section_id, song)
        HumanizeEngine().humanize_velocity(notes, self.amount)
        song.updated_at = datetime.now(timezone.utc)
        return song


class ApplyMicroTimingCommand(Command):
    def __init__(self, track_id: str, beat_offsets: dict[float, float]):
        self.track_id = track_id
        self.beat_offsets = beat_offsets

    @property
    def description(self) -> str:
        return f"Apply micro timing on track {self.track_id}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            raise ValueError(f"Track not found: {self.track_id}")
        HumanizeEngine().apply_micro_timing(track.notes, self.beat_offsets)
        song.updated_at = datetime.now(timezone.utc)
        return song


class ApplyGrooveCommand(Command):
    def __init__(
        self, track_id: str, groove_name: str, section_id: str | None = None
    ):
        self.track_id = track_id
        self.groove_name = groove_name
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Apply groove '{self.groove_name}' on track {self.track_id}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            raise ValueError(f"Track not found: {self.track_id}")
        notes = _select_notes(track.notes, self.section_id, song)
        HumanizeEngine().apply_groove(notes, self.groove_name)
        song.updated_at = datetime.now(timezone.utc)
        return song


class ApplySwingCommand(Command):
    def __init__(
        self,
        track_id: str | None = None,
        swing_amount: float = 0.5,
        section_id: str | None = None,
    ):
        self.track_id = track_id
        self.swing_amount = swing_amount
        self.section_id = section_id

    @property
    def description(self) -> str:
        target = self.track_id or "all tracks"
        return f"Apply swing ({self.swing_amount}) on {target}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        engine = HumanizeEngine()
        if self.track_id is None:
            for track in song.tracks:
                notes = _select_notes(track.notes, self.section_id, song)
                engine.apply_swing(notes, self.swing_amount)
        else:
            track = _get_track(song, self.track_id)
            if track is None:
                raise ValueError(f"Track not found: {self.track_id}")
            notes = _select_notes(track.notes, self.section_id, song)
            engine.apply_swing(notes, self.swing_amount)
        song.updated_at = datetime.now(timezone.utc)
        return song


class PushTimingCommand(Command):
    def __init__(
        self, track_id: str, amount: float = 0.5, section_id: str | None = None
    ):
        self.track_id = track_id
        self.amount = amount
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Push timing on track {self.track_id}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            raise ValueError(f"Track not found: {self.track_id}")
        notes = _select_notes(track.notes, self.section_id, song)
        HumanizeEngine().push_timing(notes, self.amount)
        song.updated_at = datetime.now(timezone.utc)
        return song


class PullTimingCommand(Command):
    def __init__(
        self, track_id: str, amount: float = 0.5, section_id: str | None = None
    ):
        self.track_id = track_id
        self.amount = amount
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Pull timing on track {self.track_id}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            raise ValueError(f"Track not found: {self.track_id}")
        notes = _select_notes(track.notes, self.section_id, song)
        HumanizeEngine().pull_timing(notes, self.amount)
        song.updated_at = datetime.now(timezone.utc)
        return song


class HandPlayedFeelCommand(Command):
    def __init__(
        self, track_id: str, intensity: float = 0.5, section_id: str | None = None
    ):
        self.track_id = track_id
        self.intensity = intensity
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Apply hand-played feel on track {self.track_id}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            raise ValueError(f"Track not found: {self.track_id}")
        notes = _select_notes(track.notes, self.section_id, song)
        HumanizeEngine().hand_played_feel(notes, self.intensity)
        song.updated_at = datetime.now(timezone.utc)
        return song
