"""Tests for InstrumentGenerator and instrument commands.

Phase 5: REQUIREMENTS.md 4.5 / TECHNICAL.md 5.12.
"""

import pytest

from composer_engine.generators.instrument_generator import InstrumentGenerator
from composer_engine.commands.instrument_commands import (
    GenerateBrassCommand,
    GenerateGuitarPartCommand,
    GeneratePianoPartCommand,
    GenerateStringsCommand,
    GenerateSynthCommand,
    GenerateWoodwindsCommand,
)
from composer_engine.models.chord import Chord, ChordQuality
from composer_engine.models.enums import (
    BrassMode,
    GuitarMode,
    InstrumentType,
    Key,
    Mode,
    PianoMode,
    StringsMode,
    SynthMode,
    WoodwindsMode,
)
from composer_engine.models.song import Song
from composer_engine.models.track import Track


def _make_song_with_chords() -> Song:
    song = Song(name="Test Instruments")
    song.global_settings.key = Key.C
    song.global_settings.mode = Mode.MAJOR
    song.chord_progression = [
        Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=0, duration_beat=4),
        Chord(root=Key.F, quality=ChordQuality.MAJOR, start_beat=4, duration_beat=4),
        Chord(root=Key.G, quality=ChordQuality.MAJOR, start_beat=8, duration_beat=4),
        Chord(root=Key.C, quality=ChordQuality.MAJOR, start_beat=12, duration_beat=4),
    ]
    return song


# ──── InstrumentGenerator tests ────

class TestInstrumentGenerator:
    def setup_method(self):
        self.gen = InstrumentGenerator()
        self.song = _make_song_with_chords()
        self.chords = self.song.chord_progression

    # Strings
    def test_strings_sustained(self):
        notes = self.gen.generate_strings(self.chords, Key.C, Mode.MAJOR, 0, 16, StringsMode.SUSTAINED)
        assert len(notes) > 0
        assert all(55 <= n.pitch <= 88 for n in notes)

    def test_strings_melody(self):
        notes = self.gen.generate_strings(self.chords, Key.C, Mode.MAJOR, 0, 16, StringsMode.MELODY)
        assert len(notes) > 0

    def test_strings_tremolo(self):
        notes = self.gen.generate_strings(self.chords, Key.C, Mode.MAJOR, 0, 16, StringsMode.TREMOLO)
        assert len(notes) > 0
        assert all(n.duration_beat <= 0.25 for n in notes)

    def test_strings_pizzicato(self):
        notes = self.gen.generate_strings(self.chords, Key.C, Mode.MAJOR, 0, 16, StringsMode.PIZZICATO)
        assert len(notes) > 0
        assert all(n.duration_beat <= 0.5 for n in notes)

    def test_strings_counterpoint(self):
        notes = self.gen.generate_strings(self.chords, Key.C, Mode.MAJOR, 0, 16, StringsMode.COUNTERPOINT)
        assert len(notes) > 0

    # Brass
    def test_brass_stabs(self):
        notes = self.gen.generate_brass(self.chords, Key.C, Mode.MAJOR, 0, 16, BrassMode.STABS)
        assert len(notes) > 0
        assert all(n.duration_beat <= 0.5 for n in notes)

    def test_brass_sustained(self):
        notes = self.gen.generate_brass(self.chords, Key.C, Mode.MAJOR, 0, 16, BrassMode.SUSTAINED)
        assert len(notes) > 0

    def test_brass_fanfare(self):
        notes = self.gen.generate_brass(self.chords, Key.C, Mode.MAJOR, 0, 16, BrassMode.FANFARE)
        assert len(notes) > 0

    def test_brass_solo(self):
        notes = self.gen.generate_brass(self.chords, Key.C, Mode.MAJOR, 0, 16, BrassMode.SOLO_LINE)
        assert len(notes) > 0

    # Woodwinds
    def test_woodwinds_sustained(self):
        notes = self.gen.generate_woodwinds(self.chords, Key.C, Mode.MAJOR, 0, 16, WoodwindsMode.SUSTAINED)
        assert len(notes) > 0

    def test_woodwinds_trill(self):
        notes = self.gen.generate_woodwinds(self.chords, Key.C, Mode.MAJOR, 0, 16, WoodwindsMode.TRILL)
        assert len(notes) > 0

    def test_woodwinds_solo(self):
        notes = self.gen.generate_woodwinds(self.chords, Key.C, Mode.MAJOR, 0, 16, WoodwindsMode.SOLO_LINE)
        assert len(notes) > 0

    def test_woodwinds_stabs(self):
        notes = self.gen.generate_woodwinds(self.chords, Key.C, Mode.MAJOR, 0, 16, WoodwindsMode.STABS)
        assert len(notes) > 0

    # Synth
    def test_synth_pad(self):
        notes = self.gen.generate_synth(self.chords, Key.C, Mode.MAJOR, 0, 16, SynthMode.PAD)
        assert len(notes) > 0

    def test_synth_lead(self):
        notes = self.gen.generate_synth(self.chords, Key.C, Mode.MAJOR, 0, 16, SynthMode.LEAD)
        assert len(notes) > 0

    def test_synth_arp(self):
        notes = self.gen.generate_synth(self.chords, Key.C, Mode.MAJOR, 0, 16, SynthMode.ARP)
        assert len(notes) > 0

    def test_synth_fx(self):
        notes = self.gen.generate_synth(self.chords, Key.C, Mode.MAJOR, 0, 16, SynthMode.FX)
        assert len(notes) > 0

    # Piano
    def test_piano_block(self):
        notes = self.gen.generate_piano_part(self.chords, Key.C, Mode.MAJOR, 0, 16, PianoMode.BLOCK_CHORDS)
        assert len(notes) > 0

    def test_piano_broken(self):
        notes = self.gen.generate_piano_part(self.chords, Key.C, Mode.MAJOR, 0, 16, PianoMode.BROKEN_CHORDS)
        assert len(notes) > 0

    def test_piano_arp(self):
        notes = self.gen.generate_piano_part(self.chords, Key.C, Mode.MAJOR, 0, 16, PianoMode.ARPEGGIO)
        assert len(notes) > 0

    def test_piano_comping(self):
        notes = self.gen.generate_piano_part(self.chords, Key.C, Mode.MAJOR, 0, 16, PianoMode.COMPING)
        assert len(notes) > 0

    # Guitar
    def test_guitar_strum(self):
        notes = self.gen.generate_guitar_part(self.chords, Key.C, Mode.MAJOR, 0, 16, GuitarMode.STRUM)
        assert len(notes) > 0

    def test_guitar_fingerpick(self):
        notes = self.gen.generate_guitar_part(self.chords, Key.C, Mode.MAJOR, 0, 16, GuitarMode.FINGERPICK)
        assert len(notes) > 0

    def test_guitar_arp(self):
        notes = self.gen.generate_guitar_part(self.chords, Key.C, Mode.MAJOR, 0, 16, GuitarMode.ARPEGGIO)
        assert len(notes) > 0

    def test_guitar_muted(self):
        notes = self.gen.generate_guitar_part(self.chords, Key.C, Mode.MAJOR, 0, 16, GuitarMode.MUTED)
        assert len(notes) > 0

    # Edge cases
    def test_empty_chords(self):
        notes = self.gen.generate_strings([], Key.C, Mode.MAJOR, 0, 16, StringsMode.SUSTAINED)
        assert notes == []

    def test_zero_range(self):
        notes = self.gen.generate_brass(self.chords, Key.C, Mode.MAJOR, 0, 0, BrassMode.STABS)
        assert notes == []


