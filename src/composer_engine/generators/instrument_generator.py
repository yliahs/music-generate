"""Extended instrument generators.

Aligned with TECHNICAL.md 5.12.
"""

import math
import random

from composer_engine.models.chord import Chord
from composer_engine.models.enums import (
    BrassMode,
    GuitarMode,
    Key,
    Mode,
    PianoMode,
    StringsMode,
    SynthMode,
    WoodwindsMode,
)
from composer_engine.models.note import Note
from composer_engine.theory.chord_utils import get_chord_pitch_classes
from composer_engine.theory.scales import get_scale_notes_in_range


def _find_chord_at(chords: list[Chord], beat: float) -> Chord | None:
    for c in chords:
        if c.start_beat <= beat < c.start_beat + c.duration_beat:
            return c
    return chords[-1] if chords else None


def _chord_pitches_in_range(chord: Chord, low: int, high: int) -> list[int]:
    """Get chord pitches within the MIDI range."""
    pcs = get_chord_pitch_classes(chord.root, chord.quality.value)
    pitches = []
    for pc in pcs:
        for octave in range(0, 10):
            p = pc + octave * 12
            if low <= p <= high:
                pitches.append(p)
    pitches.sort()
    return pitches


INSTRUMENT_RANGES = {
    "strings": (55, 88),
    "brass": (53, 82),
    "woodwinds": (60, 96),
    "synth": (36, 96),
    "piano": (36, 96),
    "guitar": (40, 84),
}


