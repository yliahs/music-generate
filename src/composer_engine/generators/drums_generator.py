"""Drums pattern generator.

Aligned with TECHNICAL.md 5.11.
"""

import random

from composer_engine.models.enums import (
    DrumStyle,
    GM_PERCUSSION,
    HiHatPattern,
    KickPattern,
    SnarePattern,
)
from composer_engine.models.note import Note

# Drum templates: each entry is (pitch, beat_offset_in_bar, duration, velocity)
DRUM_TEMPLATES: dict[str, dict[str, list[tuple[int, float, float, int]]]] = {
    "rock": {
        "kick":  [(GM_PERCUSSION["KICK"], 0.0, 0.5, 100), (GM_PERCUSSION["KICK"], 2.0, 0.5, 100)],
        "snare": [(GM_PERCUSSION["SNARE"], 1.0, 0.5, 100), (GM_PERCUSSION["SNARE"], 3.0, 0.5, 100)],
        "hihat": [(GM_PERCUSSION["CLOSED_HH"], i * 0.5, 0.5, 80) for i in range(8)],
    },
    "pop": {
        "kick":  [(GM_PERCUSSION["KICK"], 0.0, 0.5, 90), (GM_PERCUSSION["KICK"], 2.0, 0.5, 85)],
        "snare": [(GM_PERCUSSION["SNARE"], 1.0, 0.5, 95), (GM_PERCUSSION["SNARE"], 3.0, 0.5, 95)],
        "hihat": [(GM_PERCUSSION["CLOSED_HH"], i * 0.5, 0.5, 70) for i in range(8)],
    },
    "jazz": {
        "kick":  [(GM_PERCUSSION["KICK"], 0.0, 0.5, 60), (GM_PERCUSSION["KICK"], 2.5, 0.5, 50)],
        "snare": [(GM_PERCUSSION["SNARE"], 1.0, 0.5, 55), (GM_PERCUSSION["SIDE_STICK"], 3.0, 0.5, 50)],
        "ride":  [(GM_PERCUSSION["RIDE"], 0.0, 1.0, 75), (GM_PERCUSSION["RIDE"], 1.0, 0.5, 60),
                  (GM_PERCUSSION["RIDE"], 1.67, 0.33, 70), (GM_PERCUSSION["RIDE"], 2.0, 1.0, 75),
                  (GM_PERCUSSION["RIDE"], 3.0, 0.5, 60), (GM_PERCUSSION["RIDE"], 3.67, 0.33, 70)],
        "hihat": [(GM_PERCUSSION["PEDAL_HH"], 1.0, 0.5, 50), (GM_PERCUSSION["PEDAL_HH"], 3.0, 0.5, 50)],
    },
    "metal": {
        "kick":  [(GM_PERCUSSION["KICK"], i * 0.25, 0.25, 110) for i in range(16)],
        "snare": [(GM_PERCUSSION["SNARE"], 1.0, 0.5, 120), (GM_PERCUSSION["SNARE"], 3.0, 0.5, 120)],
        "hihat": [(GM_PERCUSSION["CLOSED_HH"], i * 0.25, 0.25, 90) for i in range(16)],
    },
    "edm": {
        "kick":  [(GM_PERCUSSION["KICK"], float(i), 0.5, 110) for i in range(4)],
        "snare": [(GM_PERCUSSION["CLAP"], 1.0, 0.5, 100), (GM_PERCUSSION["CLAP"], 3.0, 0.5, 100)],
        "hihat": [(GM_PERCUSSION["OPEN_HH"], i * 0.5 + 0.25, 0.25, 80) for i in range(8)],
    },
    "anime": {
        "kick":  [(GM_PERCUSSION["KICK"], 0.0, 0.5, 95), (GM_PERCUSSION["KICK"], 2.0, 0.5, 90)],
        "snare": [(GM_PERCUSSION["SNARE"], 1.0, 0.5, 100), (GM_PERCUSSION["SNARE"], 3.0, 0.5, 100)],
        "hihat": [(GM_PERCUSSION["CLOSED_HH"], i * 0.5, 0.5, 75) for i in range(8)],
    },
    "latin": {
        "kick":  [(GM_PERCUSSION["KICK"], 0.0, 0.5, 90), (GM_PERCUSSION["KICK"], 2.5, 0.5, 85)],
        "snare": [(GM_PERCUSSION["SNARE"], 2.0, 0.5, 90)],
        "conga": [(63, 0.0, 0.5, 80), (63, 1.0, 0.5, 75),
                  (64, 1.5, 0.5, 70), (63, 2.0, 0.5, 80),
                  (64, 3.0, 0.5, 75), (63, 3.5, 0.5, 70)],
        "clave": [(GM_PERCUSSION["CLAVES"], 0.0, 0.5, 85), (GM_PERCUSSION["CLAVES"], 1.5, 0.5, 85),
                  (GM_PERCUSSION["CLAVES"], 2.0, 0.5, 85)],
    },
    "swing": {
        "kick":  [(GM_PERCUSSION["KICK"], 0.0, 0.5, 65), (GM_PERCUSSION["KICK"], 2.0, 0.5, 60)],
        "snare": [(GM_PERCUSSION["SNARE"], 1.0, 0.5, 55), (GM_PERCUSSION["SNARE"], 3.0, 0.5, 55)],
        "ride":  [(GM_PERCUSSION["RIDE"], 0.0, 1.0, 80), (GM_PERCUSSION["RIDE"], 1.0, 0.33, 65),
                  (GM_PERCUSSION["RIDE"], 1.67, 0.33, 75), (GM_PERCUSSION["RIDE"], 2.0, 1.0, 80),
                  (GM_PERCUSSION["RIDE"], 3.0, 0.33, 65), (GM_PERCUSSION["RIDE"], 3.67, 0.33, 75)],
        "hihat": [(GM_PERCUSSION["PEDAL_HH"], 1.0, 0.5, 50), (GM_PERCUSSION["PEDAL_HH"], 3.0, 0.5, 50)],
    },
}

