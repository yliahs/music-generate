"""Chord spelling and Roman numeral analysis.

Aligned with TECHNICAL.md 5.8 + 5.9.
"""

from composer_engine.models.enums import Key, Mode
from composer_engine.theory.scales import KEY_TO_PITCH, SCALE_INTERVALS, pitch_class_to_key

CHORD_INTERVALS: dict[str, list[int]] = {
    "major":     [0, 4, 7],
    "minor":     [0, 3, 7],
    "diminished":[0, 3, 6],
    "augmented": [0, 4, 8],
    "dom7":      [0, 4, 7, 10],
    "maj7":      [0, 4, 7, 11],
    "min7":      [0, 3, 7, 10],
    "half_dim7": [0, 3, 6, 10],
    "dim7":      [0, 3, 6, 9],
    "sus2":      [0, 2, 7],
    "sus4":      [0, 5, 7],
    "add9":      [0, 4, 7, 14],
    "add11":     [0, 4, 7, 17],
    "dom9":      [0, 4, 7, 10, 14],
    "maj9":      [0, 4, 7, 11, 14],
    "min9":      [0, 3, 7, 10, 14],
}


def get_chord_pitch_classes(root: Key, quality: str) -> list[int]:
    """Get pitch classes for a chord."""
    base = KEY_TO_PITCH[root]
    intervals = CHORD_INTERVALS.get(quality, CHORD_INTERVALS["major"])
    return [(base + i) % 12 for i in intervals]


# Diatonic chord qualities for each scale degree (1-indexed)
DIATONIC_CHORDS: dict[Mode, list[tuple[int, str]]] = {
    Mode.MAJOR: [
        (1, "major"), (2, "minor"), (3, "minor"), (4, "major"),
        (5, "major"), (6, "minor"), (7, "diminished"),
    ],
    Mode.MINOR: [
        (1, "minor"), (2, "diminished"), (3, "major"), (4, "minor"),
        (5, "minor"), (6, "major"), (7, "major"),
    ],
    Mode.DORIAN: [
        (1, "minor"), (2, "minor"), (3, "major"), (4, "major"),
        (5, "minor"), (6, "diminished"), (7, "major"),
    ],
    Mode.MIXOLYDIAN: [
        (1, "major"), (2, "minor"), (3, "diminished"), (4, "major"),
        (5, "minor"), (6, "minor"), (7, "major"),
    ],
}

# Roman numeral labels
_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]
_ROMAN_LOWER = ["i", "ii", "iii", "iv", "v", "vi", "vii"]

_QUALITY_SUFFIXES = {
    "major": "", "minor": "", "diminished": "°", "augmented": "+",
    "dom7": "7", "maj7": "maj7", "min7": "7", "half_dim7": "ø7", "dim7": "°7",
    "sus2": "sus2", "sus4": "sus4",
}

_MINOR_QUALITIES = {"minor", "diminished", "min7", "half_dim7", "dim7", "min9"}


def _parse_roman(roman: str) -> tuple[int, str]:
    """Parse a roman numeral string into (scale_degree_0based, quality_hint)."""
    s = roman.strip()
    flat = False
    if s.startswith("b") or s.startswith("♭"):
        flat = True
        s = s[1:]

    quality_suffix = ""
    base_roman = s
    for suffix in ["maj7", "maj9", "min7", "min9", "°7", "ø7", "sus2", "sus4", "7", "°", "+"]:
        if s.endswith(suffix):
            base_roman = s[: -len(suffix)]
            quality_suffix = suffix
            break

    roman_map = {"I": 0, "II": 1, "III": 2, "IV": 3, "V": 4, "VI": 5, "VII": 6,
                 "i": 0, "ii": 1, "iii": 2, "iv": 3, "v": 4, "vi": 5, "vii": 6}
    degree = roman_map.get(base_roman, 0)
    is_lower = base_roman == base_roman.lower()

    suffix_to_quality = {
        "7": "dom7" if not is_lower else "min7",
        "maj7": "maj7", "maj9": "maj9", "min7": "min7", "min9": "min9",
        "°": "diminished", "°7": "dim7", "ø7": "half_dim7",
        "+": "augmented", "sus2": "sus2", "sus4": "sus4",
    }
    if quality_suffix:
        quality = suffix_to_quality.get(quality_suffix, "major")
    else:
        quality = "minor" if is_lower else "major"

    return degree, quality, flat


def resolve_roman(roman: str, key: Key, mode: Mode) -> tuple[Key, str]:
    """Resolve a Roman numeral to (root_key, chord_quality).

    Examples:
        resolve_roman("V", Key.C, Mode.MAJOR) → (Key.G, "major")
        resolve_roman("ii7", Key.C, Mode.MAJOR) → (Key.D, "min7")
        resolve_roman("bVII", Key.C, Mode.MAJOR) → (Key.Bb, "major")
    """
    degree, quality, flat = _parse_roman(roman)
    scale = SCALE_INTERVALS.get(mode, SCALE_INTERVALS[Mode.MAJOR])
    base_pc = KEY_TO_PITCH[key]
    root_pc = (base_pc + scale[degree]) % 12
    if flat:
        root_pc = (root_pc - 1) % 12
    root_key = pitch_class_to_key(root_pc)
    return root_key, quality


def roman_analysis(root: Key, quality: str, key: Key, mode: Mode) -> str:
    """Analyze a chord and return its Roman numeral label.

    Examples:
        roman_analysis(Key.G, "major", Key.C, Mode.MAJOR) → "V"
        roman_analysis(Key.D, "min7", Key.C, Mode.MAJOR) → "ii7"
    """
    base_pc = KEY_TO_PITCH[key]
    root_pc = KEY_TO_PITCH[root]
    interval = (root_pc - base_pc) % 12

    scale = SCALE_INTERVALS.get(mode, SCALE_INTERVALS[Mode.MAJOR])
    degree = None
    flat_prefix = ""
    for i, s in enumerate(scale):
        if s == interval:
            degree = i
            break
    if degree is None:
        for i, s in enumerate(scale):
            if (s - 1) % 12 == interval:
                degree = i
                flat_prefix = "♭"
                break
    if degree is None:
        degree = 0

    is_minor = quality in _MINOR_QUALITIES
    numeral = _ROMAN_LOWER[degree] if is_minor else _ROMAN[degree]
    suffix = _QUALITY_SUFFIXES.get(quality, "")
    return f"{flat_prefix}{numeral}{suffix}"
