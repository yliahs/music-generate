"""Tests for StyleEngine and style commands.

Phase 6: REQUIREMENTS.md 4.6 / TECHNICAL.md 5.13.
"""

import pytest

from composer_engine.commands.style_commands import (
    MixStylesCommand,
    SetGrooveCommand,
    SetMoodCommand,
    SetStyleCommand,
    SetSwingCommand,
)
from composer_engine.generators.style_engine import STYLE_PRESETS, StyleEngine
from composer_engine.models.chord import Chord, ChordQuality
from composer_engine.models.enums import InstrumentType, Key, SectionType, StylePreset
from composer_engine.models.section import Section
from composer_engine.models.song import Song
from composer_engine.models.track import Track


def _make_song() -> Song:
    song = Song(name="Style Test")
    song.global_settings.tempo = 140
    song.sections = [Section(type=SectionType.VERSE, start_beat=0, length_beats=16)]
    song.chord_progression = [
        Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
    ]
    song.tracks.append(Track.create("Piano", InstrumentType.PIANO))
    song.tracks.append(Track.create("Drums", InstrumentType.DRUMS))
    return song


class TestStyleEngine:
    def setup_method(self):
        self.engine = StyleEngine()
        self.song = _make_song()

    def test_all_presets_valid(self):
        assert len(STYLE_PRESETS) == 13
        for preset_name in StylePreset:
            preset = STYLE_PRESETS[preset_name.value]
            assert "recommended_instruments" in preset
            assert "chord_templates" in preset
            assert "tempo_range" in preset
            assert len(preset["tempo_range"]) == 2
            assert preset["tempo_range"][0] < preset["tempo_range"][1]
            assert "humanize_preset" in preset
            assert "swing" in preset

    def test_set_style_updates_global_settings(self):
        result = self.engine.set_style(self.song, "anime")
        assert self.song.global_settings.style == "anime"
        assert self.song.global_settings.swing == STYLE_PRESETS["anime"]["swing"]
        assert self.song.global_settings.groove == STYLE_PRESETS["anime"]["humanize_preset"]
        assert result["style"] == "anime"
        assert "suggestions" in result
        assert "applied" in result

    def test_set_style_returns_valid_suggestions(self):
        result = self.engine.set_style(self.song, "jazz")
        suggestions = result["suggestions"]
        assert "piano" in suggestions["recommended_instruments"]
        assert suggestions["drum_style"] == "jazz"
        assert suggestions["bass_mode"] == "walking"
        assert suggestions["tempo_range"] == (90, 160)

    def test_set_style_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown style"):
            self.engine.set_style(self.song, "unknown_style")

    def test_mix_styles_weighted(self):
        result = self.engine.mix_styles(self.song, "anime", "jazz", weight_a=0.6)
        assert self.song.global_settings.style == "anime+jazz"
        expected_swing = STYLE_PRESETS["anime"]["swing"] * 0.6 + STYLE_PRESETS["jazz"]["swing"] * 0.4
        assert self.song.global_settings.swing == pytest.approx(expected_swing)
        assert result["mixed"] is True
        assert result["weights"] == [0.6, 0.4]

    def test_mix_styles_primary_selection(self):
        result_heavy_a = self.engine.mix_styles(self.song, "rock", "jazz", weight_a=0.7)
        assert result_heavy_a["suggestions"]["drum_style"] == "rock"
        self.song.global_settings.style = ""
        result_heavy_b = self.engine.mix_styles(self.song, "rock", "jazz", weight_a=0.3)
        assert result_heavy_b["suggestions"]["drum_style"] == "jazz"

    def test_get_style_guide_no_style(self):
        guide = self.engine.get_style_guide(self.song)
        assert "message" in guide

    def test_get_style_guide_with_style(self):
        self.engine.set_style(self.song, "anime")
        guide = self.engine.get_style_guide(self.song)
        assert guide["style"] == "anime"
        assert "status" in guide
        assert "tempo_ok" in guide["status"]
        assert "missing" in guide
        assert "next_actions" in guide
        assert isinstance(guide["missing"], list)

    def test_get_style_guide_detects_missing_instruments(self):
        self.engine.set_style(self.song, "anime")
        guide = self.engine.get_style_guide(self.song)
        assert "strings" in guide["missing"]
        assert "bass" in guide["missing"]


class TestStyleCommands:
    def setup_method(self):
        self.song = _make_song()

    def test_set_style_command(self):
        cmd = SetStyleCommand("rock")
        song = cmd.execute(self.song)
        assert song.global_settings.style == "rock"
        assert cmd._result["style"] == "rock"
        assert "suggestions" in cmd._result

    def test_mix_styles_command(self):
        cmd = MixStylesCommand("anime", "lofi", weight_a=0.5)
        song = cmd.execute(self.song)
        assert song.global_settings.style == "anime+lofi"
        assert cmd._result["mixed"] is True

    def test_set_mood_command(self):
        song = SetMoodCommand("melancholic").execute(self.song)
        assert song.global_settings.mood == "melancholic"

    def test_set_swing_command(self):
        song = SetSwingCommand(0.75).execute(self.song)
        assert song.global_settings.swing == 0.75

    def test_set_swing_command_clamps(self):
        song = SetSwingCommand(1.5).execute(self.song)
        assert song.global_settings.swing == 1.0

    def test_set_groove_command(self):
        song = SetGrooveCommand("funk").execute(self.song)
        assert song.global_settings.groove == "funk"
