"""Tests for AnalysisEngine and analysis commands.

Phase 7: TECHNICAL.md 5.14.
"""

import pytest

from composer_engine.commands.analysis_commands import (
    AnalyzeCadencesCommand,
    AnalyzeChordsCommand,
    AnalyzeComplexityCommand,
    AnalyzeCounterpointCommand,
    AnalyzeDensityCommand,
    AnalyzeDynamicsCommand,
    AnalyzeEnergyCommand,
    AnalyzeKeyCommand,
    AnalyzeMotifsCommand,
    AnalyzeMoodCommand,
    AnalyzePhrasesCommand,
    AnalyzeRangeCommand,
    AnalyzeRepetitionCommand,
    AnalyzeRhythmCommand,
    AnalyzeStructureCommand,
    AnalyzeStyleCommand,
    AnalyzeTempoCommand,
    AnalyzeVoiceLeadingCommand,
    GetFullAnalysisCommand,
)
from composer_engine.commands.global_commands import SetTempoCommand
from composer_engine.engine.composer import Composer
from composer_engine.generators.analysis_engine import AnalysisEngine
from composer_engine.models.chord import Chord, ChordQuality
from composer_engine.models.enums import InstrumentType, Key, Mode, SectionType
from composer_engine.models.note import Note
from composer_engine.models.section import Section
from composer_engine.models.song import Song
from composer_engine.models.track import Track


def _make_song() -> Song:
    """Build a test song with piano, drums, sections, and chord progression."""
    song = Song(name="Test Song")
    song.global_settings.tempo = 120
    song.global_settings.key = Key.C
    song.global_settings.mode = Mode.MAJOR

    verse = Section(type=SectionType.VERSE, start_beat=0, length_beats=8)
    chorus = Section(type=SectionType.CHORUS, start_beat=8, length_beats=8)
    song.sections = [verse, chorus]

    piano = Track.create("Piano", InstrumentType.PIANO)
    piano.notes = [
        Note(pitch=60, start_beat=0, duration_beat=1, velocity=80),
        Note(pitch=62, start_beat=1, duration_beat=1, velocity=85),
        Note(pitch=64, start_beat=2, duration_beat=1, velocity=90),
        Note(pitch=65, start_beat=3, duration_beat=1, velocity=85),
        Note(pitch=67, start_beat=4, duration_beat=1, velocity=80),
        Note(pitch=69, start_beat=5, duration_beat=1, velocity=85),
        Note(pitch=71, start_beat=6, duration_beat=1, velocity=90),
        Note(pitch=72, start_beat=7, duration_beat=1, velocity=95),
        Note(pitch=60, start_beat=8, duration_beat=1, velocity=80),
        Note(pitch=62, start_beat=9, duration_beat=1, velocity=85),
        Note(pitch=64, start_beat=10, duration_beat=1, velocity=90),
        Note(pitch=65, start_beat=11, duration_beat=1, velocity=85),
        Note(pitch=0, start_beat=12, duration_beat=2, velocity=70),
        Note(pitch=60, start_beat=14, duration_beat=1, velocity=80),
        Note(pitch=62, start_beat=15, duration_beat=1, velocity=85),
    ]

    melody = Track.create("Melody", InstrumentType.LEAD)
    melody.notes = [
        Note(pitch=72, start_beat=0, duration_beat=1, velocity=90),
        Note(pitch=74, start_beat=1, duration_beat=1, velocity=90),
        Note(pitch=76, start_beat=2, duration_beat=1, velocity=90),
        Note(pitch=77, start_beat=3, duration_beat=1, velocity=90),
        Note(pitch=79, start_beat=4, duration_beat=1, velocity=90),
        Note(pitch=81, start_beat=5, duration_beat=1, velocity=90),
        Note(pitch=83, start_beat=6, duration_beat=1, velocity=90),
        Note(pitch=84, start_beat=7, duration_beat=1, velocity=90),
    ]

    drums = Track.create("Drums", InstrumentType.DRUMS)
    drums.notes = [
        Note(pitch=36, start_beat=0, duration_beat=0.5, velocity=100),
        Note(pitch=36, start_beat=2, duration_beat=0.5, velocity=100),
        Note(pitch=36, start_beat=4, duration_beat=0.5, velocity=100),
        Note(pitch=36, start_beat=6, duration_beat=0.5, velocity=100),
        Note(pitch=38, start_beat=1, duration_beat=0.5, velocity=90),
        Note(pitch=38, start_beat=3, duration_beat=0.5, velocity=90),
        Note(pitch=38, start_beat=5, duration_beat=0.5, velocity=90),
        Note(pitch=38, start_beat=7, duration_beat=0.5, velocity=90),
    ]

    song.tracks = [piano, melody, drums]

    song.chord_progression = [
        Chord(
            root=Key.C,
            quality=ChordQuality.MAJOR,
            start_beat=0,
            duration_beat=4,
            roman="I",
        ),
        Chord(
            root=Key.F,
            quality=ChordQuality.MAJOR,
            start_beat=4,
            duration_beat=4,
            roman="IV",
        ),
        Chord(
            root=Key.G,
            quality=ChordQuality.MAJOR,
            start_beat=8,
            duration_beat=4,
            roman="V",
        ),
        Chord(
            root=Key.C,
            quality=ChordQuality.MAJOR,
            start_beat=12,
            duration_beat=4,
            roman="I",
        ),
    ]

    return song


