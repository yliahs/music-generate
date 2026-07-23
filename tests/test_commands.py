"""Tests for all Commands."""

from composer_engine.commands.global_commands import (
    SetGlobalEnergyCommand,
    SetKeyCommand,
    SetMasterHumanizeCommand,
    SetMasterTimingCommand,
    SetMasterVelocityCommand,
    SetModeCommand,
    SetScaleCommand,
    SetTempoCommand,
    SetTimeSignatureCommand,
)
from composer_engine.commands.section_commands import (
    AddSectionCommand,
    DuplicateSectionCommand,
    MergeSectionsCommand,
    MoveSectionCommand,
    RemoveSectionCommand,
    ResizeSectionCommand,
    SetSectionRepeatCommand,
    SplitSectionCommand,
    SwapSectionsCommand,
)
from composer_engine.commands.track_commands import (
    AddNotesCommand,
    AddTrackCommand,
    MuteTrackCommand,
    RemoveTrackCommand,
    SetTrackComplexityCommand,
    SetTrackGrooveCommand,
    SetTrackHumanizeCommand,
    SetTrackPanCommand,
    SetTrackRangeCommand,
    SetTrackRegisterCommand,
    SetTrackRhythmCommand,
    SetTrackTimingOffsetCommand,
    SetTrackVelocityOffsetCommand,
    SetTrackVolumeCommand,
    SoloTrackCommand,
)
from composer_engine.commands.song_commands import (
    CloneSongCommand,
    CreateSongCommand,
    DeleteSongCommand,
)
from composer_engine.models import (
    InstrumentType,
    Key,
    Mode,
    Note,
    SectionType,
    Song,
    Stage,
)


def _make_song() -> Song:
    return CreateSongCommand(name="Test", tempo=120, key=Key.C).execute(None)


class TestSongCommands:
    def test_create(self):
        song = CreateSongCommand(name="My Song", tempo=140, key=Key.D).execute(None)
        assert song.name == "My Song"
        assert song.global_settings.tempo == 140
        assert song.stage == Stage.INSPIRATION

    def test_delete(self):
        song = _make_song()
        result = DeleteSongCommand().execute(song)
        assert result.name == ""

    def test_clone(self):
        song = _make_song()
        cloned = CloneSongCommand("Clone").execute(song)
        assert cloned.name == "Clone"
        assert cloned.id != song.id


class TestTrackCommands:
    def test_add_track(self):
        song = _make_song()
        song = AddTrackCommand("Piano", InstrumentType.PIANO).execute(song)
        assert len(song.tracks) == 1
        assert song.tracks[0].name == "Piano"

    def test_remove_track(self):
        song = _make_song()
        song = AddTrackCommand("Piano", InstrumentType.PIANO).execute(song)
        track_id = song.tracks[0].id
        song = RemoveTrackCommand(track_id).execute(song)
        assert len(song.tracks) == 0

    def test_mute_solo(self):
        song = _make_song()
        song = AddTrackCommand("Piano", InstrumentType.PIANO).execute(song)
        tid = song.tracks[0].id
        song = MuteTrackCommand(tid, True).execute(song)
        assert song.tracks[0].mute is True
        song = SoloTrackCommand(tid, True).execute(song)
        assert song.tracks[0].solo is True

    def test_volume_pan(self):
        song = _make_song()
        song = AddTrackCommand("Bass", InstrumentType.BASS).execute(song)
        tid = song.tracks[0].id
        song = SetTrackVolumeCommand(tid, 80).execute(song)
        assert song.tracks[0].volume == 80
        song = SetTrackPanCommand(tid, 32).execute(song)
        assert song.tracks[0].pan == 32

    def test_add_notes(self):
        song = _make_song()
        song = AddTrackCommand("Piano", InstrumentType.PIANO).execute(song)
        tid = song.tracks[0].id
        notes = [Note(pitch=60, start_beat=0, duration_beat=1)]
        song = AddNotesCommand(tid, notes).execute(song)
        assert len(song.tracks[0].notes) == 1
        assert song.tracks[0].notes[0].pitch == 60


