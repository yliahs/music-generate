"""Tests for automation engine, commands, and markers (Phase 8)."""

import pytest

from composer_engine.commands.automation_commands import (
    AddAutomationCommand,
    AddMarkerCommand,
    ApplyAutomationPresetCommand,
    ClearAutomationCommand,
    RemoveAutomationCommand,
    RemoveMarkerCommand,
)
from composer_engine.commands.song_commands import CreateSongCommand
from composer_engine.commands.track_commands import AddTrackCommand
from composer_engine.engine.composer import Composer
from composer_engine.generators.automation_engine import AUTOMATION_PRESETS, AutomationEngine
from composer_engine.models.automation import AutomationCurve, AutomationPoint, Marker
from composer_engine.models.enums import AutomationParam, InstrumentType
from composer_engine.models.song import Song
from composer_engine.models.track import Track


def _make_song_with_track() -> tuple[Song, Track]:
    song = Song(name="Automation Test")
    track = Track.create("Piano", InstrumentType.PIANO, volume=100)
    song.tracks.append(track)
    return song, track


class TestAutomationModels:
    def test_automation_point_model(self):
        pt = AutomationPoint(beat=4.0, value=64)
        assert pt.beat == 4.0
        assert pt.value == 64

    def test_automation_curve_interpolation(self):
        curve = AutomationCurve(
            param=AutomationParam.VOLUME,
            points=[
                AutomationPoint(beat=0.0, value=0),
                AutomationPoint(beat=4.0, value=100),
                AutomationPoint(beat=8.0, value=50),
            ],
        )
        assert curve.get_value_at(-1.0) == 0
        assert curve.get_value_at(0.0) == 0
        assert curve.get_value_at(2.0) == 50
        assert curve.get_value_at(4.0) == 100
        assert curve.get_value_at(6.0) == 75
        assert curve.get_value_at(8.0) == 50
        assert curve.get_value_at(10.0) == 50

    def test_automation_curve_empty(self):
        curve = AutomationCurve(param=AutomationParam.PAN)
        assert curve.get_value_at(0.0) is None


class TestAutomationEngine:
    def setup_method(self):
        self.engine = AutomationEngine()
        self.song, self.track = _make_song_with_track()

    def test_automation_engine_add_remove(self):
        self.engine.add_automation(
            self.track, AutomationParam.VOLUME, [(0.0, 20), (8.0, 120)]
        )
        assert len(self.track.automation) == 1
        assert self.track.automation[0].param == AutomationParam.VOLUME
        assert len(self.track.automation[0].points) == 2

        self.engine.remove_automation(self.track, AutomationParam.VOLUME)
        assert self.track.automation == []

    def test_automation_engine_add_point(self):
        self.engine.add_point(self.track, AutomationParam.EXPRESSION, 4.0, 80)
        self.engine.add_point(self.track, AutomationParam.EXPRESSION, 0.0, 40)
        self.engine.add_point(self.track, AutomationParam.EXPRESSION, 2.0, 60)

        curve = self.track.automation[0]
        assert len(curve.points) == 3
        assert [p.beat for p in curve.points] == [0.0, 2.0, 4.0]

    def test_automation_engine_remove_point(self):
        self.engine.add_automation(
            self.track, AutomationParam.PAN, [(0.0, 0), (4.0, 64), (8.0, 127)]
        )
        self.engine.remove_point(self.track, AutomationParam.PAN, 1)
        assert len(self.track.automation[0].points) == 2
        assert self.track.automation[0].points[0].beat == 0.0
        assert self.track.automation[0].points[1].beat == 8.0

    @pytest.mark.parametrize(
        "preset_name",
        [
            "fade_in",
            "fade_out",
            "crescendo",
            "decrescendo",
            "pan_sweep_lr",
            "pan_sweep_rl",
            "swell",
        ],
    )
    def test_automation_presets(self, preset_name):
        self.engine.apply_preset(self.track, preset_name, 0.0, 8.0)
        expected_param = AutomationParam(AUTOMATION_PRESETS[preset_name]["param"])
        assert len(self.track.automation) == 1
        assert self.track.automation[0].param == expected_param
        assert len(self.track.automation[0].points) >= 2

    def test_automation_presets_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown preset"):
            self.engine.apply_preset(self.track, "invalid", 0.0, 8.0)

    def test_clear_automation(self):
        self.engine.add_automation(
            self.track, AutomationParam.VOLUME, [(0.0, 20), (8.0, 120)]
        )
        self.engine.add_automation(
            self.track, AutomationParam.PAN, [(0.0, 0), (8.0, 127)]
        )
        assert len(self.track.automation) == 2
        self.engine.clear_all(self.track)
        assert self.track.automation == []

    def test_add_automation_replaces_existing(self):
        self.engine.add_automation(
            self.track, AutomationParam.VOLUME, [(0.0, 10), (4.0, 50)]
        )
        self.engine.add_automation(
            self.track, AutomationParam.VOLUME, [(0.0, 80), (8.0, 120)]
        )
        assert len(self.track.automation) == 1
        assert len(self.track.automation[0].points) == 2
        assert self.track.automation[0].points[1].value == 120


