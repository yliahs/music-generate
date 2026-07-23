"""Tests for MidiImporter (Phase 13).

Uses MidiRenderer to create a known MIDI file, then re-imports it
to verify round-trip correctness.
"""

import os
import tempfile

import pytest

from composer_engine.commands.global_commands import SetKeyCommand, SetTempoCommand
from composer_engine.commands.section_commands import AddSectionCommand
from composer_engine.commands.song_commands import CreateSongCommand
from composer_engine.commands.track_commands import AddNotesCommand, AddTrackCommand
from composer_engine.importer.midi_importer import MidiImporter
from composer_engine.models.enums import InstrumentType, Key, Mode, SectionType
from composer_engine.models.note import Note
from composer_engine.renderer.midi_renderer import MidiRenderer


@pytest.fixture
def importer():
    return MidiImporter()


@pytest.fixture
def sample_midi_path():
    """Create a MIDI file from a known Song for round-trip testing."""
    song = CreateSongCommand(name="Test Song", tempo=140, key=Key.D).execute(None)
    song = AddSectionCommand(SectionType.VERSE, 0.0, 16.0).execute(song)
    song = AddTrackCommand("Piano", InstrumentType.PIANO).execute(song)
    song = AddTrackCommand("Bass", InstrumentType.BASS).execute(song)

    piano_notes = [
        Note(pitch=60, start_beat=0.0, duration_beat=1.0, velocity=90),
        Note(pitch=64, start_beat=1.0, duration_beat=1.0, velocity=80),
        Note(pitch=67, start_beat=2.0, duration_beat=2.0, velocity=100),
    ]
    bass_notes = [
        Note(pitch=36, start_beat=0.0, duration_beat=4.0, velocity=70),
    ]
    song = AddNotesCommand(song.tracks[0].id, piano_notes).execute(song)
    song = AddNotesCommand(song.tracks[1].id, bass_notes).execute(song)

    renderer = MidiRenderer()
    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
        path = f.name
    renderer.render_to_file(song, path)
    yield path
    os.unlink(path)


class TestMidiImporterImportFile:
    def test_import_creates_song(self, importer, sample_midi_path):
        song = importer.import_file(sample_midi_path)
        assert song.name != ""
        assert len(song.tracks) == 2

    def test_import_preserves_tempo(self, importer, sample_midi_path):
        song = importer.import_file(sample_midi_path)
        assert abs(song.global_settings.tempo - 140.0) < 1.0

    def test_import_preserves_notes(self, importer, sample_midi_path):
        song = importer.import_file(sample_midi_path)
        total_notes = sum(len(t.notes) for t in song.tracks)
        assert total_notes == 4

    def test_import_maps_instrument_types(self, importer, sample_midi_path):
        song = importer.import_file(sample_midi_path)
        types = {t.instrument for t in song.tracks}
        assert InstrumentType.PIANO in types
        assert InstrumentType.BASS in types

    def test_import_custom_name(self, importer, sample_midi_path):
        song = importer.import_file(sample_midi_path, song_name="My Import")
        assert song.name == "My Import"

    def test_import_file_not_found(self, importer):
        with pytest.raises(FileNotFoundError):
            importer.import_file("/nonexistent/path.mid")

    def test_note_pitch_roundtrip(self, importer, sample_midi_path):
        song = importer.import_file(sample_midi_path)
        piano_track = next(t for t in song.tracks if t.instrument == InstrumentType.PIANO)
        pitches = sorted(n.pitch for n in piano_track.notes)
        assert pitches == [60, 64, 67]


class TestMidiImporterSingleTrack:
    def test_import_single_track(self, importer, sample_midi_path):
        track = importer.import_single_track(sample_midi_path, 0)
        assert isinstance(track.name, str)
        assert len(track.notes) > 0

    def test_import_second_track(self, importer, sample_midi_path):
        track = importer.import_single_track(sample_midi_path, 1)
        assert len(track.notes) > 0

    def test_import_track_out_of_range(self, importer, sample_midi_path):
        with pytest.raises(IndexError):
            importer.import_single_track(sample_midi_path, 99)

    def test_import_track_file_not_found(self, importer):
        with pytest.raises(FileNotFoundError):
            importer.import_single_track("/nonexistent.mid", 0)


class TestMidiImporterGetInfo:
    def test_get_info_returns_metadata(self, importer, sample_midi_path):
        info = importer.get_info(sample_midi_path)
        assert "tempo" in info
        assert "track_count" in info
        assert "tracks" in info
        assert info["track_count"] == 2

    def test_get_info_track_details(self, importer, sample_midi_path):
        info = importer.get_info(sample_midi_path)
        for track_info in info["tracks"]:
            assert "name" in track_info
            assert "note_count" in track_info
            assert "instrument_type" in track_info
            assert "program" in track_info

    def test_get_info_total_notes(self, importer, sample_midi_path):
        info = importer.get_info(sample_midi_path)
        assert info["total_notes"] == 4

    def test_get_info_file_not_found(self, importer):
        with pytest.raises(FileNotFoundError):
            importer.get_info("/nonexistent.mid")

    def test_get_info_duration(self, importer, sample_midi_path):
        info = importer.get_info(sample_midi_path)
        assert info["duration_seconds"] > 0
        assert info["duration_beats"] > 0


class TestProgramMapping:
    """Test GM Program → InstrumentType mapping."""

    def test_piano_range(self, importer):
        assert importer._program_to_instrument_type(0, False) == InstrumentType.PIANO
        assert importer._program_to_instrument_type(15, False) == InstrumentType.PIANO

    def test_guitar_range(self, importer):
        assert importer._program_to_instrument_type(25, False) == InstrumentType.GUITAR

    def test_bass_range(self, importer):
        assert importer._program_to_instrument_type(33, False) == InstrumentType.BASS

    def test_strings_range(self, importer):
        assert importer._program_to_instrument_type(48, False) == InstrumentType.STRINGS

    def test_brass_range(self, importer):
        assert importer._program_to_instrument_type(61, False) == InstrumentType.BRASS

    def test_woodwinds_range(self, importer):
        assert importer._program_to_instrument_type(73, False) == InstrumentType.WOODWINDS

    def test_lead_range(self, importer):
        assert importer._program_to_instrument_type(80, False) == InstrumentType.LEAD

    def test_pad_range(self, importer):
        assert importer._program_to_instrument_type(89, False) == InstrumentType.PAD

    def test_fx_range(self, importer):
        assert importer._program_to_instrument_type(98, False) == InstrumentType.FX

    def test_drums_override(self, importer):
        assert importer._program_to_instrument_type(0, True) == InstrumentType.DRUMS
        assert importer._program_to_instrument_type(80, True) == InstrumentType.DRUMS


class TestKeySignatureParsing:
    """Test key_number → (Key, Mode) mapping."""

    def test_c_major(self, importer):
        key, mode = importer._parse_key_number(0)
        assert key == Key.C
        assert mode == Mode.MAJOR

    def test_d_major(self, importer):
        key, mode = importer._parse_key_number(2)
        assert key == Key.D
        assert mode == Mode.MAJOR

    def test_a_minor(self, importer):
        key, mode = importer._parse_key_number(21)
        assert key == Key.A
        assert mode == Mode.MINOR

    def test_c_minor(self, importer):
        key, mode = importer._parse_key_number(12)
        assert key == Key.C
        assert mode == Mode.MINOR
