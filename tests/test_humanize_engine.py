"""Tests for HumanizeEngine and humanize commands.

Phase 6: REQUIREMENTS.md 4.6 / TECHNICAL.md 5.13.
"""

import random
from copy import deepcopy

import pytest

from composer_engine.commands.humanize_commands import (
    ApplyGrooveCommand,
    ApplyMicroTimingCommand,
    ApplySwingCommand,
    HandPlayedFeelCommand,
    HumanizeTimingCommand,
    HumanizeVelocityCommand,
    PullTimingCommand,
    PushTimingCommand,
)
from composer_engine.generators.humanize_engine import GROOVE_TEMPLATES, HumanizeEngine
from composer_engine.models.enums import InstrumentType, SectionType
from composer_engine.models.note import Note
from composer_engine.models.section import Section
from composer_engine.models.song import Song
from composer_engine.models.track import Track


def _make_song_with_notes() -> Song:
    song = Song(name="Humanize Test")
    song.sections = [
        Section(type=SectionType.VERSE, start_beat=0, length_beats=8),
        Section(type=SectionType.CHORUS, start_beat=8, length_beats=8),
    ]
    track = Track.create("Piano", InstrumentType.PIANO)
    track.notes = [
        Note(pitch=60, start_beat=0.0, duration_beat=1.0, velocity=80),
        Note(pitch=62, start_beat=0.5, duration_beat=0.5, velocity=90),
        Note(pitch=64, start_beat=1.0, duration_beat=1.0, velocity=70),
        Note(pitch=65, start_beat=1.5, duration_beat=0.5, velocity=85),
        Note(pitch=67, start_beat=2.0, duration_beat=1.0, velocity=75),
        Note(pitch=69, start_beat=8.0, duration_beat=1.0, velocity=80),
    ]
    song.tracks.append(track)
    return song


def _copy_notes(notes: list[Note]) -> list[Note]:
    return [n.model_copy(deep=True) for n in notes]


class TestHumanizeEngine:
    def setup_method(self):
        self.engine = HumanizeEngine()
        random.seed(42)

    def test_humanize_timing_modifies_notes(self):
        notes = _copy_notes([Note(pitch=60, start_beat=2.0, duration_beat=1.0, velocity=80)])
        original = notes[0].start_beat
        self.engine.humanize_timing(notes, amount=1.0)
        assert notes[0].start_beat != original

    def test_humanize_timing_clamps_start_beat(self):
        notes = _copy_notes([Note(pitch=60, start_beat=0.01, duration_beat=1.0, velocity=80)])
        random.seed(0)
        self.engine.humanize_timing(notes, amount=1.0)
        assert notes[0].start_beat >= 0

    def test_humanize_velocity_modifies_and_clamps(self):
        notes = _copy_notes([Note(pitch=60, start_beat=0.0, duration_beat=1.0, velocity=120)])
        random.seed(1)
        self.engine.humanize_velocity(notes, amount=1.0)
        assert 1 <= notes[0].velocity <= 127

    def test_humanize_velocity_low_clamp(self):
        notes = _copy_notes([Note(pitch=60, start_beat=0.0, duration_beat=1.0, velocity=5)])
        random.seed(2)
        self.engine.humanize_velocity(notes, amount=1.0)
        assert notes[0].velocity >= 1

    def test_apply_micro_timing(self):
        notes = _copy_notes([
            Note(pitch=60, start_beat=1.0, duration_beat=1.0, velocity=80),
            Note(pitch=62, start_beat=3.0, duration_beat=1.0, velocity=80),
        ])
        self.engine.apply_micro_timing(notes, {1.0: 0.05, 3.0: -0.03})
        assert notes[0].start_beat == pytest.approx(1.05)
        assert notes[1].start_beat == pytest.approx(2.97)

    def test_groove_templates_exist(self):
        expected = {
            "straight", "swing_light", "swing_heavy", "funk", "bossa",
            "shuffle", "human_piano", "human_guitar", "human_drums", "laid_back",
        }
        assert expected == set(GROOVE_TEMPLATES.keys())

    def test_apply_groove_straight_no_change(self):
        notes = _copy_notes([Note(pitch=60, start_beat=0.25, duration_beat=1.0, velocity=80)])
        original_beat = notes[0].start_beat
        original_vel = notes[0].velocity
        self.engine.apply_groove(notes, "straight")
        assert notes[0].start_beat == original_beat
        assert notes[0].velocity == original_vel

    def test_apply_groove_funk_modifies(self):
        notes = _copy_notes([Note(pitch=60, start_beat=0.25, duration_beat=1.0, velocity=80)])
        self.engine.apply_groove(notes, "funk")
        assert notes[0].start_beat != 0.25 or notes[0].velocity != 80

    def test_apply_groove_laid_back(self):
        notes = _copy_notes([Note(pitch=60, start_beat=1.0, duration_beat=1.0, velocity=80)])
        self.engine.apply_groove(notes, "laid_back")
        assert notes[0].start_beat == pytest.approx(1.03)
        assert notes[0].velocity == 75

    def test_apply_groove_human_piano_random(self):
        random.seed(10)
        notes = _copy_notes([Note(pitch=60, start_beat=1.0, duration_beat=1.0, velocity=80)])
        self.engine.apply_groove(notes, "human_piano")
        assert notes[0].start_beat != 1.0 or notes[0].velocity != 80

    def test_apply_swing_delays_even_eighths(self):
        notes = _copy_notes([
            Note(pitch=60, start_beat=0.0, duration_beat=0.5, velocity=80),
            Note(pitch=62, start_beat=0.5, duration_beat=0.5, velocity=80),
            Note(pitch=64, start_beat=1.0, duration_beat=0.5, velocity=80),
            Note(pitch=65, start_beat=1.5, duration_beat=0.5, velocity=80),
        ])
        self.engine.apply_swing(notes, swing_amount=1.0)
        assert notes[0].start_beat == 0.0
        assert notes[1].start_beat == pytest.approx(0.6)
        assert notes[2].start_beat == 1.0
        assert notes[3].start_beat == pytest.approx(1.6)

    def test_push_timing(self):
        notes = _copy_notes([Note(pitch=60, start_beat=2.0, duration_beat=1.0, velocity=80)])
        self.engine.push_timing(notes, amount=1.0)
        assert notes[0].start_beat < 2.0
        assert notes[0].start_beat >= 0

    def test_pull_timing(self):
        notes = _copy_notes([Note(pitch=60, start_beat=2.0, duration_beat=1.0, velocity=80)])
        self.engine.pull_timing(notes, amount=1.0)
        assert notes[0].start_beat > 2.0

    def test_hand_played_feel(self):
        random.seed(5)
        notes = _copy_notes([
            Note(pitch=60, start_beat=1.0, duration_beat=1.0, velocity=80),
        ])
        orig_beat = notes[0].start_beat
        orig_vel = notes[0].velocity
        orig_dur = notes[0].duration_beat
        self.engine.hand_played_feel(notes, intensity=1.0)
        changed = (
            notes[0].start_beat != orig_beat
            or notes[0].velocity != orig_vel
            or notes[0].duration_beat != orig_dur
        )
        assert changed
        assert notes[0].start_beat >= 0
        assert 1 <= notes[0].velocity <= 127
        assert notes[0].duration_beat > 0

    def test_empty_notes_list(self):
        notes: list[Note] = []
        assert self.engine.humanize_timing(notes) == []
        assert self.engine.humanize_velocity(notes) == []
        assert self.engine.apply_groove(notes, "funk") == []
        assert self.engine.apply_swing(notes, 0.5) == []
        assert self.engine.push_timing(notes, 0.5) == []
        assert self.engine.pull_timing(notes, 0.5) == []
        assert self.engine.hand_played_feel(notes, 0.5) == []