class InstrumentGenerator:
    """Generates parts for extended instruments."""

    # ──── Strings ────

    def generate_strings(
        self,
        chords: list[Chord],
        key: Key,
        mode: Mode,
        start_beat: float,
        end_beat: float,
        strings_mode: StringsMode = StringsMode.SUSTAINED,
    ) -> list[Note]:
        low, high = INSTRUMENT_RANGES["strings"]
        dispatch = {
            StringsMode.SUSTAINED: self._strings_sustained,
            StringsMode.MELODY: self._strings_melody,
            StringsMode.COUNTERPOINT: self._strings_counterpoint,
            StringsMode.TREMOLO: self._strings_tremolo,
            StringsMode.PIZZICATO: self._strings_pizzicato,
        }
        return dispatch.get(strings_mode, self._strings_sustained)(
            chords, key, mode, start_beat, end_beat, low, high
        )

    def _strings_sustained(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, low, high)
            if not pitches:
                continue
            # Pick 3-4 notes for the chord voicing
            voicing = pitches[:min(4, len(pitches))]
            for p in voicing:
                notes.append(Note(pitch=p, start_beat=cs, duration_beat=ce - cs,
                                  velocity=random.randint(60, 80)))
        return notes

    def _strings_melody(self, chords, key, mode, start_beat, end_beat, low, high):
        scale_notes = get_scale_notes_in_range(key, mode, low, high)
        if not scale_notes:
            return []
        notes = []
        prev = scale_notes[len(scale_notes) // 2]
        beat = start_beat
        while beat < end_beat:
            chord = _find_chord_at(chords, beat)
            chord_pcs = set(get_chord_pitch_classes(chord.root, chord.quality.value)) if chord else set()
            # Prefer stepwise (legato)
            nearby = [p for p in scale_notes if abs(p - prev) <= 3 and p != prev]
            if not nearby:
                nearby = [p for p in scale_notes if abs(p - prev) <= 5]
            if nearby:
                pitch = random.choice(nearby)
            else:
                pitch = prev
            dur = min(1.0, end_beat - beat)
            notes.append(Note(pitch=pitch, start_beat=beat, duration_beat=dur,
                              velocity=random.randint(65, 85)))
            prev = pitch
            beat += 1.0
        return notes

    def _strings_counterpoint(self, chords, key, mode, start_beat, end_beat, low, high):
        # Simple counterpoint: generate an independent line
        return self._strings_melody(chords, key, mode, start_beat, end_beat, low, high)

    def _strings_tremolo(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, low, high)
            if not pitches:
                continue
            # Tremolo: rapid repetition of chord tones
            for p in pitches[:2]:
                pos = cs
                while pos < ce:
                    vel = random.randint(55, 75) + int(10 * math.sin((pos - cs) * 2))
                    notes.append(Note(pitch=p, start_beat=pos, duration_beat=0.125,
                                      velocity=max(40, min(100, vel))))
                    pos += 0.125
        return notes

    def _strings_pizzicato(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, low, high)
            if not pitches:
                continue
            # Short plucked notes
            step = ce - cs
            num_notes = max(1, min(len(pitches), int(step)))
            note_step = step / num_notes
            for i in range(num_notes):
                p = pitches[i % len(pitches)]
                notes.append(Note(pitch=p, start_beat=cs + i * note_step,
                                  duration_beat=0.25, velocity=random.randint(80, 100)))
        return notes

    # ──── Brass ────

    def generate_brass(
        self,
        chords: list[Chord],
        key: Key,
        mode: Mode,
        start_beat: float,
        end_beat: float,
        brass_mode: BrassMode = BrassMode.STABS,
    ) -> list[Note]:
        low, high = INSTRUMENT_RANGES["brass"]
        dispatch = {
            BrassMode.STABS: self._brass_stabs,
            BrassMode.SUSTAINED: self._brass_sustained,
            BrassMode.FANFARE: self._brass_fanfare,
            BrassMode.SOLO_LINE: self._brass_solo,
        }
        return dispatch.get(brass_mode, self._brass_stabs)(
            chords, key, mode, start_beat, end_beat, low, high
        )

    def _brass_stabs(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, low, high)
            if not pitches:
                continue
            # Short stab on beat 1
            for p in pitches[:3]:
                notes.append(Note(pitch=p, start_beat=cs, duration_beat=0.25,
                                  velocity=random.randint(100, 120)))
        return notes

    def _brass_sustained(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, low, high)
            if not pitches:
                continue
            for p in pitches[:3]:
                notes.append(Note(pitch=p, start_beat=cs, duration_beat=ce - cs,
                                  velocity=random.randint(70, 90)))
        return notes

    def _brass_fanfare(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        scale_notes = get_scale_notes_in_range(key, mode, low, high)
        if not scale_notes:
            return notes
        # Dotted rhythm fanfare on chord tones
        beat = start_beat
        while beat < end_beat:
            chord = _find_chord_at(chords, beat)
            if chord:
                pitches = _chord_pitches_in_range(chord, low, high)
                if pitches:
                    p = random.choice(pitches[:3])
                    dur = min(1.5, end_beat - beat)
                    notes.append(Note(pitch=p, start_beat=beat, duration_beat=dur,
                                      velocity=random.randint(105, 127)))
            beat += 2.0
        return notes

    def _brass_solo(self, chords, key, mode, start_beat, end_beat, low, high):
        scale_notes = get_scale_notes_in_range(key, mode, low, high)
        if not scale_notes:
            return []
        notes = []
        prev = scale_notes[len(scale_notes) // 2]
        beat = start_beat
        while beat < end_beat:
            nearby = [p for p in scale_notes if abs(p - prev) <= 7 and p != prev]
            if nearby:
                pitch = random.choice(nearby)
            else:
                pitch = prev
            dur = min(random.choice([0.5, 1.0, 1.5]), end_beat - beat)
            if dur > 0:
                notes.append(Note(pitch=pitch, start_beat=beat, duration_beat=dur,
                                  velocity=random.randint(85, 110)))
            prev = pitch
            beat += dur
        return notes

    # ──── Woodwinds ────

    def generate_woodwinds(
        self,
        chords: list[Chord],
        key: Key,
        mode: Mode,
        start_beat: float,
        end_beat: float,
        woodwinds_mode: WoodwindsMode = WoodwindsMode.SUSTAINED,
    ) -> list[Note]:
        low, high = INSTRUMENT_RANGES["woodwinds"]
        dispatch = {
            WoodwindsMode.STABS: self._woodwinds_stabs,
            WoodwindsMode.SUSTAINED: self._woodwinds_sustained,
            WoodwindsMode.SOLO_LINE: self._woodwinds_solo,
            WoodwindsMode.TRILL: self._woodwinds_trill,
        }
        return dispatch.get(woodwinds_mode, self._woodwinds_sustained)(
            chords, key, mode, start_beat, end_beat, low, high
        )

    def _woodwinds_stabs(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, low, high)
            if pitches:
                p = pitches[0]
                notes.append(Note(pitch=p, start_beat=cs, duration_beat=0.25,
                                  velocity=random.randint(85, 105)))
        return notes

    def _woodwinds_sustained(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, low, high)
            if pitches:
                p = pitches[0]
                notes.append(Note(pitch=p, start_beat=cs, duration_beat=ce - cs,
                                  velocity=random.randint(65, 80)))
        return notes

    def _woodwinds_solo(self, chords, key, mode, start_beat, end_beat, low, high):
        return self._brass_solo(self, chords, key, mode, start_beat, end_beat, low, high) if False else self._generic_solo(chords, key, mode, start_beat, end_beat, low, high)

    def _generic_solo(self, chords, key, mode, start_beat, end_beat, low, high):
        scale_notes = get_scale_notes_in_range(key, mode, low, high)
        if not scale_notes:
            return []
        notes = []
        prev = scale_notes[len(scale_notes) // 2]
        beat = start_beat
        while beat < end_beat:
            nearby = [p for p in scale_notes if abs(p - prev) <= 5 and p != prev]
            pitch = random.choice(nearby) if nearby else prev
            dur = min(random.choice([0.5, 1.0]), end_beat - beat)
            if dur > 0:
                notes.append(Note(pitch=pitch, start_beat=beat, duration_beat=dur,
                                  velocity=random.randint(70, 90)))
            prev = pitch
            beat += dur
        return notes

    def _woodwinds_trill(self, chords, key, mode, start_beat, end_beat, low, high):
        scale_notes = get_scale_notes_in_range(key, mode, low, high)
        if not scale_notes:
            return []
        notes = []
        # Trill between two adjacent scale notes
        beat = start_beat
        while beat < end_beat:
            chord = _find_chord_at(chords, beat)
            pitches = _chord_pitches_in_range(chord, low, high) if chord else []
            base = pitches[0] if pitches else scale_notes[len(scale_notes) // 2]
            # Find next scale note above
            above = [p for p in scale_notes if p > base]
            upper = above[0] if above else base + 2
            # Alternate rapidly
            trill_dur = min(2.0, end_beat - beat)
            pos = beat
            toggle = True
            while pos < beat + trill_dur:
                p = base if toggle else upper
                notes.append(Note(pitch=p, start_beat=pos, duration_beat=0.125,
                                  velocity=random.randint(65, 80)))
                pos += 0.125
                toggle = not toggle
            beat += trill_dur
        return notes

    # ──── Synth ────

    def generate_synth(
        self,
        chords: list[Chord],
        key: Key,
        mode: Mode,
        start_beat: float,
        end_beat: float,
        synth_mode: SynthMode = SynthMode.PAD,
    ) -> list[Note]:
        low, high = INSTRUMENT_RANGES["synth"]
        dispatch = {
            SynthMode.PAD: self._synth_pad,
            SynthMode.LEAD: self._synth_lead,
            SynthMode.ARP: self._synth_arp,
            SynthMode.FX: self._synth_fx,
        }
        return dispatch.get(synth_mode, self._synth_pad)(
            chords, key, mode, start_beat, end_beat, low, high
        )

    def _synth_pad(self, chords, key, mode, start_beat, end_beat, low, high):
        # Similar to strings sustained, mid range
        pad_low, pad_high = 55, 79
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, pad_low, pad_high)
            if not pitches:
                continue
            for p in pitches[:3]:
                notes.append(Note(pitch=p, start_beat=cs, duration_beat=ce - cs,
                                  velocity=random.randint(55, 75)))
        return notes

    def _synth_lead(self, chords, key, mode, start_beat, end_beat, low, high):
        return self._generic_solo(chords, key, mode, start_beat, end_beat, 60, 96)

    def _synth_arp(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, 55, 84)
            if not pitches:
                continue
            # Arpeggio: cycle through chord tones at 16th or 8th speed
            step = 0.25
            pos = cs
            idx = 0
            while pos < ce:
                p = pitches[idx % len(pitches)]
                dur = min(step, ce - pos)
                notes.append(Note(pitch=p, start_beat=pos, duration_beat=dur * 0.8,
                                  velocity=random.randint(65, 85) + (3 if idx % len(pitches) == 0 else 0)))
                pos += step
                idx += 1
        return notes

    def _synth_fx(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        total = end_beat - start_beat
        if total <= 0:
            return notes
        # Rising sweep
        steps = int(total / 0.25)
        for i in range(steps):
            pitch = int(low + (high - low) * i / max(steps, 1))
            pos = start_beat + i * 0.25
            if pos >= end_beat:
                break
            notes.append(Note(pitch=pitch, start_beat=pos, duration_beat=0.25,
                              velocity=random.randint(50, 70)))
        return notes

    # ──── Piano ────

    def generate_piano_part(
        self,
        chords: list[Chord],
        key: Key,
        mode: Mode,
        start_beat: float,
        end_beat: float,
        piano_mode: PianoMode = PianoMode.BLOCK_CHORDS,
    ) -> list[Note]:
        low, high = INSTRUMENT_RANGES["piano"]
        dispatch = {
            PianoMode.BLOCK_CHORDS: self._piano_block,
            PianoMode.BROKEN_CHORDS: self._piano_broken,
            PianoMode.ARPEGGIO: self._piano_arp,
            PianoMode.COMPING: self._piano_comping,
        }
        return dispatch.get(piano_mode, self._piano_block)(
            chords, key, mode, start_beat, end_beat, low, high
        )

    def _piano_block(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, 55, 79)
            if not pitches:
                continue
            # All chord tones simultaneously
            for p in pitches[:4]:
                notes.append(Note(pitch=p, start_beat=cs, duration_beat=ce - cs,
                                  velocity=random.randint(70, 90)))
        return notes

    def _piano_broken(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, 48, 79)
            if not pitches:
                continue
            step = (ce - cs) / len(pitches)
            for i, p in enumerate(pitches):
                notes.append(Note(pitch=p, start_beat=cs + i * step,
                                  duration_beat=step * 0.9, velocity=random.randint(65, 85)))
        return notes

    def _piano_arp(self, chords, key, mode, start_beat, end_beat, low, high):
        return self._synth_arp(chords, key, mode, start_beat, end_beat, 48, 84)

    def _piano_comping(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, 55, 79)
            if not pitches:
                continue
            # Jazz comping: syncopated chords with gaps
            dur = ce - cs
            # Hit on offbeats with varying rhythm
            offsets = [0.5, 1.5, 2.5] if dur >= 3 else [0.5]
            for off in offsets:
                if cs + off < ce:
                    for p in pitches[:3]:
                        notes.append(Note(pitch=p, start_beat=cs + off,
                                          duration_beat=min(0.75, ce - cs - off),
                                          velocity=random.randint(60, 80)))
        return notes

    # ──── Guitar ────

    def generate_guitar_part(
        self,
        chords: list[Chord],
        key: Key,
        mode: Mode,
        start_beat: float,
        end_beat: float,
        guitar_mode: GuitarMode = GuitarMode.STRUM,
    ) -> list[Note]:
        low, high = INSTRUMENT_RANGES["guitar"]
        dispatch = {
            GuitarMode.STRUM: self._guitar_strum,
            GuitarMode.FINGERPICK: self._guitar_fingerpick,
            GuitarMode.ARPEGGIO: self._guitar_arp,
            GuitarMode.MUTED: self._guitar_muted,
        }
        return dispatch.get(guitar_mode, self._guitar_strum)(
            chords, key, mode, start_beat, end_beat, low, high
        )

    def _guitar_strum(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, 52, 76)
            if not pitches:
                continue
            dur = ce - cs
            # Strum: notes with slight time offsets (simulating strum)
            beats_per_strum = 1.0
            pos = cs
            down = True
            while pos < ce:
                order = pitches if down else list(reversed(pitches))
                for i, p in enumerate(order[:5]):
                    strum_offset = i * 0.03  # slight offset
                    notes.append(Note(pitch=p, start_beat=pos + strum_offset,
                                      duration_beat=min(beats_per_strum - 0.1, ce - pos - strum_offset),
                                      velocity=random.randint(75, 95)))
                pos += beats_per_strum
                down = not down
        return notes

    def _guitar_fingerpick(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, 40, 76)
            if not pitches:
                continue
            # Travis picking: bass (thumb) + treble alternating
            bass = pitches[0] if pitches else 40
            treble = pitches[1:4] if len(pitches) > 1 else [pitches[0]]
            step = 0.5
            pos = cs
            idx = 0
            while pos < ce:
                if idx % 2 == 0:
                    notes.append(Note(pitch=bass, start_beat=pos, duration_beat=step * 0.9,
                                      velocity=random.randint(75, 90)))
                else:
                    p = treble[idx // 2 % len(treble)]
                    notes.append(Note(pitch=p, start_beat=pos, duration_beat=step * 0.9,
                                      velocity=random.randint(65, 80)))
                pos += step
                idx += 1
        return notes

    def _guitar_arp(self, chords, key, mode, start_beat, end_beat, low, high):
        return self._synth_arp(chords, key, mode, start_beat, end_beat, 40, 76)

    def _guitar_muted(self, chords, key, mode, start_beat, end_beat, low, high):
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitches = _chord_pitches_in_range(c, 40, 64)
            root = pitches[0] if pitches else 40
            # Muted: short notes, dense rhythm
            pos = cs
            while pos < ce:
                notes.append(Note(pitch=root, start_beat=pos, duration_beat=0.15,
                                  velocity=random.randint(60, 80)))
                pos += 0.25
        return notes
