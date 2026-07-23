"""Chord progression generator.

Aligned with TECHNICAL.md 5.9.
"""

import random

from composer_engine.models.chord import CadenceType, Chord, ChordQuality
from composer_engine.models.enums import Key, Mode
from composer_engine.theory.chord_utils import resolve_roman, roman_analysis
from composer_engine.theory.scales import KEY_TO_PITCH

CHORD_TEMPLATES: dict[str, list[dict]] = {
    "pop": [
        {"name": "pop_classic",   "roman": ["I", "V", "vi", "IV"]},
        {"name": "pop_50s",       "roman": ["I", "vi", "IV", "V"]},
        {"name": "pop_emotional", "roman": ["vi", "IV", "I", "V"]},
        {"name": "canon",         "roman": ["I", "V", "vi", "iii", "IV", "I", "IV", "V"]},
    ],
    "rock": [
        {"name": "rock_basic", "roman": ["I", "IV", "V", "I"]},
        {"name": "rock_power", "roman": ["I", "bVII", "IV", "I"]},
        {"name": "rock_alt",   "roman": ["I", "V", "bVII", "IV"]},
    ],
    "jazz": [
        {"name": "jazz_251",        "roman": ["ii7", "V7", "Imaj7"]},
        {"name": "jazz_turnaround", "roman": ["Imaj7", "vi7", "ii7", "V7"]},
    ],
    "blues": [
        {"name": "blues_12bar", "roman": [
            "I7", "I7", "I7", "I7", "IV7", "IV7", "I7", "I7", "V7", "IV7", "I7", "V7",
        ]},
    ],
    "anime": [
        {"name": "royal_road",   "roman": ["IV", "V", "iii", "vi"]},
        {"name": "komuro",       "roman": ["vi", "V", "IV", "V"]},
        {"name": "just_the_two", "roman": ["I", "V", "vi", "iii", "IV", "I", "ii", "V"]},
    ],
    "classical": [
        {"name": "authentic", "roman": ["I", "IV", "V", "I"]},
        {"name": "romantic",  "roman": ["I", "vi", "ii", "V"]},
    ],
}

# Cadence endings: maps CadenceType to last 2 roman numerals
CADENCE_ENDINGS: dict[CadenceType, list[str]] = {
    CadenceType.AUTHENTIC: ["V", "I"],
    CadenceType.PLAGAL:    ["IV", "I"],
    CadenceType.HALF:      ["V"],
    CadenceType.DECEPTIVE: ["V", "vi"],
}

# Harmonic function classification
_TONIC_DEGREES = {0, 2, 5}       # I, iii, vi
_DOMINANT_DEGREES = {4, 6}       # V, vii
_SUBDOMINANT_DEGREES = {1, 3}    # ii, IV


class ChordGenerator:
    """Generates chord progressions."""

    def generate(
        self,
        key: Key,
        mode: Mode,
        style: str = "pop",
        length_beats: float = 16.0,
        beats_per_chord: float = 4.0,
        template_name: str | None = None,
    ) -> list[Chord]:
        """Generate a chord progression from a template."""
        templates = CHORD_TEMPLATES.get(style, CHORD_TEMPLATES["pop"])
        if template_name:
            template = next((t for t in templates if t["name"] == template_name), templates[0])
        else:
            template = random.choice(templates)

        roman_list = template["roman"]
        chords: list[Chord] = []
        beat = 0.0
        idx = 0

        while beat < length_beats:
            roman = roman_list[idx % len(roman_list)]
            root_key, quality = resolve_roman(roman, key, mode)
            duration = min(beats_per_chord, length_beats - beat)
            roman_label = roman_analysis(root_key, quality, key, mode)
            chords.append(Chord(
                root=root_key,
                quality=ChordQuality(quality),
                start_beat=beat,
                duration_beat=duration,
                roman=roman_label,
            ))
            beat += beats_per_chord
            idx += 1

        return chords

    def secondary_dominant(self, target_chord: Chord) -> Chord:
        """Create V/x - the secondary dominant of the target chord."""
        target_pc = KEY_TO_PITCH[target_chord.root]
        dom_pc = (target_pc + 7) % 12  # Perfect 5th above
        from composer_engine.theory.scales import pitch_class_to_key
        dom_key = pitch_class_to_key(dom_pc)
        return Chord(
            root=dom_key,
            quality=ChordQuality.DOM7,
            start_beat=target_chord.start_beat,
            duration_beat=target_chord.duration_beat / 2,
        )

    def passing_chord(self, chord_a: Chord, chord_b: Chord) -> Chord:
        """Create a chromatic passing chord between two chords."""
        pc_a = KEY_TO_PITCH[chord_a.root]
        pc_b = KEY_TO_PITCH[chord_b.root]
        if pc_b > pc_a or (pc_b == pc_a):
            passing_pc = (pc_a + 1) % 12
        else:
            passing_pc = (pc_a - 1) % 12
        from composer_engine.theory.scales import pitch_class_to_key
        passing_key = pitch_class_to_key(passing_pc)
        mid_beat = chord_a.start_beat + chord_a.duration_beat
        return Chord(
            root=passing_key,
            quality=ChordQuality.MAJOR,
            start_beat=mid_beat,
            duration_beat=min(chord_a.duration_beat, 2.0),
        )

    def borrow_chord(self, chord: Chord, key: Key, source_mode: Mode) -> Chord:
        """Borrow the same-degree chord from a parallel mode."""
        from composer_engine.theory.scales import SCALE_INTERVALS
        current_scale = SCALE_INTERVALS.get(Mode.MAJOR, SCALE_INTERVALS[Mode.MAJOR])
        target_scale = SCALE_INTERVALS.get(source_mode, SCALE_INTERVALS[Mode.MINOR])

        base_pc = KEY_TO_PITCH[key]
        chord_pc = KEY_TO_PITCH[chord.root]
        interval = (chord_pc - base_pc) % 12

        degree = None
        for i, s in enumerate(current_scale):
            if s == interval:
                degree = i
                break
        if degree is None:
            return chord

        new_root_pc = (base_pc + target_scale[degree]) % 12
        from composer_engine.theory.scales import pitch_class_to_key
        new_root = pitch_class_to_key(new_root_pc)

        from composer_engine.theory.chord_utils import DIATONIC_CHORDS
        diatonic = DIATONIC_CHORDS.get(source_mode, DIATONIC_CHORDS.get(Mode.MINOR))
        quality = "minor" if diatonic else "minor"
        if diatonic:
            for d, q in diatonic:
                if d == degree + 1:
                    quality = q
                    break

        return Chord(
            root=new_root,
            quality=ChordQuality(quality),
            start_beat=chord.start_beat,
            duration_beat=chord.duration_beat,
        )

    def set_cadence(
        self,
        chords: list[Chord],
        section_end_beat: float,
        cadence_type: CadenceType,
        key: Key,
        mode: Mode,
    ) -> list[Chord]:
        """Modify the ending chords to form a specific cadence."""
        ending_romans = CADENCE_ENDINGS[cadence_type]
        cadence_chords: list[Chord] = []
        beats_per = 2.0
        start = section_end_beat - beats_per * len(ending_romans)

        for i, roman in enumerate(ending_romans):
            root_key, quality = resolve_roman(roman, key, mode)
            cadence_chords.append(Chord(
                root=root_key,
                quality=ChordQuality(quality),
                start_beat=start + i * beats_per,
                duration_beat=beats_per,
                roman=roman_analysis(root_key, quality, key, mode),
            ))

        result = [c for c in chords if c.start_beat + c.duration_beat <= start]
        result.extend(cadence_chords)
        return result
