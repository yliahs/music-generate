"""Tests for Phase 10 MusicXML Export."""
import pytest
import xml.etree.ElementTree as ET

from composer_engine.models.enums import InstrumentType, Key, Mode
from composer_engine.models.note import Note
from composer_engine.models.song import Song
from composer_engine.models.track import Track
from composer_engine.renderer.musicxml_renderer import (
    MusicXMLRenderer,
    midi_to_musicxml_pitch,
    quantize_duration,
    velocity_to_dynamic,
    KEY_TO_FIFTHS,
)


def _make_song():
    song = Song(name="Test Song")
    song.global_settings.tempo = 120.0
    song.global_settings.key = Key.C
    song.global_settings.mode = Mode.MAJOR
    track = Track.create(name="Piano", instrument=InstrumentType.PIANO)
    track.notes = [
        Note(pitch=60, start_beat=0.0, duration_beat=1.0, velocity=80),
        Note(pitch=64, start_beat=1.0, duration_beat=1.0, velocity=90),
        Note(pitch=67, start_beat=2.0, duration_beat=2.0, velocity=100),
    ]
    song.tracks.append(track)
    return song


class TestHelpers:
    def test_midi_to_musicxml_pitch_c4(self):
        step, alter, octave = midi_to_musicxml_pitch(60)
        assert step == "C"
        assert alter == 0
        assert octave == 4

    def test_midi_to_musicxml_pitch_csharp(self):
        step, alter, octave = midi_to_musicxml_pitch(61)
        assert step == "C"
        assert alter == 1

    def test_midi_to_musicxml_pitch_a0(self):
        step, alter, octave = midi_to_musicxml_pitch(21)
        assert step == "A"
        assert octave == 0

    def test_quantize_duration(self):
        assert quantize_duration(1.0) == 1.0
        assert quantize_duration(0.5) == 0.5
        assert quantize_duration(0.3) == 0.25
        assert quantize_duration(0.6) == 0.5
        assert quantize_duration(1.8) == 2.0
        assert quantize_duration(3.5) == 4.0

    def test_velocity_to_dynamic(self):
        assert velocity_to_dynamic(10) == "ppp"
        assert velocity_to_dynamic(30) == "pp"
        assert velocity_to_dynamic(50) == "p"
        assert velocity_to_dynamic(65) == "mp"
        assert velocity_to_dynamic(80) == "mf"
        assert velocity_to_dynamic(95) == "f"
        assert velocity_to_dynamic(110) == "ff"
        assert velocity_to_dynamic(125) == "fff"

    def test_key_to_fifths(self):
        assert KEY_TO_FIFTHS[Key.C] == 0
        assert KEY_TO_FIFTHS[Key.G] == 1
        assert KEY_TO_FIFTHS[Key.F] == -1


class TestMusicXMLRenderer:
    def test_render_basic(self):
        song = _make_song()
        renderer = MusicXMLRenderer()
        xml_str = renderer.render(song)
        assert "score-partwise" in xml_str
        assert "Piano" in xml_str

    def test_render_has_notes(self):
        song = _make_song()
        xml_str = MusicXMLRenderer().render(song)
        root = ET.fromstring(xml_str)
        notes = root.findall(".//note")
        assert len(notes) >= 3  # at least our 3 notes (may include rests)

    def test_render_pitch_elements(self):
        song = _make_song()
        xml_str = MusicXMLRenderer().render(song)
        root = ET.fromstring(xml_str)
        pitches = root.findall(".//pitch")
        assert len(pitches) >= 1
        step = pitches[0].find("step").text
        assert step in "CDEFGAB"

    def test_render_key_signature(self):
        song = _make_song()
        song.global_settings.key = Key.G
        xml_str = MusicXMLRenderer().render(song)
        root = ET.fromstring(xml_str)
        fifths = root.find(".//fifths")
        assert fifths is not None
        assert fifths.text == "1"

    def test_render_time_signature(self):
        song = _make_song()
        xml_str = MusicXMLRenderer().render(song)
        root = ET.fromstring(xml_str)
        beats = root.find(".//beats")
        beat_type = root.find(".//beat-type")
        assert beats.text == "4"
        assert beat_type.text == "4"

    def test_render_tempo(self):
        song = _make_song()
        xml_str = MusicXMLRenderer().render(song)
        root = ET.fromstring(xml_str)
        sound = root.find(".//sound")
        assert sound is not None
        assert sound.get("tempo") == "120"

    def test_render_drums_uses_unpitched(self):
        song = Song(name="Drum Test")
        drum_track = Track.create(name="Drums", instrument=InstrumentType.DRUMS)
        drum_track.notes = [Note(pitch=36, start_beat=0.0, duration_beat=0.5, velocity=100)]
        song.tracks.append(drum_track)
        xml_str = MusicXMLRenderer().render(song)
        root = ET.fromstring(xml_str)
        unpitched = root.findall(".//unpitched")
        assert len(unpitched) >= 1

    def test_render_empty_song(self):
        song = Song(name="Empty")
        xml_str = MusicXMLRenderer().render(song)
        assert "score-partwise" in xml_str

    def test_render_to_file(self, tmp_path):
        song = _make_song()
        path = str(tmp_path / "test.musicxml")
        result = MusicXMLRenderer().render_to_file(song, path)
        assert result == path
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "score-partwise" in content

    def test_render_rests_filled(self):
        song = Song(name="Rest Test")
        track = Track.create(name="Piano", instrument=InstrumentType.PIANO)
        track.notes = [Note(pitch=60, start_beat=2.0, duration_beat=1.0, velocity=80)]
        song.tracks.append(track)
        xml_str = MusicXMLRenderer().render(song)
        root = ET.fromstring(xml_str)
        rests = root.findall(".//rest")
        assert len(rests) >= 1  # Should have rests before the note

    def test_render_percussion_clef(self):
        song = Song(name="Perc")
        drum_track = Track.create(name="Drums", instrument=InstrumentType.DRUMS)
        drum_track.notes = [Note(pitch=38, start_beat=0.0, duration_beat=0.5, velocity=100)]
        song.tracks.append(drum_track)
        xml_str = MusicXMLRenderer().render(song)
        assert "percussion" in xml_str
