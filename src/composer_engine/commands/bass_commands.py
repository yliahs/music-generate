"""Bass-level commands.

Aligned with TECHNICAL.md 5.11 - Phase 4 Command 清单.
"""

from composer_engine.commands.base import Command
from composer_engine.generators.bass_generator import BassGenerator
from composer_engine.models.enums import BassMode, InstrumentType
from composer_engine.models.note import Note
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


def _ensure_bass_track(song: Song, track_id: str | None):
    """Return (track, was_created). If track_id is None, create one."""
    if track_id:
        track = _get_track(song, track_id)
        return track, False
    # Auto-create bass track
    track = Track.create("Bass", InstrumentType.BASS)
    song.tracks.append(track)
    return track, True


class GenerateBassCommand(Command):
    """Generate a bass line for a track/section."""

    def __init__(self, track_id: str | None = None, section_id: str | None = None,
                 bass_mode: str = "generate", note_density: str = "normal", octave: int = 2):
        self.track_id = track_id
        self.section_id = section_id
        self.bass_mode = BassMode(bass_mode)
        self.note_density = note_density
        self.octave = octave

    @property
    def description(self) -> str:
        return f"Generate bass ({self.bass_mode.value})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track, _ = _ensure_bass_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = BassGenerator()
        
        # For counter_bass, find melody notes
        melody_notes = None
        if self.bass_mode == BassMode.COUNTER_BASS:
            for t in song.tracks:
                if t.instrument not in (InstrumentType.BASS, InstrumentType.DRUMS) and t.notes:
                    melody_notes = t.notes
                    break
        
        notes = gen.generate(
            song.chord_progression, song.global_settings.key, song.global_settings.mode,
            start, end, self.bass_mode, self.note_density, self.octave, melody_notes,
        )
        # Clear existing notes in range
        track.notes = [n for n in track.notes
                       if not (start <= n.start_beat < end)] + notes
        song.updated_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
        return song


class RegenerateBassCommand(Command):
    """Regenerate bass for the same track (clear and re-generate)."""

    def __init__(self, track_id: str, section_id: str | None = None,
                 bass_mode: str = "generate", note_density: str = "normal", octave: int = 2):
        self.track_id = track_id
        self.section_id = section_id
        self.bass_mode = BassMode(bass_mode)
        self.note_density = note_density
        self.octave = octave

    @property
    def description(self) -> str:
        return f"Regenerate bass ({self.bass_mode.value})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        # Clear all notes in range
        track.notes = [n for n in track.notes if not (start <= n.start_beat < end)]
        gen = BassGenerator()
        notes = gen.generate(
            song.chord_progression, song.global_settings.key, song.global_settings.mode,
            start, end, self.bass_mode, self.note_density, self.octave,
        )
        track.notes.extend(notes)
        song.updated_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
        return song


class SetBassPatternCommand(Command):
    """Directly set bass notes for a track."""

    def __init__(self, track_id: str, notes: list[dict]):
        self.track_id = track_id
        self.notes_data = notes

    @property
    def description(self) -> str:
        return f"Set bass pattern ({len(self.notes_data)} notes)"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        new_notes = [Note(**n) for n in self.notes_data]
        track.notes = new_notes
        song.updated_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
        return song


class SimplifyBassCommand(Command):
    """Simplify bass line (keep root notes on strong beats)."""

    def __init__(self, track_id: str):
        self.track_id = track_id

    @property
    def description(self) -> str:
        return "Simplify bass"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        gen = BassGenerator()
        track.notes = gen.simplify(track.notes)
        song.updated_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
        return song


class TransposeBassCommand(Command):
    """Transpose bass by semitones."""

    def __init__(self, track_id: str, semitones: int):
        self.track_id = track_id
        self.semitones = semitones

    @property
    def description(self) -> str:
        return f"Transpose bass by {self.semitones} semitones"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        gen = BassGenerator()
        track.notes = gen.transpose(track.notes, self.semitones)
        song.updated_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
        return song
