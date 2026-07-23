"""Stage definitions for the creation pipeline.

Aligned with TECHNICAL.md 5.7 - Stage 定义 table.
"""

from pydantic import BaseModel

from composer_engine.models.enums import Stage


class StageDefinition(BaseModel):
    """Definition of a single pipeline stage."""

    stage: Stage
    name: str
    description: str
    entry_conditions: dict[str, str]
    exit_conditions: dict[str, str]
    suggested_actions: list[str]
    primary_tools: list[str]


STAGE_DEFINITIONS: dict[Stage, StageDefinition] = {
    Stage.INSPIRATION: StageDefinition(
        stage=Stage.INSPIRATION,
        name="Inspiration",
        description="Define the basic direction: style, mood, tempo, key",
        entry_conditions={"song_exists": "A song must be created"},
        exit_conditions={
            "has_name": "Song must have a name",
            "has_tempo": "Tempo must be set",
            "has_key": "Key must be set",
        },
        suggested_actions=[
            "Set song name, tempo (BPM), key signature",
            "Choose a style (Anime/Jazz/Rock/...)",
            "Describe the mood and energy direction",
            "Decide approximate song length",
        ],
        primary_tools=[
            "create_song", "set_tempo", "set_key", "set_mode", "set_time_signature",
            "set_style", "set_mood", "set_swing", "set_groove",
        ],
    ),
    Stage.COMPOSITION: StageDefinition(
        stage=Stage.COMPOSITION,
        name="Composition",
        description="Build the musical skeleton: structure, chords, melody",
        entry_conditions={"has_tempo": "Tempo must be set", "has_key": "Key must be set"},
        exit_conditions={
            "has_sections": "At least one section (Verse/Chorus/...)",
        },
        suggested_actions=[
            "Design song structure (Intro -> Verse -> Chorus -> ...)",
            "Set length for each section",
            "Generate chord progression (Phase 2+)",
            "Create main melody (Phase 3+)",
        ],
        primary_tools=[
            "add_section", "remove_section", "duplicate_section",
            "generate_chords", "set_chords", "replace_chord",
            "generate_melody", "transpose_melody",
            "analyze_key", "analyze_chords",
        ],
    ),
    Stage.ARRANGEMENT: StageDefinition(
        stage=Stage.ARRANGEMENT,
        name="Arrangement",
        description="Assign instruments and create parts for each track",
        entry_conditions={"has_sections": "Song must have sections"},
        exit_conditions={
            "min_4_tracks_with_notes": "At least 4 tracks with notes (rhythm section)",
        },
        suggested_actions=[
            "Add rhythm section tracks (Piano, Guitar, Bass, Drums)",
            "Generate bass line",
            "Generate drum pattern",
            "Generate piano/guitar accompaniment",
            "Consider adding Strings/Brass/Synth",
            "Adjust volume and pan balance",
        ],
        primary_tools=[
            "add_track", "add_notes", "set_track_volume", "set_track_pan",
            "generate_bass", "generate_drums", "generate_strings",
            "generate_brass", "generate_woodwinds", "generate_synth",
            "generate_piano_part", "generate_guitar_part",
            "increase_energy", "decrease_energy", "add_layer", "remove_layer",
            "add_build_up", "add_transition", "add_fill",
        ],
    ),
    Stage.PRODUCTION: StageDefinition(
        stage=Stage.PRODUCTION,
        name="Production",
        description="Polish and optimize: humanize, balance, fine-tune",
        entry_conditions={"has_tracks_with_notes": "At least some tracks with notes"},
        exit_conditions={"user_satisfied": "User decides the song is ready"},
        suggested_actions=[
            "Apply humanization for natural feel",
            "Adjust volume balance across tracks",
            "Set pan distribution",
            "Check pitch ranges",
            "Listen and fine-tune",
        ],
        primary_tools=[
            "mute_track", "solo_track", "set_track_volume", "set_track_pan",
            "humanize_timing", "humanize_velocity", "apply_micro_timing",
            "apply_groove", "apply_swing", "hand_played_feel",
            "add_automation", "apply_automation_preset", "add_marker",
            "analyze_energy", "analyze_density", "analyze_dynamic",
            "get_full_analysis",
        ],
    ),
    Stage.EXPORT: StageDefinition(
        stage=Stage.EXPORT,
        name="Export",
        description="Export final output files",
        entry_conditions={"has_tracks_with_notes": "At least some tracks with notes"},
        exit_conditions={},
        suggested_actions=[
            "Export MIDI file",
            "Save song project file (JSON)",
            "Save snapshot as version record",
        ],
        primary_tools=["export_midi", "export_musicxml", "save_song", "save_snapshot"],
    ),
}

STAGE_ORDER = [
    Stage.EMPTY,
    Stage.INSPIRATION,
    Stage.COMPOSITION,
    Stage.ARRANGEMENT,
    Stage.PRODUCTION,
    Stage.EXPORT,
]
