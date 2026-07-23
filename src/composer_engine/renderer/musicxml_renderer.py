"""MusicXML Renderer - Song -> MusicXML string/file.

Phase 10: Converts Song data model to MusicXML format.
Uses xml.etree.ElementTree for XML generation.
"""

import xml.etree.ElementTree as ET
from math import ceil

from composer_engine.models.enums import InstrumentType, Key
from composer_engine.models.song import Song
from composer_engine.models.track import Track


KEY_TO_FIFTHS = {
    Key.C: 0, Key.G: 1, Key.D: 2, Key.A: 3, Key.E: 4, Key.B: 5,
    Key.Gb: -6, Key.F: -1, Key.Bb: -2, Key.Eb: -3, Key.Ab: -4, Key.Db: -5,
}

PITCH_MAP = {
    0: ("C", 0), 1: ("C", 1), 2: ("D", 0), 3: ("E", -1),
    4: ("E", 0), 5: ("F", 0), 6: ("F", 1), 7: ("G", 0),
    8: ("A", -1), 9: ("A", 0), 10: ("B", -1), 11: ("B", 0),
}

STANDARD_DURATIONS = [4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.375, 0.25, 0.125]

BEAT_TYPE_MAP = {
    4.0: "whole",
    3.0: "half",  # dotted
    2.0: "half",
    1.5: "quarter",  # dotted
    1.0: "quarter",
    0.75: "eighth",  # dotted
    0.5: "eighth",
    0.375: "16th",  # dotted
    0.25: "16th",
    0.125: "32nd",
}

DOTTED_DURATIONS = {3.0, 1.5, 0.75, 0.375}


