"""Tests for melody generator and melody commands."""

from composer_engine.commands.melody_commands import (
    CallResponseCommand,
    ComplexifyMelodyCommand,
    DevelopMotifCommand,
    ExtendMelodyCommand,
    GenerateHookCommand,
    GenerateMelodyCommand,
    InvertMelodyCommand,
    QuestionAnswerCommand,
    RegenerateMelodyCommand,
    ReverseMelodyCommand,
    SequenceMelodyCommand,
    ShortenMelodyCommand,
    SimplifyMelodyCommand,
    TransposeMelodyCommand,
    VariationMelodyCommand,
)
from composer_engine.generators.melody_generator import MelodyGenerator
from composer_engine.models.chord import Chord, ChordQuality
from composer_engine.models.enums import InstrumentType, Key, Mode, SectionType
from composer_engine.models.note import Note
from composer_engine.models.section import Section
from composer_engine.models.song import Song
from composer_engine.models.track import Track


def _make_song_with_chords() -> Song:
    song = Song(
        name="Melody Test",
        sections=[Section(type=SectionType.VERSE, start_beat=0, length_beats=16)],
        chord_progression=[
            Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
            Chord(root=Key.G, quality=ChordQuality.MAJOR, start_beat=4, duration_beat=4),
            Chord(root=Key.A, quality=ChordQuality.MINOR, start_beat=8, duration_beat=4),
            Chord(root=Key.F, quality=ChordQuality.MAJOR, start_beat=12, duration_beat=4),
        ],
    )
    track = Track.create("Lead", InstrumentType.LEAD)
    song.tracks.append(track)
    return song


def _sample_notes() -> list[Note]:
    return [
        Note(pitch=60, start_beat=0, duration_beat=1, velocity=100),
        Note(pitch=64, start_beat=1, duration_beat=1, velocity=100),
        Note(pitch=67, start_beat=2, duration_beat=1, velocity=100),
        Note(pitch=72, start_beat=3, duration_beat=1, velocity=100),
    ]


class TestMelodyGenerator:
    def test_generate_basic(self):
        gen = MelodyGenerator()
        chords = [
            Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
            Chord(root=Key.G, quality=ChordQuality.MAJOR, start_beat=4, duration_beat=4),
        ]
        notes = gen.generate(chords, Key.C, Mode.MAJOR, 0, 8)
        assert len(notes) > 0
        assert all(isinstance(n, Note) for n in notes)
        assert all(60 <= n.pitch <= 84 for n in notes)

    def test_generate_sparse(self):
        gen = MelodyGenerator()
        chords = [Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=8)]
        sparse = gen.generate(chords, Key.C, Mode.MAJOR, 0, 8, note_density="sparse")
        dense = gen.generate(chords, Key.C, Mode.MAJOR, 0, 8, note_density="dense")
        assert len(sparse) <= len(dense)

    def test_generate_pitch_range(self):
        gen = MelodyGenerator()
        chords = [Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=8)]
        notes = gen.generate(chords, Key.C, Mode.MAJOR, 0, 8, pitch_range=(48, 60))
        assert all(48 <= n.pitch <= 60 for n in notes)

    def test_simplify(self):
        gen = MelodyGenerator()
        notes = _sample_notes() + [Note(pitch=65, start_beat=3.5, duration_beat=0.25, velocity=80)]
        simplified = gen.simplify(notes, strength=0.5)
        assert len(simplified) <= len(notes)

    def test_complexify(self):
        gen = MelodyGenerator()
        notes = [
            Note(pitch=60, start_beat=0, duration_beat=2, velocity=100),
            Note(pitch=67, start_beat=2, duration_beat=2, velocity=100),
        ]
        chords = [Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4)]
        result = gen.complexify(notes, Key.C, Mode.MAJOR, chords, strength=1.0)
        assert len(result) >= len(notes)

    def test_transpose(self):
        gen = MelodyGenerator()
        notes = _sample_notes()
        transposed = gen.transpose(notes, 5)
        for orig, trans in zip(notes, transposed):
            assert trans.pitch == orig.pitch + 5

    def test_invert(self):
        gen = MelodyGenerator()
        notes = _sample_notes()
        inverted = gen.invert(notes, 60)
        assert inverted[0].pitch == 60  # pivot stays
        assert inverted[1].pitch == 56  # 60 - (64-60) = 56

    def test_reverse(self):
        gen = MelodyGenerator()
        notes = _sample_notes()
        reversed_notes = gen.reverse(notes)
        assert len(reversed_notes) == len(notes)
        assert reversed_notes[0].start_beat != notes[0].start_beat

    def test_sequence(self):
        gen = MelodyGenerator()
        notes = _sample_notes()
        sequenced = gen.sequence(notes, 2, 2)
        assert len(sequenced) == len(notes) * 3  # original + 2 copies

    def test_variation(self):
        gen = MelodyGenerator()
        notes = _sample_notes()
        chords = [Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4)]
        varied = gen.variation(notes, chords, Key.C, Mode.MAJOR)
        assert len(varied) == len(notes)

    def test_develop_motif(self):
        gen = MelodyGenerator()
        notes = _sample_notes()
        developed = gen.develop_motif(notes, 2.0, Key.C, Mode.MAJOR)
        assert len(developed) > len(notes)

    def test_extend(self):
        gen = MelodyGenerator()
        notes = _sample_notes()
        chords = [Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=16)]
        extended = gen.extend(notes, 4.0, chords, Key.C, Mode.MAJOR)
        assert len(extended) > len(notes)

    def test_shorten(self):
        gen = MelodyGenerator()
        notes = _sample_notes()
        shortened = gen.shorten(notes, 2.0)
        assert len(shortened) < len(notes)

    def test_call_response_echo(self):
        gen = MelodyGenerator()
        notes = _sample_notes()
        result = gen.call_response(notes, "echo")
        assert len(result) > len(notes)

    def test_call_response_mirror(self):
        gen = MelodyGenerator()
        notes = _sample_notes()
        result = gen.call_response(notes, "mirror")
        assert len(result) > len(notes)

    def test_generate_hook(self):
        gen = MelodyGenerator()
        chords = [Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4)]
        hook = gen.generate_hook(chords, Key.C, Mode.MAJOR, 4.0)
        assert len(hook) > 0

    def test_question_answer(self):
        gen = MelodyGenerator()
        chords = [Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=8)]
        qa = gen.question_answer(chords, Key.C, Mode.MAJOR, 4.0)
        assert len(qa) > 0


