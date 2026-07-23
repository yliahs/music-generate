"""Scale computation utilities.

Aligned with TECHNICAL.md 5.8.
"""

from composer_engine.models.enums import Key, Mode

KEY_TO_PITCH: dict[Key, int] = {
    Key.C: 0, Key.Db: 1, Key.D: 2, Key.Eb: 3, Key.E: 4, Key.F: 5,
    Key.Gb: 6, Key.G: 7, Key.Ab: 8, Key.A: 9, Key.Bb: 10, Key.B: 11,
}

PITCH_TO_KEY: dict[int, Key] = {v: k for k, v in KEY_TO_PITCH.items()}

SCALE_INTERVALS: dict[Mode, list[int]] = {
    Mode.MAJOR:      [0, 2, 4, 5, 7, 9, 11],
    Mode.MINOR:      [0, 2, 3, 5, 7, 8, 10],
    Mode.DORIAN:     [0, 2, 3, 5, 7, 9, 10],
    Mode.MIXOLYDIAN: [0, 2, 4, 5, 7, 9, 10],
    Mode.LYDIAN:     [0, 2, 4, 6, 7, 9, 11],
    Mode.PHRYGIAN:   [0, 1, 3, 5, 7, 8, 10],
    Mode.LOCRIAN:    [0, 1, 3, 5, 6, 8, 10],
}


def get_scale_pitches(key: Key, mode: Mode) -> list[int]:
    """Get pitch classes (0-11) for a scale."""
    base = KEY_TO_PITCH[key]
    return [(base + interval) % 12 for interval in SCALE_INTERVALS[mode]]


def get_scale_notes_in_range(key: Key, mode: Mode, min_pitch: int, max_pitch: int) -> list[int]:
    """Get all MIDI pitches in a scale within a range."""
    pitch_classes = set(get_scale_pitches(key, mode))
    return [p for p in range(min_pitch, max_pitch + 1) if p % 12 in pitch_classes]


def is_in_scale(pitch: int, key: Key, mode: Mode) -> bool:
    """Check if a pitch belongs to the scale."""
    return pitch % 12 in set(get_scale_pitches(key, mode))


def get_scale_degree(pitch: int, key: Key, mode: Mode) -> int | None:
    """Get the 1-based scale degree of a pitch (None if not in scale)."""
    pc = pitch % 12
    scale = get_scale_pitches(key, mode)
    try:
        return scale.index(pc) + 1
    except ValueError:
        return None


def pitch_class_to_key(pc: int) -> Key:
    """Convert a pitch class (0-11) to a Key enum."""
    return PITCH_TO_KEY[pc % 12]