FILL_TEMPLATES = {
    "basic": [
        (GM_PERCUSSION["SNARE"], 0.0, 0.25, 100),
        (GM_PERCUSSION["SNARE"], 0.25, 0.25, 105),
        (GM_PERCUSSION["HIGH_TOM"], 0.5, 0.25, 100),
        (GM_PERCUSSION["LOW_TOM"], 0.75, 0.25, 95),
    ],
    "double": [
        (GM_PERCUSSION["SNARE"], 0.0, 0.25, 95),
        (GM_PERCUSSION["SNARE"], 0.25, 0.25, 100),
        (GM_PERCUSSION["SNARE"], 0.5, 0.25, 105),
        (GM_PERCUSSION["SNARE"], 0.75, 0.25, 110),
        (GM_PERCUSSION["HIGH_TOM"], 1.0, 0.25, 105),
        (GM_PERCUSSION["MID_TOM"], 1.25, 0.25, 100),
        (GM_PERCUSSION["LOW_TOM"], 1.5, 0.25, 95),
        (GM_PERCUSSION["FLOOR_TOM"], 1.75, 0.25, 90),
    ],
    "crescendo": [
        (GM_PERCUSSION["SNARE"], i * 0.125, 0.125, 60 + i * 5) for i in range(8)
    ],
    "tom_cascade": [
        (GM_PERCUSSION["HIGH_TOM"], 0.0, 0.25, 105),
        (GM_PERCUSSION["HIGH_TOM"], 0.25, 0.25, 100),
        (GM_PERCUSSION["MID_TOM"], 0.5, 0.25, 100),
        (GM_PERCUSSION["LOW_TOM"], 0.75, 0.25, 95),
    ],
}