class TestHumanizeCommands:
    def setup_method(self):
        random.seed(42)
        self.song = _make_song_with_notes()

    def test_humanize_timing_command(self):
        track_id = self.song.tracks[0].id
        orig = self.song.tracks[0].notes[0].start_beat
        song = HumanizeTimingCommand(track_id, amount=1.0).execute(self.song)
        assert song.tracks[0].notes[0].start_beat != orig

    def test_humanize_velocity_command(self):
        track_id = self.song.tracks[0].id
        song = HumanizeVelocityCommand(track_id, amount=1.0).execute(self.song)
        assert 1 <= song.tracks[0].notes[0].velocity <= 127

    def test_apply_micro_timing_command(self):
        track_id = self.song.tracks[0].id
        song = ApplyMicroTimingCommand(track_id, {1.0: 0.05}).execute(self.song)
        note_at_1 = next(n for n in song.tracks[0].notes if n.start_beat == pytest.approx(1.05))
        assert note_at_1 is not None

    def test_apply_groove_command_section_scope(self):
        track_id = self.song.tracks[0].id
        section_id = self.song.sections[0].id
        orig_chorus_vel = deepcopy(self.song.tracks[0].notes[-1].velocity)
        song = ApplyGrooveCommand(track_id, "laid_back", section_id).execute(self.song)
        verse_notes = [n for n in song.tracks[0].notes if n.start_beat < 8]
        chorus_note = song.tracks[0].notes[-1]
        assert verse_notes[0].velocity == 75
        assert chorus_note.velocity == orig_chorus_vel

    def test_apply_swing_all_tracks(self):
        song = ApplySwingCommand(swing_amount=1.0).execute(self.song)
        note_at_half = next(n for n in song.tracks[0].notes if n.start_beat == pytest.approx(0.6))
        assert note_at_half.pitch == 62

    def test_push_timing_command(self):
        track_id = self.song.tracks[0].id
        orig = self.song.tracks[0].notes[2].start_beat
        song = PushTimingCommand(track_id, amount=1.0).execute(self.song)
        assert song.tracks[0].notes[2].start_beat < orig

    def test_pull_timing_command(self):
        track_id = self.song.tracks[0].id
        orig = self.song.tracks[0].notes[2].start_beat
        song = PullTimingCommand(track_id, amount=1.0).execute(self.song)
        assert song.tracks[0].notes[2].start_beat > orig

    def test_hand_played_feel_command(self):
        track_id = self.song.tracks[0].id
        song = HandPlayedFeelCommand(track_id, intensity=1.0).execute(self.song)
        assert song.tracks[0].notes[0].start_beat >= 0
        assert 1 <= song.tracks[0].notes[0].velocity <= 127

    def test_command_track_not_found(self):
        with pytest.raises(ValueError, match="Track not found"):
            HumanizeTimingCommand("bad-id").execute(self.song)
