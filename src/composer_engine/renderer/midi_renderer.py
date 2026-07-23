"""MIDI Renderer - Song -> pretty_midi -> .mid file.

Render rules (TECHNICAL.md 5.4 / 5.15):
1. Only render non-muted tracks
2. If any solo track exists, only render solo tracks
3. Beat units converted to seconds via tempo
4. Drums track uses Channel 9
5. Track automation curves rendered as MIDI CC events

Solo/Mute priority (TECHNICAL.md 6.5):
  solo=True tracks override mute logic.
"""

import pretty_midi

from composer_engine.models.enums import AUTOMATION_CC, InstrumentType
from composer_engine.models.song import Song
from composer_engine.models.track import Track

CC_INTERPOLATION_STEP = 0.25  # 16th note granularity for CC interpolation


class MidiRenderer:
    """Renders Song to MIDI."""

    def render(self, song: Song) -> pretty_midi.PrettyMIDI:
        """Render Song to a PrettyMIDI object."""
        midi = pretty_midi.PrettyMIDI(initial_tempo=song.global_settings.tempo)
        tempo = song.global_settings.tempo
        master_vel = song.global_settings.master_velocity

        for track in self._get_renderable_tracks(song):
            is_drum = track.instrument == InstrumentType.DRUMS
            instrument = pretty_midi.Instrument(
                program=track.program,
                is_drum=is_drum,
                name=track.name,
            )
            for note in track.notes:
                start = self._beat_to_seconds(note.start_beat, tempo)
                end = self._beat_to_seconds(note.start_beat + note.duration_beat, tempo)
                velocity = max(0, min(127, int(note.velocity * master_vel / 100)))
                instrument.notes.append(
                    pretty_midi.Note(velocity=velocity, pitch=note.pitch, start=start, end=end)
                )
            self._render_automation(instrument, track, tempo)
            midi.instruments.append(instrument)

        return midi

    def _render_automation(self, instrument: pretty_midi.Instrument, track: Track, tempo: float) -> None:
        """Render Track automation curves as MIDI CC events (TECHNICAL.md 5.15)."""
        for curve in track.automation:
            cc_number = AUTOMATION_CC.get(curve.param.value)
            if cc_number is None or len(curve.points) == 0:
                continue
            sorted_pts = sorted(curve.points, key=lambda p: p.beat)
            if len(sorted_pts) == 1:
                t = self._beat_to_seconds(sorted_pts[0].beat, tempo)
                instrument.control_changes.append(
                    pretty_midi.ControlChange(number=cc_number, value=sorted_pts[0].value, time=t)
                )
                continue
            for i in range(len(sorted_pts) - 1):
                p0, p1 = sorted_pts[i], sorted_pts[i + 1]
                beat = p0.beat
                while beat <= p1.beat:
                    if abs(p1.beat - p0.beat) < 1e-6:
                        val = p0.value
                    else:
                        ratio = (beat - p0.beat) / (p1.beat - p0.beat)
                        val = round(p0.value + ratio * (p1.value - p0.value))
                    val = max(0, min(127, val))
                    t = self._beat_to_seconds(beat, tempo)
                    instrument.control_changes.append(
                        pretty_midi.ControlChange(number=cc_number, value=val, time=t)
                    )
                    beat += CC_INTERPOLATION_STEP
                    if beat > p1.beat and abs(beat - CC_INTERPOLATION_STEP - p1.beat) > 1e-6:
                        t = self._beat_to_seconds(p1.beat, tempo)
                        instrument.control_changes.append(
                            pretty_midi.ControlChange(number=cc_number, value=p1.value, time=t)
                        )

    def render_to_file(self, song: Song, path: str) -> str:
        """Render and save as .mid file."""
        midi = self.render(song)
        midi.write(path)
        return path

    def _beat_to_seconds(self, beat: float, tempo: float) -> float:
        """Convert beat position to seconds. (TECHNICAL.md 6.3)"""
        return beat * 60.0 / tempo

    def _get_renderable_tracks(self, song: Song) -> list[Track]:
        """Get tracks to render based on solo/mute logic. (TECHNICAL.md 6.5)"""
        solo_tracks = [t for t in song.tracks if t.solo]
        if solo_tracks:
            return solo_tracks
        return [t for t in song.tracks if not t.mute]
