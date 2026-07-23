"""Tests for BassGenerator and bass commands.

Phase 4: REQUIREMENTS.md 4.4 / TECHNICAL.md 5.11.
"""

import pytest

from composer_engine.generators.bass_generator import BassGenerator
from composer_engine.commands.bass_commands import (
    GenerateBassCommand,
    RegenerateBassCommand,
    SetBassPatternCommand,
    SimplifyBassCommand,
    TransposeBassCommand,
)
from composer_engine.models.chord import Chord, ChordQuality
from composer_engine.models.enums import BassMode, InstrumentType, Key, Mode
from composer_engine.models.note import Note
from composer_engine.models.song import Song
from composer_engine.models.track import Track


def _make_song_with_chords() -> Song:
    """Helper: song with C major chords over 16 beats."""
    song = Song(name="Test Bass")
    song.global_settings.key = Key.C
    song.global_settings.mode = Mode.MAJOR
    song.chord_progression = [
        Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
        Chord(root=Key.F, quality=ChordQuality.MAJOR, start_beat=4, duration_beat=4),
        Chord(root=Key.G, quality=ChordQuality.MAJOR, start_beat=8, duration_beat=4),
        Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=12, duration_beat=4),
    ]
    return song


# ──── BassGenerator tests ────

class TestBassGenerator:
    def setup_method(self):
        self.gen = BassGenerator()
        self.chords = _make_song_with_chords().chord_progression

    def test_root_mode(self):
        notes = self.gen.generate(self.chords, Key.C, Mode.MAJOR, 0, 16, BassMode.ROOT)
        assert len(notes) == 4  # one per chord
        assert all(28 <= n.pitch <= 55 for n in notes)

    def test_octave_mode(self):
        notes = self.gen.generate(self.chords, Key.C, Mode.MAJOR, 0, 16, BassMode.OCTAVE)
        assert len(notes) >= 4  # at least one per chord, likely 2 per chord
        assert all(n.pitch >= 0 for n in notes)

    def test_walking_mode(self):
        notes = self.gen.generate(self.chords, Key.C, Mode.MAJOR, 0, 16, BassMode.WALKING)
        assert len(notes) >= 14  # roughly one per beat
        assert all(n.duration_beat > 0 for n in notes)

    def test_syncopation_mode(self):
        notes = self.gen.generate(self.chords, Key.C, Mode.MAJOR, 0, 16, BassMode.SYNCOPATION)
        assert len(notes) >= 4
        # Check some notes are on offbeats
        has_offbeat = any(n.start_beat % 1.0 > 0.01 for n in notes)
        assert has_offbeat

    def test_follow_chords_mode(self):
        notes = self.gen.generate(self.chords, Key.C, Mode.MAJOR, 0, 16, BassMode.FOLLOW_CHORDS)
        assert len(notes) >= 4

    def test_independent_mode(self):
        notes = self.gen.generate(self.chords, Key.C, Mode.MAJOR, 0, 16, BassMode.INDEPENDENT)
        assert len(notes) >= 10

    def test_counter_bass_mode(self):
        melody = [Note(pitch=72, start_beat=i, duration_beat=1.0, velocity=100) for i in range(16)]
        notes = self.gen.generate(self.chords, Key.C, Mode.MAJOR, 0, 16,
                                  BassMode.COUNTER_BASS, melody_notes=melody)
        assert len(notes) >= 10

    def test_generate_mode(self):
        notes = self.gen.generate(self.chords, Key.C, Mode.MAJOR, 0, 16, BassMode.GENERATE)
        assert len(notes) >= 4

    def test_octave_range(self):
        notes_low = self.gen.generate(self.chords, Key.C, Mode.MAJOR, 0, 16,
                                      BassMode.ROOT, octave=1)
        notes_high = self.gen.generate(self.chords, Key.C, Mode.MAJOR, 0, 16,
                                       BassMode.ROOT, octave=3)
        if notes_low and notes_high:
            avg_low = sum(n.pitch for n in notes_low) / len(notes_low)
            avg_high = sum(n.pitch for n in notes_high) / len(notes_high)
            assert avg_low < avg_high

    def test_simplify(self):
        notes = self.gen.generate(self.chords, Key.C, Mode.MAJOR, 0, 16, BassMode.WALKING)
        simplified = self.gen.simplify(notes)
        assert len(simplified) <= len(notes)
        assert len(simplified) >= 1

    def test_transpose(self):
        notes = [Note(pitch=36, start_beat=0, duration_beat=1, velocity=100)]
        transposed = self.gen.transpose(notes, 12)
        assert transposed[0].pitch == 48

    def test_empty_chords(self):
        notes = self.gen.generate([], Key.C, Mode.MAJOR, 0, 16, BassMode.ROOT)
        assert notes == []

    def test_zero_range(self):
        notes = self.gen.generate(self.chords, Key.C, Mode.MAJOR, 0, 0, BassMode.ROOT)
        assert notes == []


