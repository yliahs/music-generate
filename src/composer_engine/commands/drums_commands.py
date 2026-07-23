"""Drums-level commands.

Aligned with TECHNICAL.md 5.11 - Phase 4 Command 清单.
"""

from datetime import datetime, timezone

from composer_engine.commands.base import Command
from composer_engine.generators.drums_generator import DrumsGenerator
from composer_engine.models.enums import (
    DrumStyle,
    HiHatPattern,
    InstrumentType,
    KickPattern,
    SnarePattern,
)
from composer_engine.models.song import Song
from composer_engine.models.track import Track


def _get_track(song: Song, track_id: str):
    for t in song.tracks:
        if t.id == track_id:
            return t
    return None


def _get_section_range(song: Song, section_id: str | None):
    if section_id:
        for s in song.sections:
            if s.id == section_id:
                return s.start_beat, s.start_beat + s.length_beats
    if song.sections:
        start = min(s.start_beat for s in song.sections)
        end = max(s.start_beat + s.length_beats for s in song.sections)
        return start, end
    return 0.0, 16.0


def _ensure_drums_track(song: Song, track_id: str | None):
    """Return (track, was_created). If track_id is None, create one."""
    if track_id:
        track = _get_track(song, track_id)
        return track, False
    track = Track.create("Drums", InstrumentType.DRUMS)
    song.tracks.append(track)
    return track, True


class GenerateDrumsCommand(Command):
    """Generate a full drum pattern for a section."""

    def __init__(self, track_id: str | None = None, section_id: str | None = None,
                 style: str = "rock"):
        self.track_id = track_id
        self.section_id = section_id
        self.style = DrumStyle(style)

    @property
    def description(self) -> str:
        return f"Generate drums ({self.style.value})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track, _ = _ensure_drums_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        ts = (song.global_settings.time_signature[0], song.global_settings.time_signature[1])
        gen = DrumsGenerator()
        notes = gen.generate(self.style, start, end, ts)
        track.notes = [n for n in track.notes if not (start <= n.start_beat < end)] + notes
        song.updated_at = datetime.now(timezone.utc)
        return song


class RegenerateDrumsCommand(Command):
    """Regenerate drums for a track."""

    def __init__(self, track_id: str, section_id: str | None = None, style: str = "rock"):
        self.track_id = track_id
        self.section_id = section_id
        self.style = DrumStyle(style)

    @property
    def description(self) -> str:
        return f"Regenerate drums ({self.style.value})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        track.notes = [n for n in track.notes if not (start <= n.start_beat < end)]
        ts = (song.global_settings.time_signature[0], song.global_settings.time_signature[1])
        gen = DrumsGenerator()
        track.notes.extend(gen.generate(self.style, start, end, ts))
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetDrumStyleCommand(Command):
    """Switch drum style preset for a section."""

    def __init__(self, track_id: str, style: str, section_id: str | None = None):
        self.track_id = track_id
        self.style = DrumStyle(style)
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Set drum style to {self.style.value}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        ts = (song.global_settings.time_signature[0], song.global_settings.time_signature[1])
        gen = DrumsGenerator()
        track.notes = gen.set_style(track.notes, self.style, start, end, ts)
        song.updated_at = datetime.now(timezone.utc)
        return song


class AddDrumFillCommand(Command):
    """Insert a drum fill at the specified beat."""

    def __init__(self, track_id: str, beat_position: float, fill_type: str = "basic"):
        self.track_id = track_id
        self.beat_position = beat_position
        self.fill_type = fill_type

    @property
    def description(self) -> str:
        return f"Add drum fill at beat {self.beat_position}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        gen = DrumsGenerator()
        track.notes = gen.add_fill(track.notes, self.beat_position, self.fill_type)
        song.updated_at = datetime.now(timezone.utc)
        return song