class TestSectionCommands:
    def test_add_section(self):
        song = _make_song()
        song = AddSectionCommand(SectionType.VERSE, 0.0, 16.0).execute(song)
        assert len(song.sections) == 1

    def test_remove_section(self):
        song = _make_song()
        song = AddSectionCommand(SectionType.CHORUS, 16.0, 16.0).execute(song)
        sid = song.sections[0].id
        song = RemoveSectionCommand(sid).execute(song)
        assert len(song.sections) == 0

    def test_duplicate_section(self):
        song = _make_song()
        song = AddSectionCommand(SectionType.VERSE, 0.0, 16.0).execute(song)
        sid = song.sections[0].id
        song = DuplicateSectionCommand(sid).execute(song)
        assert len(song.sections) == 2
        assert song.sections[1].start_beat == 16.0

    def test_move_section(self):
        song = _make_song()
        song = AddSectionCommand(SectionType.VERSE, 0.0, 16.0).execute(song)
        sid = song.sections[0].id
        song = MoveSectionCommand(sid, 32.0).execute(song)
        assert song.sections[0].start_beat == 32.0

    def test_resize_section(self):
        song = _make_song()
        song = AddSectionCommand(SectionType.CHORUS, 0.0, 16.0).execute(song)
        sid = song.sections[0].id
        song = ResizeSectionCommand(sid, 32.0).execute(song)
        assert song.sections[0].length_beats == 32.0

    def test_set_section_repeat(self):
        song = _make_song()
        song = AddSectionCommand(SectionType.VERSE, 0.0, 16.0).execute(song)
        sid = song.sections[0].id
        assert song.sections[0].repeat == 1
        song = SetSectionRepeatCommand(sid, 4).execute(song)
        assert song.sections[0].repeat == 4

    def test_set_section_repeat_clamps_min(self):
        song = _make_song()
        song = AddSectionCommand(SectionType.VERSE, 0.0, 16.0).execute(song)
        sid = song.sections[0].id
        song = SetSectionRepeatCommand(sid, 0).execute(song)
        assert song.sections[0].repeat == 1


class TestGlobalCommands:
    def test_set_tempo(self):
        song = _make_song()
        song = SetTempoCommand(180).execute(song)
        assert song.global_settings.tempo == 180

    def test_set_key(self):
        song = _make_song()
        song = SetKeyCommand(Key.Bb).execute(song)
        assert song.global_settings.key == Key.Bb

    def test_set_mode(self):
        song = _make_song()
        song = SetModeCommand(Mode.DORIAN).execute(song)
        assert song.global_settings.mode == Mode.DORIAN

    def test_set_time_signature(self):
        song = _make_song()
        song = SetTimeSignatureCommand(3, 4).execute(song)
        assert song.global_settings.time_signature == (3, 4)

    def test_set_master_velocity(self):
        song = _make_song()
        assert song.global_settings.master_velocity == 100
        song = SetMasterVelocityCommand(80).execute(song)
        assert song.global_settings.master_velocity == 80

    def test_set_master_velocity_clamps(self):
        song = _make_song()
        song = SetMasterVelocityCommand(200).execute(song)
        assert song.global_settings.master_velocity == 127
        song = SetMasterVelocityCommand(-10).execute(song)
        assert song.global_settings.master_velocity == 0

    def test_set_master_humanize(self):
        song = _make_song()
        assert song.global_settings.master_humanize == 0.0
        song = SetMasterHumanizeCommand(0.7).execute(song)
        assert song.global_settings.master_humanize == 0.7

    def test_set_master_humanize_clamps(self):
        song = _make_song()
        song = SetMasterHumanizeCommand(2.0).execute(song)
        assert song.global_settings.master_humanize == 1.0
        song = SetMasterHumanizeCommand(-0.5).execute(song)
        assert song.global_settings.master_humanize == 0.0

    def test_set_scale(self):
        song = _make_song()
        assert song.global_settings.scale is None
        song = SetScaleCommand("C major pentatonic").execute(song)
        assert song.global_settings.scale == "C major pentatonic"
        song = SetScaleCommand(None).execute(song)
        assert song.global_settings.scale is None

    def test_set_master_timing(self):
        song = _make_song()
        song = SetMasterTimingCommand(0.05).execute(song)
        assert song.global_settings.master_timing == 0.05
        song = SetMasterTimingCommand(-0.1).execute(song)
        assert song.global_settings.master_timing == -0.1

    def test_set_global_energy(self):
        song = _make_song()
        assert song.global_settings.global_energy == 0.5
        song = SetGlobalEnergyCommand(0.8).execute(song)
        assert song.global_settings.global_energy == 0.8

    def test_set_global_energy_clamps(self):
        song = _make_song()
        song = SetGlobalEnergyCommand(2.0).execute(song)
        assert song.global_settings.global_energy == 1.0
        song = SetGlobalEnergyCommand(-1.0).execute(song)
        assert song.global_settings.global_energy == 0.0


