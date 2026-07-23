"""Tests for the music theory module."""

from composer_engine.models.enums import Key, Mode
from composer_engine.theory.chord_utils import (
    get_chord_pitch_classes,
    resolve_roman,
    roman_analysis,
)
from composer_engine.theory.intervals import interval_between, interval_name, transpose
from composer_engine.theory.scales import (
    get_scale_notes_in_range,
    get_scale_pitches,
    is_in_scale,
    get_scale_degree,
    pitch_class_to_key,
)


class TestScales:
    def test_c_major_scale(self):
        pcs = get_scale_pitches(Key.C, Mode.MAJOR)
        assert pcs == [0, 2, 4, 5, 7, 9, 11]

    def test_a_minor_scale(self):
        pcs = get_scale_pitches(Key.A, Mode.MINOR)
        assert pcs == [9, 11, 0, 2, 4, 5, 7]

    def test_g_major_scale(self):
        pcs = get_scale_pitches(Key.G, Mode.MAJOR)
        assert 7 in pcs  # G
        assert 11 in pcs  # B
        assert 6 in pcs  # F#

    def test_scale_notes_in_range(self):
        notes = get_scale_notes_in_range(Key.C, Mode.MAJOR, 60, 72)
        assert 60 in notes  # C4
        assert 64 in notes  # E4
        assert 67 in notes  # G4
        assert 72 in notes  # C5
        assert 61 not in notes  # C#4 not in C major
        assert 63 not in notes  # Eb4 not in C major

    def test_is_in_scale(self):
        assert is_in_scale(60, Key.C, Mode.MAJOR)  # C
        assert not is_in_scale(61, Key.C, Mode.MAJOR)  # C#

    def test_scale_degree(self):
        assert get_scale_degree(60, Key.C, Mode.MAJOR) == 1  # C is 1st
        assert get_scale_degree(64, Key.C, Mode.MAJOR) == 3  # E is 3rd
        assert get_scale_degree(67, Key.C, Mode.MAJOR) == 5  # G is 5th
        assert get_scale_degree(61, Key.C, Mode.MAJOR) is None  # C# not in scale

    def test_pitch_class_to_key(self):
        assert pitch_class_to_key(0) == Key.C
        assert pitch_class_to_key(7) == Key.G
        assert pitch_class_to_key(12) == Key.C  # wraps


class TestIntervals:
    def test_interval_between(self):
        assert interval_between(60, 67) == 7  # C to G = P5
        assert interval_between(60, 64) == 4  # C to E = M3

    def test_interval_name(self):
        assert interval_name(7) == "P5"
        assert interval_name(4) == "M3"
        assert interval_name(0) == "P1"

    def test_transpose(self):
        assert transpose(60, 7) == 67
        assert transpose(60, -12) == 48


class TestChordUtils:
    def test_c_major_chord(self):
        pcs = get_chord_pitch_classes(Key.C, "major")
        assert pcs == [0, 4, 7]

    def test_a_minor_chord(self):
        pcs = get_chord_pitch_classes(Key.A, "minor")
        assert 9 in pcs  # A
        assert 0 in pcs  # C
        assert 4 in pcs  # E

    def test_g_dom7_chord(self):
        pcs = get_chord_pitch_classes(Key.G, "dom7")
        assert 7 in pcs  # G
        assert 11 in pcs  # B
        assert 2 in pcs  # D
        assert 5 in pcs  # F

    def test_resolve_roman_v_in_c(self):
        root, quality = resolve_roman("V", Key.C, Mode.MAJOR)
        assert root == Key.G
        assert quality == "major"

    def test_resolve_roman_ii7_in_c(self):
        root, quality = resolve_roman("ii7", Key.C, Mode.MAJOR)
        assert root == Key.D
        assert quality == "min7"

    def test_resolve_roman_bvii_in_c(self):
        root, quality = resolve_roman("bVII", Key.C, Mode.MAJOR)
        assert root == Key.Bb
        assert quality == "major"

    def test_resolve_roman_vi_in_c(self):
        root, quality = resolve_roman("vi", Key.C, Mode.MAJOR)
        assert root == Key.A
        assert quality == "minor"

    def test_roman_analysis_v(self):
        label = roman_analysis(Key.G, "major", Key.C, Mode.MAJOR)
        assert label == "V"

    def test_roman_analysis_ii(self):
        label = roman_analysis(Key.D, "minor", Key.C, Mode.MAJOR)
        assert label == "ii"

    def test_roman_analysis_iv(self):
        label = roman_analysis(Key.F, "major", Key.C, Mode.MAJOR)
        assert label == "IV"
