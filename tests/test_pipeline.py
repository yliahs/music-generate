"""Tests for Pipeline system."""

from composer_engine.models import InstrumentType, Note, Song, Stage
from composer_engine.models.chord import Chord, ChordQuality
from composer_engine.models.enums import Key, SectionType
from composer_engine.models.section import Section
from composer_engine.models.track import Track
from composer_engine.pipeline.pipeline_manager import PipelineManager


class TestPipelineEvaluation:
    def test_empty_stage(self):
        pm = PipelineManager()
        ev = pm.evaluate(None)
        assert ev.current_stage == Stage.EMPTY

    def test_inspiration_auto_advance(self):
        pm = PipelineManager()
        song = Song(name="Test")
        ev = pm.evaluate(song)
        # Song has name + tempo + key by default → Inspiration exit met → auto advance to Composition
        assert pm.current_stage == Stage.COMPOSITION

    def test_composition_needs_sections(self):
        pm = PipelineManager()
        song = Song(name="Test")
        ev = pm.evaluate(song)
        # Now in Composition, no sections → missing
        assert pm.current_stage == Stage.COMPOSITION
        assert ev.progress < 100

    def test_composition_to_arrangement(self):
        pm = PipelineManager()
        song = Song(name="Test")
        song.sections.append(Section(type=SectionType.VERSE, start_beat=0, length_beats=16))
        song.chord_progression = [
            Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
        ]
        t = Track.create("Lead", InstrumentType.LEAD)
        t.notes = [Note(pitch=60, start_beat=0, duration_beat=1)]
        song.tracks.append(t)
        ev = pm.evaluate(song)
        # Sections + chords + melody → Composition exit met → advance to Arrangement
        assert pm.current_stage == Stage.ARRANGEMENT

    def test_arrangement_needs_4_tracks(self):
        pm = PipelineManager()
        song = Song(name="Test")
        song.sections.append(Section(type=SectionType.VERSE, start_beat=0, length_beats=16))
        song.chord_progression = [
            Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
        ]
        # Only 2 tracks with notes
        for name, inst in [("Piano", InstrumentType.PIANO), ("Bass", InstrumentType.BASS)]:
            t = Track.create(name, inst)
            t.notes = [Note(pitch=60, start_beat=0, duration_beat=1)]
            song.tracks.append(t)
        ev = pm.evaluate(song)
        assert pm.current_stage == Stage.ARRANGEMENT
        assert "2/4" in ev.missing_conditions[0]


class TestPipelineGoBack:
    def test_go_back(self):
        pm = PipelineManager()
        song = Song(name="Test")
        pm.evaluate(song)
        assert pm.current_stage == Stage.COMPOSITION
        pm.go_back(Stage.INSPIRATION)
        assert pm.current_stage == Stage.INSPIRATION

    def test_advance(self):
        pm = PipelineManager()
        pm.current_stage = Stage.PRODUCTION
        pm.advance()
        assert pm.current_stage == Stage.EXPORT


class TestStageGuide:
    def test_guide_structure(self):
        pm = PipelineManager()
        guide = pm.get_guide(None)
        assert guide.stage == "empty"
        assert len(guide.recommended_tools) > 0

    def test_guide_with_song(self):
        pm = PipelineManager()
        song = Song(name="Test")
        guide = pm.get_guide(song)
        assert guide.stage == "Composition"
        assert len(guide.what_to_do) > 0