# ──── Instrument Command tests ────

class TestInstrumentCommands:
    def test_generate_strings_command(self):
        song = _make_song_with_chords()
        cmd = GenerateStringsCommand(strings_mode="sustained")
        result = cmd.execute(song)
        strings = [t for t in result.tracks if t.instrument == InstrumentType.STRINGS]
        assert len(strings) >= 1
        assert len(strings[0].notes) > 0

    def test_generate_brass_command(self):
        song = _make_song_with_chords()
        cmd = GenerateBrassCommand(brass_mode="stabs")
        result = cmd.execute(song)
        brass = [t for t in result.tracks if t.instrument == InstrumentType.BRASS]
        assert len(brass) >= 1
        assert len(brass[0].notes) > 0

    def test_generate_woodwinds_command(self):
        song = _make_song_with_chords()
        cmd = GenerateWoodwindsCommand(woodwinds_mode="trill")
        result = cmd.execute(song)
        ww = [t for t in result.tracks if t.instrument == InstrumentType.WOODWINDS]
        assert len(ww) >= 1
        assert len(ww[0].notes) > 0

    def test_generate_synth_command(self):
        song = _make_song_with_chords()
        cmd = GenerateSynthCommand(synth_mode="pad")
        result = cmd.execute(song)
        synths = [t for t in result.tracks if t.instrument == InstrumentType.SYNTH]
        assert len(synths) >= 1
        assert len(synths[0].notes) > 0

    def test_generate_piano_part_command(self):
        song = _make_song_with_chords()
        cmd = GeneratePianoPartCommand(piano_mode="broken_chords")
        result = cmd.execute(song)
        pianos = [t for t in result.tracks if t.instrument == InstrumentType.PIANO]
        assert len(pianos) >= 1
        assert len(pianos[0].notes) > 0

    def test_generate_guitar_part_command(self):
        song = _make_song_with_chords()
        cmd = GenerateGuitarPartCommand(guitar_mode="strum")
        result = cmd.execute(song)
        guitars = [t for t in result.tracks if t.instrument == InstrumentType.GUITAR]
        assert len(guitars) >= 1
        assert len(guitars[0].notes) > 0

    def test_generate_with_existing_track(self):
        song = _make_song_with_chords()
        track = Track.create("My Strings", InstrumentType.STRINGS)
        song.tracks.append(track)
        cmd = GenerateStringsCommand(track_id=track.id, strings_mode="pizzicato")
        result = cmd.execute(song)
        t = next(t for t in result.tracks if t.id == track.id)
        assert len(t.notes) > 0
