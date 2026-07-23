"""Automation and marker commands for Phase 8."""

from datetime import datetime, timezone

from composer_engine.commands.base import Command
from composer_engine.generators.automation_engine import AutomationEngine
from composer_engine.models.automation import Marker
from composer_engine.models.enums import AutomationParam
from composer_engine.models.song import Song


def _get_track(song, track_id):
    for t in song.tracks:
        if t.id == track_id:
            return t
    return None


class AddAutomationCommand(Command):
    def __init__(self, track_id: str, param: str, points: list[dict]):
        self.track_id = track_id
        self.param = AutomationParam(param)
        self.points = [(p["beat"], p["value"]) for p in points]

    @property
    def description(self) -> str:
        return f"Add {self.param.value} automation"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            AutomationEngine().add_automation(track, self.param, self.points)
        song.updated_at = datetime.now(timezone.utc)
        return song


class RemoveAutomationCommand(Command):
    def __init__(self, track_id: str, param: str):
        self.track_id = track_id
        self.param = AutomationParam(param)

    @property
    def description(self) -> str:
        return f"Remove {self.param.value} automation"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            AutomationEngine().remove_automation(track, self.param)
        song.updated_at = datetime.now(timezone.utc)
        return song


class AddAutomationPointCommand(Command):
    def __init__(self, track_id: str, param: str, beat: float, value: int):
        self.track_id = track_id
        self.param = AutomationParam(param)
        self.beat = beat
        self.value = value

    @property
    def description(self) -> str:
        return f"Add automation point at beat {self.beat}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            AutomationEngine().add_point(track, self.param, self.beat, self.value)
        song.updated_at = datetime.now(timezone.utc)
        return song


class RemoveAutomationPointCommand(Command):
    def __init__(self, track_id: str, param: str, point_index: int):
        self.track_id = track_id
        self.param = AutomationParam(param)
        self.point_index = point_index

    @property
    def description(self) -> str:
        return f"Remove automation point {self.point_index}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            AutomationEngine().remove_point(track, self.param, self.point_index)
        song.updated_at = datetime.now(timezone.utc)
        return song


class ApplyAutomationPresetCommand(Command):
    def __init__(
        self, track_id: str, preset_name: str, start_beat: float, end_beat: float
    ):
        self.track_id = track_id
        self.preset_name = preset_name
        self.start_beat = start_beat
        self.end_beat = end_beat

    @property
    def description(self) -> str:
        return f"Apply automation preset '{self.preset_name}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            AutomationEngine().apply_preset(
                track, self.preset_name, self.start_beat, self.end_beat
            )
        song.updated_at = datetime.now(timezone.utc)
        return song


class ClearAutomationCommand(Command):
    def __init__(self, track_id: str):
        self.track_id = track_id

    @property
    def description(self) -> str:
        return "Clear all automation"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        track = _get_track(song, self.track_id)
        if track:
            AutomationEngine().clear_all(track)
        song.updated_at = datetime.now(timezone.utc)
        return song


class AddMarkerCommand(Command):
    def __init__(self, beat: float, label: str, color: str = ""):
        self.beat = beat
        self.label = label
        self.color = color

    @property
    def description(self) -> str:
        return f"Add marker '{self.label}' at beat {self.beat}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        marker = Marker(beat=self.beat, label=self.label, color=self.color)
        song.markers.append(marker)
        song.updated_at = datetime.now(timezone.utc)
        return song


class RemoveMarkerCommand(Command):
    def __init__(self, marker_id: str):
        self.marker_id = marker_id

    @property
    def description(self) -> str:
        return f"Remove marker {self.marker_id}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.markers = [m for m in song.markers if m.id != self.marker_id]
        song.updated_at = datetime.now(timezone.utc)
        return song
