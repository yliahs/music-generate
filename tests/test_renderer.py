"""Tests for MIDI renderer."""

import tempfile
from pathlib import Path

from composer_engine.models import InstrumentType, Note, Song
from composer_engine.models.track import Track
from composer_engine.renderer.midi_renderer import MidiRenderer


class TestMidiRenderer:
    def _make_song_with_notes(self) -> Song:
        song = Song(name="Test")
        track = Track.create("Piano", InstrumentType.PIANO)
        track.notes = [
            Note(pitch=60, start_beat=0, duration_beat=1),
            Note(pitch=64, start_beat=1, duration_beat=1),
            Note(pitch=67, start_beat=2, duration_beat=1),
        ]
        song.tracks.append(track)
        return song

    def test_render(self):
        song = self._make_song_with_notes()
        r = MidiRenderer()
        midi = r.render(song)
        assert len(midi.instruments) == 1
        assert len(midi.instruments[0].notes) == 3

    def test_render_to_file(self):
        song = self._make_song_with_notes()
        r = MidiRenderer()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "test.mid")
            r.render_to_file(song, path)
            assert Path(path).exists()
            assert Path(path).stat().st_size > 0

    def test_mute_track_not_rendered(self):
        song = self._make_song_with_notes()
        song.tracks[0].mute = True
        r = MidiRenderer()
        midi = r.render(song)
        assert len(midi.instruments) == 0

    def test_solo_overrides_mute(self):
        song = Song(name="Test")
        t1 = Track.create("Piano", InstrumentType.PIANO)
        t1.notes = [Note(pitch=60, start_beat=0, duration_beat=1)]
        t1.mute = True
        t2 = Track.create("Bass", InstrumentType.BASS)
        t2.notes = [Note(pitch=36, start_beat=0, duration_beat=1)]
        t2.solo = True
        song.tracks = [t1, t2]

        r = MidiRenderer()
        midi = r.render(song)
        assert len(midi.instruments) == 1
        assert midi.instruments[0].name == "Bass"

    def test_beat_to_seconds(self):
        r = MidiRenderer()
        assert r._beat_to_seconds(1.0, 120.0) == 0.5
        assert r._beat_to_seconds(4.0, 60.0) == 4.0
