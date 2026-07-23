"""Extended instrument commands.

Aligned with TECHNICAL.md 5.12 - Phase 5 Command 清单.
"""

from datetime import datetime, timezone

from composer_engine.commands.base import Command
from composer_engine.generators.instrument_generator import InstrumentGenerator
from composer_engine.models.enums import (
    BrassMode,
    GuitarMode,
    InstrumentType,
    PianoMode,
    StringsMode,
    SynthMode,
    WoodwindsMode,
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


def _ensure_track(song: Song, track_id: str | None, instrument: InstrumentType):
    if track_id:
        return _get_track(song, track_id)
    track = Track.create(instrument.value.capitalize(), instrument)
    song.tracks.append(track)
    return track


class GenerateStringsCommand(Command):
    def __init__(self, track_id: str | None = None, section_id: str | None = None,
                 strings_mode: str = "sustained"):
        self.track_id = track_id
        self.section_id = section_id
        self.strings_mode = StringsMode(strings_mode)

    @property
    def description(self) -> str:
        return f"Generate strings ({self.strings_mode.value})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _ensure_track(song, self.track_id, InstrumentType.STRINGS)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = InstrumentGenerator()
        notes = gen.generate_strings(
            song.chord_progression, song.global_settings.key, song.global_settings.mode,
            start, end, self.strings_mode,
        )
        track.notes = [n for n in track.notes if not (start <= n.start_beat < end)] + notes
        song.updated_at = datetime.now(timezone.utc)
        return song


class GenerateBrassCommand(Command):
    def __init__(self, track_id: str | None = None, section_id: str | None = None,
                 brass_mode: str = "stabs"):
        self.track_id = track_id
        self.section_id = section_id
        self.brass_mode = BrassMode(brass_mode)

    @property
    def description(self) -> str:
        return f"Generate brass ({self.brass_mode.value})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _ensure_track(song, self.track_id, InstrumentType.BRASS)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = InstrumentGenerator()
        notes = gen.generate_brass(
            song.chord_progression, song.global_settings.key, song.global_settings.mode,
            start, end, self.brass_mode,
        )
        track.notes = [n for n in track.notes if not (start <= n.start_beat < end)] + notes
        song.updated_at = datetime.now(timezone.utc)
        return song


class GenerateWoodwindsCommand(Command):
    def __init__(self, track_id: str | None = None, section_id: str | None = None,
                 woodwinds_mode: str = "sustained"):
        self.track_id = track_id
        self.section_id = section_id
        self.woodwinds_mode = WoodwindsMode(woodwinds_mode)

    @property
    def description(self) -> str:
        return f"Generate woodwinds ({self.woodwinds_mode.value})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _ensure_track(song, self.track_id, InstrumentType.WOODWINDS)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = InstrumentGenerator()
        notes = gen.generate_woodwinds(
            song.chord_progression, song.global_settings.key, song.global_settings.mode,
            start, end, self.woodwinds_mode,
        )
        track.notes = [n for n in track.notes if not (start <= n.start_beat < end)] + notes
        song.updated_at = datetime.now(timezone.utc)
        return song


class GenerateSynthCommand(Command):
    def __init__(self, track_id: str | None = None, section_id: str | None = None,
                 synth_mode: str = "pad"):
        self.track_id = track_id
        self.section_id = section_id
        self.synth_mode = SynthMode(synth_mode)

    @property
    def description(self) -> str:
        return f"Generate synth ({self.synth_mode.value})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _ensure_track(song, self.track_id, InstrumentType.SYNTH)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = InstrumentGenerator()
        notes = gen.generate_synth(
            song.chord_progression, song.global_settings.key, song.global_settings.mode,
            start, end, self.synth_mode,
        )
        track.notes = [n for n in track.notes if not (start <= n.start_beat < end)] + notes
        song.updated_at = datetime.now(timezone.utc)
        return song


class GeneratePianoPartCommand(Command):
    def __init__(self, track_id: str | None = None, section_id: str | None = None,
                 piano_mode: str = "block_chords"):
        self.track_id = track_id
        self.section_id = section_id
        self.piano_mode = PianoMode(piano_mode)

    @property
    def description(self) -> str:
        return f"Generate piano part ({self.piano_mode.value})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _ensure_track(song, self.track_id, InstrumentType.PIANO)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = InstrumentGenerator()
        notes = gen.generate_piano_part(
            song.chord_progression, song.global_settings.key, song.global_settings.mode,
            start, end, self.piano_mode,
        )
        track.notes = [n for n in track.notes if not (start <= n.start_beat < end)] + notes
        song.updated_at = datetime.now(timezone.utc)
        return song


class GenerateGuitarPartCommand(Command):
    def __init__(self, track_id: str | None = None, section_id: str | None = None,
                 guitar_mode: str = "strum"):
        self.track_id = track_id
        self.section_id = section_id
        self.guitar_mode = GuitarMode(guitar_mode)

    @property
    def description(self) -> str:
        return f"Generate guitar part ({self.guitar_mode.value})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _ensure_track(song, self.track_id, InstrumentType.GUITAR)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = InstrumentGenerator()
        notes = gen.generate_guitar_part(
            song.chord_progression, song.global_settings.key, song.global_settings.mode,
            start, end, self.guitar_mode,
        )
        track.notes = [n for n in track.notes if not (start <= n.start_beat < end)] + notes
        song.updated_at = datetime.now(timezone.utc)
        return song