class AddGhostNotesCommand(Command):
    """Add ghost notes to snare in a section."""

    def __init__(self, track_id: str, section_id: str | None = None, density: float = 0.3):
        self.track_id = track_id
        self.section_id = section_id
        self.density = density

    @property
    def description(self) -> str:
        return "Add ghost notes"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = DrumsGenerator()
        track.notes = gen.add_ghost_notes(track.notes, start, end, self.density)
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetHiHatPatternCommand(Command):
    """Set hi-hat pattern for a section."""

    def __init__(self, track_id: str, pattern: str, section_id: str | None = None):
        self.track_id = track_id
        self.pattern = HiHatPattern(pattern)
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Set hi-hat to {self.pattern.value}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = DrumsGenerator()
        track.notes = gen.set_hihat_pattern(track.notes, self.pattern, start, end)
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetKickPatternCommand(Command):
    """Set kick drum pattern for a section."""

    def __init__(self, track_id: str, pattern: str, section_id: str | None = None):
        self.track_id = track_id
        self.pattern = KickPattern(pattern)
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Set kick to {self.pattern.value}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = DrumsGenerator()
        track.notes = gen.set_kick_pattern(track.notes, self.pattern, start, end)
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetSnarePatternCommand(Command):
    """Set snare pattern for a section."""

    def __init__(self, track_id: str, pattern: str, section_id: str | None = None):
        self.track_id = track_id
        self.pattern = SnarePattern(pattern)
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Set snare to {self.pattern.value}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = DrumsGenerator()
        track.notes = gen.set_snare_pattern(track.notes, self.pattern, start, end)
        song.updated_at = datetime.now(timezone.utc)
        return song


class AddCrashCommand(Command):
    """Add a crash cymbal at the specified beat."""

    def __init__(self, track_id: str, beat_position: float):
        self.track_id = track_id
        self.beat_position = beat_position

    @property
    def description(self) -> str:
        return f"Add crash at beat {self.beat_position}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        gen = DrumsGenerator()
        track.notes = gen.add_crash(track.notes, self.beat_position)
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetRidePatternCommand(Command):
    """Set ride cymbal pattern."""

    def __init__(self, track_id: str, section_id: str | None = None, swing: bool = False):
        self.track_id = track_id
        self.section_id = section_id
        self.swing = swing

    @property
    def description(self) -> str:
        return f"Set ride pattern (swing={self.swing})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = DrumsGenerator()
        track.notes = gen.set_ride_pattern(track.notes, start, end, self.swing)
        song.updated_at = datetime.now(timezone.utc)
        return song


class AddTomFillCommand(Command):
    """Add a tom cascade fill."""

    def __init__(self, track_id: str, beat_position: float, fill_beats: float = 1.0):
        self.track_id = track_id
        self.beat_position = beat_position
        self.fill_beats = fill_beats

    @property
    def description(self) -> str:
        return f"Add tom fill at beat {self.beat_position}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        gen = DrumsGenerator()
        track.notes = gen.add_tom_fill(track.notes, self.beat_position, self.fill_beats)
        song.updated_at = datetime.now(timezone.utc)
        return song


class AddPercussionCommand(Command):
    """Add a percussion element (tambourine, cowbell, claves)."""

    def __init__(self, track_id: str, element: str, section_id: str | None = None,
                 pattern: str = "quarter"):
        self.track_id = track_id
        self.element = element
        self.section_id = section_id
        self.pattern = pattern

    @property
    def description(self) -> str:
        return f"Add {self.element} percussion"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = DrumsGenerator()
        track.notes = gen.add_percussion(track.notes, self.element, start, end, self.pattern)
        song.updated_at = datetime.now(timezone.utc)
        return song


class ClearDrumElementCommand(Command):
    """Clear a specific drum element from a section."""

    def __init__(self, track_id: str, element: str, section_id: str | None = None):
        self.track_id = track_id
        self.element = element
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Clear {self.element} drums"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = DrumsGenerator()
        track.notes = gen.clear_element(track.notes, self.element, start, end)
        song.updated_at = datetime.now(timezone.utc)
        return song
