"""Tests for DrumsGenerator and drums commands.

Phase 4: REQUIREMENTS.md 4.4 / TECHNICAL.md 5.11.
"""

import pytest

from composer_engine.generators.drums_generator import DrumsGenerator, DRUM_TEMPLATES
from composer_engine.commands.drums_commands import (
    AddCrashCommand,
    AddDrumFillCommand,
    AddGhostNotesCommand,
    AddPercussionCommand,
    AddTomFillCommand,
    ClearDrumElementCommand,
    GenerateDrumsCommand,
    RegenerateDrumsCommand,
    SetDrumStyleCommand,
    SetHiHatPatternCommand,
    SetKickPatternCommand,
    SetRidePatternCommand,
    SetSnarePatternCommand,
)
from composer_engine.models.enums import (
    DrumStyle,
    GM_PERCUSSION,
    HiHatPattern,
    InstrumentType,
    KickPattern,
    SnarePattern,
)
from composer_engine.models.note import Note
from composer_engine.models.song import Song
from composer_engine.models.track import Track


def _make_song() -> Song:
    song = Song(name="Test Drums")
    return song


# ──── DrumsGenerator tests ────

class TestDrumsGenerator:
    def setup_method(self):
        self.gen = DrumsGenerator()

    def test_generate_rock(self):
        notes = self.gen.generate(DrumStyle.ROCK, 0, 16)
        assert len(notes) > 0
        pitches = {n.pitch for n in notes}
        assert GM_PERCUSSION["KICK"] in pitches
        assert GM_PERCUSSION["SNARE"] in pitches

    def test_generate_all_styles(self):
        for style in DrumStyle:
            notes = self.gen.generate(style, 0, 8)
            assert len(notes) > 0, f"Style {style.value} produced no notes"

    def test_generate_empty_range(self):
        notes = self.gen.generate(DrumStyle.ROCK, 0, 0)
        assert notes == []

    def test_set_style(self):
        notes = self.gen.generate(DrumStyle.ROCK, 0, 8)
        new_notes = self.gen.set_style(notes, DrumStyle.JAZZ, 0, 8)
        assert len(new_notes) > 0

    def test_add_fill(self):
        notes = self.gen.generate(DrumStyle.ROCK, 0, 8)
        count_before = len(notes)
        notes = self.gen.add_fill(notes, 7.0, "basic")
        # Fill should add notes + crash
        assert len(notes) > count_before - 5  # some removed, some added

    def test_add_ghost_notes(self):
        notes = self.gen.generate(DrumStyle.ROCK, 0, 8)
        count_before = len(notes)
        notes = self.gen.add_ghost_notes(notes, 0, 8, density=0.5)
        assert len(notes) >= count_before  # should add some ghost notes

    def test_set_hihat_eighths(self):
        notes = self.gen.generate(DrumStyle.ROCK, 0, 8)
        notes = self.gen.set_hihat_pattern(notes, HiHatPattern.SIXTEENTHS, 0, 8)
        hh_notes = [n for n in notes if n.pitch == GM_PERCUSSION["CLOSED_HH"]]
        assert len(hh_notes) > 0

    def test_set_kick_four_on_floor(self):
        notes = self.gen.generate(DrumStyle.ROCK, 0, 8)
        notes = self.gen.set_kick_pattern(notes, KickPattern.FOUR_ON_FLOOR, 0, 8)
        kick_notes = [n for n in notes if n.pitch == GM_PERCUSSION["KICK"]]
        assert len(kick_notes) >= 8  # one per beat for 2 bars

    def test_set_snare_rimshot(self):
        notes = self.gen.generate(DrumStyle.ROCK, 0, 8)
        notes = self.gen.set_snare_pattern(notes, SnarePattern.RIMSHOT, 0, 8)
        rim_notes = [n for n in notes if n.pitch == GM_PERCUSSION["SIDE_STICK"]]
        assert len(rim_notes) >= 2

    def test_add_crash(self):
        notes = []
        notes = self.gen.add_crash(notes, 0.0)
        assert len(notes) == 1
        assert notes[0].pitch == GM_PERCUSSION["CRASH_1"]

    def test_set_ride_pattern(self):
        notes = self.gen.set_ride_pattern([], 0, 4, swing=True)
        ride_notes = [n for n in notes if n.pitch == GM_PERCUSSION["RIDE"]]
        assert len(ride_notes) > 0

    def test_add_tom_fill(self):
        notes = self.gen.add_tom_fill([], 0, 1.0)
        assert len(notes) == 4
        toms = {GM_PERCUSSION["HIGH_TOM"], GM_PERCUSSION["MID_TOM"],
                GM_PERCUSSION["LOW_TOM"], GM_PERCUSSION["FLOOR_TOM"]}
        assert {n.pitch for n in notes} == toms

    def test_add_percussion_tambourine(self):
        notes = self.gen.add_percussion([], "tambourine", 0, 4, "quarter")
        assert len(notes) == 4
        assert all(n.pitch == GM_PERCUSSION["TAMBOURINE"] for n in notes)

    def test_clear_element(self):
        notes = self.gen.generate(DrumStyle.ROCK, 0, 8)
        hihat_before = len([n for n in notes if n.pitch in {42, 44, 46}])
        notes = self.gen.clear_element(notes, "hihat", 0, 8)
        hihat_after = len([n for n in notes if n.pitch in {42, 44, 46}])
        assert hihat_after == 0
        assert hihat_before > 0

    def test_templates_exist(self):
        for style in DrumStyle:
            assert style.value in DRUM_TEMPLATES