def _make_parallel_fifths_song() -> Song:
    song = _make_song()
    track_a = Track.create("Voice A", InstrumentType.STRINGS)
    track_b = Track.create("Voice B", InstrumentType.STRINGS)
    for i in range(4):
        track_a.notes.append(Note(pitch=60 + i * 2, start_beat=i, duration_beat=1, velocity=80))
        track_b.notes.append(Note(pitch=67 + i * 2, start_beat=i, duration_beat=1, velocity=80))
    song.tracks.extend([track_a, track_b])
    return song


def _make_motif_song() -> Song:
    song = Song(name="Motif Test")
    track = Track.create("Piano", InstrumentType.PIANO)
    motif = [
        (60, 0), (62, 1), (64, 2),
        (60, 4), (62, 5), (64, 6),
        (60, 8), (62, 9), (64, 10),
    ]
    for pitch, beat in motif:
        track.notes.append(Note(pitch=pitch, start_beat=beat, duration_beat=0.5, velocity=80))
    song.tracks = [track]
    return song


def _make_repetition_song() -> Song:
    song = Song(name="Repetition Test")
    track = Track.create("Piano", InstrumentType.PIANO)
    pattern = [
        Note(pitch=60, start_beat=0, duration_beat=1, velocity=80),
        Note(pitch=64, start_beat=1, duration_beat=1, velocity=80),
    ]
    for bar in range(4):
        for note in pattern:
            track.notes.append(
                Note(
                    pitch=note.pitch,
                    start_beat=note.start_beat + bar * 4,
                    duration_beat=note.duration_beat,
                    velocity=note.velocity,
                )
            )
    song.tracks = [track]
    song.sections = [Section(type=SectionType.VERSE, start_beat=0, length_beats=16)]
    return song


@pytest.fixture
def song():
    return _make_song()


@pytest.fixture
def engine():
    return AnalysisEngine()


class TestAnalyzeKey:
    def test_analyze_key(self, engine, song):
        result = engine.analyze_key(song)
        assert "key" in result
        assert "mode" in result
        assert "confidence" in result
        assert isinstance(result["confidence"], float)
        assert "alternatives" in result


class TestAnalyzeTempo:
    def test_analyze_tempo(self, engine, song):
        result = engine.analyze_tempo(song)
        assert result["bpm"] == 120
        assert "stability" in result
        assert "detected_bpm" in result


class TestAnalyzeChords:
    def test_analyze_chords(self, engine, song):
        piano_id = song.tracks[0].id
        result = engine.analyze_chords(song, piano_id)
        assert "chords" in result
        assert isinstance(result["chords"], list)


class TestAnalyzePhrases:
    def test_analyze_phrases(self, engine, song):
        piano_id = song.tracks[0].id
        result = engine.analyze_phrases(song, piano_id)
        assert "phrases" in result
        assert len(result["phrases"]) >= 1
        gap_song = Song(name="Gap")
        track = Track.create("Piano", InstrumentType.PIANO)
        track.notes = [
            Note(pitch=60, start_beat=0, duration_beat=1, velocity=80),
            Note(pitch=64, start_beat=3, duration_beat=1, velocity=80),
        ]
        gap_song.tracks = [track]
        gap_result = engine.analyze_phrases(gap_song, track.id)
        assert len(gap_result["phrases"]) >= 2


class TestAnalyzeMotifs:
    def test_analyze_motifs(self, engine):
        song = _make_motif_song()
        track_id = song.tracks[0].id
        result = engine.analyze_motifs(song, track_id)
        assert "motifs" in result
        assert len(result["motifs"]) >= 1


class TestAnalyzeRhythm:
    def test_analyze_rhythm(self, engine, song):
        piano_id = song.tracks[0].id
        result = engine.analyze_rhythm(song, piano_id)
        assert "dominant_value" in result
        assert "syncopation_ratio" in result
        assert "complexity" in result
        assert "distribution" in result


class TestAnalyzeDensity:
    def test_analyze_density(self, engine, song):
        result = engine.analyze_density(song)
        assert result["resolution"] == "beat"
        assert "data" in result
        assert "avg" in result
        assert "max" in result
        assert result["max"] >= 1


class TestAnalyzeEnergy:
    def test_analyze_energy(self, engine, song):
        result = engine.analyze_energy(song)
        assert "curve" in result
        assert len(result["curve"]) >= 1
        assert "avg" in result
        assert "peak_bar" in result


class TestAnalyzeRange:
    def test_analyze_range(self, engine, song):
        piano_id = song.tracks[0].id
        result = engine.analyze_range(song, piano_id)
        assert "min" in result
        assert "max" in result
        assert "span" in result
        assert result["max"] >= result["min"]


