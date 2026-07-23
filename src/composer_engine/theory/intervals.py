"""Interval utilities.

Aligned with TECHNICAL.md 5.8.
"""

INTERVAL_NAMES: dict[int, str] = {
    0: "P1", 1: "m2", 2: "M2", 3: "m3", 4: "M3", 5: "P4",
    6: "A4/d5", 7: "P5", 8: "m6", 9: "M6", 10: "m7", 11: "M7",
}


def interval_between(pitch_a: int, pitch_b: int) -> int:
    """Get the interval in semitones between two pitches (mod 12)."""
    return (pitch_b - pitch_a) % 12


def interval_name(semitones: int) -> str:
    """Get the name of an interval."""
    return INTERVAL_NAMES.get(semitones % 12, "?")


def transpose(pitch: int, semitones: int) -> int:
    """Transpose a pitch by semitones (preserves octave)."""
    return pitch + semitones
