"""Humanize engine for timing, velocity, and groove adjustments.

Aligned with TECHNICAL.md 5.13 - Phase 6 HumanizeEngine.
"""

import random

from composer_engine.models.note import Note

GROOVE_TEMPLATES: dict[str, dict[str, list]] = {
    "straight": {
        "timing_offsets": [0] * 16,
        "velocity_offsets": [0] * 16,
    },
    "swing_light": {
        "timing_offsets": [0, 0, 0.04, 0, 0, 0, 0.04, 0, 0, 0, 0.04, 0, 0, 0, 0.04, 0],
        "velocity_offsets": [0, 0, -5, 0, 0, 0, -5, 0, 0, 0, -5, 0, 0, 0, -5, 0],
    },
    "swing_heavy": {
        "timing_offsets": [0, 0, 0.08, 0, 0, 0, 0.08, 0, 0, 0, 0.08, 0, 0, 0, 0.08, 0],
        "velocity_offsets": [0, 0, -10, 0, 0, 0, -10, 0, 0, 0, -10, 0, 0, 0, -10, 0],
    },
    "funk": {
        "timing_offsets": [
            0, 0.02, -0.02, 0.03, 0, -0.02, 0.02, 0,
            0, 0.02, -0.02, 0.03, 0, -0.02, 0.02, 0,
        ],
        "velocity_offsets": [
            5, -3, 3, -5, 5, -3, 3, -5,
            5, -3, 3, -5, 5, -3, 3, -5,
        ],
    },
    "bossa": {
        "timing_offsets": [
            0, 0, 0.03, 0, -0.02, 0, 0.03, 0,
            0, 0, 0.03, 0, -0.02, 0, 0.03, 0,
        ],
        "velocity_offsets": [
            3, -2, 0, -3, 3, -2, 0, -3,
            3, -2, 0, -3, 3, -2, 0, -3,
        ],
    },
    "shuffle": {
        "timing_offsets": [0, 0, 0.1, 0, 0, 0, 0.1, 0, 0, 0, 0.1, 0, 0, 0, 0.1, 0],
        "velocity_offsets": [0, 0, -8, 0, 0, 0, -8, 0, 0, 0, -8, 0, 0, 0, -8, 0],
    },
    "human_piano": {
        "timing_offsets": "random",
        "velocity_offsets": "random",
        "timing_range": 0.02,
        "velocity_range": 5,
    },
    "human_guitar": {
        "timing_offsets": "random",
        "velocity_offsets": "random",
        "timing_range": 0.03,
        "velocity_range": 7,
    },
    "human_drums": {
        "timing_offsets": "random",
        "velocity_offsets": "random",
        "timing_range": 0.015,
        "velocity_range": 10,
    },
    "laid_back": {
        "timing_offsets": [0.03] * 16,
        "velocity_offsets": [-5] * 16,
    },
}

_RANDOM_GROOVES = {"human_piano", "human_guitar", "human_drums"}


def _clamp_velocity(velocity: int) -> int:
    return max(1, min(127, velocity))


def _clamp_start_beat(start_beat: float) -> float:
    return max(0.0, start_beat)


class HumanizeEngine:
    """Directly modifies Note start_beat, velocity, and duration_beat."""

    def humanize_timing(self, notes: list[Note], amount: float = 0.5) -> list[Note]:
        max_offset = amount * 0.05
        for note in notes:
            note.start_beat += random.uniform(-max_offset, max_offset)
            note.start_beat = _clamp_start_beat(note.start_beat)
        return notes

    def humanize_velocity(self, notes: list[Note], amount: float = 0.5) -> list[Note]:
        max_offset = int(amount * 15)
        for note in notes:
            note.velocity += random.randint(-max_offset, max_offset)
            note.velocity = _clamp_velocity(note.velocity)
        return notes

    def apply_micro_timing(
        self, notes: list[Note], beat_offsets: dict[float, float]
    ) -> list[Note]:
        beats_per_bar = 4
        for note in notes:
            bar_pos = note.start_beat % beats_per_bar
            for target_beat, offset in beat_offsets.items():
                if abs(bar_pos - target_beat) < 0.01:
                    note.start_beat += offset
                    note.start_beat = _clamp_start_beat(note.start_beat)
        return notes

    def apply_groove(self, notes: list[Note], groove_name: str) -> list[Note]:
        template = GROOVE_TEMPLATES.get(groove_name)
        if template is None:
            raise ValueError(f"Unknown groove: {groove_name}")

        if groove_name in _RANDOM_GROOVES:
            timing_range = template["timing_range"]
            velocity_range = template["velocity_range"]
            for note in notes:
                note.start_beat += random.gauss(0, timing_range)
                note.start_beat = _clamp_start_beat(note.start_beat)
                note.velocity += random.randint(-velocity_range, velocity_range)
                note.velocity = _clamp_velocity(note.velocity)
            return notes

        timing_offsets = template["timing_offsets"]
        velocity_offsets = template["velocity_offsets"]
        beats_per_bar = 4

        for note in notes:
            bar_pos = note.start_beat % beats_per_bar
            sub_beat_index = round(bar_pos / 0.25) % 16
            note.start_beat += timing_offsets[sub_beat_index]
            note.start_beat = _clamp_start_beat(note.start_beat)
            note.velocity += velocity_offsets[sub_beat_index]
            note.velocity = _clamp_velocity(note.velocity)
        return notes

    def apply_swing(self, notes: list[Note], swing_amount: float) -> list[Note]:
        delay = swing_amount * 0.1
        beats_per_bar = 4
        for note in notes:
            bar_pos = note.start_beat % beats_per_bar
            eighth_pos = round(bar_pos / 0.5)
            if eighth_pos % 2 == 1:
                note.start_beat += delay
        return notes

    def push_timing(self, notes: list[Note], amount: float) -> list[Note]:
        offset = -(amount * 0.05)
        for note in notes:
            note.start_beat += offset
            note.start_beat = _clamp_start_beat(note.start_beat)
        return notes

    def pull_timing(self, notes: list[Note], amount: float) -> list[Note]:
        offset = amount * 0.05
        for note in notes:
            note.start_beat += offset
        return notes

    def hand_played_feel(self, notes: list[Note], intensity: float) -> list[Note]:
        t_max = intensity * 0.04
        v_max = int(intensity * 10)
        d_factor = intensity * 0.1
        for note in notes:
            note.start_beat += random.uniform(-t_max, t_max)
            note.start_beat = _clamp_start_beat(note.start_beat)
            note.velocity += random.randint(-v_max, v_max)
            note.velocity = _clamp_velocity(note.velocity)
            note.duration_beat *= random.uniform(1 - d_factor, 1 + d_factor)
            if note.duration_beat <= 0:
                note.duration_beat = 0.01
        return notes
