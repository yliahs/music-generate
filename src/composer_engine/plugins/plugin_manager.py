"""Plugin manager for Composer Engine - Phase 9.

Supports 5 plugin types: Generator, Analyzer, Pattern, Style, Renderer.
Plugins are discovered from ~/.composer-engine/plugins/ directory.
"""

import importlib.util
import json
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class PluginType(str, Enum):
    """Plugin type."""
    GENERATOR = "generator"
    ANALYZER = "analyzer"
    PATTERN = "pattern"
    STYLE = "style"
    RENDERER = "renderer"


class PluginInfo(BaseModel):
    """Plugin metadata."""
    name: str
    version: str
    type: PluginType
    entry: str
    class_name: str
    description: str = ""
    enabled: bool = True


# Plugin interfaces (ABCs)

class GeneratorPlugin(ABC):
    @abstractmethod
    def generate(self, **kwargs) -> list:
        ...

class AnalyzerPlugin(ABC):
    @abstractmethod
    def analyze(self, song: Any, **kwargs) -> dict:
        ...

class PatternPlugin(ABC):
    @abstractmethod
    def get_pattern(self, **kwargs) -> list:
        ...

class StylePlugin(ABC):
    @abstractmethod
    def get_preset(self) -> dict:
        ...

class RendererPlugin(ABC):
    @abstractmethod
    def render(self, song: Any, **kwargs) -> str | bytes:
        ...


PLUGIN_INTERFACES = {
    PluginType.GENERATOR: GeneratorPlugin,
    PluginType.ANALYZER: AnalyzerPlugin,
    PluginType.PATTERN: PatternPlugin,
    PluginType.STYLE: StylePlugin,
    PluginType.RENDERER: RendererPlugin,
}


class PluginManager:
    """Manages plugin discovery, loading, and invocation."""

    def __init__(self, plugins_dir: Path | None = None):
        self.plugins_dir = plugins_dir or Path.home() / ".composer-engine" / "plugins"
        self.registry: dict[str, PluginInfo] = {}
        self.instances: dict[str, Any] = {}

    def discover(self) -> list[PluginInfo]:
        """Scan plugins directory for plugin.json files."""
        self.registry.clear()
        if not self.plugins_dir.exists():
            return []
        for subdir in self.plugins_dir.iterdir():
            if not subdir.is_dir():
                continue
            plugin_json = subdir / "plugin.json"
            if plugin_json.exists():
                try:
                    data = json.loads(plugin_json.read_text(encoding="utf-8"))
                    info = PluginInfo(**data)
                    self.registry[info.name] = info
                except Exception:
                    pass  # Skip invalid plugins
        return list(self.registry.values())

    def load(self, name: str) -> Any:
        """Load a plugin by name."""
        if name in self.instances:
            return self.instances[name]
        if name not in self.registry:
            raise ValueError(f"Plugin not found: {name}")
        info = self.registry[name]
        if not info.enabled:
            raise ValueError(f"Plugin disabled: {name}")
        plugin_path = self.plugins_dir / name / info.entry
        if not plugin_path.exists():
            raise FileNotFoundError(f"Plugin entry not found: {plugin_path}")
        spec = importlib.util.spec_from_file_location(name, str(plugin_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load plugin: {name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls = getattr(module, info.class_name)
        instance = cls()
        self.instances[name] = instance
        return instance

    def enable(self, name: str) -> None:
        if name not in self.registry:
            raise ValueError(f"Plugin not found: {name}")
        self.registry[name].enabled = True

    def disable(self, name: str) -> None:
        if name not in self.registry:
            raise ValueError(f"Plugin not found: {name}")
        self.registry[name].enabled = False
        self.instances.pop(name, None)

    def reload(self) -> list[PluginInfo]:
        """Reload all plugins: clear cache and re-discover."""
        self.instances.clear()
        return self.discover()

    def list_plugins(self) -> list[dict]:
        return [info.model_dump() for info in self.registry.values()]