# ──── Drums Command tests ────

class TestDrumsCommands:
    def test_generate_drums_command(self):
        song = _make_song()
        cmd = GenerateDrumsCommand(style="rock")
        result = cmd.execute(song)
        drums_tracks = [t for t in result.tracks if t.instrument == InstrumentType.DRUMS]
        assert len(drums_tracks) >= 1
        assert len(drums_tracks[0].notes) > 0

    def test_regenerate_drums_command(self):
        song = _make_song()
        track = Track.create("Drums", InstrumentType.DRUMS)
        track.notes = [Note(pitch=36, start_beat=0, duration_beat=0.5, velocity=100)]
        song.tracks.append(track)
        cmd = RegenerateDrumsCommand(track.id, style="jazz")
        result = cmd.execute(song)
        drums_track = next(t for t in result.tracks if t.id == track.id)
        assert len(drums_track.notes) >= 1

    def test_set_drum_style_command(self):
        song = _make_song()
        track = Track.create("Drums", InstrumentType.DRUMS)
        song.tracks.append(track)
        cmd = SetDrumStyleCommand(track.id, "pop")
        result = cmd.execute(song)
        drums_track = next(t for t in result.tracks if t.id == track.id)
        assert len(drums_track.notes) > 0

    def test_add_drum_fill_command(self):
        song = _make_song()
        track = Track.create("Drums", InstrumentType.DRUMS)
        song.tracks.append(track)
        cmd = AddDrumFillCommand(track.id, 3.0, "basic")
        result = cmd.execute(song)
        drums_track = next(t for t in result.tracks if t.id == track.id)
        assert len(drums_track.notes) > 0

    def test_add_ghost_notes_command(self):
        song = _make_song()
        track = Track.create("Drums", InstrumentType.DRUMS)
        track.notes = [Note(pitch=38, start_beat=1.0, duration_beat=0.5, velocity=100)]
        song.tracks.append(track)
        cmd = AddGhostNotesCommand(track.id, density=0.5)
        result = cmd.execute(song)
        drums_track = next(t for t in result.tracks if t.id == track.id)
        assert len(drums_track.notes) >= 1

    def test_set_hihat_command(self):
        song = _make_song()
        track = Track.create("Drums", InstrumentType.DRUMS)
        song.tracks.append(track)
        cmd = SetHiHatPatternCommand(track.id, "eighths")
        result = cmd.execute(song)
        drums_track = next(t for t in result.tracks if t.id == track.id)
        assert len(drums_track.notes) > 0

    def test_add_crash_command(self):
        song = _make_song()
        track = Track.create("Drums", InstrumentType.DRUMS)
        song.tracks.append(track)
        cmd = AddCrashCommand(track.id, 0.0)
        result = cmd.execute(song)
        drums_track = next(t for t in result.tracks if t.id == track.id)
        crash_notes = [n for n in drums_track.notes if n.pitch == GM_PERCUSSION["CRASH_1"]]
        assert len(crash_notes) == 1

    def test_add_tom_fill_command(self):
        song = _make_song()
        track = Track.create("Drums", InstrumentType.DRUMS)
        song.tracks.append(track)
        cmd = AddTomFillCommand(track.id, 0.0, 1.0)
        result = cmd.execute(song)
        drums_track = next(t for t in result.tracks if t.id == track.id)
        assert len(drums_track.notes) == 4

    def test_add_percussion_command(self):
        song = _make_song()
        track = Track.create("Drums", InstrumentType.DRUMS)
        song.tracks.append(track)
        cmd = AddPercussionCommand(track.id, "cowbell", pattern="quarter")
        result = cmd.execute(song)
        drums_track = next(t for t in result.tracks if t.id == track.id)
        cowbell_notes = [n for n in drums_track.notes if n.pitch == GM_PERCUSSION["COWBELL"]]
        assert len(cowbell_notes) > 0

    def test_clear_drum_element_command(self):
        song = _make_song()
        track = Track.create("Drums", InstrumentType.DRUMS)
        track.notes = [
            Note(pitch=36, start_beat=0, duration_beat=0.5, velocity=100),
            Note(pitch=42, start_beat=0, duration_beat=0.5, velocity=80),
        ]
        song.tracks.append(track)
        cmd = ClearDrumElementCommand(track.id, "hihat")
        result = cmd.execute(song)
        drums_track = next(t for t in result.tracks if t.id == track.id)
        hh = [n for n in drums_track.notes if n.pitch in {42, 44, 46}]
        assert len(hh) == 0
        assert len(drums_track.notes) == 1  # kick remains
