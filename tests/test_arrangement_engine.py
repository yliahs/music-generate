"""Tests for ArrangementEngine and arrangement/track commands.

Phase 5: REQUIREMENTS.md 4.5 / TECHNICAL.md 5.12.
"""

import pytest

from composer_engine.generators.arrangement_engine import ArrangementEngine
from composer_engine.commands.arrangement_commands import (
    AddFillCommand,
    AddLayerCommand,
    AddSilenceCommand,
    AddTransitionCommand,
    BreakDownCommand,
    BuildUpCommand,
    DecreaseEnergyCommand,
    DecreaseDensityCommand,
    IncreaseEnergyCommand,
    IncreaseDensityCommand,
    RemoveLayerCommand,
    SetTrackDensityCommand,
    SetTrackEnergyCommand,
    SetTrackOctaveCommand,
)
from composer_engine.models.chord import Chord, ChordQuality
from composer_engine.models.enums import InstrumentType, Key, Mode, SectionType
from composer_engine.models.note import Note
from composer_engine.models.section import Section
from composer_engine.models.song import Song
from composer_engine.models.track import Track


def _make_full_song() -> Song:
    song = Song(name="Test Arrangement")
    song.global_settings.key = Key.C
    song.global_settings.mode = Mode.MAJOR
    song.sections = [
        Section(type=SectionType.VERSE, start_beat=0, length_beats=16),
        Section(type=SectionType.CHORUS, start_beat=16, length_beats=16),
    ]
    song.chord_progression = [
        Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
        Chord(root=Key.F, quality=ChordQuality.MAJOR, start_beat=4, duration_beat=4),
    ]
    # Add piano track with notes
    piano = Track.create("Piano", InstrumentType.PIANO)
    piano.notes = [Note(pitch=60+i, start_beat=float(i*2), duration_beat=2.0, velocity=80) for i in range(16)]
    song.tracks.append(piano)
    # Add drums track
    drums = Track.create("Drums", InstrumentType.DRUMS)
    drums.notes = [Note(pitch=36, start_beat=float(i*2), duration_beat=0.5, velocity=100) for i in range(16)]
    song.tracks.append(drums)
    return song


# ──── ArrangementEngine tests ────

