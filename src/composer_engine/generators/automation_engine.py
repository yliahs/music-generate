"""Automation engine with preset templates."""

from composer_engine.models.automation import AutomationCurve, AutomationPoint
from composer_engine.models.enums import AutomationParam
from composer_engine.models.track import Track


AUTOMATION_PRESETS = {
    "fade_in": {"param": "volume", "type": "ramp_up"},
    "fade_out": {"param": "volume", "type": "ramp_down"},
    "crescendo": {"param": "expression", "type": "ramp_up"},
    "decrescendo": {"param": "expression", "type": "ramp_down"},
    "pan_sweep_lr": {"param": "pan", "type": "ramp_up_full"},
    "pan_sweep_rl": {"param": "pan", "type": "ramp_down_full"},
    "swell": {"param": "expression", "type": "swell"},
}


class AutomationEngine:
    def add_automation(
        self, track: Track, param: AutomationParam, points: list[tuple[float, int]]
    ) -> None:
        track.automation = [c for c in track.automation if c.param != param]
        curve = AutomationCurve(
            param=param,
            points=[AutomationPoint(beat=b, value=v) for b, v in points],
        )
        track.automation.append(curve)

    def remove_automation(self, track: Track, param: AutomationParam) -> None:
        track.automation = [c for c in track.automation if c.param != param]

    def add_point(
        self, track: Track, param: AutomationParam, beat: float, value: int
    ) -> None:
        curve = None
        for c in track.automation:
            if c.param == param:
                curve = c
                break
        if curve is None:
            curve = AutomationCurve(param=param)
            track.automation.append(curve)
        curve.points.append(AutomationPoint(beat=beat, value=value))
        curve.points.sort(key=lambda p: p.beat)

    def remove_point(
        self, track: Track, param: AutomationParam, point_index: int
    ) -> None:
        for c in track.automation:
            if c.param == param:
                if 0 <= point_index < len(c.points):
                    del c.points[point_index]
                break

    def apply_preset(
        self, track: Track, preset_name: str, start_beat: float, end_beat: float
    ) -> None:
        preset = AUTOMATION_PRESETS.get(preset_name)
        if not preset:
            raise ValueError(f"Unknown preset: {preset_name}")
        param = AutomationParam(preset["param"])
        ptype = preset["type"]
        if ptype == "ramp_up":
            points = [(start_beat, 20), (end_beat, 120)]
        elif ptype == "ramp_down":
            points = [(start_beat, track.volume), (end_beat, 0)]
        elif ptype == "ramp_up_full":
            points = [(start_beat, 0), (end_beat, 127)]
        elif ptype == "ramp_down_full":
            points = [(start_beat, 127), (end_beat, 0)]
        elif ptype == "swell":
            mid = (start_beat + end_beat) / 2
            points = [(start_beat, 40), (mid, 120), (end_beat, 40)]
        else:
            points = [(start_beat, 64), (end_beat, 64)]
        self.add_automation(track, param, points)

    def clear_all(self, track: Track) -> None:
        track.automation.clear()
