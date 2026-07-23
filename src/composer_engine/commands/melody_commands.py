"""Melody-level commands.

Aligned with TECHNICAL.md 5.10 - Phase 3 Command 清单.
"""

from datetime import datetime, timezone

from composer_engine.commands.base import Command
from composer_engine.generators.melody_generator import MelodyGenerator
from composer_engine.models.enums import Key, Mode
from composer_engine.models.song import Song


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


class GenerateMelodyCommand(Command):
    def __init__(self, track_id: str, section_id: str | None = None,
                 note_density: str = "normal", pitch_range_low: int = 60,
                 pitch_range_high: int = 84, contour: str = "arch",
                 chord_tone_weight: float = 0.7, rhythm_complexity: str = "moderate"):
        self.track_id = track_id
        self.section_id = section_id
        self.note_density = note_density
        self.pitch_range = (pitch_range_low, pitch_range_high)
        self.contour = contour
        self.chord_tone_weight = chord_tone_weight
        self.rhythm_complexity = rhythm_complexity

    @property
    def description(self) -> str:
        return f"Generate melody for track '{self.track_id}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = MelodyGenerator()
        notes = gen.generate(
            song.chord_progression, song.global_settings.key, song.global_settings.mode,
            start, end, self.note_density, self.pitch_range, self.contour,
            self.chord_tone_weight, self.rhythm_complexity,
        )
        track.notes = notes
        song.updated_at = datetime.now(timezone.utc)
        return song


class RegenerateMelodyCommand(Command):
    def __init__(self, track_id: str, section_id: str | None = None):
        self.track_id = track_id
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Regenerate melody for track '{self.track_id}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track is None:
            return song
        start, end = _get_section_range(song, self.section_id)
        gen = MelodyGenerator()
        track.notes = gen.generate(
            song.chord_progression, song.global_settings.key, song.global_settings.mode,
            start, end,
        )
        song.updated_at = datetime.now(timezone.utc)
        return song


class SimplifyMelodyCommand(Command):
    def __init__(self, track_id: str, strength: float = 0.5):
        self.track_id = track_id
        self.strength = strength

    @property
    def description(self) -> str:
        return f"Simplify melody (strength={self.strength})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.simplify(track.notes, self.strength)
        song.updated_at = datetime.now(timezone.utc)
        return song


class ComplexifyMelodyCommand(Command):
    def __init__(self, track_id: str, strength: float = 0.5):
        self.track_id = track_id
        self.strength = strength

    @property
    def description(self) -> str:
        return f"Complexify melody (strength={self.strength})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.complexify(
                track.notes, song.global_settings.key, song.global_settings.mode,
                song.chord_progression, self.strength,
            )
        song.updated_at = datetime.now(timezone.utc)
        return song


class TransposeMelodyCommand(Command):
    def __init__(self, track_id: str, semitones: int):
        self.track_id = track_id
        self.semitones = semitones

    @property
    def description(self) -> str:
        return f"Transpose melody by {self.semitones} semitones"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.transpose(track.notes, self.semitones)
        song.updated_at = datetime.now(timezone.utc)
        return song


class InvertMelodyCommand(Command):
    def __init__(self, track_id: str, pivot_pitch: int = 60):
        self.track_id = track_id
        self.pivot_pitch = pivot_pitch

    @property
    def description(self) -> str:
        return f"Invert melody around pitch {self.pivot_pitch}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.invert(track.notes, self.pivot_pitch)
        song.updated_at = datetime.now(timezone.utc)
        return song


class ReverseMelodyCommand(Command):
    def __init__(self, track_id: str):
        self.track_id = track_id

    @property
    def description(self) -> str:
        return "Reverse melody"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.reverse(track.notes)
        song.updated_at = datetime.now(timezone.utc)
        return song


class SequenceMelodyCommand(Command):
    def __init__(self, track_id: str, interval: int = 2, count: int = 2):
        self.track_id = track_id
        self.interval = interval
        self.count = count

    @property
    def description(self) -> str:
        return f"Sequence melody (interval={self.interval}, count={self.count})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.sequence(track.notes, self.interval, self.count)
        song.updated_at = datetime.now(timezone.utc)
        return song


class VariationMelodyCommand(Command):
    def __init__(self, track_id: str):
        self.track_id = track_id

    @property
    def description(self) -> str:
        return "Create melody variation"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.variation(
                track.notes, song.chord_progression,
                song.global_settings.key, song.global_settings.mode,
            )
        song.updated_at = datetime.now(timezone.utc)
        return song


class DevelopMotifCommand(Command):
    def __init__(self, track_id: str, motif_beats: float = 4.0):
        self.track_id = track_id
        self.motif_beats = motif_beats

    @property
    def description(self) -> str:
        return f"Develop motif ({self.motif_beats} beats)"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.develop_motif(
                track.notes, self.motif_beats,
                song.global_settings.key, song.global_settings.mode,
            )
        song.updated_at = datetime.now(timezone.utc)
        return song


class ExtendMelodyCommand(Command):
    def __init__(self, track_id: str, extra_beats: float = 8.0):
        self.track_id = track_id
        self.extra_beats = extra_beats

    @property
    def description(self) -> str:
        return f"Extend melody by {self.extra_beats} beats"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.extend(
                track.notes, self.extra_beats, song.chord_progression,
                song.global_settings.key, song.global_settings.mode,
            )
        song.updated_at = datetime.now(timezone.utc)
        return song


class ShortenMelodyCommand(Command):
    def __init__(self, track_id: str, cut_beats: float = 4.0):
        self.track_id = track_id
        self.cut_beats = cut_beats

    @property
    def description(self) -> str:
        return f"Shorten melody by {self.cut_beats} beats"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.shorten(track.notes, self.cut_beats)
        song.updated_at = datetime.now(timezone.utc)
        return song


class CallResponseCommand(Command):
    def __init__(self, track_id: str, response_style: str = "echo"):
        self.track_id = track_id
        self.response_style = response_style

    @property
    def description(self) -> str:
        return f"Call & response ({self.response_style})"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.call_response(track.notes, self.response_style)
        song.updated_at = datetime.now(timezone.utc)
        return song


class GenerateHookCommand(Command):
    def __init__(self, track_id: str, hook_beats: float = 4.0):
        self.track_id = track_id
        self.hook_beats = hook_beats

    @property
    def description(self) -> str:
        return f"Generate hook ({self.hook_beats} beats)"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.generate_hook(
                song.chord_progression, song.global_settings.key,
                song.global_settings.mode, self.hook_beats,
            )
        song.updated_at = datetime.now(timezone.utc)
        return song


class QuestionAnswerCommand(Command):
    def __init__(self, track_id: str, phrase_beats: float = 4.0):
        self.track_id = track_id
        self.phrase_beats = phrase_beats

    @property
    def description(self) -> str:
        return f"Question & answer ({self.phrase_beats} beats)"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            gen = MelodyGenerator()
            track.notes = gen.question_answer(
                song.chord_progression, song.global_settings.key,
                song.global_settings.mode, self.phrase_beats,
            )
        song.updated_at = datetime.now(timezone.utc)
        return song