class TestAnalyzeRepetition:
    def test_analyze_repetition(self, engine):
        song = _make_repetition_song()
        track_id = song.tracks[0].id
        result = engine.analyze_repetition(song, track_id)
        assert "patterns" in result
        assert "repetition_rate" in result
        assert result["repetition_rate"] > 0


class TestAnalyzeVoiceLeading:
    def test_analyze_voice_leading(self, engine):
        song = _make_parallel_fifths_song()
        result = engine.analyze_voice_leading(song)
        assert "issues" in result
        assert "issue_count" in result
        assert "severity" in result
        assert result["issue_count"] >= 1


class TestAnalyzeCadences:
    def test_analyze_cadences(self, engine, song):
        result = engine.analyze_cadences(song)
        assert "cadences" in result
        types = {c["type"] for c in result["cadences"]}
        assert "authentic" in types or "plagal" in types


class TestAnalyzeCounterpoint:
    def test_analyze_counterpoint(self, engine, song):
        track_a = song.tracks[0].id
        track_b = song.tracks[1].id
        result = engine.analyze_counterpoint(song, track_a, track_b)
        assert "parallel_ratio" in result
        assert "contrary_ratio" in result
        assert "oblique_ratio" in result
        assert "similar_ratio" in result


class TestAnalyzeStyle:
    def test_analyze_style(self, engine, song):
        result = engine.analyze_style(song)
        assert "style" in result
        assert "confidence" in result
        assert "scores" in result
        assert len(result["scores"]) > 0


class TestAnalyzeMood:
    def test_analyze_mood(self, engine, song):
        result = engine.analyze_mood(song)
        assert "valence" in result
        assert "arousal" in result
        assert "tags" in result


class TestAnalyzeComplexity:
    def test_analyze_complexity(self, engine, song):
        result = engine.analyze_complexity(song)
        assert "total" in result
        assert "pitch" in result
        assert "rhythm" in result
        assert "harmony" in result
        assert "structure" in result


class TestAnalyzeDynamics:
    def test_analyze_dynamics(self, engine, song):
        result = engine.analyze_dynamics(song)
        assert "velocity_range" in result
        assert "avg_velocity" in result
        assert "contour" in result
        assert result["avg_velocity"] > 0


class TestAnalyzeStructure:
    def test_analyze_structure(self, engine, song):
        result = engine.analyze_structure(song)
        assert "segments" in result
        assert "form" in result
        assert len(result["segments"]) == 2


class TestGetFullAnalysis:
    def test_get_full_analysis(self, engine, song):
        result = engine.get_full_analysis(song)
        assert "key" in result
        assert "tempo" in result
        assert "energy" in result
        assert "tracks" in result
        assert len(result["tracks"]) >= 1


class TestCacheInvalidation:
    def test_cache_invalidation(self, song):
        from composer_engine.models.analysis import AnalysisResult

        composer = Composer()
        composer.song = song
        composer.song.analysis_cache["manual"] = AnalysisResult(
            type="manual", data={"test": True}
        )
        assert len(composer.song.analysis_cache) == 1
        composer.execute(SetTempoCommand(140))
        assert len(composer.song.analysis_cache) == 0


class TestAnalysisCommands:
    def test_analysis_commands_store_result(self, song):
        composer = Composer()
        composer.song = song

        cmd = AnalyzeKeyCommand()
        composer.execute(cmd)
        assert "key" in cmd._result
        assert "mode" in cmd._result

        cmd = AnalyzeTempoCommand()
        composer.execute(cmd)
        assert cmd._result["bpm"] == 120

        piano_id = song.tracks[0].id
        cmd = AnalyzeRangeCommand(piano_id)
        composer.execute(cmd)
        assert "min" in cmd._result

        cmd = GetFullAnalysisCommand()
        composer.execute(cmd)
        assert "key" in cmd._result
        assert "tracks" in cmd._result


class TestEmptySong:
    def test_empty_song(self, engine):
        song = Song(name="Empty")
        assert engine.analyze_key(song)["confidence"] == 0.0
        assert engine.analyze_tempo(song)["bpm"] == 120
        assert engine.analyze_energy(song)["curve"] == [0.0]
        assert engine.analyze_structure(song)["form"] == "unknown"
        assert engine.analyze_cadences(song)["cadences"] == []
        assert isinstance(engine.analyze_mood(song)["tags"], list)
        assert engine.analyze_style(song)["scores"]

    def test_empty_track_analysis(self, engine):
        song = Song(name="Empty Track")
        track = Track.create("Piano", InstrumentType.PIANO)
        song.tracks = [track]
        result = engine.analyze_range(song, track.id)
        assert result["min"] == 0
        assert result["max"] == 0

    def test_no_song_command_raises(self):
        composer = Composer()
        with pytest.raises(ValueError, match="No song loaded"):
            composer.execute(AnalyzeKeyCommand())
