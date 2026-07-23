"""Melody generation engine.

Aligned with TECHNICAL.md 5.10.
"""

import math
import random

from composer_engine.models.chord import Chord
from composer_engine.models.enums import Key, Mode
from composer_engine.models.note import Note
from composer_engine.theory.chord_utils import get_chord_pitch_classes
from composer_engine.theory.scales import get_scale_notes_in_range, get_scale_pitches


def _find_chord_at(chords: list[Chord], beat: float) -> Chord | None:
    for c in chords:
        if c.start_beat <= beat < c.start_beat + c.duration_beat:
            return c
    return chords[-1] if chords else None


def _closest_pitch(candidates: list[int], target: int) -> int:
    if not candidates:
        return target
    return min(candidates, key=lambda p: abs(p - target))


class MelodyGenerator:
    """Generates and manipulates melodies."""

    def generate(
        self,
        chord_progression: list[Chord],
        key: Key,
        mode: Mode,
        start_beat: float,
        end_beat: float,
        note_density: str = "normal",
        pitch_range: tuple[int, int] = (60, 84),
        contour: str = "arch",
        chord_tone_weight: float = 0.7,
        rhythm_complexity: str = "moderate",
    ) -> list[Note]:
        """Generate a melody based on chords, key, and constraints."""
        min_p, max_p = pitch_range
        scale_notes = get_scale_notes_in_range(key, mode, min_p, max_p)
        if not scale_notes:
            return []

        step = {"sparse": 2.0, "normal": 1.0, "dense": 0.5}.get(note_density, 1.0)
        total_beats = end_beat - start_beat
        if total_beats <= 0:
            return []

        positions = []
        pos = 0.0
        while pos < total_beats:
            if rhythm_complexity == "complex" and random.random() < 0.3:
                dur = random.choice([0.5, 0.75, 1.5, 0.25])
            else:
                dur = step
            positions.append((pos, min(dur, total_beats - pos)))
            pos += dur

        notes: list[Note] = []
        prev_pitch = (min_p + max_p) // 2
        center = prev_pitch

        for beat_offset, duration in positions:
            if duration <= 0:
                continue
            abs_beat = start_beat + beat_offset
            frac = beat_offset / total_beats if total_beats > 0 else 0.5

            target = self._contour_target(contour, frac, min_p, max_p)

            chord = _find_chord_at(chord_progression, abs_beat)
            chord_pcs = set(get_chord_pitch_classes(chord.root, chord.quality.value)) if chord else set()
            chord_tones = [p for p in scale_notes if p % 12 in chord_pcs]
            non_chord_tones = [p for p in scale_notes if p % 12 not in chord_pcs]

            is_strong = (beat_offset % 2) < 0.01
            if is_strong and chord_tones and random.random() < chord_tone_weight:
                candidates = chord_tones
            else:
                candidates = scale_notes

            near_target = [p for p in candidates if abs(p - target) <= 7]
            if not near_target:
                near_target = candidates

            near_prev = [p for p in near_target if abs(p - prev_pitch) <= 7]
            pool = near_prev if near_prev else near_target

            pitch = _closest_pitch(pool, int((target + prev_pitch) / 2))
            if abs(pitch - prev_pitch) > 7 and len(pool) > 1:
                pool_filtered = [p for p in pool if abs(p - prev_pitch) <= 5]
                if pool_filtered:
                    pitch = _closest_pitch(pool_filtered, target)

            notes.append(Note(
                pitch=max(min_p, min(max_p, pitch)),
                start_beat=abs_beat,
                duration_beat=duration,
                velocity=random.randint(80, 110),
            ))
            prev_pitch = pitch

        if notes and scale_notes:
            scale_pcs = set(get_scale_pitches(key, mode))
            stable_degrees = {0, 4, 7}
            base_pc = scale_pcs
            stable_pitches = [p for p in scale_notes if (p % 12 - list(scale_pcs)[0]) % 12 in {0, 4, 7}]
            if stable_pitches:
                notes[-1].pitch = _closest_pitch(stable_pitches, notes[-1].pitch)

        return notes

    def simplify(self, notes: list[Note], strength: float = 0.5) -> list[Note]:
        """Remove short notes and merge adjacent same-pitch notes."""
        if not notes:
            return notes
        sorted_notes = sorted(notes, key=lambda n: n.start_beat)
        min_dur = 0.25 + strength * 1.75
        result = [n for n in sorted_notes if n.duration_beat >= min_dur]
        if not result and sorted_notes:
            result = [sorted_notes[0]]
        return result

    def complexify(
        self, notes: list[Note], key: Key, mode: Mode,
        chord_progression: list[Chord], strength: float = 0.5
    ) -> list[Note]:
        """Add passing tones and ornaments between existing notes."""
        if len(notes) < 2:
            return notes
        scale_pcs = set(get_scale_pitches(key, mode))
        result = list(notes)
        insertions = []

        for i in range(len(notes) - 1):
            if random.random() > strength:
                continue
            curr = notes[i]
            nxt = notes[i + 1]
            gap = nxt.start_beat - (curr.start_beat + curr.duration_beat)
            if gap < 0.25:
                if curr.duration_beat > 0.5:
                    passing_start = curr.start_beat + curr.duration_beat - 0.25
                    mid_pitch = (curr.pitch + nxt.pitch) // 2
                    candidates = [p for p in range(min(curr.pitch, nxt.pitch), max(curr.pitch, nxt.pitch) + 1)
                                  if p % 12 in scale_pcs and p != curr.pitch and p != nxt.pitch]
                    if candidates:
                        passing_pitch = _closest_pitch(candidates, mid_pitch)
                        insertions.append(Note(
                            pitch=passing_pitch, start_beat=passing_start,
                            duration_beat=0.25, velocity=curr.velocity - 10,
                        ))

        result.extend(insertions)
        result.sort(key=lambda n: n.start_beat)
        return result

    def transpose(self, notes: list[Note], semitones: int) -> list[Note]:
        """Transpose all notes by semitones."""
        return [Note(pitch=max(0, min(127, n.pitch + semitones)),
                     start_beat=n.start_beat, duration_beat=n.duration_beat,
                     velocity=n.velocity) for n in notes]

    def invert(self, notes: list[Note], pivot_pitch: int) -> list[Note]:
        """Invert melody around a pivot pitch."""
        return [Note(pitch=max(0, min(127, 2 * pivot_pitch - n.pitch)),
                     start_beat=n.start_beat, duration_beat=n.duration_beat,
                     velocity=n.velocity) for n in notes]

    def reverse(self, notes: list[Note]) -> list[Note]:
        """Reverse the melody in time."""
        if not notes:
            return notes
        min_start = min(n.start_beat for n in notes)
        max_end = max(n.start_beat + n.duration_beat for n in notes)
        total = max_end - min_start
        return [Note(pitch=n.pitch,
                     start_beat=min_start + total - (n.start_beat - min_start + n.duration_beat),
                     duration_beat=n.duration_beat,
                     velocity=n.velocity) for n in notes]

    def sequence(self, notes: list[Note], interval: int, count: int) -> list[Note]:
        """Create a melodic sequence (modulation by interval, repeated count times)."""
        if not notes:
            return notes
        min_start = min(n.start_beat for n in notes)
        max_end = max(n.start_beat + n.duration_beat for n in notes)
        phrase_len = max_end - min_start
        result = list(notes)
        for i in range(1, count + 1):
            for n in notes:
                result.append(Note(
                    pitch=max(0, min(127, n.pitch + interval * i)),
                    start_beat=n.start_beat + phrase_len * i,
                    duration_beat=n.duration_beat,
                    velocity=n.velocity,
                ))
        return result

    def variation(self, notes: list[Note], chord_progression: list[Chord],
                  key: Key, mode: Mode) -> list[Note]:
        """Create a variation: keep strong-beat chord tones, vary weak-beat notes."""
        if not notes:
            return notes
        scale_notes_full = get_scale_notes_in_range(key, mode, 48, 96)
        result = []
        for n in notes:
            is_strong = (n.start_beat % 2) < 0.01
            if is_strong:
                result.append(n.model_copy())
            else:
                nearby = [p for p in scale_notes_full if abs(p - n.pitch) <= 4 and p != n.pitch]
                new_pitch = random.choice(nearby) if nearby else n.pitch
                result.append(Note(pitch=new_pitch, start_beat=n.start_beat,
                                   duration_beat=n.duration_beat, velocity=n.velocity))
        return result

    def develop_motif(self, notes: list[Note], motif_beats: float,
                      key: Key, mode: Mode) -> list[Note]:
        """Develop a motif from the first N beats into a longer melody."""
        if not notes:
            return notes
        min_start = min(n.start_beat for n in notes)
        motif = [n for n in notes if n.start_beat < min_start + motif_beats]
        if not motif:
            motif = notes[:4]

        phrase_len = motif_beats
        result = list(motif)
        offset = phrase_len

        transposed = self.transpose(motif, 2)
        for n in transposed:
            result.append(Note(pitch=n.pitch, start_beat=min_start + offset + (n.start_beat - min_start),
                               duration_beat=n.duration_beat, velocity=n.velocity))
        offset += phrase_len

        inverted = self.invert(motif, motif[0].pitch)
        for n in inverted:
            result.append(Note(pitch=n.pitch, start_beat=min_start + offset + (n.start_beat - min_start),
                               duration_beat=n.duration_beat, velocity=n.velocity))
        offset += phrase_len

        varied_trans = self.transpose(motif, 4)
        for n in varied_trans:
            result.append(Note(pitch=n.pitch, start_beat=min_start + offset + (n.start_beat - min_start),
                               duration_beat=n.duration_beat, velocity=n.velocity))

        return result

    def extend(self, notes: list[Note], extra_beats: float,
               chord_progression: list[Chord], key: Key, mode: Mode) -> list[Note]:
        """Extend melody by generating additional beats at the end."""
        if not notes:
            return notes
        max_end = max(n.start_beat + n.duration_beat for n in notes)
        extension = self.generate(
            chord_progression, key, mode,
            start_beat=max_end, end_beat=max_end + extra_beats,
            pitch_range=(min(n.pitch for n in notes), max(n.pitch for n in notes)),
        )
        return list(notes) + extension

    def shorten(self, notes: list[Note], cut_beats: float) -> list[Note]:
        """Remove notes from the end."""
        if not notes:
            return notes
        max_end = max(n.start_beat + n.duration_beat for n in notes)
        cutoff = max_end - cut_beats
        result = []
        for n in notes:
            if n.start_beat < cutoff:
                if n.start_beat + n.duration_beat > cutoff:
                    result.append(Note(pitch=n.pitch, start_beat=n.start_beat,
                                       duration_beat=cutoff - n.start_beat, velocity=n.velocity))
                else:
                    result.append(n)
        return result

    def call_response(self, notes: list[Note], response_style: str = "echo") -> list[Note]:
        """Generate a response phrase after the call."""
        if not notes:
            return notes
        min_start = min(n.start_beat for n in notes)
        max_end = max(n.start_beat + n.duration_beat for n in notes)
        phrase_len = max_end - min_start

        if response_style == "mirror":
            response = self.invert(notes, notes[0].pitch)
        elif response_style == "complement":
            response = self.invert(notes, notes[0].pitch)
            response = [Note(pitch=n.pitch, start_beat=n.start_beat,
                            duration_beat=n.duration_beat * 1.5 if n.duration_beat < 1 else n.duration_beat * 0.5,
                            velocity=n.velocity) for n in response]
        else:
            response = [n.model_copy() for n in notes]
            for n in response:
                if random.random() < 0.2:
                    n.pitch = max(0, min(127, n.pitch + random.choice([-2, -1, 1, 2])))

        for n in response:
            n.start_beat = n.start_beat + phrase_len

        return list(notes) + response

    def generate_hook(self, chord_progression: list[Chord], key: Key, mode: Mode,
                      hook_beats: float = 4.0) -> list[Note]:
        """Generate a short, memorable hook melody."""
        start = chord_progression[0].start_beat if chord_progression else 0
        notes = self.generate(
            chord_progression, key, mode,
            start_beat=start, end_beat=start + hook_beats / 2,
            note_density="normal", pitch_range=(67, 79),
            contour="arch", chord_tone_weight=0.9,
        )
        repeated = [Note(pitch=n.pitch, start_beat=n.start_beat + hook_beats / 2,
                         duration_beat=n.duration_beat, velocity=n.velocity) for n in notes]
        return notes + repeated

    def question_answer(self, chord_progression: list[Chord], key: Key, mode: Mode,
                        phrase_beats: float = 4.0) -> list[Note]:
        """Generate a question-answer phrase pair."""
        start = chord_progression[0].start_beat if chord_progression else 0
        question = self.generate(
            chord_progression, key, mode,
            start_beat=start, end_beat=start + phrase_beats,
            contour="ascending", chord_tone_weight=0.6,
        )
        if question:
            scale_pcs = set(get_scale_pitches(key, mode))
            unstable = [2, 4, 6]  # 2nd, 5th, 7th degrees as indices
            scale = sorted(scale_pcs)
            if len(scale) > max(unstable):
                target_pc = scale[random.choice(unstable)]
                candidates = [p for p in range(55, 85) if p % 12 == target_pc]
                if candidates:
                    question[-1].pitch = _closest_pitch(candidates, question[-1].pitch)

        answer = self.generate(
            chord_progression, key, mode,
            start_beat=start + phrase_beats, end_beat=start + phrase_beats * 2,
            contour="descending", chord_tone_weight=0.8,
        )
        if answer:
            scale_pcs = sorted(get_scale_pitches(key, mode))
            stable = [0, 2, 4]  # 1st, 3rd, 5th degrees
            if len(scale_pcs) > max(stable):
                target_pc = scale_pcs[random.choice(stable)]
                candidates = [p for p in range(55, 85) if p % 12 == target_pc]
                if candidates:
                    answer[-1].pitch = _closest_pitch(candidates, answer[-1].pitch)

        return question + answer

    def _contour_target(self, contour: str, fraction: float,
                        min_p: int, max_p: int) -> float:
        """Calculate target pitch center based on contour and position."""
        mid = (min_p + max_p) / 2
        rng = (max_p - min_p) / 2

        if contour == "ascending":
            return min_p + fraction * (max_p - min_p)
        elif contour == "descending":
            return max_p - fraction * (max_p - min_p)
        elif contour == "arch":
            peak_pos = 0.6
            if fraction < peak_pos:
                return min_p + (fraction / peak_pos) * (max_p - min_p)
            else:
                return max_p - ((fraction - peak_pos) / (1 - peak_pos)) * (max_p - min_p)
        elif contour == "wave":
            return mid + rng * 0.6 * math.sin(fraction * 2 * math.pi)
        else:
            return mid
