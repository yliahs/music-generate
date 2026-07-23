"""Tests for Phase 9 Plugin System."""
import json
import pytest
from pathlib import Path
import tempfile

from composer_engine.plugins.plugin_manager import (
    PluginManager, PluginType, PluginInfo,
    GeneratorPlugin, AnalyzerPlugin, PatternPlugin, StylePlugin, RendererPlugin,
)


class TestPluginInfo:
    def test_create_plugin_info(self):
        info = PluginInfo(
            name="test-gen", version="1.0.0", type=PluginType.GENERATOR,
            entry="gen.py", class_name="TestGen"
        )
        assert info.name == "test-gen"
        assert info.type == PluginType.GENERATOR
        assert info.enabled is True

    def test_plugin_type_values(self):
        assert PluginType.GENERATOR == "generator"
        assert PluginType.ANALYZER == "analyzer"
        assert PluginType.PATTERN == "pattern"
        assert PluginType.STYLE == "style"
        assert PluginType.RENDERER == "renderer"


class TestPluginManager:
    def test_empty_discover(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(plugins_dir=Path(tmpdir))
            plugins = pm.discover()
            assert plugins == []

    def test_discover_plugin(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "my-plugin"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.json").write_text(json.dumps({
                "name": "my-plugin",
                "version": "1.0.0",
                "type": "generator",
                "entry": "gen.py",
                "class_name": "MyGen",
                "description": "Test generator"
            }))
            pm = PluginManager(plugins_dir=Path(tmpdir))
            plugins = pm.discover()
            assert len(plugins) == 1
            assert plugins[0].name == "my-plugin"

    def test_enable_disable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "test"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.json").write_text(json.dumps({
                "name": "test", "version": "1.0.0", "type": "analyzer",
                "entry": "a.py", "class_name": "A"
            }))
            pm = PluginManager(plugins_dir=Path(tmpdir))
            pm.discover()
            pm.disable("test")
            assert pm.registry["test"].enabled is False
            pm.enable("test")
            assert pm.registry["test"].enabled is True

    def test_load_plugin(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "simple"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.json").write_text(json.dumps({
                "name": "simple", "version": "1.0.0", "type": "generator",
                "entry": "gen.py", "class_name": "SimpleGen"
            }))
            (plugin_dir / "gen.py").write_text(
                "class SimpleGen:\n    def generate(self, **kwargs):\n        return []\n"
            )
            pm = PluginManager(plugins_dir=Path(tmpdir))
            pm.discover()
            instance = pm.load("simple")
            assert hasattr(instance, "generate")
            result = instance.generate()
            assert result == []

    def test_load_disabled_plugin_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "dis"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.json").write_text(json.dumps({
                "name": "dis", "version": "1.0.0", "type": "style",
                "entry": "s.py", "class_name": "S"
            }))
            pm = PluginManager(plugins_dir=Path(tmpdir))
            pm.discover()
            pm.disable("dis")
            with pytest.raises(ValueError, match="disabled"):
                pm.load("dis")

    def test_load_nonexistent_fails(self):
        pm = PluginManager(plugins_dir=Path("/nonexistent"))
        with pytest.raises(ValueError, match="not found"):
            pm.load("nope")

    def test_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(plugins_dir=Path(tmpdir))
            pm.discover()
            assert len(pm.list_plugins()) == 0
            plugin_dir = Path(tmpdir) / "new"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.json").write_text(json.dumps({
                "name": "new", "version": "1.0.0", "type": "renderer",
                "entry": "r.py", "class_name": "R"
            }))
            pm.reload()
            assert len(pm.list_plugins()) == 1

    def test_list_plugins(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                d = Path(tmpdir) / f"p{i}"
                d.mkdir()
                (d / "plugin.json").write_text(json.dumps({
                    "name": f"p{i}", "version": "1.0.0", "type": "pattern",
                    "entry": "x.py", "class_name": "X"
                }))
            pm = PluginManager(plugins_dir=Path(tmpdir))
            pm.discover()
            plugins = pm.list_plugins()
            assert len(plugins) == 3

    def test_plugin_interfaces_exist(self):
        """Verify all 5 plugin interface ABCs are defined."""
        assert GeneratorPlugin is not None
        assert AnalyzerPlugin is not None
        assert PatternPlugin is not None
        assert StylePlugin is not None
        assert RendererPlugin is not None