class TestMelodyCommands:
    def test_generate_melody_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        cmd = GenerateMelodyCommand(track_id)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) > 0

    def test_regenerate_melody_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        song.tracks[0].notes = _sample_notes()
        cmd = RegenerateMelodyCommand(track_id)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) > 0

    def test_simplify_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        song.tracks[0].notes = _sample_notes() + [
            Note(pitch=62, start_beat=3.5, duration_beat=0.1, velocity=80),
        ]
        cmd = SimplifyMelodyCommand(track_id, strength=0.8)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) <= 5

    def test_transpose_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        song.tracks[0].notes = _sample_notes()
        cmd = TransposeMelodyCommand(track_id, 7)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert track.notes[0].pitch == 67

    def test_invert_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        song.tracks[0].notes = _sample_notes()
        cmd = InvertMelodyCommand(track_id, 60)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert track.notes[1].pitch == 56

    def test_reverse_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        song.tracks[0].notes = _sample_notes()
        cmd = ReverseMelodyCommand(track_id)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) == 4

    def test_sequence_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        song.tracks[0].notes = _sample_notes()
        cmd = SequenceMelodyCommand(track_id, interval=2, count=1)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) == 8

    def test_variation_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        song.tracks[0].notes = _sample_notes()
        cmd = VariationMelodyCommand(track_id)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) == 4

    def test_extend_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        song.tracks[0].notes = _sample_notes()
        cmd = ExtendMelodyCommand(track_id, extra_beats=4.0)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) > 4

    def test_shorten_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        song.tracks[0].notes = _sample_notes()
        cmd = ShortenMelodyCommand(track_id, cut_beats=2.0)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) < 4

    def test_hook_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        cmd = GenerateHookCommand(track_id, hook_beats=4.0)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) > 0

    def test_question_answer_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        cmd = QuestionAnswerCommand(track_id, phrase_beats=4.0)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) > 0

    def test_call_response_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        song.tracks[0].notes = _sample_notes()
        cmd = CallResponseCommand(track_id, response_style="echo")
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) > 4

    def test_develop_motif_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        song.tracks[0].notes = _sample_notes()
        cmd = DevelopMotifCommand(track_id, motif_beats=2.0)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) > 4

    def test_complexify_command(self):
        song = _make_song_with_chords()
        track_id = song.tracks[0].id
        song.tracks[0].notes = [
            Note(pitch=60, start_beat=0, duration_beat=2, velocity=100),
            Note(pitch=67, start_beat=2, duration_beat=2, velocity=100),
        ]
        cmd = ComplexifyMelodyCommand(track_id, strength=1.0)
        result = cmd.execute(song)
        track = next(t for t in result.tracks if t.id == track_id)
        assert len(track.notes) >= 2
