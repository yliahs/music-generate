"""Stage evaluation logic.

Each stage has an exit check function.
Returns (completed_conditions, missing_conditions).

Aligned with TECHNICAL.md 5.7 - 阶段评估逻辑.
"""

from composer_engine.models.enums import Stage
from composer_engine.models.song import Song


def check_inspiration_exit(song: Song) -> tuple[list[str], list[str]]:
    """Check Inspiration stage exit conditions."""
    completed, missing = [], []

    if song.name:
        completed.append("Song has a name")
    else:
        missing.append("Song needs a name")

    if song.global_settings.tempo > 0:
        completed.append(f"Tempo is set ({song.global_settings.tempo} BPM)")
    else:
        missing.append("Tempo needs to be set")

    if song.global_settings.key:
        completed.append(f"Key is set ({song.global_settings.key.value})")
    else:
        missing.append("Key needs to be set")

    return completed, missing


def check_composition_exit(song: Song) -> tuple[list[str], list[str]]:
    """Check Composition stage exit conditions."""
    completed, missing = [], []

    if len(song.sections) > 0:
        completed.append(f"Has {len(song.sections)} section(s)")
    else:
        missing.append("Needs at least one section")

    if len(song.chord_progression) > 0:
        completed.append(f"Has {len(song.chord_progression)} chord(s)")
    else:
        missing.append("Needs a chord progression (use generate_chords)")

    tracks_with_notes = [t for t in song.tracks if len(t.notes) > 0]
    if len(tracks_with_notes) > 0:
        completed.append(f"Has melody ({len(tracks_with_notes)} track(s) with notes)")
    else:
        missing.append("Needs melody (use generate_melody)")

    return completed, missing


def check_arrangement_exit(song: Song) -> tuple[list[str], list[str]]:
    """Check Arrangement stage exit conditions."""
    completed, missing = [], []
    tracks_with_notes = [t for t in song.tracks if len(t.notes) > 0]
    count = len(tracks_with_notes)

    if count >= 4:
        completed.append(f"Has {count} tracks with notes (>= 4)")
    else:
        missing.append(f"Has {count}/4 tracks with notes, need at least 4")

    return completed, missing


def check_production_exit(song: Song) -> tuple[list[str], list[str]]:
    """Check Production stage exit conditions. User-driven, no hard requirement."""
    return ["User can advance when satisfied"], []


def check_export_exit(song: Song) -> tuple[list[str], list[str]]:
    """Check Export stage exit conditions. No restrictions."""
    return [], []


EXIT_CHECKERS: dict[Stage, callable] = {
    Stage.INSPIRATION: check_inspiration_exit,
    Stage.COMPOSITION: check_composition_exit,
    Stage.ARRANGEMENT: check_arrangement_exit,
    Stage.PRODUCTION: check_production_exit,
    Stage.EXPORT: check_export_exit,
}
