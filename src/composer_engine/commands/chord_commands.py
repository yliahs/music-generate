"""Chord-level commands.

Aligned with TECHNICAL.md 5.9 - Phase 2 Command 清单.
"""

from datetime import datetime, timezone

from composer_engine.commands.base import Command
from composer_engine.generators.chord_generator import ChordGenerator
from composer_engine.models.chord import CadenceType, Chord, ChordQuality
from composer_engine.models.enums import Key, Mode
from composer_engine.models.song import Song
from composer_engine.theory.chord_utils import roman_analysis


class GenerateChordsCommand(Command):
    """Generate a chord progression for a section or the whole song."""

    def __init__(self, style: str = "pop", template_name: str | None = None,
                 beats_per_chord: float = 4.0, section_id: str | None = None):
        self.style = style
        self.template_name = template_name
        self.beats_per_chord = beats_per_chord
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Generate {self.style} chords"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        gen = ChordGenerator()
        if self.section_id:
            section = next((s for s in song.sections if s.id == self.section_id), None)
            if section:
                length = section.length_beats
                new_chords = gen.generate(
                    song.global_settings.key, song.global_settings.mode,
                    self.style, length, self.beats_per_chord, self.template_name,
                )
                for c in new_chords:
                    c.start_beat += section.start_beat
                song.chord_progression = [
                    c for c in song.chord_progression
                    if not (section.start_beat <= c.start_beat < section.start_beat + section.length_beats)
                ] + new_chords
        else:
            total = max((s.start_beat + s.length_beats for s in song.sections), default=16.0)
            song.chord_progression = gen.generate(
                song.global_settings.key, song.global_settings.mode,
                self.style, total, self.beats_per_chord, self.template_name,
            )
        song.chord_progression.sort(key=lambda c: c.start_beat)
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetChordsCommand(Command):
    """Directly set the chord progression."""

    def __init__(self, chords: list[Chord]):
        self.chords = chords

    @property
    def description(self) -> str:
        return f"Set {len(self.chords)} chords"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.chord_progression = sorted(self.chords, key=lambda c: c.start_beat)
        song.updated_at = datetime.now(timezone.utc)
        return song


class ReplaceChordCommand(Command):
    """Replace a chord at a specific index."""

    def __init__(self, chord_index: int, new_root: Key, new_quality: ChordQuality):
        self.chord_index = chord_index
        self.new_root = new_root
        self.new_quality = new_quality

    @property
    def description(self) -> str:
        return f"Replace chord #{self.chord_index}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        if 0 <= self.chord_index < len(song.chord_progression):
            c = song.chord_progression[self.chord_index]
            c.root = self.new_root
            c.quality = self.new_quality
            c.roman = roman_analysis(self.new_root, self.new_quality.value,
                                     song.global_settings.key, song.global_settings.mode)
        song.updated_at = datetime.now(timezone.utc)
        return song


class InsertChordCommand(Command):
    """Insert a chord at a specific beat position."""

    def __init__(self, position_beat: float, root: Key, quality: ChordQuality,
                 duration_beat: float = 4.0):
        self.position_beat = position_beat
        self.root = root
        self.quality = quality
        self.duration_beat = duration_beat

    @property
    def description(self) -> str:
        return f"Insert {self.root.value}{self.quality.value} at beat {self.position_beat}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        chord = Chord(
            root=self.root, quality=self.quality,
            start_beat=self.position_beat, duration_beat=self.duration_beat,
            roman=roman_analysis(self.root, self.quality.value,
                                 song.global_settings.key, song.global_settings.mode),
        )
        song.chord_progression.append(chord)
        song.chord_progression.sort(key=lambda c: c.start_beat)
        song.updated_at = datetime.now(timezone.utc)
        return song


class RemoveChordCommand(Command):
    """Remove a chord by index."""

    def __init__(self, chord_index: int):
        self.chord_index = chord_index

    @property
    def description(self) -> str:
        return f"Remove chord #{self.chord_index}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        if 0 <= self.chord_index < len(song.chord_progression):
            song.chord_progression.pop(self.chord_index)
        song.updated_at = datetime.now(timezone.utc)
        return song