class TestMarkerModels:
    def test_marker_model(self):
        m1 = Marker(beat=16.0, label="Chorus", color="blue")
        m2 = Marker(beat=32.0, label="Bridge")
        assert m1.id
        assert m2.id
        assert m1.id != m2.id
        assert m1.beat == 16.0
        assert m1.label == "Chorus"
        assert m1.color == "blue"
        assert m2.color == ""


class TestAutomationCommands:
    def setup_method(self):
        self.composer = Composer()
        self.composer.execute(CreateSongCommand("Automation Test"))
        self.composer.execute(AddTrackCommand("Piano", InstrumentType.PIANO))
        self.track_id = self.composer.song.tracks[0].id

    def test_add_marker_command(self):
        self.composer.execute(AddMarkerCommand(8.0, "Verse", "green"))
        assert len(self.composer.song.markers) == 1
        assert self.composer.song.markers[0].beat == 8.0
        assert self.composer.song.markers[0].label == "Verse"
        assert self.composer.song.markers[0].color == "green"

    def test_remove_marker_command(self):
        self.composer.execute(AddMarkerCommand(4.0, "Intro"))
        marker_id = self.composer.song.markers[0].id
        self.composer.execute(RemoveMarkerCommand(marker_id))
        assert self.composer.song.markers == []

    def test_add_automation_command(self):
        points = [{"beat": 0.0, "value": 20}, {"beat": 8.0, "value": 120}]
        self.composer.execute(
            AddAutomationCommand(self.track_id, "volume", points)
        )
        track = self.composer.song.tracks[0]
        assert len(track.automation) == 1
        assert track.automation[0].param == AutomationParam.VOLUME
        assert track.automation[0].points[0].value == 20

    def test_apply_preset_command(self):
        self.composer.execute(
            ApplyAutomationPresetCommand(self.track_id, "fade_in", 0.0, 16.0)
        )
        track = self.composer.song.tracks[0]
        assert len(track.automation) == 1
        assert track.automation[0].param == AutomationParam.VOLUME

    def test_remove_automation_command(self):
        points = [{"beat": 0.0, "value": 64}, {"beat": 4.0, "value": 100}]
        self.composer.execute(
            AddAutomationCommand(self.track_id, "pan", points)
        )
        self.composer.execute(RemoveAutomationCommand(self.track_id, "pan"))
        assert self.composer.song.tracks[0].automation == []

    def test_clear_automation_command(self):
        self.composer.execute(
            AddAutomationCommand(
                self.track_id, "volume", [{"beat": 0.0, "value": 50}]
            )
        )
        self.composer.execute(
            AddAutomationCommand(self.track_id, "pan", [{"beat": 0.0, "value": 64}])
        )
        self.composer.execute(ClearAutomationCommand(self.track_id))
        assert self.composer.song.tracks[0].automation == []

    def test_undo_automation(self):
        points = [{"beat": 0.0, "value": 30}, {"beat": 8.0, "value": 110}]
        self.composer.execute(
            AddAutomationCommand(self.track_id, "expression", points)
        )
        assert len(self.composer.song.tracks[0].automation) == 1
        self.composer.undo()
        assert self.composer.song.tracks[0].automation == []

    def test_song_has_markers_field(self):
        assert hasattr(self.composer.song, "markers")
        assert self.composer.song.markers == []

    def test_track_has_automation_field(self):
        track = self.composer.song.tracks[0]
        assert hasattr(track, "automation")
        assert track.automation == []
