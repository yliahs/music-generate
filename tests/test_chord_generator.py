"""Tests for chord generator and chord commands."""

from composer_engine.commands.chord_commands import (
    GenerateChordsCommand,
    InsertChordCommand,
    RemoveChordCommand,
    ReplaceChordCommand,
    SecondaryDominantCommand,
    SetCadenceCommand,
    SetChordsCommand,
)
from composer_engine.generators.chord_generator import ChordGenerator
from composer_engine.models.chord import CadenceType, Chord, ChordQuality
from composer_engine.models.enums import Key, Mode
from composer_engine.models.song import Song


def _make_song() -> Song:
    from composer_engine.models.section import Section
    from composer_engine.models.enums import SectionType
    return Song(
        name="Test Song",
        sections=[
            Section(type=SectionType.VERSE, start_beat=0, length_beats=16),
            Section(type=SectionType.CHORUS, start_beat=16, length_beats=16),
        ],
    )


class TestChordGenerator:
    def test_generate_pop(self):
        gen = ChordGenerator()
        chords = gen.generate(Key.C, Mode.MAJOR, "pop", 16.0)
        assert len(chords) > 0
        assert all(isinstance(c, Chord) for c in chords)
        total_duration = sum(c.duration_beat for c in chords)
        assert total_duration == 16.0

    def test_generate_specific_template(self):
        gen = ChordGenerator()
        chords = gen.generate(Key.C, Mode.MAJOR, "anime", 16.0, template_name="royal_road")
        assert len(chords) == 4
        assert chords[0].root == Key.F   # IV in C
        assert chords[1].root == Key.G   # V in C

    def test_generate_jazz(self):
        gen = ChordGenerator()
        chords = gen.generate(Key.C, Mode.MAJOR, "jazz", 12.0, template_name="jazz_251")
        assert len(chords) > 0
        assert any(c.quality == ChordQuality.MIN7 for c in chords)

    def test_generate_fills_length(self):
        gen = ChordGenerator()
        chords = gen.generate(Key.C, Mode.MAJOR, "pop", 32.0, beats_per_chord=4.0)
        total = sum(c.duration_beat for c in chords)
        assert total == 32.0

    def test_secondary_dominant(self):
        gen = ChordGenerator()
        target = Chord(root=Key.A, quality=ChordQuality.MINOR, start_beat=4.0, duration_beat=4.0)
        sec_dom = gen.secondary_dominant(target)
        assert sec_dom.root == Key.E  # V/vi = E
        assert sec_dom.quality == ChordQuality.DOM7

    def test_set_cadence_authentic(self):
        gen = ChordGenerator()
        chords = gen.generate(Key.C, Mode.MAJOR, "pop", 16.0)
        result = gen.set_cadence(chords, 16.0, CadenceType.AUTHENTIC, Key.C, Mode.MAJOR)
        assert result[-1].root == Key.C  # ends on I
        assert result[-2].root == Key.G  # V before I


class TestChordCommands:
    def test_generate_chords_command(self):
        song = _make_song()
        cmd = GenerateChordsCommand(style="pop")
        result = cmd.execute(song)
        assert len(result.chord_progression) > 0

    def test_set_chords_command(self):
        song = _make_song()
        chords = [
            Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
            Chord(root=Key.G, quality=ChordQuality.MAJOR, start_beat=4, duration_beat=4),
        ]
        cmd = SetChordsCommand(chords)
        result = cmd.execute(song)
        assert len(result.chord_progression) == 2

    def test_replace_chord_command(self):
        song = _make_song()
        song.chord_progression = [
            Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
        ]
        cmd = ReplaceChordCommand(0, Key.D, ChordQuality.MINOR)
        result = cmd.execute(song)
        assert result.chord_progression[0].root == Key.D
        assert result.chord_progression[0].quality == ChordQuality.MINOR

    def test_insert_chord_command(self):
        song = _make_song()
        song.chord_progression = [
            Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
        ]
        cmd = InsertChordCommand(4.0, Key.F, ChordQuality.MAJOR, 4.0)
        result = cmd.execute(song)
        assert len(result.chord_progression) == 2
        assert result.chord_progression[1].root == Key.F

    def test_remove_chord_command(self):
        song = _make_song()
        song.chord_progression = [
            Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
            Chord(root=Key.G, quality=ChordQuality.MAJOR, start_beat=4, duration_beat=4),
        ]
        cmd = RemoveChordCommand(0)
        result = cmd.execute(song)
        assert len(result.chord_progression) == 1
        assert result.chord_progression[0].root == Key.G

    def test_secondary_dominant_command(self):
        song = _make_song()
        song.chord_progression = [
            Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
            Chord(root=Key.A, quality=ChordQuality.MINOR, start_beat=4, duration_beat=4),
        ]
        cmd = SecondaryDominantCommand(1)
        result = cmd.execute(song)
        assert len(result.chord_progression) == 3

    def test_set_cadence_command(self):
        song = _make_song()
        song.chord_progression = [
            Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
            Chord(root=Key.F, quality=ChordQuality.MAJOR, start_beat=4, duration_beat=4),
            Chord(root=Key.G, quality=ChordQuality.MAJOR, start_beat=8, duration_beat=4),
            Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=12, duration_beat=4),
        ]
        section_id = song.sections[0].id
        cmd = SetCadenceCommand(section_id, CadenceType.AUTHENTIC)
        result = cmd.execute(song)
        assert len(result.chord_progression) > 0