class TestArrangementEngine:
    def setup_method(self):
        self.engine = ArrangementEngine()

    def test_increase_energy(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        old_vel = song.tracks[0].notes[0].velocity
        song = self.engine.increase_energy(song, section_id, 0.5)
        new_vel = song.tracks[0].notes[0].velocity
        assert new_vel > old_vel

    def test_decrease_energy(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        old_vel = song.tracks[0].notes[0].velocity
        song = self.engine.decrease_energy(song, section_id, 0.5)
        new_vel = song.tracks[0].notes[0].velocity
        assert new_vel < old_vel

    def test_increase_density(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        old_count = len(song.tracks[0].notes)
        song = self.engine.increase_density(song, section_id, 1.0)
        new_count = len(song.tracks[0].notes)
        assert new_count >= old_count

    def test_decrease_density(self):
        song = _make_full_song()
        # Add some short notes
        song.tracks[0].notes.extend([
            Note(pitch=60, start_beat=0.25, duration_beat=0.1, velocity=70),
            Note(pitch=60, start_beat=0.5, duration_beat=0.1, velocity=70),
        ])
        section_id = song.sections[0].id
        old_count = len(song.tracks[0].notes)
        song = self.engine.decrease_density(song, section_id, 0.5)
        new_count = len(song.tracks[0].notes)
        assert new_count <= old_count

    def test_add_layer(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        old_tracks = len(song.tracks)
        song = self.engine.add_layer(song, section_id)
        assert len(song.tracks) > old_tracks

    def test_add_layer_specific(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        song = self.engine.add_layer(song, section_id, InstrumentType.STRINGS)
        strings = [t for t in song.tracks if t.instrument == InstrumentType.STRINGS]
        assert len(strings) >= 1

    def test_remove_layer(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        track_id = song.tracks[0].id
        notes_before = len(song.tracks[0].notes)
        song = self.engine.remove_layer(song, section_id, track_id)
        remaining = [n for n in song.tracks[0].notes if 0 <= n.start_beat < 16]
        assert len(remaining) == 0

    def test_build_up(self):
        song = _make_full_song()
        drums = song.tracks[1]
        old_count = len(drums.notes)
        song = self.engine.build_up(song, 16.0, 4.0)
        assert len(song.tracks[1].notes) > old_count

    def test_break_down(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        song = self.engine.break_down(song, section_id)
        # Drums should be removed
        drums_notes_in_section = [n for n in song.tracks[1].notes if 0 <= n.start_beat < 16]
        assert len(drums_notes_in_section) == 0

    def test_add_silence(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        song = self.engine.add_silence(song, section_id)
        for track in song.tracks:
            notes_in_section = [n for n in track.notes if 0 <= n.start_beat < 16]
            assert len(notes_in_section) == 0

    def test_add_silence_specific_track(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        track_id = song.tracks[0].id
        song = self.engine.add_silence(song, section_id, track_id)
        # Only piano should be silenced
        piano_in_section = [n for n in song.tracks[0].notes if 0 <= n.start_beat < 16]
        drums_in_section = [n for n in song.tracks[1].notes if 0 <= n.start_beat < 16]
        assert len(piano_in_section) == 0
        assert len(drums_in_section) > 0


# ──── Arrangement Command tests ────

class TestArrangementCommands:
    def test_increase_energy_command(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        cmd = IncreaseEnergyCommand(section_id, 0.5)
        result = cmd.execute(song)
        assert result.tracks[0].notes[0].velocity > song.tracks[0].notes[0].velocity

    def test_decrease_energy_command(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        cmd = DecreaseEnergyCommand(section_id, 0.5)
        result = cmd.execute(song)
        assert result.tracks[0].notes[0].velocity < song.tracks[0].notes[0].velocity

    def test_add_layer_command(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        cmd = AddLayerCommand(section_id, "strings")
        result = cmd.execute(song)
        assert len(result.tracks) > len(song.tracks)

    def test_build_up_command(self):
        song = _make_full_song()
        cmd = BuildUpCommand(16.0, 4.0)
        result = cmd.execute(song)
        assert len(result.tracks[1].notes) > len(song.tracks[1].notes)

    def test_break_down_command(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        cmd = BreakDownCommand(section_id)
        result = cmd.execute(song)
        assert result is not None

    def test_add_silence_command(self):
        song = _make_full_song()
        section_id = song.sections[0].id
        cmd = AddSilenceCommand(section_id)
        result = cmd.execute(song)
        for track in result.tracks:
            notes_in_section = [n for n in track.notes if 0 <= n.start_beat < 16]
            assert len(notes_in_section) == 0

    def test_add_transition_command(self):
        song = _make_full_song()
        # Add drums notes so transition has something to work with
        s1 = song.sections[0].id
        s2 = song.sections[1].id
        cmd = AddTransitionCommand(s1, s2)
        result = cmd.execute(song)
        assert result is not None


# ──── Track Advanced Command tests ────

class TestTrackAdvancedCommands:
    def test_set_track_octave(self):
        song = _make_full_song()
        track_id = song.tracks[0].id
        cmd = SetTrackOctaveCommand(track_id, 2)
        result = cmd.execute(song)
        t = next(t for t in result.tracks if t.id == track_id)
        assert t.octave_offset == 2

    def test_set_track_octave_clamp(self):
        song = _make_full_song()
        track_id = song.tracks[0].id
        cmd = SetTrackOctaveCommand(track_id, 5)  # Should clamp to 3
        result = cmd.execute(song)
        t = next(t for t in result.tracks if t.id == track_id)
        assert t.octave_offset == 3

    def test_set_track_density(self):
        song = _make_full_song()
        track_id = song.tracks[0].id
        cmd = SetTrackDensityCommand(track_id, 0.8)
        result = cmd.execute(song)
        t = next(t for t in result.tracks if t.id == track_id)
        assert t.density == 0.8

    def test_set_track_energy(self):
        song = _make_full_song()
        track_id = song.tracks[0].id
        cmd = SetTrackEnergyCommand(track_id, 0.9)
        result = cmd.execute(song)
        t = next(t for t in result.tracks if t.id == track_id)
        assert t.energy == 0.9

    def test_set_track_density_clamp(self):
        song = _make_full_song()
        track_id = song.tracks[0].id
        cmd = SetTrackDensityCommand(track_id, 1.5)  # Should clamp to 1.0
        result = cmd.execute(song)
        t = next(t for t in result.tracks if t.id == track_id)
        assert t.density == 1.0
