"""Tests for data models."""

import json

from composer_engine.models import (
    GlobalSettings,
    InstrumentType,
    Key,
    Mode,
    Note,
    Section,
    SectionType,
    Song,
    Stage,
    Track,
)


class TestNote:
    def test_create(self):
        note = Note(pitch=60, start_beat=0.0, duration_beat=1.0)
        assert note.pitch == 60
        assert note.velocity == 100

    def test_json_roundtrip(self):
        note = Note(pitch=72, start_beat=4.0, duration_beat=0.5, velocity=80)
        data = json.loads(note.model_dump_json())
        restored = Note.model_validate(data)
        assert restored == note


class TestTrack:
    def test_create_factory(self):
        track = Track.create(name="Piano", instrument=InstrumentType.PIANO)
        assert track.program == 0
        assert track.channel == 0

    def test_drums_auto_channel(self):
        track = Track.create(name="Drums", instrument=InstrumentType.DRUMS)
        assert track.channel == 9

    def test_custom_program(self):
        track = Track.create(name="Guitar", instrument=InstrumentType.GUITAR, program=27)
        assert track.program == 27


class TestSection:
    def test_create(self):
        section = Section(type=SectionType.CHORUS, start_beat=32.0, length_beats=16.0)
        assert section.type == SectionType.CHORUS
        assert section.repeat == 1


class TestSong:
    def test_create(self):
        song = Song(name="Test Song")
        assert song.name == "Test Song"
        assert song.stage == Stage.INSPIRATION
        assert song.global_settings.tempo == 120.0
        assert song.global_settings.key == Key.C

    def test_json_roundtrip(self):
        song = Song(
            name="Test",
            global_settings=GlobalSettings(tempo=140, key=Key.Eb, mode=Mode.MINOR),
        )
        song.tracks.append(Track.create("Bass", InstrumentType.BASS))
        song.sections.append(Section(type=SectionType.VERSE, start_beat=0, length_beats=16))

        json_str = song.model_dump_json()
        restored = Song.model_validate_json(json_str)
        assert restored.name == "Test"
        assert restored.global_settings.tempo == 140
        assert len(restored.tracks) == 1
        assert len(restored.sections) == 1

    def test_deep_copy(self):
        song = Song(name="Original")
        song.tracks.append(Track.create("Piano", InstrumentType.PIANO))
        copy = song.model_copy(deep=True)
        copy.name = "Copy"
        copy.tracks[0].name = "Modified Piano"
        assert song.name == "Original"
        assert song.tracks[0].name == "Piano"