class ReharmonizeCommand(Command):
    """Reharmonize using a different style."""

    def __init__(self, target_style: str, section_id: str | None = None):
        self.target_style = target_style
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Reharmonize to {self.target_style}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        gen = ChordGenerator()
        if song.chord_progression:
            length = max(c.start_beat + c.duration_beat for c in song.chord_progression)
            song.chord_progression = gen.generate(
                song.global_settings.key, song.global_settings.mode,
                self.target_style, length,
            )
        song.updated_at = datetime.now(timezone.utc)
        return song


class BorrowChordCommand(Command):
    """Borrow a chord from a parallel mode."""

    def __init__(self, chord_index: int, source_mode: Mode):
        self.chord_index = chord_index
        self.source_mode = source_mode

    @property
    def description(self) -> str:
        return f"Borrow chord #{self.chord_index} from {self.source_mode.value}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        gen = ChordGenerator()
        if 0 <= self.chord_index < len(song.chord_progression):
            original = song.chord_progression[self.chord_index]
            borrowed = gen.borrow_chord(original, song.global_settings.key, self.source_mode)
            borrowed.roman = roman_analysis(borrowed.root, borrowed.quality.value,
                                            song.global_settings.key, song.global_settings.mode)
            song.chord_progression[self.chord_index] = borrowed
        song.updated_at = datetime.now(timezone.utc)
        return song


class SecondaryDominantCommand(Command):
    """Insert a secondary dominant before a target chord."""

    def __init__(self, target_chord_index: int):
        self.target_chord_index = target_chord_index

    @property
    def description(self) -> str:
        return f"Add V/ before chord #{self.target_chord_index}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        gen = ChordGenerator()
        if 0 <= self.target_chord_index < len(song.chord_progression):
            target = song.chord_progression[self.target_chord_index]
            sec_dom = gen.secondary_dominant(target)
            half_dur = target.duration_beat / 2
            sec_dom.start_beat = target.start_beat
            sec_dom.duration_beat = half_dur
            target.start_beat += half_dur
            target.duration_beat -= half_dur
            song.chord_progression.insert(self.target_chord_index, sec_dom)
        song.updated_at = datetime.now(timezone.utc)
        return song


class PassingChordCommand(Command):
    """Insert a passing chord between two chords."""

    def __init__(self, chord_index_a: int, chord_index_b: int):
        self.chord_index_a = chord_index_a
        self.chord_index_b = chord_index_b

    @property
    def description(self) -> str:
        return f"Add passing chord between #{self.chord_index_a} and #{self.chord_index_b}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        gen = ChordGenerator()
        cp = song.chord_progression
        if 0 <= self.chord_index_a < len(cp) and 0 <= self.chord_index_b < len(cp):
            passing = gen.passing_chord(cp[self.chord_index_a], cp[self.chord_index_b])
            cp.insert(self.chord_index_b, passing)
        song.updated_at = datetime.now(timezone.utc)
        return song


class ModulateCommand(Command):
    """Modulate to a new key from a pivot beat."""

    def __init__(self, target_key: Key, target_mode: Mode | None = None, pivot_beat: float = 0.0):
        self.target_key = target_key
        self.target_mode = target_mode
        self.pivot_beat = pivot_beat

    @property
    def description(self) -> str:
        return f"Modulate to {self.target_key.value} at beat {self.pivot_beat}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        gen = ChordGenerator()
        after_pivot = [c for c in song.chord_progression if c.start_beat >= self.pivot_beat]
        if after_pivot:
            total_len = sum(c.duration_beat for c in after_pivot)
            new_mode = self.target_mode or song.global_settings.mode
            new_chords = gen.generate(self.target_key, new_mode, "pop", total_len)
            for i, c in enumerate(new_chords):
                c.start_beat += self.pivot_beat
            song.chord_progression = [c for c in song.chord_progression if c.start_beat < self.pivot_beat] + new_chords
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetCadenceCommand(Command):
    """Set a cadence at the end of a section."""

    def __init__(self, section_id: str, cadence_type: CadenceType):
        self.section_id = section_id
        self.cadence_type = cadence_type

    @property
    def description(self) -> str:
        return f"Set {self.cadence_type.value} cadence"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        section = next((s for s in song.sections if s.id == self.section_id), None)
        if section:
            gen = ChordGenerator()
            end_beat = section.start_beat + section.length_beats
            song.chord_progression = gen.set_cadence(
                song.chord_progression, end_beat, self.cadence_type,
                song.global_settings.key, song.global_settings.mode,
            )
        song.updated_at = datetime.now(timezone.utc)
        return song
