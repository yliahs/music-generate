"""Tests for Composer engine (execute, undo, redo, snapshots)."""

import pytest

from composer_engine.commands.global_commands import SetTempoCommand
from composer_engine.commands.song_commands import CreateSongCommand
from composer_engine.commands.track_commands import AddTrackCommand
from composer_engine.engine.composer import Composer, ComposerError
from composer_engine.models import InstrumentType, Key


class TestComposerExecute:
    def test_create_and_execute(self):
        c = Composer()
        c.execute(CreateSongCommand("Test"))
        assert c.song is not None
        assert c.song.name == "Test"

    def test_execute_chain(self):
        c = Composer()
        c.execute(CreateSongCommand("Test"))
        c.execute(AddTrackCommand("Piano", InstrumentType.PIANO))
        c.execute(SetTempoCommand(140))
        assert len(c.song.tracks) == 1
        assert c.song.global_settings.tempo == 140


class TestUndoRedo:
    def test_undo(self):
        c = Composer()
        c.execute(CreateSongCommand("Test"))
        c.execute(SetTempoCommand(180))
        assert c.song.global_settings.tempo == 180
        c.undo()
        assert c.song.global_settings.tempo == 120

    def test_redo(self):
        c = Composer()
        c.execute(CreateSongCommand("Test"))
        c.execute(SetTempoCommand(180))
        c.undo()
        c.redo()
        assert c.song.global_settings.tempo == 180

    def test_undo_empty_raises(self):
        c = Composer()
        c.execute(CreateSongCommand("Test"))
        c.undo()
        with pytest.raises(ComposerError):
            c.undo()

    def test_redo_empty_raises(self):
        c = Composer()
        c.execute(CreateSongCommand("Test"))
        with pytest.raises(ComposerError):
            c.redo()


class TestSnapshots:
    def test_save_and_load(self):
        c = Composer()
        c.execute(CreateSongCommand("Test"))
        c.save_snapshot("v1")
        c.execute(SetTempoCommand(200))
        c.load_snapshot("v1")
        assert c.song.global_settings.tempo == 120

    def test_list_snapshots(self):
        c = Composer()
        c.execute(CreateSongCommand("Test"))
        c.save_snapshot("a")
        c.save_snapshot("b")
        assert sorted(c.snapshots.list()) == ["a", "b"]

    def test_load_missing_raises(self):
        c = Composer()
        c.execute(CreateSongCommand("Test"))
        with pytest.raises(KeyError):
            c.load_snapshot("nonexistent")


class TestGetState:
    def test_state_structure(self):
        c = Composer()
        c.execute(CreateSongCommand("Test"))
        state = c.get_state()
        assert "song" in state
        assert "pipeline" in state
        assert "history" in state
        assert state["pipeline"]["stage"] in ["inspiration", "composition", "arrangement",
                                                "production", "export", "empty"]
