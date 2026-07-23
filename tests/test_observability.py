"""Tests for Phase 11 Observability."""

import logging
import os
import time

import pytest

from composer_engine.observability.banner import print_banner
from composer_engine.observability.logger import log, setup_logger, get_logger
from composer_engine.observability.stats import ServerStats


class TestLogger:
    def test_setup_logger(self):
        logger = setup_logger()
        assert logger is not None
        assert logger.name == "composer_engine"

    def test_get_logger_returns_same_instance(self):
        l1 = get_logger()
        l2 = get_logger()
        assert l1 is l2

    def test_log_does_not_raise(self):
        log("Test message", level="INFO", tag="TEST")
        log("Debug message", level="DEBUG", tag="TEST")
        log("Warning message", level="WARN", tag="TEST")
        log("Error message", level="ERROR", tag="TEST")

    def test_log_level_from_env(self, monkeypatch):
        import composer_engine.observability.logger as lmod
        lmod._logger = None
        monkeypatch.setenv("COMPOSER_LOG_LEVEL", "DEBUG")
        logger = setup_logger()
        assert logger.level == logging.DEBUG
        lmod._logger = None
        monkeypatch.delenv("COMPOSER_LOG_LEVEL", raising=False)
        setup_logger()

    def test_log_to_file(self, tmp_path, monkeypatch):
        import composer_engine.observability.logger as lmod
        lmod._logger = None
        log_file = str(tmp_path / "test.log")
        monkeypatch.setenv("COMPOSER_LOG_FILE", log_file)
        monkeypatch.setenv("COMPOSER_LOG_LEVEL", "INFO")
        setup_logger()
        log("File log test", tag="TEST")
        lmod._logger = None
        monkeypatch.delenv("COMPOSER_LOG_FILE", raising=False)
        monkeypatch.delenv("COMPOSER_LOG_LEVEL", raising=False)
        setup_logger()
        with open(log_file, encoding="utf-8") as f:
            content = f.read()
        assert "File log test" in content


class TestServerStats:
    def test_initial_state(self):
        s = ServerStats()
        assert s.tool_calls == 0
        assert s.tool_errors == 0
        assert s.commands_executed == 0

    def test_record_tool_call_success(self):
        s = ServerStats()
        s.record_tool_call("create_song", True, 12.5)
        assert s.tool_calls == 1
        assert s.tool_errors == 0
        assert "create_song" in s.last_tool
        assert "OK" in s.last_tool

    def test_record_tool_call_failure(self):
        s = ServerStats()
        s.record_tool_call("remove_track", False, 3.0)
        assert s.tool_calls == 1
        assert s.tool_errors == 1
        assert "FAIL" in s.last_tool

    def test_record_command(self):
        s = ServerStats()
        s.record_command()
        s.record_command()
        assert s.commands_executed == 2

    def test_record_undo_redo(self):
        s = ServerStats()
        s.record_undo()
        s.record_redo()
        assert s.undo_count == 1
        assert s.redo_count == 1

    def test_get_uptime(self):
        s = ServerStats()
        uptime = s.get_uptime()
        assert "h" in uptime and "m" in uptime and "s" in uptime

    def test_to_dict(self):
        s = ServerStats()
        s.record_tool_call("test", True, 5.0)
        d = s.to_dict()
        assert "uptime" in d
        assert "tool_calls" in d
        assert d["tool_calls"] == 1
        assert "error_rate" in d
        assert d["error_rate"] == "0.0%"

    def test_error_rate(self):
        s = ServerStats()
        s.record_tool_call("a", True, 1)
        s.record_tool_call("b", False, 1)
        s.record_tool_call("c", True, 1)
        s.record_tool_call("d", False, 1)
        d = s.to_dict()
        assert d["error_rate"] == "50.0%"


class TestBanner:
    def test_print_banner_does_not_raise(self, capsys):
        print_banner(tool_count=146)

    def test_banner_suppressed_by_env(self, monkeypatch, capsys):
        monkeypatch.setenv("COMPOSER_NO_BANNER", "1")
        print_banner()
        captured = capsys.readouterr()
        assert "Composer Engine" not in captured.out
        assert "Composer Engine" not in captured.err

    def test_banner_shows_tool_count(self, monkeypatch, capsys):
        monkeypatch.delenv("COMPOSER_NO_BANNER", raising=False)
        print_banner(tool_count=146)
        captured = capsys.readouterr()
        assert "146" in captured.err


class TestComposerLogging:
    def test_execute_logs_command(self, caplog):
        from composer_engine.engine.composer import Composer
        from composer_engine.commands.song_commands import CreateSongCommand

        with caplog.at_level(logging.DEBUG, logger="composer_engine"):
            c = Composer()
            c.execute(CreateSongCommand("LogTest"))

        log_text = caplog.text
        assert "CreateSongCommand" in log_text or "LogTest" in log_text