def midi_to_musicxml_pitch(midi_pitch: int) -> tuple[str, int, int]:
    """Convert MIDI pitch to (step, alter, octave)."""
    pc = midi_pitch % 12
    octave = (midi_pitch // 12) - 1
    step, alter = PITCH_MAP[pc]
    return step, alter, octave


def quantize_duration(beats: float) -> float:
    """Quantize to nearest standard duration."""
    if beats <= 0:
        return 0.125
    return min(STANDARD_DURATIONS, key=lambda s: abs(s - beats))


def velocity_to_dynamic(velocity: int) -> str:
    """Map velocity to dynamic marking."""
    if velocity <= 20:
        return "ppp"
    elif velocity <= 40:
        return "pp"
    elif velocity <= 55:
        return "p"
    elif velocity <= 70:
        return "mp"
    elif velocity <= 85:
        return "mf"
    elif velocity <= 100:
        return "f"
    elif velocity <= 115:
        return "ff"
    else:
        return "fff"


class MusicXMLRenderer:
    """Renders Song to MusicXML format."""

    DIVISIONS = 4  # divisions per quarter note (supports 16th notes)

    def render(self, song: Song) -> str:
        """Render Song to MusicXML XML string."""
        root = ET.Element("score-partwise", version="4.0")

        tracks = self._get_renderable_tracks(song)
        if not tracks:
            # Empty score
            ET.SubElement(root, "part-list")
            return ET.tostring(root, encoding="unicode", xml_declaration=True)

        # Part list
        part_list = ET.SubElement(root, "part-list")
        for i, track in enumerate(tracks):
            sp = ET.SubElement(part_list, "score-part", id=f"P{i + 1}")
            ET.SubElement(sp, "part-name").text = track.name

        beats_per_bar = song.global_settings.time_signature[0]
        total_beats = self._calc_total_beats(song)
        num_measures = max(1, ceil(total_beats / beats_per_bar))

        for i, track in enumerate(tracks):
            part = ET.SubElement(root, "part", id=f"P{i + 1}")
            is_drum = track.instrument == InstrumentType.DRUMS

            for m in range(num_measures):
                measure = ET.SubElement(part, "measure", number=str(m + 1))
                bar_start = m * beats_per_bar
                bar_end = bar_start + beats_per_bar

                if m == 0:
                    self._write_attributes(measure, song, is_drum)
                    self._write_direction(measure, song)

                bar_notes = sorted(
                    [n for n in track.notes if bar_start <= n.start_beat < bar_end],
                    key=lambda n: n.start_beat,
                )

                current_beat = bar_start
                for note in bar_notes:
                    if note.start_beat > current_beat + 0.01:
                        gap = note.start_beat - current_beat
                        self._write_rest(measure, gap)
                    self._write_note(measure, note, is_drum)
                    current_beat = note.start_beat + note.duration_beat

                remaining = bar_end - current_beat
                if remaining > 0.01:
                    self._write_rest(measure, remaining)

        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def render_to_file(self, song: Song, path: str) -> str:
        """Render and save as .musicxml file."""
        xml_str = self.render(song)
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        return path

    def _write_attributes(self, measure, song: Song, is_drum: bool):
        attrs = ET.SubElement(measure, "attributes")
        ET.SubElement(attrs, "divisions").text = str(self.DIVISIONS)

        key_el = ET.SubElement(attrs, "key")
        fifths = KEY_TO_FIFTHS.get(song.global_settings.key, 0)
        ET.SubElement(key_el, "fifths").text = str(fifths)

        time_el = ET.SubElement(attrs, "time")
        ET.SubElement(time_el, "beats").text = str(song.global_settings.time_signature[0])
        ET.SubElement(time_el, "beat-type").text = str(song.global_settings.time_signature[1])

        clef = ET.SubElement(attrs, "clef")
        if is_drum:
            ET.SubElement(clef, "sign").text = "percussion"
        else:
            ET.SubElement(clef, "sign").text = "G"
            ET.SubElement(clef, "line").text = "2"

    def _write_direction(self, measure, song: Song):
        direction = ET.SubElement(measure, "direction", placement="above")
        dt = ET.SubElement(direction, "direction-type")
        metronome = ET.SubElement(dt, "metronome")
        ET.SubElement(metronome, "beat-unit").text = "quarter"
        ET.SubElement(metronome, "per-minute").text = str(int(song.global_settings.tempo))
        ET.SubElement(direction, "sound", tempo=str(int(song.global_settings.tempo)))

    def _write_note(self, measure, note, is_drum: bool):
        note_el = ET.SubElement(measure, "note")

        if is_drum:
            unpitched = ET.SubElement(note_el, "unpitched")
            step, _, octave = midi_to_musicxml_pitch(note.pitch)
            ET.SubElement(unpitched, "display-step").text = step
            ET.SubElement(unpitched, "display-octave").text = str(octave)
        else:
            pitch_el = ET.SubElement(note_el, "pitch")
            step, alter, octave = midi_to_musicxml_pitch(note.pitch)
            ET.SubElement(pitch_el, "step").text = step
            if alter != 0:
                ET.SubElement(pitch_el, "alter").text = str(alter)
            ET.SubElement(pitch_el, "octave").text = str(octave)

        q_dur = quantize_duration(note.duration_beat)
        ET.SubElement(note_el, "duration").text = str(round(q_dur * self.DIVISIONS))
        note_type = BEAT_TYPE_MAP.get(q_dur, "quarter")
        ET.SubElement(note_el, "type").text = note_type

        if q_dur in DOTTED_DURATIONS:
            ET.SubElement(note_el, "dot")

    def _write_rest(self, measure, duration_beats: float):
        while duration_beats > 0.01:
            q_dur = quantize_duration(min(duration_beats, 4.0))
            note_el = ET.SubElement(measure, "note")
            ET.SubElement(note_el, "rest")
            ET.SubElement(note_el, "duration").text = str(round(q_dur * self.DIVISIONS))
            note_type = BEAT_TYPE_MAP.get(q_dur, "quarter")
            ET.SubElement(note_el, "type").text = note_type
            if q_dur in DOTTED_DURATIONS:
                ET.SubElement(note_el, "dot")
            duration_beats -= q_dur

    def _get_renderable_tracks(self, song: Song) -> list[Track]:
        solo_tracks = [t for t in song.tracks if t.solo]
        if solo_tracks:
            return solo_tracks
        return [t for t in song.tracks if not t.mute]

    def _calc_total_beats(self, song: Song) -> float:
        max_beat = 0.0
        for track in song.tracks:
            for note in track.notes:
                end = note.start_beat + note.duration_beat
                if end > max_beat:
                    max_beat = end
        for section in song.sections:
            end = section.start_beat + section.length_beats
            if end > max_beat:
                max_beat = end
        return max_beat if max_beat > 0 else 4.0