# ──── Bass Command tests ────

class TestBassCommands:
    def test_generate_bass_command(self):
        song = _make_song_with_chords()
        cmd = GenerateBassCommand(bass_mode="root")
        result = cmd.execute(song)
        # Should have auto-created a bass track
        bass_tracks = [t for t in result.tracks if t.instrument == InstrumentType.BASS]
        assert len(bass_tracks) >= 1
        assert len(bass_tracks[0].notes) >= 1

    def test_generate_bass_with_existing_track(self):
        song = _make_song_with_chords()
        track = Track.create("Bass", InstrumentType.BASS)
        song.tracks.append(track)
        cmd = GenerateBassCommand(track_id=track.id, bass_mode="walking")
        result = cmd.execute(song)
        bass_track = next(t for t in result.tracks if t.id == track.id)
        assert len(bass_track.notes) >= 1

    def test_regenerate_bass_command(self):
        song = _make_song_with_chords()
        track = Track.create("Bass", InstrumentType.BASS)
        track.notes = [Note(pitch=36, start_beat=0, duration_beat=1, velocity=100)]
        song.tracks.append(track)
        cmd = RegenerateBassCommand(track.id, bass_mode="root")
        result = cmd.execute(song)
        bass_track = next(t for t in result.tracks if t.id == track.id)
        assert len(bass_track.notes) >= 1

    def test_set_bass_pattern_command(self):
        song = _make_song_with_chords()
        track = Track.create("Bass", InstrumentType.BASS)
        song.tracks.append(track)
        notes_data = [{"pitch": 36, "start_beat": 0, "duration_beat": 4, "velocity": 100}]
        cmd = SetBassPatternCommand(track.id, notes_data)
        result = cmd.execute(song)
        bass_track = next(t for t in result.tracks if t.id == track.id)
        assert len(bass_track.notes) == 1

    def test_simplify_bass_command(self):
        song = _make_song_with_chords()
        track = Track.create("Bass", InstrumentType.BASS)
        track.notes = [Note(pitch=36, start_beat=i*0.5, duration_beat=0.5, velocity=100) for i in range(16)]
        song.tracks.append(track)
        cmd = SimplifyBassCommand(track.id)
        result = cmd.execute(song)
        bass_track = next(t for t in result.tracks if t.id == track.id)
        assert len(bass_track.notes) <= 16

    def test_transpose_bass_command(self):
        song = _make_song_with_chords()
        track = Track.create("Bass", InstrumentType.BASS)
        track.notes = [Note(pitch=36, start_beat=0, duration_beat=4, velocity=100)]
        song.tracks.append(track)
        cmd = TransposeBassCommand(track.id, 12)
        result = cmd.execute(song)
        bass_track = next(t for t in result.tracks if t.id == track.id)
        assert bass_track.notes[0].pitch == 48