class TestPhase12SectionCommands:
    def test_swap_sections(self):
        song = _make_song()
        song = AddSectionCommand(SectionType.VERSE, 0.0, 16.0).execute(song)
        song = AddSectionCommand(SectionType.CHORUS, 16.0, 16.0).execute(song)
        a_id = song.sections[0].id
        b_id = song.sections[1].id
        song = SwapSectionsCommand(a_id, b_id).execute(song)
        assert song.sections[0].start_beat == 16.0
        assert song.sections[1].start_beat == 0.0

    def test_split_section(self):
        song = _make_song()
        song = AddSectionCommand(SectionType.VERSE, 0.0, 16.0).execute(song)
        sid = song.sections[0].id
        song = SplitSectionCommand(sid, 8.0).execute(song)
        assert len(song.sections) == 2
        assert song.sections[0].length_beats == 8.0
        assert song.sections[1].start_beat == 8.0
        assert song.sections[1].length_beats == 8.0

    def test_split_section_invalid_beat(self):
        song = _make_song()
        song = AddSectionCommand(SectionType.VERSE, 0.0, 16.0).execute(song)
        sid = song.sections[0].id
        song = SplitSectionCommand(sid, 0.0).execute(song)
        assert len(song.sections) == 1

    def test_merge_sections(self):
        song = _make_song()
        song = AddSectionCommand(SectionType.VERSE, 0.0, 16.0).execute(song)
        song = AddSectionCommand(SectionType.CHORUS, 16.0, 16.0).execute(song)
        a_id = song.sections[0].id
        b_id = song.sections[1].id
        song = MergeSectionsCommand(a_id, b_id).execute(song)
        assert len(song.sections) == 1
        assert song.sections[0].length_beats == 32.0
        assert song.sections[0].start_beat == 0.0


class TestPhase12TrackCommands:
    def _song_with_track(self):
        song = _make_song()
        song = AddTrackCommand("Piano", InstrumentType.PIANO).execute(song)
        return song, song.tracks[0].id

    def test_set_track_register(self):
        song, tid = self._song_with_track()
        assert song.tracks[0].track_register == "mid"
        song = SetTrackRegisterCommand(tid, "high").execute(song)
        assert song.tracks[0].track_register == "high"

    def test_set_track_register_invalid(self):
        song, tid = self._song_with_track()
        song = SetTrackRegisterCommand(tid, "ultra").execute(song)
        assert song.tracks[0].track_register == "mid"

    def test_set_track_complexity(self):
        song, tid = self._song_with_track()
        song = SetTrackComplexityCommand(tid, 0.9).execute(song)
        assert song.tracks[0].complexity == 0.9

    def test_set_track_complexity_clamps(self):
        song, tid = self._song_with_track()
        song = SetTrackComplexityCommand(tid, 2.0).execute(song)
        assert song.tracks[0].complexity == 1.0

    def test_set_track_velocity_offset(self):
        song, tid = self._song_with_track()
        song = SetTrackVelocityOffsetCommand(tid, 20).execute(song)
        assert song.tracks[0].velocity_offset == 20

    def test_set_track_velocity_offset_clamps(self):
        song, tid = self._song_with_track()
        song = SetTrackVelocityOffsetCommand(tid, 200).execute(song)
        assert song.tracks[0].velocity_offset == 127
        song = SetTrackVelocityOffsetCommand(tid, -200).execute(song)
        assert song.tracks[0].velocity_offset == -127

    def test_set_track_timing_offset(self):
        song, tid = self._song_with_track()
        song = SetTrackTimingOffsetCommand(tid, 0.1).execute(song)
        assert song.tracks[0].timing_offset == 0.1

    def test_set_track_humanize(self):
        song, tid = self._song_with_track()
        song = SetTrackHumanizeCommand(tid, 0.6).execute(song)
        assert song.tracks[0].humanize == 0.6

    def test_set_track_groove(self):
        song, tid = self._song_with_track()
        song = SetTrackGrooveCommand(tid, "funk").execute(song)
        assert song.tracks[0].groove == "funk"

    def test_set_track_rhythm(self):
        song, tid = self._song_with_track()
        song = SetTrackRhythmCommand(tid, "swing-8th").execute(song)
        assert song.tracks[0].rhythm_pattern == "swing-8th"

    def test_set_track_range(self):
        song, tid = self._song_with_track()
        song = SetTrackRangeCommand(tid, 48, 84).execute(song)
        assert song.tracks[0].pitch_range_low == 48
        assert song.tracks[0].pitch_range_high == 84

    def test_set_track_range_clamps(self):
        song, tid = self._song_with_track()
        song = SetTrackRangeCommand(tid, -10, 200).execute(song)
        assert song.tracks[0].pitch_range_low == 0
        assert song.tracks[0].pitch_range_high == 127