class DrumsGenerator:
    """Generates drum patterns in various styles."""

    def generate(
        self,
        style: DrumStyle,
        start_beat: float,
        end_beat: float,
        time_sig: tuple[int, int] = (4, 4),
    ) -> list[Note]:
        """Generate a full drum pattern for a given range."""
        template = DRUM_TEMPLATES.get(style.value, DRUM_TEMPLATES["rock"])
        beats_per_bar = time_sig[0]
        total_beats = end_beat - start_beat
        if total_beats <= 0:
            return []

        bars = int(total_beats / beats_per_bar)
        if bars < 1:
            bars = 1

        notes = []
        for bar_idx in range(bars):
            bar_offset = start_beat + bar_idx * beats_per_bar
            for _element_name, hits in template.items():
                for pitch, beat_off, dur, vel in hits:
                    abs_beat = bar_offset + beat_off
                    if abs_beat >= end_beat:
                        continue
                    notes.append(Note(
                        pitch=pitch, start_beat=abs_beat,
                        duration_beat=min(dur, end_beat - abs_beat),
                        velocity=vel + random.randint(-5, 5),
                    ))
        return notes

    def set_style(self, notes: list[Note], new_style: DrumStyle,
                  start_beat: float, end_beat: float,
                  time_sig: tuple[int, int] = (4, 4)) -> list[Note]:
        """Replace drum pattern in range with new style."""
        # Keep notes outside range
        outside = [n for n in notes if n.start_beat < start_beat or n.start_beat >= end_beat]
        new_notes = self.generate(new_style, start_beat, end_beat, time_sig)
        return outside + new_notes

    def add_fill(self, notes: list[Note], beat_position: float,
                 fill_type: str = "basic") -> list[Note]:
        """Insert a drum fill at the given beat position."""
        fill = FILL_TEMPLATES.get(fill_type, FILL_TEMPLATES["basic"])
        fill_dur = max(beat_off + dur for _, beat_off, dur, _ in fill) if fill else 1.0

        # Remove existing notes in fill range
        result = [n for n in notes
                  if not (beat_position <= n.start_beat < beat_position + fill_dur)]

        for pitch, beat_off, dur, vel in fill:
            result.append(Note(
                pitch=pitch, start_beat=beat_position + beat_off,
                duration_beat=dur, velocity=vel + random.randint(-3, 3),
            ))

        # Add crash at fill end
        result.append(Note(
            pitch=GM_PERCUSSION["CRASH_1"], start_beat=beat_position + fill_dur,
            duration_beat=0.5, velocity=110,
        ))

        return result

    def add_ghost_notes(self, notes: list[Note], start_beat: float,
                        end_beat: float, density: float = 0.3) -> list[Note]:
        """Add ghost notes (low velocity snare) on empty 16th positions."""
        result = list(notes)
        existing_beats = {round(n.start_beat, 4) for n in notes
                          if n.pitch in (GM_PERCUSSION["SNARE"], GM_PERCUSSION["SIDE_STICK"])}

        pos = start_beat
        while pos < end_beat:
            if round(pos, 4) not in existing_beats and random.random() < density:
                result.append(Note(
                    pitch=GM_PERCUSSION["SNARE"], start_beat=pos,
                    duration_beat=0.125, velocity=random.randint(20, 40),
                ))
            pos += 0.25

        return result

    def set_hihat_pattern(self, notes: list[Note], pattern: HiHatPattern,
                          start_beat: float, end_beat: float) -> list[Note]:
        """Set hi-hat pattern, replacing existing hi-hat notes in range."""
        hh_pitches = {GM_PERCUSSION["CLOSED_HH"], GM_PERCUSSION["OPEN_HH"], GM_PERCUSSION["PEDAL_HH"]}
        result = [n for n in notes
                  if not (start_beat <= n.start_beat < end_beat and n.pitch in hh_pitches)]

        pos = start_beat
        if pattern == HiHatPattern.EIGHTHS:
            while pos < end_beat:
                result.append(Note(pitch=GM_PERCUSSION["CLOSED_HH"], start_beat=pos,
                                   duration_beat=0.5, velocity=random.randint(70, 85)))
                pos += 0.5
        elif pattern == HiHatPattern.SIXTEENTHS:
            while pos < end_beat:
                result.append(Note(pitch=GM_PERCUSSION["CLOSED_HH"], start_beat=pos,
                                   duration_beat=0.25, velocity=random.randint(60, 80)))
                pos += 0.25
        elif pattern == HiHatPattern.OFFBEAT:
            while pos < end_beat:
                result.append(Note(pitch=GM_PERCUSSION["OPEN_HH"], start_beat=pos + 0.25,
                                   duration_beat=0.25, velocity=random.randint(70, 85)))
                pos += 0.5
        elif pattern == HiHatPattern.OPEN_CLOSE:
            i = 0
            while pos < end_beat:
                pitch = GM_PERCUSSION["CLOSED_HH"] if i % 2 == 0 else GM_PERCUSSION["OPEN_HH"]
                result.append(Note(pitch=pitch, start_beat=pos,
                                   duration_beat=0.5, velocity=random.randint(70, 85)))
                pos += 0.5
                i += 1

        return result

    def set_kick_pattern(self, notes: list[Note], pattern: KickPattern,
                         start_beat: float, end_beat: float) -> list[Note]:
        """Set kick drum pattern, replacing existing kicks in range."""
        result = [n for n in notes
                  if not (start_beat <= n.start_beat < end_beat and n.pitch == GM_PERCUSSION["KICK"])]

        beats_per_bar = 4
        bar_start = start_beat
        while bar_start < end_beat:
            if pattern == KickPattern.STRAIGHT:
                for off in [0.0, 2.0]:
                    if bar_start + off < end_beat:
                        result.append(Note(pitch=GM_PERCUSSION["KICK"], start_beat=bar_start + off,
                                           duration_beat=0.5, velocity=random.randint(95, 110)))
            elif pattern == KickPattern.OFFBEAT:
                for off in [0.5, 2.5]:
                    if bar_start + off < end_beat:
                        result.append(Note(pitch=GM_PERCUSSION["KICK"], start_beat=bar_start + off,
                                           duration_beat=0.5, velocity=random.randint(90, 105)))
            elif pattern == KickPattern.DOUBLE:
                for off in [0.0, 0.5, 2.0, 2.5]:
                    if bar_start + off < end_beat:
                        result.append(Note(pitch=GM_PERCUSSION["KICK"], start_beat=bar_start + off,
                                           duration_beat=0.5, velocity=random.randint(95, 110)))
            elif pattern == KickPattern.FOUR_ON_FLOOR:
                for off in [0.0, 1.0, 2.0, 3.0]:
                    if bar_start + off < end_beat:
                        result.append(Note(pitch=GM_PERCUSSION["KICK"], start_beat=bar_start + off,
                                           duration_beat=0.5, velocity=random.randint(100, 115)))
            bar_start += beats_per_bar

        return result

    def set_snare_pattern(self, notes: list[Note], pattern: SnarePattern,
                          start_beat: float, end_beat: float) -> list[Note]:
        """Set snare pattern, replacing existing snares in range."""
        snare_pitches = {GM_PERCUSSION["SNARE"], GM_PERCUSSION["SIDE_STICK"]}
        result = [n for n in notes
                  if not (start_beat <= n.start_beat < end_beat and n.pitch in snare_pitches)]

        beats_per_bar = 4
        bar_start = start_beat
        while bar_start < end_beat:
            if pattern == SnarePattern.BACKBEAT:
                for off in [1.0, 3.0]:
                    if bar_start + off < end_beat:
                        result.append(Note(pitch=GM_PERCUSSION["SNARE"], start_beat=bar_start + off,
                                           duration_beat=0.5, velocity=random.randint(95, 110)))
            elif pattern == SnarePattern.GHOST:
                for off in [1.0, 3.0]:
                    if bar_start + off < end_beat:
                        result.append(Note(pitch=GM_PERCUSSION["SNARE"], start_beat=bar_start + off,
                                           duration_beat=0.5, velocity=random.randint(95, 110)))
                # Add ghost notes
                for off in [0.75, 1.5, 2.75, 3.5]:
                    if bar_start + off < end_beat and random.random() < 0.5:
                        result.append(Note(pitch=GM_PERCUSSION["SNARE"], start_beat=bar_start + off,
                                           duration_beat=0.125, velocity=random.randint(25, 40)))
            elif pattern == SnarePattern.RIMSHOT:
                for off in [1.0, 3.0]:
                    if bar_start + off < end_beat:
                        result.append(Note(pitch=GM_PERCUSSION["SIDE_STICK"], start_beat=bar_start + off,
                                           duration_beat=0.5, velocity=random.randint(80, 100)))
            bar_start += beats_per_bar

        return result

    def add_crash(self, notes: list[Note], beat_position: float) -> list[Note]:
        """Add a crash cymbal at the specified beat."""
        result = list(notes)
        result.append(Note(
            pitch=GM_PERCUSSION["CRASH_1"], start_beat=beat_position,
            duration_beat=1.0, velocity=random.randint(100, 120),
        ))
        return result

    def set_ride_pattern(self, notes: list[Note], start_beat: float,
                         end_beat: float, swing: bool = False) -> list[Note]:
        """Set ride cymbal pattern."""
        ride_pitches = {GM_PERCUSSION["RIDE"], GM_PERCUSSION["RIDE_BELL"]}
        result = [n for n in notes
                  if not (start_beat <= n.start_beat < end_beat and n.pitch in ride_pitches)]

        beats_per_bar = 4
        bar_start = start_beat
        while bar_start < end_beat:
            if swing:
                hits = [(0.0, 1.0, 80), (1.0, 0.33, 65), (1.67, 0.33, 75),
                        (2.0, 1.0, 80), (3.0, 0.33, 65), (3.67, 0.33, 75)]
            else:
                hits = [(i * 0.5, 0.5, 75) for i in range(8)]

            for off, dur, vel in hits:
                if bar_start + off < end_beat:
                    result.append(Note(
                        pitch=GM_PERCUSSION["RIDE"], start_beat=bar_start + off,
                        duration_beat=dur, velocity=vel + random.randint(-3, 3),
                    ))
            bar_start += beats_per_bar

        return result

    def add_tom_fill(self, notes: list[Note], beat_position: float,
                     fill_beats: float = 1.0) -> list[Note]:
        """Add a tom cascade fill."""
        result = list(notes)
        toms = [GM_PERCUSSION["HIGH_TOM"], GM_PERCUSSION["MID_TOM"],
                GM_PERCUSSION["LOW_TOM"], GM_PERCUSSION["FLOOR_TOM"]]
        step = fill_beats / len(toms)
        for i, tom in enumerate(toms):
            result.append(Note(
                pitch=tom, start_beat=beat_position + i * step,
                duration_beat=step, velocity=random.randint(90, 110) - i * 3,
            ))
        return result

    def add_percussion(self, notes: list[Note], element: str,
                       start_beat: float, end_beat: float,
                       pattern: str = "quarter") -> list[Note]:
        """Add a percussion element (tambourine, cowbell, etc)."""
        pitch_map = {
            "tambourine": GM_PERCUSSION["TAMBOURINE"],
            "cowbell": GM_PERCUSSION["COWBELL"],
            "claves": GM_PERCUSSION["CLAVES"],
        }
        pitch = pitch_map.get(element.lower(), GM_PERCUSSION["TAMBOURINE"])

        step_map = {"quarter": 1.0, "eighth": 0.5, "sixteenth": 0.25}
        step = step_map.get(pattern, 1.0)

        result = list(notes)
        pos = start_beat
        while pos < end_beat:
            result.append(Note(
                pitch=pitch, start_beat=pos,
                duration_beat=step * 0.8, velocity=random.randint(70, 90),
            ))
            pos += step

        return result

    def clear_element(self, notes: list[Note], element: str,
                      start_beat: float, end_beat: float) -> list[Note]:
        """Remove a specific drum element from the range."""
        element_pitches = {
            "kick": {GM_PERCUSSION["KICK"]},
            "snare": {GM_PERCUSSION["SNARE"], GM_PERCUSSION["SIDE_STICK"]},
            "hihat": {GM_PERCUSSION["CLOSED_HH"], GM_PERCUSSION["OPEN_HH"], GM_PERCUSSION["PEDAL_HH"]},
            "crash": {GM_PERCUSSION["CRASH_1"], GM_PERCUSSION["CRASH_2"]},
            "ride": {GM_PERCUSSION["RIDE"], GM_PERCUSSION["RIDE_BELL"]},
            "tom": {GM_PERCUSSION["HIGH_TOM"], GM_PERCUSSION["MID_TOM"],
                    GM_PERCUSSION["LOW_TOM"], GM_PERCUSSION["FLOOR_TOM"]},
            "tambourine": {GM_PERCUSSION["TAMBOURINE"]},
            "cowbell": {GM_PERCUSSION["COWBELL"]},
            "claves": {GM_PERCUSSION["CLAVES"]},
        }
        pitches_to_remove = element_pitches.get(element.lower(), set())
        return [n for n in notes
                if not (start_beat <= n.start_beat < end_beat and n.pitch in pitches_to_remove)]
