"""Analysis engine for musical content inspection.

Phase 7: TECHNICAL.md 5.14 - read-only analysis of Song data.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from composer_engine.generators.style_engine import STYLE_PRESETS
from composer_engine.models.analysis import AnalysisResult
from composer_engine.models.chord import CadenceType
from composer_engine.models.enums import InstrumentType, Key, Mode
from composer_engine.models.note import Note
from composer_engine.models.song import Song
from composer_engine.models.track import Track
from composer_engine.theory.chord_utils import CHORD_INTERVALS, roman_analysis
from composer_engine.theory.scales import PITCH_TO_KEY

# Simplified Krumhansl-Kessler key profiles
_MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
_MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]


class AnalysisEngine:
    """Stateless analysis methods operating on Song data with optional caching."""

    def _cache_key(self, analysis_type: str, track_id: str | None = None) -> str:
        if track_id:
            return f"{analysis_type}:{track_id}"
        return analysis_type

    def _get_cached(
        self, song: Song, analysis_type: str, track_id: str | None = None
    ) -> dict | None:
        key = self._cache_key(analysis_type, track_id)
        cached = song.analysis_cache.get(key)
        return cached.data if cached else None

    def _set_cache(
        self,
        song: Song,
        analysis_type: str,
        data: dict,
        track_id: str | None = None,
    ) -> None:
        key = self._cache_key(analysis_type, track_id)
        song.analysis_cache[key] = AnalysisResult(
            type=analysis_type, data=data, track_id=track_id
        )

    def invalidate_cache(self, song: Song) -> None:
        """Clear all cached analysis results."""
        song.analysis_cache.clear()

    def _get_track(self, song: Song, track_id: str) -> Track:
        for track in song.tracks:
            if track.id == track_id:
                return track
        raise ValueError(f"Track not found: {track_id}")

    def _melodic_tracks(self, song: Song) -> list[Track]:
        return [
            t
            for t in song.tracks
            if t.instrument != InstrumentType.DRUMS and not t.mute
        ]

    def _track_notes(self, track: Track) -> list[Note]:
        return sorted(track.notes, key=lambda n: n.start_beat)

    def _all_notes(self, song: Song, track_id: str | None = None) -> list[Note]:
        if track_id:
            return self._track_notes(self._get_track(song, track_id))
        notes: list[Note] = []
        for track in song.tracks:
            if track.instrument != InstrumentType.DRUMS and not track.mute:
                notes.extend(track.notes)
        return sorted(notes, key=lambda n: n.start_beat)

    def _song_end_beat(self, song: Song) -> float:
        end = 0.0
        for section in song.sections:
            end = max(end, section.start_beat + section.length_beats * section.repeat)
        for track in song.tracks:
            for note in track.notes:
                end = max(end, note.start_beat + note.duration_beat)
        for chord in song.chord_progression:
            end = max(end, chord.start_beat + chord.duration_beat)
        return max(end, 1.0)

    def _bars(self, song: Song) -> int:
        beats_per_bar = song.global_settings.time_signature[0]
        end = self._song_end_beat(song)
        return max(1, math.ceil(end / beats_per_bar))

    @staticmethod
    def _correlate(profile: list[float], distribution: list[float]) -> float:
        n = len(profile)
        mean_p = sum(profile) / n
        mean_d = sum(distribution) / n
        num = sum((profile[i] - mean_p) * (distribution[i] - mean_d) for i in range(n))
        den_p = math.sqrt(sum((profile[i] - mean_p) ** 2 for i in range(n)))
        den_d = math.sqrt(sum((distribution[i] - mean_d) ** 2 for i in range(n)))
        if den_p == 0 or den_d == 0:
            return 0.0
        return num / (den_p * den_d)

    def analyze_key(self, song: Song) -> dict:
        cached = self._get_cached(song, "key")
        if cached is not None:
            return cached

        pitch_counts = [0.0] * 12
        for track in self._melodic_tracks(song):
            for note in track.notes:
                pitch_counts[note.pitch % 12] += note.duration_beat

        total = sum(pitch_counts)
        if total == 0:
            result = {
                "key": song.global_settings.key.value,
                "mode": song.global_settings.mode.value,
                "confidence": 0.0,
                "alternatives": [],
            }
            self._set_cache(song, "key", result)
            return result

        distribution = [c / total for c in pitch_counts]
        scores: list[tuple[str, str, float]] = []
        for root_pc in range(12):
            for mode, profile in [(Mode.MAJOR, _MAJOR_PROFILE), (Mode.MINOR, _MINOR_PROFILE)]:
                rotated = [profile[(i - root_pc) % 12] for i in range(12)]
                score = self._correlate(rotated, distribution)
                key_name = PITCH_TO_KEY[root_pc].value
                scores.append((key_name, mode.value, score))

        scores.sort(key=lambda x: x[2], reverse=True)
        best_key, best_mode, best_score = scores[0]
        confidence = max(0.0, min(1.0, (best_score + 1) / 2))
        alternatives = [
            {"key": k, "mode": m, "confidence": max(0.0, min(1.0, (s + 1) / 2))}
            for k, m, s in scores[1:4]
        ]
        result = {
            "key": best_key,
            "mode": best_mode,
            "confidence": round(confidence, 3),
            "alternatives": alternatives,
        }
        self._set_cache(song, "key", result)
        return result

    def analyze_tempo(self, song: Song) -> dict:
        cached = self._get_cached(song, "tempo")
        if cached is not None:
            return cached

        bpm = song.global_settings.tempo
        onsets: list[float] = []
        for track in song.tracks:
            if track.instrument == InstrumentType.DRUMS:
                for note in track.notes:
                    onsets.append(note.start_beat)
        if not onsets:
            for note in self._all_notes(song):
                onsets.append(note.start_beat)

        onsets = sorted(set(onsets))
        stability = 1.0
        detected_bpm = bpm
        if len(onsets) >= 2:
            iois = [onsets[i + 1] - onsets[i] for i in range(len(onsets) - 1) if onsets[i + 1] - onsets[i] > 0]
            if iois:
                avg_ioi = sum(iois) / len(iois)
                if avg_ioi > 0:
                    detected_bpm = round(60.0 * song.global_settings.time_signature[0] / (avg_ioi * 4), 1)
                    variance = sum((ioi - avg_ioi) ** 2 for ioi in iois) / len(iois)
                    stability = max(0.0, min(1.0, 1.0 - math.sqrt(variance) / max(avg_ioi, 0.01)))

        result = {
            "bpm": bpm,
            "stability": round(stability, 3),
            "detected_bpm": detected_bpm,
        }
        self._set_cache(song, "tempo", result)
        return result

    def _match_chord(self, pitch_classes: set[int]) -> tuple[str, str] | None:
        if len(pitch_classes) < 2:
            return None
        best: tuple[str, str, float] | None = None
        for root_pc in range(12):
            root = PITCH_TO_KEY[root_pc]
            for quality, intervals in CHORD_INTERVALS.items():
                if quality in ("add9", "add11", "dom9", "maj9", "min9"):
                    continue
                expected = {(root_pc + i) % 12 for i in intervals if i < 12}
                if not expected:
                    continue
                overlap = len(pitch_classes & expected)
                precision = overlap / len(expected)
                recall = overlap / len(pitch_classes)
                score = (precision + recall) / 2
                if best is None or score > best[2]:
                    best = (root.value, quality, score)
        if best and best[2] >= 0.6:
            return best[0], best[1]
        return None

    def analyze_chords(self, song: Song, track_id: str) -> dict:
        cached = self._get_cached(song, "chords", track_id)
        if cached is not None:
            return cached

        notes = self._track_notes(self._get_track(song, track_id))
        window = 2.0
        end_beat = self._song_end_beat(song)
        chords: list[dict] = []
        beat = 0.0
        while beat < end_beat:
            window_end = beat + window
            active_pcs: set[int] = set()
            for note in notes:
                if note.start_beat < window_end and note.start_beat + note.duration_beat > beat:
                    active_pcs.add(note.pitch % 12)
            match = self._match_chord(active_pcs)
            if match:
                root, quality = match
                chords.append({
                    "root": root,
                    "quality": quality,
                    "start_beat": beat,
                    "duration_beat": window,
                })
            beat += window

        result = {"chords": chords}
        self._set_cache(song, "chords", result, track_id)
        return result

    def analyze_phrases(self, song: Song, track_id: str) -> dict:
        cached = self._get_cached(song, "phrases", track_id)
        if cached is not None:
            return cached

        notes = self._track_notes(self._get_track(song, track_id))
        phrases: list[dict] = []
        if not notes:
            result = {"phrases": phrases}
            self._set_cache(song, "phrases", result, track_id)
            return result

        phrase_start = notes[0].start_beat
        phrase_notes = [notes[0]]
        for i in range(1, len(notes)):
            prev = notes[i - 1]
            curr = notes[i]
            gap = curr.start_beat - (prev.start_beat + prev.duration_beat)
            interval_jump = abs(curr.pitch - prev.pitch)
            if gap > 1.0 or interval_jump > 7:
                phrases.append({
                    "start_beat": phrase_start,
                    "end_beat": prev.start_beat + prev.duration_beat,
                    "note_count": len(phrase_notes),
                })
                phrase_start = curr.start_beat
                phrase_notes = [curr]
            else:
                phrase_notes.append(curr)
        last = notes[-1]
        phrases.append({
            "start_beat": phrase_start,
            "end_beat": last.start_beat + last.duration_beat,
            "note_count": len(phrase_notes),
        })

        result = {"phrases": phrases}
        self._set_cache(song, "phrases", result, track_id)
        return result

    def analyze_motifs(self, song: Song, track_id: str) -> dict:
        cached = self._get_cached(song, "motifs", track_id)
        if cached is not None:
            return cached

        notes = self._track_notes(self._get_track(song, track_id))
        motifs: list[dict] = []
        if len(notes) < 3:
            result = {"motifs": motifs}
            self._set_cache(song, "motifs", result, track_id)
            return result

        intervals = [notes[i + 1].pitch - notes[i].pitch for i in range(len(notes) - 1)]
        rhythms = [
            notes[i + 1].start_beat - notes[i].start_beat for i in range(len(notes) - 1)
        ]

        found: dict[tuple, list[float]] = defaultdict(list)
        for size in range(3, min(7, len(notes) + 1)):
            for i in range(len(intervals) - size + 2):
                pattern = tuple(intervals[i : i + size - 1])
                found[pattern].append(notes[i].start_beat)

        for pattern, occurrences in found.items():
            if len(occurrences) >= 2:
                start_idx = next(
                    i for i, n in enumerate(notes) if n.start_beat == occurrences[0]
                )
                motif_pitches = [notes[start_idx + j].pitch for j in range(len(pattern) + 1)]
                motif_rhythm = rhythms[start_idx : start_idx + len(pattern)]
                motifs.append({
                    "pitches": motif_pitches,
                    "rhythm": motif_rhythm,
                    "occurrences": occurrences,
                })

        result = {"motifs": motifs}
        self._set_cache(song, "motifs", result, track_id)
        return result

    def analyze_rhythm(self, song: Song, track_id: str) -> dict:
        cached = self._get_cached(song, "rhythm", track_id)
        if cached is not None:
            return cached

        notes = self._track_notes(self._get_track(song, track_id))
        if not notes:
            result = {
                "dominant_value": 1.0,
                "syncopation_ratio": 0.0,
                "complexity": 0.0,
                "distribution": {},
            }
            self._set_cache(song, "rhythm", result, track_id)
            return result

        durations = [round(n.duration_beat, 2) for n in notes]
        dur_counts = Counter(durations)
        dominant_value = dur_counts.most_common(1)[0][0]
        distribution = {str(k): v for k, v in dur_counts.items()}

        syncopated = sum(
            1 for n in notes if abs(n.start_beat - round(n.start_beat)) > 0.01
        )
        syncopation_ratio = syncopated / len(notes)

        unique_durations = len(dur_counts)
        complexity = min(1.0, unique_durations / 8.0 + syncopation_ratio * 0.5)

        result = {
            "dominant_value": dominant_value,
            "syncopation_ratio": round(syncopation_ratio, 3),
            "complexity": round(complexity, 3),
            "distribution": distribution,
        }
        self._set_cache(song, "rhythm", result, track_id)
        return result

    def analyze_density(self, song: Song, track_id: str | None = None) -> dict:
        cached = self._get_cached(song, "density", track_id)
        if cached is not None:
            return cached

        end_beat = math.ceil(self._song_end_beat(song))
        data = [0] * end_beat
        if track_id:
            tracks = [self._get_track(song, track_id)]
        else:
            tracks = [t for t in song.tracks if not t.mute]

        for track in tracks:
            for note in track.notes:
                beat_idx = int(note.start_beat)
                if 0 <= beat_idx < len(data):
                    data[beat_idx] += 1

        avg = sum(data) / len(data) if data else 0.0
        result = {
            "resolution": "beat",
            "data": data,
            "avg": round(avg, 3),
            "max": max(data) if data else 0,
        }
        self._set_cache(song, "density", result, track_id)
        return result

    def analyze_energy(self, song: Song) -> dict:
        cached = self._get_cached(song, "energy")
        if cached is not None:
            return cached

        beats_per_bar = song.global_settings.time_signature[0]
        num_bars = self._bars(song)
        curve: list[float] = []

        for bar in range(num_bars):
            bar_start = bar * beats_per_bar
            bar_end = bar_start + beats_per_bar
            bar_notes: list[Note] = []
            for track in song.tracks:
                if not track.mute:
                    for note in track.notes:
                        if bar_start <= note.start_beat < bar_end:
                            bar_notes.append(note)

            density = len(bar_notes) / beats_per_bar
            max_density = 4.0
            norm_density = min(1.0, density / max_density)

            if bar_notes:
                avg_vel = sum(n.velocity for n in bar_notes) / len(bar_notes)
                avg_pitch = sum(n.pitch for n in bar_notes) / len(bar_notes)
            else:
                avg_vel = 0.0
                avg_pitch = 0.0

            energy = norm_density * 0.4 + (avg_vel / 127) * 0.4 + (avg_pitch / 127) * 0.2
            curve.append(round(energy, 3))

        avg = sum(curve) / len(curve) if curve else 0.0
        peak_bar = curve.index(max(curve)) if curve else 0
        result = {"curve": curve, "avg": round(avg, 3), "peak_bar": peak_bar}
        self._set_cache(song, "energy", result)
        return result

    def analyze_range(self, song: Song, track_id: str) -> dict:
        cached = self._get_cached(song, "range", track_id)
        if cached is not None:
            return cached

        notes = self._track_notes(self._get_track(song, track_id))
        if not notes:
            result = {"min": 0, "max": 0, "avg": 0.0, "span": 0}
        else:
            pitches = [n.pitch for n in notes]
            result = {
                "min": min(pitches),
                "max": max(pitches),
                "avg": round(sum(pitches) / len(pitches), 1),
                "span": max(pitches) - min(pitches),
            }
        self._set_cache(song, "range", result, track_id)
        return result

    def _bar_fingerprint(self, notes: list[Note], bar: int, beats_per_bar: int) -> str:
        bar_start = bar * beats_per_bar
        bar_end = bar_start + beats_per_bar
        bar_notes = [n for n in notes if bar_start <= n.start_beat < bar_end]
        bar_notes.sort(key=lambda n: n.start_beat)
        parts = [
            f"{n.pitch}:{round(n.start_beat - bar_start, 2)}:{round(n.duration_beat, 2)}"
            for n in bar_notes
        ]
        return "|".join(parts)

    def analyze_repetition(self, song: Song, track_id: str) -> dict:
        cached = self._get_cached(song, "repetition", track_id)
        if cached is not None:
            return cached

        notes = self._track_notes(self._get_track(song, track_id))
        beats_per_bar = song.global_settings.time_signature[0]
        num_bars = self._bars(song)
        fingerprints: dict[str, list[int]] = defaultdict(list)
        for bar in range(num_bars):
            fp = self._bar_fingerprint(notes, bar, beats_per_bar)
            if fp:
                fingerprints[fp].append(bar)

        patterns = [
            {"bars": bars, "length": len(bars)}
            for bars in fingerprints.values()
            if len(bars) >= 2
        ]
        repeated_bars = sum(len(p["bars"]) for p in patterns)
        repetition_rate = repeated_bars / num_bars if num_bars else 0.0

        result = {
            "patterns": patterns,
            "repetition_rate": round(repetition_rate, 3),
        }
        self._set_cache(song, "repetition", result, track_id)
        return result

    def analyze_voice_leading(self, song: Song) -> dict:
        cached = self._get_cached(song, "voice_leading")
        if cached is not None:
            return cached

        issues: list[dict] = []
        tracks = self._melodic_tracks(song)
        for i in range(len(tracks)):
            for j in range(i + 1, len(tracks)):
                ta, tb = tracks[i], tracks[j]
                notes_a = self._track_notes(ta)
                notes_b = self._track_notes(tb)
                if not notes_a or not notes_b:
                    continue

                for idx in range(min(len(notes_a), len(notes_b)) - 1):
                    a0, a1 = notes_a[idx], notes_a[idx + 1]
                    b0, b1 = notes_b[idx], notes_b[idx + 1]
                    if abs(a0.start_beat - b0.start_beat) > 0.5:
                        continue
                    motion_a = a1.pitch - a0.pitch
                    motion_b = b1.pitch - b0.pitch
                    interval_before = (b0.pitch - a0.pitch) % 12
                    interval_after = (b1.pitch - a1.pitch) % 12
                    if motion_a == motion_b and motion_a != 0:
                        if interval_before in (0, 7) and interval_after in (0, 7):
                            issue_type = (
                                "parallel_octaves" if interval_before == 0 else "parallel_fifths"
                            )
                            issues.append({
                                "beat": a0.start_beat,
                                "type": issue_type,
                                "description": (
                                    f"Parallel motion detected between {ta.name} and {tb.name}"
                                ),
                                "track_a": ta.id,
                                "track_b": tb.id,
                            })

        issue_count = len(issues)
        if issue_count == 0:
            severity = "none"
        elif issue_count <= 2:
            severity = "low"
        elif issue_count <= 5:
            severity = "medium"
        else:
            severity = "high"

        result = {"issues": issues, "issue_count": issue_count, "severity": severity}
        self._set_cache(song, "voice_leading", result)
        return result

    def analyze_cadences(self, song: Song) -> dict:
        cached = self._get_cached(song, "cadences")
        if cached is not None:
            return cached

        progression = sorted(song.chord_progression, key=lambda c: c.start_beat)
        cadences: list[dict] = []
        key = song.global_settings.key
        mode = song.global_settings.mode

        for i in range(len(progression) - 1):
            curr = progression[i]
            nxt = progression[i + 1]
            curr_roman = curr.roman or roman_analysis(
                curr.root, curr.quality.value, key, mode
            )
            nxt_roman = nxt.roman or roman_analysis(
                nxt.root, nxt.quality.value, key, mode
            )
            cadence_type = None
            if curr_roman.startswith("V") and nxt_roman.startswith("I"):
                cadence_type = CadenceType.AUTHENTIC.value
            elif curr_roman.startswith("IV") and nxt_roman.startswith("I"):
                cadence_type = CadenceType.PLAGAL.value
            elif nxt_roman.startswith("V"):
                cadence_type = CadenceType.HALF.value
            elif curr_roman.startswith("V") and nxt_roman.startswith("vi"):
                cadence_type = CadenceType.DECEPTIVE.value

            if cadence_type:
                cadences.append({
                    "type": cadence_type,
                    "from": curr_roman,
                    "to": nxt_roman,
                    "beat": nxt.start_beat,
                })

        result = {"cadences": cadences}
        self._set_cache(song, "cadences", result)
        return result

    def _motion(self, prev_pitch: int | None, curr_pitch: int | None) -> str:
        if prev_pitch is None or curr_pitch is None:
            return "oblique"
        if curr_pitch > prev_pitch:
            return "up"
        if curr_pitch < prev_pitch:
            return "down"
        return "same"

    def analyze_counterpoint(self, song: Song, track_id_a: str, track_id_b: str) -> dict:
        cache_key = f"counterpoint:{track_id_a}:{track_id_b}"
        cached = song.analysis_cache.get(cache_key)
        if cached:
            return cached.data

        track_a = self._get_track(song, track_id_a)
        track_b = self._get_track(song, track_id_b)
        notes_a = self._track_notes(track_a)
        notes_b = self._track_notes(track_b)

        end_beat = math.ceil(self._song_end_beat(song))
        parallel = contrary = oblique = similar = 0
        total = 0

        for beat in range(end_beat):
            pitch_a = next(
                (n.pitch for n in notes_a if int(n.start_beat) == beat), None
            )
            pitch_b = next(
                (n.pitch for n in notes_b if int(n.start_beat) == beat), None
            )
            prev_a = next(
                (n.pitch for n in notes_a if int(n.start_beat) == beat - 1), None
            )
            prev_b = next(
                (n.pitch for n in notes_b if int(n.start_beat) == beat - 1), None
            )

            motion_a = self._motion(prev_a, pitch_a)
            motion_b = self._motion(prev_b, pitch_b)

            if motion_a == "oblique" or motion_b == "oblique":
                if pitch_a is None or pitch_b is None or motion_a == "oblique" or motion_b == "oblique":
                    if motion_a == "oblique" or motion_b == "oblique":
                        oblique += 1
                        total += 1
                    continue

            if motion_a == motion_b and motion_a != "same":
                parallel += 1
            elif motion_a != motion_b and "up" in (motion_a, motion_b) and "down" in (motion_a, motion_b):
                contrary += 1
            elif motion_a == motion_b:
                similar += 1
            else:
                oblique += 1
            total += 1

        if total == 0:
            ratios = {
                "parallel_ratio": 0.0,
                "contrary_ratio": 0.0,
                "oblique_ratio": 0.0,
                "similar_ratio": 0.0,
            }
        else:
            ratios = {
                "parallel_ratio": round(parallel / total, 3),
                "contrary_ratio": round(contrary / total, 3),
                "oblique_ratio": round(oblique / total, 3),
                "similar_ratio": round(similar / total, 3),
            }

        result = {**ratios, "issues": []}
        song.analysis_cache[cache_key] = AnalysisResult(
            type="counterpoint",
            data=result,
            track_id=f"{track_id_a}:{track_id_b}",
        )
        return result

    def analyze_style(self, song: Song) -> dict:
        cached = self._get_cached(song, "style")
        if cached is not None:
            return cached

        tempo = song.global_settings.tempo
        instruments = {t.instrument for t in song.tracks}
        chord_count = len(song.chord_progression)
        unique_qualities = len({c.quality for c in song.chord_progression})
        chord_complexity = min(1.0, unique_qualities / 5.0)

        all_notes = self._all_notes(song)
        syncopated = sum(
            1 for n in all_notes if abs(n.start_beat - round(n.start_beat)) > 0.01
        )
        rhythm_complexity = syncopated / len(all_notes) if all_notes else 0.0

        scores: dict[str, float] = {}
        for style_name, preset in STYLE_PRESETS.items():
            score = 0.0
            t_min, t_max = preset["tempo_range"]
            if t_min <= tempo <= t_max:
                score += 0.3
            else:
                dist = min(abs(tempo - t_min), abs(tempo - t_max))
                score += max(0.0, 0.3 - dist / 200)

            recommended = set(preset["recommended_instruments"])
            overlap = len(instruments & recommended) / max(len(recommended), 1)
            score += overlap * 0.4

            if chord_count > 0:
                score += 0.15
            score += chord_complexity * 0.1
            score += rhythm_complexity * 0.05

            scores[style_name] = round(score, 3)

        best_style = max(scores, key=scores.get) if scores else ""
        confidence = scores.get(best_style, 0.0)

        result = {
            "style": best_style,
            "confidence": confidence,
            "scores": scores,
        }
        self._set_cache(song, "style", result)
        return result

    def analyze_mood(self, song: Song) -> dict:
        cached = self._get_cached(song, "mood")
        if cached is not None:
            return cached

        mode = song.global_settings.mode
        valence = 0.5
        if mode == Mode.MAJOR:
            valence += 0.3
        elif mode in (Mode.MINOR, Mode.PHRYGIAN, Mode.LOCRIAN):
            valence -= 0.3
        elif mode in (Mode.DORIAN, Mode.MIXOLYDIAN):
            valence += 0.1

        tempo = song.global_settings.tempo
        arousal = min(1.0, max(0.0, (tempo - 60) / 140))

        notes = self._all_notes(song)
        if notes:
            span = max(n.pitch for n in notes) - min(n.pitch for n in notes)
            valence += min(0.2, span / 127 * 0.2)
            arousal += min(0.2, span / 127 * 0.2)

        valence = max(-1.0, min(1.0, valence * 2 - 1))
        arousal = max(0.0, min(1.0, arousal))

        tags: list[str] = []
        if valence > 0.3:
            tags.append("positive")
        elif valence < -0.3:
            tags.append("melancholic")
        if arousal > 0.6:
            tags.append("energetic")
        elif arousal < 0.3:
            tags.append("calm")
        if song.global_settings.mood:
            tags.append(song.global_settings.mood)

        result = {
            "valence": round(valence, 3),
            "arousal": round(arousal, 3),
            "tags": tags,
        }
        self._set_cache(song, "mood", result)
        return result

    def analyze_complexity(self, song: Song, track_id: str | None = None) -> dict:
        cached = self._get_cached(song, "complexity", track_id)
        if cached is not None:
            return cached

        notes = self._all_notes(song, track_id)
        if notes:
            unique_pitches = len({n.pitch for n in notes})
            pitch_score = min(1.0, unique_pitches / 12)
            unique_durations = len({round(n.duration_beat, 2) for n in notes})
            rhythm_score = min(1.0, unique_durations / 8)
        else:
            pitch_score = rhythm_score = 0.0

        unique_qualities = len({c.quality for c in song.chord_progression})
        harmony_score = min(1.0, unique_qualities / 6 + len(song.chord_progression) / 20)

        section_types = len({s.type for s in song.sections})
        structure_score = min(1.0, section_types / 4 + len(song.sections) / 8)

        total = (pitch_score + rhythm_score + harmony_score + structure_score) / 4
        result = {
            "total": round(total, 3),
            "pitch": round(pitch_score, 3),
            "rhythm": round(rhythm_score, 3),
            "harmony": round(harmony_score, 3),
            "structure": round(structure_score, 3),
        }
        self._set_cache(song, "complexity", result, track_id)
        return result

    def analyze_dynamics(self, song: Song, track_id: str | None = None) -> dict:
        cached = self._get_cached(song, "dynamics", track_id)
        if cached is not None:
            return cached

        notes = self._all_notes(song, track_id)
        if not notes:
            result = {
                "velocity_range": (0, 0),
                "avg_velocity": 0.0,
                "contour": [],
                "trend": "flat",
            }
            self._set_cache(song, "dynamics", result, track_id)
            return result

        velocities = [n.velocity for n in notes]
        beats_per_bar = song.global_settings.time_signature[0]
        num_bars = self._bars(song)
        contour: list[tuple[float, float]] = []
        for bar in range(num_bars):
            bar_start = bar * beats_per_bar
            bar_end = bar_start + beats_per_bar
            bar_vels = [n.velocity for n in notes if bar_start <= n.start_beat < bar_end]
            if bar_vels:
                contour.append((float(bar_start), sum(bar_vels) / len(bar_vels)))

        trend = "flat"
        if len(contour) >= 2:
            first_avg = contour[0][1]
            last_avg = contour[-1][1]
            if last_avg - first_avg > 10:
                trend = "crescendo"
            elif first_avg - last_avg > 10:
                trend = "decrescendo"

        result = {
            "velocity_range": (min(velocities), max(velocities)),
            "avg_velocity": round(sum(velocities) / len(velocities), 1),
            "contour": contour,
            "trend": trend,
        }
        self._set_cache(song, "dynamics", result, track_id)
        return result

    def _section_fingerprint(self, song: Song, section) -> str:
        notes: list[Note] = []
        sec_end = section.start_beat + section.length_beats
        for track in song.tracks:
            if track.instrument != InstrumentType.DRUMS:
                for note in track.notes:
                    if section.start_beat <= note.start_beat < sec_end:
                        notes.append(note)
        notes.sort(key=lambda n: n.start_beat)
        return "|".join(f"{n.pitch}:{round(n.start_beat, 1)}" for n in notes[:20])

    def analyze_structure(self, song: Song) -> dict:
        cached = self._get_cached(song, "structure")
        if cached is not None:
            return cached

        segments: list[dict] = []
        fingerprints: dict[str, str] = {}

        for section in song.sections:
            fp = self._section_fingerprint(song, section)
            label = section.type.value
            similarity_to: list[str] = []
            for other_id, other_fp in fingerprints.items():
                if fp and fp == other_fp:
                    similarity_to.append(other_id)
            segments.append({
                "type": label,
                "start_beat": section.start_beat,
                "end_beat": section.start_beat + section.length_beats,
                "similarity_to": similarity_to,
                "id": section.id,
            })
            fingerprints[section.id] = fp

        types = [s.type.value for s in song.sections]
        if len(types) >= 3 and types[0] == types[2] and types[0] != types[1]:
            form = "ABA"
        elif len(types) >= 4 and types[0] == types[1] and types[2] == types[3]:
            form = "AABB"
        elif len(types) >= 2 and types[0] == types[-1]:
            form = "A...A"
        elif types:
            form = "-".join(types[:4])
        else:
            form = "unknown"

        result = {"segments": segments, "form": form}
        self._set_cache(song, "structure", result)
        return result

    def get_full_analysis(self, song: Song) -> dict:
        cached = self._get_cached(song, "full")
        if cached is not None:
            return cached

        report: dict = {
            "key": self.analyze_key(song),
            "tempo": self.analyze_tempo(song),
            "energy": self.analyze_energy(song),
            "density": self.analyze_density(song),
            "complexity": self.analyze_complexity(song),
            "structure": self.analyze_structure(song),
            "dynamics": self.analyze_dynamics(song),
            "mood": self.analyze_mood(song),
            "cadences": self.analyze_cadences(song),
            "tracks": {},
        }
        for track in song.tracks:
            if track.instrument == InstrumentType.DRUMS:
                continue
            report["tracks"][track.id] = {
                "name": track.name,
                "range": self.analyze_range(song, track.id),
            }

        self._set_cache(song, "full", report)
        return report
