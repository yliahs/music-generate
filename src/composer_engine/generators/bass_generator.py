"""Bass line generator.

Aligned with TECHNICAL.md 5.11.
"""

import random

from composer_engine.models.chord import Chord
from composer_engine.models.enums import BassMode, Key, Mode
from composer_engine.models.note import Note
from composer_engine.theory.chord_utils import get_chord_pitch_classes
from composer_engine.theory.scales import KEY_TO_PITCH, get_scale_notes_in_range


def _find_chord_at(chords: list[Chord], beat: float) -> Chord | None:
    for c in chords:
        if c.start_beat <= beat < c.start_beat + c.duration_beat:
            return c
    return chords[-1] if chords else None


def _root_pitch_in_range(root: Key, low: int, high: int) -> int:
    """Find the root pitch within the given MIDI range."""
    pc = KEY_TO_PITCH[root]
    for octave in range(0, 10):
        p = pc + octave * 12
        if low <= p <= high:
            return p
    # Fallback to closest
    candidates = [pc + o * 12 for o in range(0, 10)]
    candidates = [p for p in candidates if low <= p <= high]
    return candidates[0] if candidates else low


class BassGenerator:
    """Generates bass lines in various modes."""

    # Bass octave ranges: 1=low, 2=mid, 3=high
    OCTAVE_RANGES = {
        1: (28, 40),   # E1 - E2
        2: (36, 48),   # C2 - C3
        3: (43, 55),   # G2 - G3
    }

    def generate(
        self,
        chords: list[Chord],
        key: Key,
        mode: Mode,
        start_beat: float,
        end_beat: float,
        bass_mode: BassMode = BassMode.GENERATE,
        note_density: str = "normal",
        octave: int = 2,
        melody_notes: list[Note] | None = None,
    ) -> list[Note]:
        """Generate a bass line based on chords and mode."""
        if not chords or end_beat <= start_beat:
            return []

        low, high = self.OCTAVE_RANGES.get(octave, self.OCTAVE_RANGES[2])

        dispatch = {
            BassMode.ROOT: self._root,
            BassMode.OCTAVE: self._octave,
            BassMode.WALKING: self._walking,
            BassMode.SYNCOPATION: self._syncopation,
            BassMode.FOLLOW_CHORDS: self._follow_chords,
            BassMode.INDEPENDENT: self._independent,
            BassMode.COUNTER_BASS: self._counter_bass,
            BassMode.GENERATE: self._generate,
        }

        method = dispatch.get(bass_mode, self._generate)

        if bass_mode == BassMode.COUNTER_BASS:
            return method(chords, key, mode, start_beat, end_beat, low, high, melody_notes)
        elif bass_mode in (BassMode.WALKING, BassMode.INDEPENDENT):
            return method(chords, key, mode, start_beat, end_beat, low, high)
        elif bass_mode == BassMode.GENERATE:
            return method(chords, key, mode, start_beat, end_beat, low, high, note_density)
        else:
            return method(chords, start_beat, end_beat, low, high)

    def _root(self, chords: list[Chord], start_beat: float, end_beat: float,
              low: int, high: int) -> list[Note]:
        """Root bass: one root note per chord."""
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            pitch = _root_pitch_in_range(c.root, low, high)
            notes.append(Note(pitch=pitch, start_beat=cs, duration_beat=ce - cs,
                              velocity=random.randint(90, 110)))
        return notes

    def _octave(self, chords: list[Chord], start_beat: float, end_beat: float,
                low: int, high: int) -> list[Note]:
        """Octave bass: root + octave alternating."""
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            root = _root_pitch_in_range(c.root, low, high)
            oct_up = root + 12 if root + 12 <= high else root - 12
            if oct_up < low:
                oct_up = root
            dur = ce - cs
            if dur >= 2.0:
                half = dur / 2
                notes.append(Note(pitch=root, start_beat=cs, duration_beat=half,
                                  velocity=random.randint(90, 110)))
                notes.append(Note(pitch=oct_up, start_beat=cs + half, duration_beat=half,
                                  velocity=random.randint(85, 105)))
            else:
                notes.append(Note(pitch=root, start_beat=cs, duration_beat=dur,
                                  velocity=random.randint(90, 110)))
        return notes

    def _walking(self, chords: list[Chord], key: Key, mode: Mode,
                 start_beat: float, end_beat: float,
                 low: int, high: int) -> list[Note]:
        """Walking bass: stepwise motion between chord tones, one note per beat."""
        scale_notes = get_scale_notes_in_range(key, mode, low, high)
        if not scale_notes:
            return self._root(chords, start_beat, end_beat, low, high)

        notes = []
        prev_pitch = None
        beat = start_beat
        while beat < end_beat:
            chord = _find_chord_at(chords, beat)
            if chord is None:
                beat += 1.0
                continue

            chord_end = min(chord.start_beat + chord.duration_beat, end_beat)
            chord_pcs = set(get_chord_pitch_classes(chord.root, chord.quality.value))
            chord_tones = [p for p in scale_notes if p % 12 in chord_pcs]

            # Beat 1 of chord: root
            is_chord_start = abs(beat - max(chord.start_beat, start_beat)) < 0.01
            if is_chord_start and chord_tones:
                root = _root_pitch_in_range(chord.root, low, high)
                pitch = root
            elif prev_pitch is not None:
                # Stepwise: choose nearby scale note
                nearby = [p for p in scale_notes if abs(p - prev_pitch) <= 3 and p != prev_pitch]
                if not nearby:
                    nearby = [p for p in scale_notes if abs(p - prev_pitch) <= 5]
                if nearby:
                    # If last beat before next chord, aim for chromatic approach
                    if beat + 1.0 >= chord_end and beat + 1.0 < end_beat:
                        next_chord = _find_chord_at(chords, beat + 1.0)
                        if next_chord and next_chord is not chord:
                            next_root = _root_pitch_in_range(next_chord.root, low, high)
                            approach = [p for p in range(next_root - 2, next_root + 3) if low <= p <= high and p != prev_pitch]
                            if approach:
                                pitch = min(approach, key=lambda p: abs(p - next_root))
                            else:
                                pitch = random.choice(nearby)
                        else:
                            pitch = random.choice(nearby)
                    else:
                        pitch = random.choice(nearby)
                else:
                    pitch = prev_pitch
            else:
                pitch = _root_pitch_in_range(chord.root, low, high) if chord_tones else scale_notes[len(scale_notes)//2]

            pitch = max(low, min(high, pitch))
            notes.append(Note(pitch=pitch, start_beat=beat, duration_beat=0.9,
                              velocity=random.randint(85, 105)))
            prev_pitch = pitch
            beat += 1.0

        return notes

    def _syncopation(self, chords: list[Chord], start_beat: float, end_beat: float,
                     low: int, high: int) -> list[Note]:
        """Syncopated bass: offbeat hits with ties."""
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            root = _root_pitch_in_range(c.root, low, high)
            dur = ce - cs
            # Syncopation patterns: offbeat
            if dur >= 4.0:
                # Beat pattern: rest, 0.5, rest, 1.5, rest, 0.5, rest, 1.5
                notes.append(Note(pitch=root, start_beat=cs + 0.5, duration_beat=1.0,
                                  velocity=random.randint(95, 115)))
                notes.append(Note(pitch=root, start_beat=cs + 2.5, duration_beat=1.0,
                                  velocity=random.randint(90, 110)))
            elif dur >= 2.0:
                notes.append(Note(pitch=root, start_beat=cs + 0.5, duration_beat=1.0,
                                  velocity=random.randint(95, 115)))
            else:
                notes.append(Note(pitch=root, start_beat=cs, duration_beat=dur,
                                  velocity=random.randint(90, 110)))
        return notes

    def _follow_chords(self, chords: list[Chord], start_beat: float, end_beat: float,
                       low: int, high: int) -> list[Note]:
        """Follow chords: arpeggiate through chord tones."""
        notes = []
        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue
            chord_pcs = get_chord_pitch_classes(c.root, c.quality.value)
            # Map to actual MIDI pitches in range
            pitches = []
            for pc in chord_pcs:
                for octave in range(0, 10):
                    p = pc + octave * 12
                    if low <= p <= high:
                        pitches.append(p)
                        break
            if not pitches:
                pitches = [_root_pitch_in_range(c.root, low, high)]
            pitches.sort()

            dur = ce - cs
            step = dur / len(pitches) if pitches else dur
            for i, pitch in enumerate(pitches):
                note_start = cs + i * step
                note_dur = min(step, ce - note_start)
                if note_dur > 0:
                    notes.append(Note(pitch=pitch, start_beat=note_start, duration_beat=note_dur * 0.9,
                                      velocity=random.randint(85, 105)))
        return notes

    def _independent(self, chords: list[Chord], key: Key, mode: Mode,
                     start_beat: float, end_beat: float,
                     low: int, high: int) -> list[Note]:
        """Independent melodic bass line."""
        scale_notes = get_scale_notes_in_range(key, mode, low, high)
        if not scale_notes:
            return self._root(chords, start_beat, end_beat, low, high)

        notes = []
        prev_pitch = scale_notes[len(scale_notes) // 2]
        beat = start_beat
        step = 1.0

        while beat < end_beat:
            chord = _find_chord_at(chords, beat)
            chord_pcs = set(get_chord_pitch_classes(chord.root, chord.quality.value)) if chord else set()

            # Mix chord tones and scale tones
            is_strong = (beat - start_beat) % 2 < 0.01
            if is_strong and random.random() < 0.6:
                candidates = [p for p in scale_notes if p % 12 in chord_pcs]
                if not candidates:
                    candidates = scale_notes
            else:
                candidates = scale_notes

            # Prefer stepwise motion
            nearby = [p for p in candidates if abs(p - prev_pitch) <= 4 and p != prev_pitch]
            if nearby:
                pitch = random.choice(nearby)
            else:
                pitch = min(candidates, key=lambda p: abs(p - prev_pitch))

            dur = min(step, end_beat - beat)
            if dur > 0:
                notes.append(Note(pitch=pitch, start_beat=beat, duration_beat=dur * 0.9,
                                  velocity=random.randint(80, 105)))
            prev_pitch = pitch
            beat += step

        return notes

    def _counter_bass(self, chords: list[Chord], key: Key, mode: Mode,
                      start_beat: float, end_beat: float,
                      low: int, high: int,
                      melody_notes: list[Note] | None = None) -> list[Note]:
        """Counter bass: inverse motion to melody."""
        if not melody_notes:
            return self._independent(chords, key, mode, start_beat, end_beat, low, high)

        scale_notes = get_scale_notes_in_range(key, mode, low, high)
        if not scale_notes:
            return self._root(chords, start_beat, end_beat, low, high)

        notes = []
        mel_sorted = sorted(melody_notes, key=lambda n: n.start_beat)
        mel_center = sum(n.pitch for n in mel_sorted) / len(mel_sorted) if mel_sorted else 72
        bass_center = (low + high) // 2

        prev_pitch = bass_center
        beat = start_beat
        step = 1.0

        while beat < end_beat:
            chord = _find_chord_at(chords, beat)
            chord_pcs = set(get_chord_pitch_classes(chord.root, chord.quality.value)) if chord else set()

            # Find melody direction at this beat
            mel_at = [n for n in mel_sorted if n.start_beat <= beat < n.start_beat + n.duration_beat]
            mel_after = [n for n in mel_sorted if n.start_beat > beat and n.start_beat <= beat + 2]

            direction = 0  # counter direction
            if mel_at and mel_after:
                direction = mel_after[0].pitch - mel_at[0].pitch
            elif mel_at and len(mel_at) > 1:
                direction = mel_at[-1].pitch - mel_at[0].pitch

            # Counter: if melody goes up, bass goes down
            if direction > 0:
                candidates = [p for p in scale_notes if p < prev_pitch and p % 12 in chord_pcs]
                if not candidates:
                    candidates = [p for p in scale_notes if p < prev_pitch]
            elif direction < 0:
                candidates = [p for p in scale_notes if p > prev_pitch and p % 12 in chord_pcs]
                if not candidates:
                    candidates = [p for p in scale_notes if p > prev_pitch]
            else:
                candidates = [p for p in scale_notes if p % 12 in chord_pcs]

            if not candidates:
                candidates = scale_notes

            pitch = min(candidates, key=lambda p: abs(p - prev_pitch)) if candidates else prev_pitch
            dur = min(step, end_beat - beat)
            if dur > 0:
                notes.append(Note(pitch=pitch, start_beat=beat, duration_beat=dur * 0.9,
                                  velocity=random.randint(85, 105)))
            prev_pitch = pitch
            beat += step

        return notes

    def _generate(self, chords: list[Chord], key: Key, mode: Mode,
                  start_beat: float, end_beat: float,
                  low: int, high: int, note_density: str = "normal") -> list[Note]:
        """Generic bass: root-based with passing tones and occasional octave jumps."""
        notes = []
        scale_notes = get_scale_notes_in_range(key, mode, low, high)

        for c in chords:
            cs = max(c.start_beat, start_beat)
            ce = min(c.start_beat + c.duration_beat, end_beat)
            if cs >= ce:
                continue

            root = _root_pitch_in_range(c.root, low, high)
            dur = ce - cs

            # Beat 1: always root
            notes.append(Note(pitch=root, start_beat=cs, duration_beat=min(1.0, dur),
                              velocity=random.randint(95, 115)))

            if note_density == "sparse" or dur < 2:
                continue

            # Beat 3 (or halfway): fifth or octave
            if dur >= 2.0:
                fifth = root + 7 if root + 7 <= high else root - 5
                if fifth < low:
                    fifth = root
                mid_beat = cs + dur / 2
                notes.append(Note(pitch=fifth, start_beat=mid_beat, duration_beat=min(1.0, ce - mid_beat),
                                  velocity=random.randint(85, 105)))

            if note_density == "dense" and dur >= 4.0 and scale_notes:
                # Add passing tones
                for offset in [1.0, 3.0]:
                    if cs + offset < ce and random.random() < 0.5:
                        nearby = [p for p in scale_notes if abs(p - root) <= 5 and p != root]
                        if nearby:
                            pt = random.choice(nearby)
                            notes.append(Note(pitch=pt, start_beat=cs + offset, duration_beat=0.5,
                                              velocity=random.randint(75, 95)))

        return notes

    def simplify(self, notes: list[Note]) -> list[Note]:
        """Simplify bass: keep root notes on strong beats."""
        if not notes:
            return notes
        sorted_n = sorted(notes, key=lambda n: n.start_beat)
        result = []
        for n in sorted_n:
            is_strong = (n.start_beat % 2) < 0.01
            if is_strong or n.duration_beat >= 1.0:
                result.append(n)
        return result if result else [sorted_n[0]]

    def transpose(self, notes: list[Note], semitones: int) -> list[Note]:
        """Transpose bass notes by semitones, clamping to valid MIDI range."""
        return [Note(pitch=max(0, min(127, n.pitch + semitones)),
                     start_beat=n.start_beat, duration_beat=n.duration_beat,
                     velocity=n.velocity) for n in notes]
