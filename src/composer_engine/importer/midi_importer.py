"""MIDI Importer - .mid file -> Song model.

Symmetric counterpart of renderer/midi_renderer.py.
Aligned with TECHNICAL.md 5.19 / REQUIREMENTS.md 4.13.
"""

from pathlib import Path

import pretty_midi

from composer_engine.models.enums import (
    DRUMS_CHANNEL,
    InstrumentType,
    Key,
    Mode,
)
from composer_engine.models.note import Note
from composer_engine.models.song import Song
from composer_engine.models.track import Track


# GM Program ranges → InstrumentType (REQUIREMENTS.md 4.13.1)
_PROGRAM_RANGES: list[tuple[range, InstrumentType]] = [
    (range(0, 24), InstrumentType.PIANO),
    (range(24, 32), InstrumentType.GUITAR),
    (range(32, 40), InstrumentType.BASS),
    (range(40, 56), InstrumentType.STRINGS),
    (range(56, 64), InstrumentType.BRASS),
    (range(64, 80), InstrumentType.WOODWINDS),
    (range(80, 88), InstrumentType.LEAD),
    (range(88, 96), InstrumentType.PAD),
    (range(96, 104), InstrumentType.FX),
    (range(104, 112), InstrumentType.GUITAR),
    (range(112, 128), InstrumentType.FX),
]

_KEY_MAP = [Key.C, Key.Db, Key.D, Key.Eb, Key.E, Key.F,
            Key.Gb, Key.G, Key.Ab, Key.A, Key.Bb, Key.B]


class MidiImporter:
    """Import MIDI files into Song model."""

    def import_file(self, file_path: str, song_name: str | None = None) -> Song:
        """Parse a complete MIDI file into a Song.

        Args:
            file_path: Path to the .mid file
            song_name: Optional song name (defaults to filename)

        Returns:
            A fully populated Song object
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"MIDI file not found: {file_path}")

        pm = pretty_midi.PrettyMIDI(str(path))
        tempo = self._get_tempo(pm)
        key, mode = self._get_key_signature(pm)
        ts_num, ts_den = self._get_time_signature(pm)

        name = song_name or path.stem
        song = Song(name=name)
        song.global_settings.tempo = tempo
        song.global_settings.key = key
        song.global_settings.mode = mode
        song.global_settings.time_signature = (ts_num, ts_den)

        for i, instrument in enumerate(pm.instruments):
            track = self._instrument_to_track(instrument, i, tempo)
            song.tracks.append(track)

        return song

    def import_single_track(self, file_path: str, track_index: int) -> Track:
        """Parse a single track from a MIDI file.

        Args:
            file_path: Path to the .mid file
            track_index: Index of the MIDI instrument/track to import

        Returns:
            A Track object with notes
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"MIDI file not found: {file_path}")

        pm = pretty_midi.PrettyMIDI(str(path))
        if track_index < 0 or track_index >= len(pm.instruments):
            raise IndexError(
                f"Track index {track_index} out of range "
                f"(file has {len(pm.instruments)} tracks)"
            )

        tempo = self._get_tempo(pm)
        return self._instrument_to_track(pm.instruments[track_index], track_index, tempo)

    def get_info(self, file_path: str) -> dict:
        """Get MIDI file metadata without creating a Song.

        Args:
            file_path: Path to the .mid file

        Returns:
            Dict with file info: tempo, time_signature, key, duration,
            total_notes, and per-track details
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"MIDI file not found: {file_path}")

        pm = pretty_midi.PrettyMIDI(str(path))
        tempo = self._get_tempo(pm)
        key, mode = self._get_key_signature(pm)
        ts_num, ts_den = self._get_time_signature(pm)

        tracks_info = []
        total_notes = 0
        for i, inst in enumerate(pm.instruments):
            note_count = len(inst.notes)
            total_notes += note_count
            pitches = [n.pitch for n in inst.notes] if inst.notes else []
            tracks_info.append({
                "index": i,
                "name": inst.name or f"Track {i + 1}",
                "program": inst.program,
                "is_drum": inst.is_drum,
                "instrument_type": self._program_to_instrument_type(
                    inst.program, inst.is_drum
                ).value,
                "note_count": note_count,
                "pitch_range": [min(pitches), max(pitches)] if pitches else None,
            })

        return {
            "file": str(path.name),
            "tempo": round(tempo, 2),
            "time_signature": f"{ts_num}/{ts_den}",
            "key": f"{key.value} {mode.value}",
            "duration_seconds": round(pm.get_end_time(), 2),
            "duration_beats": round(self._seconds_to_beat(pm.get_end_time(), tempo), 2),
            "track_count": len(pm.instruments),
            "total_notes": total_notes,
            "tracks": tracks_info,
        }

    # ── Internal helpers ──────────────────────────────────────────────────

    def _get_tempo(self, pm: pretty_midi.PrettyMIDI) -> float:
        """Extract tempo (first value, or 120 default)."""
        tempi = pm.get_tempo_changes()
        if tempi is not None and len(tempi[1]) > 0:
            return float(tempi[1][0])
        return 120.0

    def _get_time_signature(self, pm: pretty_midi.PrettyMIDI) -> tuple[int, int]:
        """Extract time signature (first value, or 4/4 default)."""
        if pm.time_signature_changes:
            ts = pm.time_signature_changes[0]
            return ts.numerator, ts.denominator
        return 4, 4

    def _get_key_signature(self, pm: pretty_midi.PrettyMIDI) -> tuple[Key, Mode]:
        """Extract key signature (first value, or C Major default)."""
        if pm.key_signature_changes:
            return self._parse_key_number(pm.key_signature_changes[0].key_number)
        return Key.C, Mode.MAJOR

    def _parse_key_number(self, key_number: int) -> tuple[Key, Mode]:
        """Convert pretty_midi key_number to (Key, Mode)."""
        idx = key_number % 12
        mode = Mode.MINOR if key_number >= 12 else Mode.MAJOR
        return _KEY_MAP[idx], mode

    def _seconds_to_beat(self, seconds: float, tempo: float) -> float:
        """Convert seconds to beat position (inverse of MidiRenderer._beat_to_seconds)."""
        return seconds * tempo / 60.0

    def _program_to_instrument_type(self, program: int, is_drum: bool) -> InstrumentType:
        """Map GM program number to InstrumentType."""
        if is_drum:
            return InstrumentType.DRUMS
        for r, itype in _PROGRAM_RANGES:
            if program in r:
                return itype
        return InstrumentType.PIANO

    def _instrument_to_track(
        self, instrument: pretty_midi.Instrument, index: int, tempo: float
    ) -> Track:
        """Convert a pretty_midi Instrument to a Track."""
        is_drum = instrument.is_drum
        inst_type = self._program_to_instrument_type(instrument.program, is_drum)
        name = instrument.name or f"Track {index + 1}"

        notes = []
        for n in instrument.notes:
            start_beat = self._seconds_to_beat(n.start, tempo)
            end_beat = self._seconds_to_beat(n.end, tempo)
            duration_beat = max(0.01, end_beat - start_beat)
            notes.append(Note(
                pitch=n.pitch,
                start_beat=round(start_beat, 4),
                duration_beat=round(duration_beat, 4),
                velocity=n.velocity,
            ))

        return Track(
            name=name,
            instrument=inst_type,
            program=instrument.program,
            channel=DRUMS_CHANNEL if is_drum else 0,
            notes=notes,
        )
