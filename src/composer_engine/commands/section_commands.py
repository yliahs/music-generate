"""Section-level commands.

Aligned with TECHNICAL.md 5.2 - Section Commands.
Phase 1: Add, Remove, Duplicate, Move, Resize, SetRepeat.
Phase 12: Swap, Split, Merge.
"""

from datetime import datetime, timezone
from uuid import uuid4

from composer_engine.commands.base import Command
from composer_engine.models.enums import SectionType
from composer_engine.models.section import Section
from composer_engine.models.song import Song


class AddSectionCommand(Command):
    """Add a new section to the song."""

    def __init__(self, type: SectionType, start_beat: float, length_beats: float):
        self.type = type
        self.start_beat = start_beat
        self.length_beats = length_beats

    @property
    def description(self) -> str:
        return f"Add {self.type.value} section at beat {self.start_beat}"

    def execute(self, song: Song) -> Song:
        section = Section(
            type=self.type,
            start_beat=self.start_beat,
            length_beats=self.length_beats,
        )
        song = song.model_copy(deep=True)
        song.sections.append(section)
        song.updated_at = datetime.now(timezone.utc)
        return song


class RemoveSectionCommand(Command):
    """Remove a section from the song."""

    def __init__(self, section_id: str):
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Remove section '{self.section_id}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        song.sections = [s for s in song.sections if s.id != self.section_id]
        song.updated_at = datetime.now(timezone.utc)
        return song


class DuplicateSectionCommand(Command):
    """Duplicate a section."""

    def __init__(self, section_id: str):
        self.section_id = section_id

    @property
    def description(self) -> str:
        return f"Duplicate section '{self.section_id}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for section in song.sections:
            if section.id == self.section_id:
                new_section = section.model_copy(deep=True)
                new_section.id = str(uuid4())
                new_section.start_beat = section.start_beat + section.length_beats
                song.sections.append(new_section)
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class MoveSectionCommand(Command):
    """Move a section to a new start beat."""

    def __init__(self, section_id: str, new_start_beat: float):
        self.section_id = section_id
        self.new_start_beat = new_start_beat

    @property
    def description(self) -> str:
        return f"Move section '{self.section_id}' to beat {self.new_start_beat}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for section in song.sections:
            if section.id == self.section_id:
                section.start_beat = self.new_start_beat
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class ResizeSectionCommand(Command):
    """Resize a section."""

    def __init__(self, section_id: str, new_length_beats: float):
        self.section_id = section_id
        self.new_length_beats = new_length_beats

    @property
    def description(self) -> str:
        return f"Resize section '{self.section_id}' to {self.new_length_beats} beats"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for section in song.sections:
            if section.id == self.section_id:
                section.length_beats = self.new_length_beats
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class SetSectionRepeatCommand(Command):
    """Set a section's repeat count."""

    def __init__(self, section_id: str, repeat: int):
        self.section_id = section_id
        self.repeat = max(1, repeat)

    @property
    def description(self) -> str:
        return f"Set section '{self.section_id}' repeat to {self.repeat}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for section in song.sections:
            if section.id == self.section_id:
                section.repeat = self.repeat
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class SwapSectionsCommand(Command):
    """Swap two sections' start_beat positions."""

    def __init__(self, section_id_a: str, section_id_b: str):
        self.section_id_a = section_id_a
        self.section_id_b = section_id_b

    @property
    def description(self) -> str:
        return f"Swap sections '{self.section_id_a}' and '{self.section_id_b}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        sec_a = sec_b = None
        for s in song.sections:
            if s.id == self.section_id_a:
                sec_a = s
            elif s.id == self.section_id_b:
                sec_b = s
        if sec_a and sec_b:
            sec_a.start_beat, sec_b.start_beat = sec_b.start_beat, sec_a.start_beat
        song.updated_at = datetime.now(timezone.utc)
        return song


class SplitSectionCommand(Command):
    """Split a section at a given beat into two."""

    def __init__(self, section_id: str, split_beat: float):
        self.section_id = section_id
        self.split_beat = split_beat

    @property
    def description(self) -> str:
        return f"Split section '{self.section_id}' at beat {self.split_beat}"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        for i, section in enumerate(song.sections):
            if section.id == self.section_id:
                rel = self.split_beat - section.start_beat
                if rel <= 0 or rel >= section.length_beats:
                    break
                new_section = Section(
                    type=section.type,
                    start_beat=self.split_beat,
                    length_beats=section.length_beats - rel,
                )
                section.length_beats = rel
                song.sections.insert(i + 1, new_section)
                break
        song.updated_at = datetime.now(timezone.utc)
        return song


class MergeSectionsCommand(Command):
    """Merge two sections into one (keeps first section's type)."""

    def __init__(self, section_id_a: str, section_id_b: str):
        self.section_id_a = section_id_a
        self.section_id_b = section_id_b

    @property
    def description(self) -> str:
        return f"Merge sections '{self.section_id_a}' and '{self.section_id_b}'"

    def execute(self, song: Song) -> Song:
        song = song.model_copy(deep=True)
        sec_a = sec_b = None
        for s in song.sections:
            if s.id == self.section_id_a:
                sec_a = s
            elif s.id == self.section_id_b:
                sec_b = s
        if sec_a and sec_b:
            new_start = min(sec_a.start_beat, sec_b.start_beat)
            new_end = max(
                sec_a.start_beat + sec_a.length_beats,
                sec_b.start_beat + sec_b.length_beats,
            )
            sec_a.start_beat = new_start
            sec_a.length_beats = new_end - new_start
            song.sections = [s for s in song.sections if s.id != self.section_id_b]
        song.updated_at = datetime.now(timezone.utc)
        return song
