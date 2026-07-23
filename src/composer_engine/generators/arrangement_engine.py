"""Arrangement engine for high-level song arrangement operations.

Aligned with TECHNICAL.md 5.12.
"""

import random

from composer_engine.generators.drums_generator import DrumsGenerator
from composer_engine.models.enums import GM_PERCUSSION, InstrumentType
from composer_engine.models.note import Note
from composer_engine.models.song import Song
from composer_engine.models.track import Track


def _get_section_range(song: Song, section_id: str):
    for s in song.sections:
        if s.id == section_id:
            return s.start_beat, s.start_beat + s.length_beats
    return None


def _tracks_with_notes_in_range(song: Song, start: float, end: float) -> list:
    result = []
    for t in song.tracks:
        has_notes = any(start <= n.start_beat < end for n in t.notes)
        if has_notes:
            result.append(t)
    return result


class ArrangementEngine:
    """High-level arrangement operations that affect multiple tracks."""

    def increase_energy(self, song: Song, section_id: str, amount: float = 0.5) -> Song:
        """Increase energy: boost velocities, optionally add layers."""
        rng = _get_section_range(song, section_id)
        if not rng:
            return song
        start, end = rng
        vel_boost = int(amount * 20)
        for track in song.tracks:
            for note in track.notes:
                if start <= note.start_beat < end:
                    note.velocity = min(127, note.velocity + vel_boost)
        return song

    def decrease_energy(self, song: Song, section_id: str, amount: float = 0.5) -> Song:
        """Decrease energy: reduce velocities."""
        rng = _get_section_range(song, section_id)
        if not rng:
            return song
        start, end = rng
        vel_drop = int(amount * 20)
        for track in song.tracks:
            for note in track.notes:
                if start <= note.start_beat < end:
                    note.velocity = max(1, note.velocity - vel_drop)
        return song

    def increase_density(self, song: Song, section_id: str, amount: float = 0.5) -> Song:
        """Increase density: subdivide long notes."""
        rng = _get_section_range(song, section_id)
        if not rng:
            return song
        start, end = rng
        for track in song.tracks:
            if track.instrument == InstrumentType.DRUMS:
                continue
            new_notes = []
            for note in track.notes:
                if start <= note.start_beat < end and note.duration_beat >= 1.0 and random.random() < amount:
                    half = note.duration_beat / 2
                    new_notes.append(Note(pitch=note.pitch, start_beat=note.start_beat,
                                          duration_beat=half, velocity=note.velocity))
                    new_notes.append(Note(pitch=note.pitch, start_beat=note.start_beat + half,
                                          duration_beat=half, velocity=note.velocity - 5))
                else:
                    new_notes.append(note)
            track.notes = new_notes
        return song

    def decrease_density(self, song: Song, section_id: str, amount: float = 0.5) -> Song:
        """Decrease density: remove short notes, merge same-pitch neighbors."""
        rng = _get_section_range(song, section_id)
        if not rng:
            return song
        start, end = rng
        min_dur = 0.25 + amount * 0.75
        for track in song.tracks:
            if track.instrument == InstrumentType.DRUMS:
                continue
            track.notes = [n for n in track.notes
                           if not (start <= n.start_beat < end) or n.duration_beat >= min_dur]
        return song

    def add_layer(self, song: Song, section_id: str,
                  instrument_type: InstrumentType | None = None) -> Song:
        """Add an instrument layer to a section."""
        rng = _get_section_range(song, section_id)
        if not rng:
            return song
        start, end = rng

        if instrument_type is None:
            existing = {t.instrument for t in song.tracks if any(start <= n.start_beat < end for n in t.notes)}
            priority = [InstrumentType.DRUMS, InstrumentType.BASS, InstrumentType.PIANO,
                        InstrumentType.STRINGS, InstrumentType.PAD]
            instrument_type = next((i for i in priority if i not in existing), InstrumentType.PAD)

        track = Track.create(instrument_type.value.capitalize(), instrument_type)
        song.tracks.append(track)
        return song

    def remove_layer(self, song: Song, section_id: str, track_id: str) -> Song:
        """Remove notes from a track in a section."""
        rng = _get_section_range(song, section_id)
        if not rng:
            return song
        start, end = rng
        for track in song.tracks:
            if track.id == track_id:
                track.notes = [n for n in track.notes if not (start <= n.start_beat < end)]
                break
        return song

    def build_up(self, song: Song, target_beat: float, build_beats: float = 4.0) -> Song:
        """Create a build-up leading to target_beat."""
        build_start = target_beat - build_beats
        # Add snare roll crescendo to drums tracks
        for track in song.tracks:
            if track.instrument == InstrumentType.DRUMS:
                steps = int(build_beats / 0.25)
                for i in range(steps):
                    pos = build_start + i * 0.25
                    vel = int(60 + (i / max(steps, 1)) * 60)
                    track.notes.append(Note(
                        pitch=GM_PERCUSSION["SNARE"], start_beat=pos,
                        duration_beat=0.25, velocity=min(127, vel),
                    ))
                # Crash at target
                track.notes.append(Note(
                    pitch=GM_PERCUSSION["CRASH_1"], start_beat=target_beat,
                    duration_beat=1.0, velocity=120,
                ))
            else:
                # Increase velocities linearly
                for note in track.notes:
                    if build_start <= note.start_beat < target_beat:
                        frac = (note.start_beat - build_start) / build_beats
                        note.velocity = min(127, note.velocity + int(frac * 20))
        return song

    def break_down(self, song: Song, section_id: str) -> Song:
        """Break down: mute non-core tracks, reduce velocity."""
        rng = _get_section_range(song, section_id)
        if not rng:
            return song
        start, end = rng
        core_instruments = {InstrumentType.PIANO, InstrumentType.GUITAR, InstrumentType.PAD,
                            InstrumentType.LEAD, InstrumentType.VOICE}
        for track in song.tracks:
            has_notes = any(start <= n.start_beat < end for n in track.notes)
            if has_notes and track.instrument not in core_instruments:
                # Remove non-core notes in section
                track.notes = [n for n in track.notes if not (start <= n.start_beat < end)]
            elif has_notes:
                # Reduce velocity of core
                for note in track.notes:
                    if start <= note.start_beat < end:
                        note.velocity = max(1, note.velocity - 15)
        return song

    def add_transition(self, song: Song, from_section_id: str, to_section_id: str) -> Song:
        """Add a transition between two sections."""
        from_rng = _get_section_range(song, from_section_id)
        to_rng = _get_section_range(song, to_section_id)
        if not from_rng or not to_rng:
            return song
        _, from_end = from_rng
        to_start, _ = to_rng

        # Add crash at new section start
        for track in song.tracks:
            if track.instrument == InstrumentType.DRUMS:
                gen = DrumsGenerator()
                track.notes = gen.add_fill(track.notes, from_end - 1.0, "basic")
                track.notes = gen.add_crash(track.notes, to_start)
                break
        return song

    def add_fill(self, song: Song, section_id: str, beat_position: float) -> Song:
        """Add a fill at the specified beat position."""
        for track in song.tracks:
            if track.instrument == InstrumentType.DRUMS:
                gen = DrumsGenerator()
                track.notes = gen.add_fill(track.notes, beat_position, "basic")
                break
        return song

    def add_silence(self, song: Song, section_id: str, track_id: str | None = None) -> Song:
        """Clear notes in a section (all tracks or specific track)."""
        rng = _get_section_range(song, section_id)
        if not rng:
            return song
        start, end = rng
        for track in song.tracks:
            if track_id is None or track.id == track_id:
                track.notes = [n for n in track.notes if not (start <= n.start_beat < end)]
        return song
