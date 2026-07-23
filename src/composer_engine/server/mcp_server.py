"""MCP Server for Composer Engine.

Phase 1: 29 tools (#1-#29) | Phase 2: 13 tools (#30-#42) | Phase 3: 15 tools (#43-#57)
Phase 4: 18 tools (#58-#75) | Phase 5: 20 tools (#76-#95)
Phase 6: 14 tools (#96-#109) | Phase 7: 19 tools (#110-#128)
Phase 8: 9 tools (#129-#137) | Phase 9: 4 tools (#138-#141) | Phase 10: 2 tools (#142-#143)
Phase 11: 3 tools (#150-#152)
Phase 12: 14 tools (#153-#166) — property completion
Phase 13: 3 tools (#167-#169) — MIDI import
Total: 169 tools (REQUIREMENTS.md 4.1-4.13).

Design principles (TECHNICAL.md 5.5):
1. Global singleton Composer
2. Tools are thin wrappers: validate params -> create Command -> composer.execute()
3. Return full state (song + pipeline + history)
4. English interface enforced (Design Principle G7)
5. Rich docstrings for LLM understanding
"""

from fastmcp import FastMCP

from composer_engine.commands.global_commands import (
    SetGlobalEnergyCommand,
    SetKeyCommand,
    SetMasterHumanizeCommand,
    SetMasterTimingCommand,
    SetMasterVelocityCommand,
    SetModeCommand,
    SetScaleCommand,
    SetTempoCommand,
    SetTimeSignatureCommand,
)
from composer_engine.commands.section_commands import (
    AddSectionCommand,
    DuplicateSectionCommand,
    MergeSectionsCommand,
    MoveSectionCommand,
    RemoveSectionCommand,
    ResizeSectionCommand,
    SetSectionRepeatCommand,
    SplitSectionCommand,
    SwapSectionsCommand,
)
from composer_engine.commands.song_commands import (
    CloneSongCommand,
    CreateSongCommand,
    DeleteSongCommand,
)
from composer_engine.commands.track_commands import (
    AddNotesCommand,
    AddTrackCommand,
    MuteTrackCommand,
    RemoveTrackCommand,
    SetTrackComplexityCommand,
    SetTrackGrooveCommand,
    SetTrackHumanizeCommand,
    SetTrackPanCommand,
    SetTrackRangeCommand,
    SetTrackRegisterCommand,
    SetTrackRhythmCommand,
    SetTrackTimingOffsetCommand,
    SetTrackVelocityOffsetCommand,
    SetTrackVolumeCommand,
    SoloTrackCommand,
)
from composer_engine.commands.chord_commands import (
    BorrowChordCommand,
    GenerateChordsCommand,
    InsertChordCommand,
    ModulateCommand,
    PassingChordCommand,
    ReharmonizeCommand,
    RemoveChordCommand,
    ReplaceChordCommand,
    SecondaryDominantCommand,
    SetCadenceCommand,
    SetChordsCommand,
)
from composer_engine.commands.melody_commands import (
    CallResponseCommand,
    ComplexifyMelodyCommand,
    DevelopMotifCommand,
    ExtendMelodyCommand,
    GenerateHookCommand,
    GenerateMelodyCommand,
    InvertMelodyCommand,
    QuestionAnswerCommand,
    RegenerateMelodyCommand,
    ReverseMelodyCommand,
    SequenceMelodyCommand,
    ShortenMelodyCommand,
    SimplifyMelodyCommand,
    TransposeMelodyCommand,
    VariationMelodyCommand,
)
from composer_engine.commands.bass_commands import (
    GenerateBassCommand,
    RegenerateBassCommand,
    SetBassPatternCommand,
    SimplifyBassCommand,
    TransposeBassCommand,
)
from composer_engine.commands.drums_commands import (
    AddCrashCommand,
    AddDrumFillCommand,
    AddGhostNotesCommand,
    AddPercussionCommand,
    AddTomFillCommand,
    ClearDrumElementCommand,
    GenerateDrumsCommand,
    RegenerateDrumsCommand,
    SetDrumStyleCommand,
    SetHiHatPatternCommand,
    SetKickPatternCommand,
    SetRidePatternCommand,
    SetSnarePatternCommand,
)
from composer_engine.commands.instrument_commands import (
    GenerateBrassCommand,
    GenerateGuitarPartCommand,
    GeneratePianoPartCommand,
    GenerateStringsCommand,
    GenerateSynthCommand,
    GenerateWoodwindsCommand,
)
from composer_engine.commands.arrangement_commands import (
    AddFillCommand,
    AddLayerCommand,
    AddSilenceCommand,
    AddTransitionCommand,
    BreakDownCommand,
    BuildUpCommand,
    DecreaseEnergyCommand,
    DecreaseDensityCommand,
    IncreaseEnergyCommand,
    IncreaseDensityCommand,
    RemoveLayerCommand,
    SetTrackDensityCommand,
    SetTrackEnergyCommand,
    SetTrackOctaveCommand,
)
from composer_engine.commands.humanize_commands import (
    ApplyGrooveCommand,
    ApplyMicroTimingCommand,
    ApplySwingCommand,
    HandPlayedFeelCommand,
    HumanizeTimingCommand,
    HumanizeVelocityCommand,
    PullTimingCommand,
    PushTimingCommand,
)
from composer_engine.commands.style_commands import (
    MixStylesCommand,
    SetGrooveCommand,
    SetMoodCommand,
    SetStyleCommand,
    SetSwingCommand,
)
from composer_engine.commands.analysis_commands import (
    AnalyzeCadencesCommand,
    AnalyzeChordsCommand,
    AnalyzeComplexityCommand,
    AnalyzeCounterpointCommand,
    AnalyzeDensityCommand,
    AnalyzeDynamicsCommand,
    AnalyzeEnergyCommand,
    AnalyzeKeyCommand,
    AnalyzeMotifsCommand,
    AnalyzeMoodCommand,
    AnalyzePhrasesCommand,
    AnalyzeRangeCommand,
    AnalyzeRepetitionCommand,
    AnalyzeRhythmCommand,
    AnalyzeStructureCommand,
    AnalyzeStyleCommand,
    AnalyzeTempoCommand,
    AnalyzeVoiceLeadingCommand,
    GetFullAnalysisCommand,
)
from composer_engine.commands.automation_commands import (
    AddAutomationCommand,
    AddAutomationPointCommand,
    AddMarkerCommand,
    ApplyAutomationPresetCommand,
    ClearAutomationCommand,
    RemoveAutomationCommand,
    RemoveAutomationPointCommand,
    RemoveMarkerCommand,
)
from composer_engine.engine.composer import Composer, ComposerError
from composer_engine.models.chord import CadenceType, Chord, ChordQuality
from composer_engine.models.enums import InstrumentType, Key, Mode, SectionType, Stage
from composer_engine.models.note import Note
from composer_engine.observability.banner import print_banner
from composer_engine.observability.logger import log, setup_logger
from composer_engine.observability.stats import ServerStats
from composer_engine.persistence.json_store import JsonStore
from composer_engine.renderer.midi_renderer import MidiRenderer
from composer_engine.theory.chord_utils import roman_analysis

setup_logger()

mcp = FastMCP("Composer Engine")
composer = Composer()
renderer = MidiRenderer()
store = JsonStore()
stats = ServerStats()

import inspect as _inspect
import time as _time

_tool_starts: dict[str, float] = {}


def _caller_tool_name() -> str:
    """Walk the call stack to find the @mcp.tool() function name."""
    for frame_info in _inspect.stack():
        name = frame_info.function
        if name.startswith("_") or name in ("_ok", "_err", "_caller_tool_name"):
            continue
        if frame_info.frame.f_globals.get("mcp") is mcp:
            return name
    return "unknown"


def _ok(data: dict | None = None, message: str = "OK") -> dict:
    tool_name = _caller_tool_name()
    start = _tool_starts.pop(tool_name, None)
    elapsed = (_time.perf_counter() - start) * 1000 if start else 0
    log(f"{tool_name}() → OK ({elapsed:.0f}ms): {message}", tag="TOOL")
    stats.record_tool_call(tool_name, True, elapsed)
    result = {"success": True, "message": message}
    result.update(composer.get_state())
    if data:
        result["data"] = data
    return result


def _err(error: str, message: str = "") -> dict:
    tool_name = _caller_tool_name()
    start = _tool_starts.pop(tool_name, None)
    elapsed = (_time.perf_counter() - start) * 1000 if start else 0
    log(f"{tool_name}() → FAIL ({elapsed:.0f}ms): {error} {message}", tag="TOOL", level="WARN")
    stats.record_tool_call(tool_name, False, elapsed)
    return {"success": False, "error": error, "message": message}


def _begin() -> None:
    """Record start time for the calling tool function."""
    tool_name = _caller_tool_name()
    _tool_starts[tool_name] = _time.perf_counter()


# ──────────────────────────── Song Tools (#1-#4) ────────────────────────────


@mcp.tool()
def create_song(
    name: str,
    tempo: float = 120.0,
    key: str = "C",
    mode: str = "major",
    time_signature_numerator: int = 4,
    time_signature_denominator: int = 4,
) -> dict:
    """Create a new song. This is the starting point of all composition.

    Args:
        name: Song name
        tempo: Tempo in BPM, default 120
        key: Key signature. Options: C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B
        mode: Mode. Options: major, minor, dorian, mixolydian, lydian, phrygian, locrian
        time_signature_numerator: Time signature numerator, default 4
        time_signature_denominator: Time signature denominator, default 4

    Returns:
        Current song state with pipeline info
    """
    try:
        _begin()
        cmd = CreateSongCommand(
            name=name, tempo=tempo, key=Key(key), mode=Mode(mode),
            time_signature=(time_signature_numerator, time_signature_denominator),
        )
        composer.execute(cmd)
        return _ok(message=f"Song '{name}' created")
    except Exception as e:
        return _err("create_failed", str(e))


@mcp.tool()
def delete_song() -> dict:
    """Delete the current song and reset the session.

    Returns:
        Empty state
    """
    try:
        _begin()
        composer.execute(DeleteSongCommand())
        composer.history.clear()
        return _ok(message="Song deleted")
    except Exception as e:
        return _err("delete_failed", str(e))


@mcp.tool()
def clone_song(new_name: str) -> dict:
    """Clone the current song with a new name.

    Args:
        new_name: Name for the cloned song

    Returns:
        Cloned song state
    """
    try:
        _begin()
        composer.execute(CloneSongCommand(new_name))
        return _ok(message=f"Song cloned as '{new_name}'")
    except Exception as e:
        return _err("clone_failed", str(e))


@mcp.tool()
def get_song_state() -> dict:
    """Get the current song's complete state including pipeline and history info.

    Returns:
        Full state: song data, pipeline stage/progress, history undo/redo counts,
        and computed song_length_beats.
    """
    result = _ok()
    if result.get("success") and composer.song and composer.song.sections:
        result["data"]["song_length_beats"] = max(
            s.start_beat + s.length_beats * s.repeat
            for s in composer.song.sections
        )
    elif result.get("success") and composer.song:
        result["data"]["song_length_beats"] = 0.0
    return result


# ──────────────────────────── Track Tools (#5-#10) ──────────────────────────


@mcp.tool()
def add_track(
    name: str,
    instrument: str,
    program: int | None = None,
    channel: int | None = None,
) -> dict:
    """Add a new track to the song.

    Args:
        name: Track name (e.g. "Piano", "Lead Guitar")
        instrument: Instrument type. Options: piano, bass, strings, pad, lead, synth, drums, fx, brass, woodwinds, guitar, voice
        program: MIDI program number (0-127). Auto-assigned if omitted.
        channel: MIDI channel (0-15). Auto-assigned if omitted (drums=9).

    Returns:
        Updated song state
    """
    try:
        _begin()
        cmd = AddTrackCommand(name=name, instrument=InstrumentType(instrument),
                              program=program, channel=channel)
        composer.execute(cmd)
        return _ok(message=f"Track '{name}' added")
    except Exception as e:
        return _err("add_track_failed", str(e))


@mcp.tool()
def remove_track(track_id: str) -> dict:
    """Remove a track from the song.

    Args:
        track_id: ID of the track to remove

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(RemoveTrackCommand(track_id))
        return _ok(message="Track removed")
    except Exception as e:
        return _err("remove_track_failed", str(e))


@mcp.tool()
def mute_track(track_id: str, mute: bool = True) -> dict:
    """Mute or unmute a track.

    Args:
        track_id: ID of the track
        mute: True to mute, False to unmute

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(MuteTrackCommand(track_id, mute))
        return _ok(message=f"Track {'muted' if mute else 'unmuted'}")
    except Exception as e:
        return _err("mute_failed", str(e))


@mcp.tool()
def solo_track(track_id: str, solo: bool = True) -> dict:
    """Solo or unsolo a track.

    Args:
        track_id: ID of the track
        solo: True to solo, False to unsolo

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SoloTrackCommand(track_id, solo))
        return _ok(message=f"Track {'soloed' if solo else 'unsoloed'}")
    except Exception as e:
        return _err("solo_failed", str(e))


@mcp.tool()
def set_track_volume(track_id: str, volume: int) -> dict:
    """Set track volume.

    Args:
        track_id: ID of the track
        volume: Volume level (0-127)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackVolumeCommand(track_id, volume))
        return _ok(message=f"Track volume set to {volume}")
    except Exception as e:
        return _err("set_volume_failed", str(e))


@mcp.tool()
def set_track_pan(track_id: str, pan: int) -> dict:
    """Set track pan position.

    Args:
        track_id: ID of the track
        pan: Pan position (0=left, 64=center, 127=right)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackPanCommand(track_id, pan))
        return _ok(message=f"Track pan set to {pan}")
    except Exception as e:
        return _err("set_pan_failed", str(e))


# ──────────────────────────── Section Tools (#11-#13) ───────────────────────


@mcp.tool()
def add_section(section_type: str, start_beat: float, length_beats: float) -> dict:
    """Add a new section to the song.

    Args:
        section_type: Section type. Options: intro, verse, pre_chorus, chorus, bridge, solo, breakdown, outro
        start_beat: Start position in beats
        length_beats: Length in beats (e.g. 16 for 4 bars in 4/4)

    Returns:
        Updated song state
    """
    try:
        _begin()
        cmd = AddSectionCommand(SectionType(section_type), start_beat, length_beats)
        composer.execute(cmd)
        return _ok(message=f"Section '{section_type}' added")
    except Exception as e:
        return _err("add_section_failed", str(e))


@mcp.tool()
def remove_section(section_id: str) -> dict:
    """Remove a section from the song.

    Args:
        section_id: ID of the section to remove

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(RemoveSectionCommand(section_id))
        return _ok(message="Section removed")
    except Exception as e:
        return _err("remove_section_failed", str(e))


@mcp.tool()
def duplicate_section(section_id: str) -> dict:
    """Duplicate a section. The copy is placed right after the original.

    Args:
        section_id: ID of the section to duplicate

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(DuplicateSectionCommand(section_id))
        return _ok(message="Section duplicated")
    except Exception as e:
        return _err("duplicate_section_failed", str(e))


@mcp.tool()
def move_section(section_id: str, new_start_beat: float) -> dict:
    """Move a section to a new start beat position.

    Args:
        section_id: ID of the section to move
        new_start_beat: New start position in beats (>= 0)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(MoveSectionCommand(section_id, new_start_beat))
        return _ok(message=f"Section moved to beat {new_start_beat}")
    except Exception as e:
        return _err("move_section_failed", str(e))


@mcp.tool()
def resize_section(section_id: str, new_length_beats: float) -> dict:
    """Resize a section (change its length in beats).

    Args:
        section_id: ID of the section to resize
        new_length_beats: New length in beats (> 0, e.g. 16 for 4 bars in 4/4)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(ResizeSectionCommand(section_id, new_length_beats))
        return _ok(message=f"Section resized to {new_length_beats} beats")
    except Exception as e:
        return _err("resize_section_failed", str(e))


@mcp.tool()
def set_section_repeat(section_id: str, repeat: int) -> dict:
    """Set how many times a section repeats.

    Args:
        section_id: ID of the section
        repeat: Number of repetitions (>= 1, default 1 means play once)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetSectionRepeatCommand(section_id, repeat))
        return _ok(message=f"Section repeat set to {repeat}")
    except Exception as e:
        return _err("set_section_repeat_failed", str(e))


# ──────────────────────────── Note Tool (#14) ──────────────────────────────


@mcp.tool()
def add_notes(track_id: str, notes: list[dict]) -> dict:
    """Add notes to a track.

    Args:
        track_id: ID of the track
        notes: List of note objects, each with: pitch (0-127), start_beat (float), duration_beat (float), velocity (0-127, optional default 100)

    Returns:
        Updated song state
    """
    try:
        _begin()
        note_objects = [Note(**n) for n in notes]
        composer.execute(AddNotesCommand(track_id, note_objects))
        return _ok(message=f"{len(note_objects)} note(s) added")
    except Exception as e:
        return _err("add_notes_failed", str(e))


# ──────────────────────────── Global Tools (#15-#17) ───────────────────────


@mcp.tool()
def set_tempo(tempo: float) -> dict:
    """Set the song tempo.

    Args:
        tempo: Tempo in BPM (e.g. 120, 140, 80)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTempoCommand(tempo))
        return _ok(message=f"Tempo set to {tempo} BPM")
    except Exception as e:
        return _err("set_tempo_failed", str(e))


@mcp.tool()
def set_key(key: str) -> dict:
    """Set the song key.

    Args:
        key: Key signature. Options: C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetKeyCommand(Key(key)))
        return _ok(message=f"Key set to {key}")
    except Exception as e:
        return _err("set_key_failed", str(e))


@mcp.tool()
def set_time_signature(numerator: int, denominator: int) -> dict:
    """Set the song time signature.

    Args:
        numerator: Time signature numerator (e.g. 4, 3, 6)
        denominator: Time signature denominator (e.g. 4, 8)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTimeSignatureCommand(numerator, denominator))
        return _ok(message=f"Time signature set to {numerator}/{denominator}")
    except Exception as e:
        return _err("set_time_signature_failed", str(e))


@mcp.tool()
def set_mode(mode: str) -> dict:
    """Set the song mode (scale type).

    Args:
        mode: Mode/scale type. Options: major, minor, dorian, mixolydian, lydian, phrygian, locrian

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetModeCommand(Mode(mode)))
        return _ok(message=f"Mode set to {mode}")
    except Exception as e:
        return _err("set_mode_failed", str(e))


@mcp.tool()
def set_master_velocity(velocity: int) -> dict:
    """Set the global master velocity baseline.

    All note velocities are scaled relative to this value during MIDI rendering.

    Args:
        velocity: Master velocity (0-127, default 100)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetMasterVelocityCommand(velocity))
        return _ok(message=f"Master velocity set to {velocity}")
    except Exception as e:
        return _err("set_master_velocity_failed", str(e))


@mcp.tool()
def set_master_humanize(amount: float) -> dict:
    """Set the global master humanize amount.

    Controls the overall humanization intensity applied during rendering.

    Args:
        amount: Humanize amount (0.0 = fully mechanical, 1.0 = maximum humanization)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetMasterHumanizeCommand(amount))
        return _ok(message=f"Master humanize set to {amount}")
    except Exception as e:
        return _err("set_master_humanize_failed", str(e))


# ──────────────────────────── Undo/Redo (#18-#19) ─────────────────────────


@mcp.tool()
def undo() -> dict:
    """Undo the most recent operation.

    Returns:
        Restored song state
    """
    try:
        _begin()
        composer.undo()
        return _ok(message="Undone")
    except ComposerError as e:
        return _err("undo_failed", str(e))


@mcp.tool()
def redo() -> dict:
    """Redo the most recently undone operation.

    Returns:
        Restored song state
    """
    try:
        _begin()
        composer.redo()
        return _ok(message="Redone")
    except ComposerError as e:
        return _err("redo_failed", str(e))


# ──────────────────────────── Snapshot (#20-#22) ──────────────────────────


@mcp.tool()
def save_snapshot(name: str) -> dict:
    """Save the current song state as a named snapshot.

    Args:
        name: Snapshot name (e.g. "before_chorus_edit", "v1")

    Returns:
        Confirmation with snapshot name
    """
    try:
        _begin()
        composer.save_snapshot(name)
        return _ok(message=f"Snapshot '{name}' saved")
    except ComposerError as e:
        return _err("snapshot_failed", str(e))


@mcp.tool()
def load_snapshot(name: str) -> dict:
    """Load a previously saved snapshot, replacing the current state.

    Args:
        name: Snapshot name to load

    Returns:
        Restored song state
    """
    try:
        _begin()
        composer.load_snapshot(name)
        return _ok(message=f"Snapshot '{name}' loaded")
    except KeyError:
        return _err("snapshot_not_found", f"Snapshot '{name}' not found")


@mcp.tool()
def list_snapshots() -> dict:
    """List all saved snapshots.

    Returns:
        List of snapshot names
    """
    names = composer.snapshots.list()
    return _ok(data={"snapshots": names}, message=f"{len(names)} snapshot(s)")


# ──────────────────────────── Save/Load (#23-#24) ─────────────────────────


@mcp.tool()
def save_song(filename: str | None = None) -> dict:
    """Save the current song to a JSON file.

    Args:
        filename: Optional filename. Auto-generated from song ID if omitted.

    Returns:
        File path where the song was saved
    """
    try:
        _begin()
        if composer.song is None:
            return _err("no_song", "No song to save")
        path = store.save_song(composer.song, filename)
        return _ok(data={"path": str(path)}, message=f"Song saved to {path}")
    except Exception as e:
        return _err("save_failed", str(e))


@mcp.tool()
def load_song(filename: str) -> dict:
    """Load a song from a JSON file.

    Args:
        filename: Filename of the song to load

    Returns:
        Loaded song state
    """
    try:
        _begin()
        composer.song = store.load_song(filename)
        composer.pipeline.evaluate(composer.song)
        composer.history.clear()
        return _ok(message=f"Song loaded from {filename}")
    except FileNotFoundError:
        return _err("file_not_found", f"File '{filename}' not found")
    except Exception as e:
        return _err("load_failed", str(e))


# ──────────────────────────── Export (#25) ─────────────────────────────────


@mcp.tool()
def export_midi(output_path: str = "output.mid") -> dict:
    """Export the current song as a MIDI file.

    Args:
        output_path: Output file path, default "output.mid"

    Returns:
        File path where the MIDI was exported
    """
    try:
        _begin()
        if composer.song is None:
            return _err("no_song", "No song to export")
        path = renderer.render_to_file(composer.song, output_path)
        return _ok(data={"path": path}, message=f"MIDI exported to {path}")
    except Exception as e:
        return _err("export_failed", str(e))


# ──────────────────────────── History (#26) ────────────────────────────────


@mcp.tool()
def list_history() -> dict:
    """List the operation history (event log).

    Returns:
        List of past operations with timestamps and descriptions
    """
    events = [e.model_dump(mode="json") for e in composer.history.event_log]
    return _ok(data={"history": events}, message=f"{len(events)} event(s)")


# ──────────────────────────── Pipeline (#27-#29) ──────────────────────────


@mcp.tool()
def get_stage_guide() -> dict:
    """Get the current creation stage guide.

    Call this tool when:
    1. Starting a new composition session
    2. After completing a set of operations, to confirm next steps
    3. When unsure about what to do next

    Returns:
        Current stage info, progress percentage, suggested actions, missing items, recommended tools
    """
    guide = composer.get_stage_guide()
    return _ok(data=guide, message=f"Stage: {guide.get('stage', 'unknown')}")


@mcp.tool()
def advance_stage() -> dict:
    """Manually advance to the next pipeline stage.

    Use when the current stage exit conditions are met and you want
    to move forward in the creation pipeline.

    Returns:
        Updated stage info and song state
    """
    composer.pipeline.advance()
    return _ok(message=f"Advanced to {composer.pipeline.current_stage.value}")


@mcp.tool()
def go_back_stage(target_stage: str) -> dict:
    """Go back to a previous pipeline stage.

    Use when you need to revisit and modify earlier creative decisions.

    Args:
        target_stage: Target stage name. Options: inspiration, composition, arrangement, production

    Returns:
        Updated stage info and song state
    """
    try:
        _begin()
        composer.pipeline.go_back(Stage(target_stage))
        return _ok(message=f"Went back to {target_stage}")
    except ValueError:
        return _err("invalid_stage", f"Unknown stage: {target_stage}")


# ──────────────────────────── Chord Tools (#30-#42) ──────────────────────


@mcp.tool()
def generate_chords(
    style: str = "pop",
    template_name: str | None = None,
    beats_per_chord: float = 4.0,
    section_id: str | None = None,
) -> dict:
    """Generate a chord progression for a section or the whole song.

    Args:
        style: Style preset. Options: pop, rock, jazz, blues, anime, classical
        template_name: Specific template name (e.g. "royal_road", "jazz_251"). Random if omitted.
        beats_per_chord: Duration of each chord in beats, default 4
        section_id: Optional section ID to generate chords for. Whole song if omitted.

    Returns:
        Updated song state with chord progression
    """
    try:
        _begin()
        cmd = GenerateChordsCommand(style, template_name, beats_per_chord, section_id)
        composer.execute(cmd)
        return _ok(message=f"Generated {style} chords")
    except Exception as e:
        return _err("generate_chords_failed", str(e))


@mcp.tool()
def set_chords(chords: list[dict]) -> dict:
    """Directly set the chord progression.

    Args:
        chords: List of chord objects, each with: root (key name), quality (chord quality), start_beat (float), duration_beat (float), bass (optional key name)

    Returns:
        Updated song state
    """
    try:
        _begin()
        chord_objs = [Chord(**c) for c in chords]
        composer.execute(SetChordsCommand(chord_objs))
        return _ok(message=f"Set {len(chord_objs)} chords")
    except Exception as e:
        return _err("set_chords_failed", str(e))


@mcp.tool()
def replace_chord(chord_index: int, new_root: str, new_quality: str) -> dict:
    """Replace a chord at a specific index in the progression.

    Args:
        chord_index: Index of the chord to replace (0-based)
        new_root: New root note. Options: C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B
        new_quality: New chord quality. Options: major, minor, diminished, augmented, dom7, maj7, min7, half_dim7, dim7, sus2, sus4

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(ReplaceChordCommand(chord_index, Key(new_root), ChordQuality(new_quality)))
        return _ok(message=f"Replaced chord #{chord_index}")
    except Exception as e:
        return _err("replace_chord_failed", str(e))


@mcp.tool()
def insert_chord(position_beat: float, root: str, quality: str = "major",
                 duration_beat: float = 4.0) -> dict:
    """Insert a new chord at a specific beat position.

    Args:
        position_beat: Beat position to insert the chord
        root: Root note. Options: C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B
        quality: Chord quality, default "major"
        duration_beat: Duration in beats, default 4

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(InsertChordCommand(position_beat, Key(root), ChordQuality(quality), duration_beat))
        return _ok(message=f"Inserted {root}{quality} at beat {position_beat}")
    except Exception as e:
        return _err("insert_chord_failed", str(e))


@mcp.tool()
def remove_chord(chord_index: int) -> dict:
    """Remove a chord from the progression by index.

    Args:
        chord_index: Index of the chord to remove (0-based)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(RemoveChordCommand(chord_index))
        return _ok(message=f"Removed chord #{chord_index}")
    except Exception as e:
        return _err("remove_chord_failed", str(e))


@mcp.tool()
def reharmonize(target_style: str, section_id: str | None = None) -> dict:
    """Reharmonize the chord progression using a different style.

    Args:
        target_style: Target style. Options: pop, rock, jazz, blues, anime, classical
        section_id: Optional section ID. Whole song if omitted.

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(ReharmonizeCommand(target_style, section_id))
        return _ok(message=f"Reharmonized to {target_style}")
    except Exception as e:
        return _err("reharmonize_failed", str(e))


@mcp.tool()
def borrow_chord(chord_index: int, source_mode: str = "minor") -> dict:
    """Borrow a chord from a parallel mode (e.g. borrow from minor while in major).

    Args:
        chord_index: Index of the chord to replace with borrowed version
        source_mode: Mode to borrow from. Options: major, minor, dorian, mixolydian

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(BorrowChordCommand(chord_index, Mode(source_mode)))
        return _ok(message=f"Borrowed chord #{chord_index} from {source_mode}")
    except Exception as e:
        return _err("borrow_chord_failed", str(e))


@mcp.tool()
def secondary_dominant(target_chord_index: int) -> dict:
    """Insert a secondary dominant (V/x) before a target chord.

    Args:
        target_chord_index: Index of the target chord

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SecondaryDominantCommand(target_chord_index))
        return _ok(message=f"Added secondary dominant before chord #{target_chord_index}")
    except Exception as e:
        return _err("secondary_dominant_failed", str(e))


@mcp.tool()
def add_passing_chord(chord_index_a: int, chord_index_b: int) -> dict:
    """Insert a chromatic passing chord between two chords.

    Args:
        chord_index_a: Index of the first chord
        chord_index_b: Index of the second chord

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(PassingChordCommand(chord_index_a, chord_index_b))
        return _ok(message=f"Added passing chord between #{chord_index_a} and #{chord_index_b}")
    except Exception as e:
        return _err("passing_chord_failed", str(e))


@mcp.tool()
def modulate(target_key: str, target_mode: str | None = None,
             pivot_beat: float = 0.0) -> dict:
    """Modulate to a new key starting from a pivot beat.

    Args:
        target_key: Target key. Options: C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B
        target_mode: Target mode (optional, keeps current if omitted)
        pivot_beat: Beat position where modulation begins

    Returns:
        Updated song state
    """
    try:
        _begin()
        mode = Mode(target_mode) if target_mode else None
        composer.execute(ModulateCommand(Key(target_key), mode, pivot_beat))
        return _ok(message=f"Modulated to {target_key} at beat {pivot_beat}")
    except Exception as e:
        return _err("modulate_failed", str(e))


@mcp.tool()
def set_cadence(section_id: str, cadence_type: str) -> dict:
    """Set the cadence type at the end of a section.

    Args:
        section_id: ID of the section
        cadence_type: Cadence type. Options: authentic (V→I), plagal (IV→I), half (→V), deceptive (V→vi)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetCadenceCommand(section_id, CadenceType(cadence_type)))
        return _ok(message=f"Set {cadence_type} cadence")
    except Exception as e:
        return _err("set_cadence_failed", str(e))


@mcp.tool()
def get_roman_analysis() -> dict:
    """Get Roman numeral analysis of the current chord progression.

    Returns:
        List of chords with their Roman numeral labels, root, quality, and beat positions
    """
    if composer.song is None:
        return _err("no_song", "No song")
    chords = []
    key = composer.song.global_settings.key
    mode = composer.song.global_settings.mode
    for i, c in enumerate(composer.song.chord_progression):
        roman = c.roman or roman_analysis(c.root, c.quality.value, key, mode)
        chords.append({
            "index": i, "roman": roman,
            "root": c.root.value, "quality": c.quality.value,
            "start_beat": c.start_beat, "duration_beat": c.duration_beat,
        })
    return _ok(data={"analysis": chords}, message=f"{len(chords)} chord(s) analyzed")


@mcp.tool()
def get_chord_progression() -> dict:
    """Get the current chord progression details.

    Returns:
        Full chord progression with chord names, positions, and Roman numerals
    """
    if composer.song is None:
        return _err("no_song", "No song")
    chords = []
    key = composer.song.global_settings.key
    mode = composer.song.global_settings.mode
    for i, c in enumerate(composer.song.chord_progression):
        roman = c.roman or roman_analysis(c.root, c.quality.value, key, mode)
        name = f"{c.root.value}{'' if c.quality == ChordQuality.MAJOR else c.quality.value}"
        chords.append({
            "index": i, "name": name, "roman": roman,
            "root": c.root.value, "quality": c.quality.value,
            "bass": c.bass.value if c.bass else None,
            "start_beat": c.start_beat, "duration_beat": c.duration_beat,
        })
    return _ok(data={"chord_progression": chords}, message=f"{len(chords)} chord(s)")


# ──────────────────────────── Melody Tools (#43-#57) ────────────────────


@mcp.tool()
def generate_melody(
    track_id: str,
    section_id: str | None = None,
    note_density: str = "normal",
    pitch_range_low: int = 60,
    pitch_range_high: int = 84,
    contour: str = "arch",
    chord_tone_weight: float = 0.7,
    rhythm_complexity: str = "moderate",
) -> dict:
    """Generate a melody for a track based on the chord progression.

    Args:
        track_id: ID of the target track
        section_id: Optional section ID. Uses full song range if omitted.
        note_density: Note density. Options: sparse, normal, dense
        pitch_range_low: Lowest MIDI pitch (default 60 = C4)
        pitch_range_high: Highest MIDI pitch (default 84 = C6)
        contour: Melodic contour shape. Options: arch, ascending, descending, wave, flat
        chord_tone_weight: How closely to follow chord tones (0.0-1.0, default 0.7)
        rhythm_complexity: Rhythm complexity. Options: simple, moderate, complex

    Returns:
        Updated song state with generated melody
    """
    try:
        _begin()
        cmd = GenerateMelodyCommand(
            track_id, section_id, note_density, pitch_range_low,
            pitch_range_high, contour, chord_tone_weight, rhythm_complexity,
        )
        composer.execute(cmd)
        return _ok(message="Melody generated")
    except Exception as e:
        return _err("generate_melody_failed", str(e))


@mcp.tool()
def regenerate_melody(track_id: str, section_id: str | None = None) -> dict:
    """Regenerate melody with the same constraints (clears existing notes and creates new ones).

    Args:
        track_id: ID of the target track
        section_id: Optional section ID

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(RegenerateMelodyCommand(track_id, section_id))
        return _ok(message="Melody regenerated")
    except Exception as e:
        return _err("regenerate_failed", str(e))


@mcp.tool()
def simplify_melody(track_id: str, strength: float = 0.5) -> dict:
    """Simplify the melody by removing short notes and ornaments.

    Args:
        track_id: ID of the target track
        strength: Simplification strength (0.0-1.0, higher = more aggressive)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SimplifyMelodyCommand(track_id, strength))
        return _ok(message="Melody simplified")
    except Exception as e:
        return _err("simplify_failed", str(e))


@mcp.tool()
def complexify_melody(track_id: str, strength: float = 0.5) -> dict:
    """Add passing tones, ornaments, and embellishments to the melody.

    Args:
        track_id: ID of the target track
        strength: Complexity strength (0.0-1.0, higher = more additions)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(ComplexifyMelodyCommand(track_id, strength))
        return _ok(message="Melody complexified")
    except Exception as e:
        return _err("complexify_failed", str(e))


@mcp.tool()
def transpose_melody(track_id: str, semitones: int) -> dict:
    """Transpose the melody by a number of semitones.

    Args:
        track_id: ID of the target track
        semitones: Number of semitones to transpose (positive=up, negative=down)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(TransposeMelodyCommand(track_id, semitones))
        return _ok(message=f"Melody transposed by {semitones} semitones")
    except Exception as e:
        return _err("transpose_failed", str(e))


@mcp.tool()
def invert_melody(track_id: str, pivot_pitch: int = 60) -> dict:
    """Invert the melody around a pivot pitch (melodic inversion).

    Args:
        track_id: ID of the target track
        pivot_pitch: MIDI pitch to invert around (default 60 = C4)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(InvertMelodyCommand(track_id, pivot_pitch))
        return _ok(message=f"Melody inverted around pitch {pivot_pitch}")
    except Exception as e:
        return _err("invert_failed", str(e))


@mcp.tool()
def reverse_melody(track_id: str) -> dict:
    """Reverse the melody in time (retrograde).

    Args:
        track_id: ID of the target track

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(ReverseMelodyCommand(track_id))
        return _ok(message="Melody reversed")
    except Exception as e:
        return _err("reverse_failed", str(e))


@mcp.tool()
def sequence_melody(track_id: str, interval: int = 2, count: int = 2) -> dict:
    """Create a melodic sequence (repeat the phrase transposed by interval).

    Args:
        track_id: ID of the target track
        interval: Transposition interval in semitones for each repetition
        count: Number of sequential repetitions

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SequenceMelodyCommand(track_id, interval, count))
        return _ok(message=f"Melody sequenced {count} times at interval {interval}")
    except Exception as e:
        return _err("sequence_failed", str(e))


@mcp.tool()
def variation_melody(track_id: str) -> dict:
    """Create a variation of the melody (keep skeleton notes, vary passing tones).

    Args:
        track_id: ID of the target track

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(VariationMelodyCommand(track_id))
        return _ok(message="Melody variation created")
    except Exception as e:
        return _err("variation_failed", str(e))


@mcp.tool()
def develop_motif(track_id: str, motif_beats: float = 4.0) -> dict:
    """Develop the first N beats as a motif into a longer melody through transformation.

    Args:
        track_id: ID of the target track
        motif_beats: Length of the motif in beats (default 4)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(DevelopMotifCommand(track_id, motif_beats))
        return _ok(message=f"Motif developed from first {motif_beats} beats")
    except Exception as e:
        return _err("develop_failed", str(e))


@mcp.tool()
def extend_melody(track_id: str, extra_beats: float = 8.0) -> dict:
    """Extend the melody by generating additional beats at the end.

    Args:
        track_id: ID of the target track
        extra_beats: Number of beats to add (default 8)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(ExtendMelodyCommand(track_id, extra_beats))
        return _ok(message=f"Melody extended by {extra_beats} beats")
    except Exception as e:
        return _err("extend_failed", str(e))


@mcp.tool()
def shorten_melody(track_id: str, cut_beats: float = 4.0) -> dict:
    """Shorten the melody by removing beats from the end.

    Args:
        track_id: ID of the target track
        cut_beats: Number of beats to cut from the end (default 4)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(ShortenMelodyCommand(track_id, cut_beats))
        return _ok(message=f"Melody shortened by {cut_beats} beats")
    except Exception as e:
        return _err("shorten_failed", str(e))


@mcp.tool()
def call_response(track_id: str, response_style: str = "echo") -> dict:
    """Generate a response phrase to the existing melody (call and response).

    Args:
        track_id: ID of the target track
        response_style: Response style. Options: mirror (inversion), echo (varied repeat), complement (opposite character)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(CallResponseCommand(track_id, response_style))
        return _ok(message=f"Call & response ({response_style}) created")
    except Exception as e:
        return _err("call_response_failed", str(e))


@mcp.tool()
def generate_hook(track_id: str, hook_beats: float = 4.0) -> dict:
    """Generate a short, memorable hook melody (earworm).

    Args:
        track_id: ID of the target track
        hook_beats: Length of the hook in beats (default 4)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(GenerateHookCommand(track_id, hook_beats))
        return _ok(message=f"Hook generated ({hook_beats} beats)")
    except Exception as e:
        return _err("hook_failed", str(e))


@mcp.tool()
def question_answer(track_id: str, phrase_beats: float = 4.0) -> dict:
    """Generate a question-answer phrase pair (question ends unresolved, answer resolves).

    Args:
        track_id: ID of the target track
        phrase_beats: Length of each phrase in beats (default 4, total = 2x)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(QuestionAnswerCommand(track_id, phrase_beats))
        return _ok(message=f"Q&A phrase pair generated ({phrase_beats} beats each)")
    except Exception as e:
        return _err("qa_failed", str(e))


# ═══════════════════════════ Phase 4: Bass (#58-#62) ═══════════════════════


@mcp.tool()
def generate_bass(
    track_id: str = "", section_id: str = "",
    bass_mode: str = "generate", note_density: str = "normal", octave: int = 2,
) -> dict:
    """Generate a bass line for a track/section.

    Args:
        track_id: ID of the target track (empty = auto-create bass track)
        section_id: Section to generate for (empty = entire song)
        bass_mode: Bass mode. Options: root, octave, walking, syncopation, follow_chords, independent, counter_bass, generate
        note_density: Note density. Options: sparse, normal, dense
        octave: Bass octave range (1=low E1-E2, 2=mid C2-C3, 3=high G2-G3)

    Returns:
        Updated song state
    """
    try:
        _begin()
        tid = track_id or None
        sid = section_id or None
        composer.execute(GenerateBassCommand(tid, sid, bass_mode, note_density, octave))
        return _ok(message=f"Bass generated ({bass_mode})")
    except Exception as e:
        return _err("bass_generate_failed", str(e))


@mcp.tool()
def regenerate_bass(track_id: str, section_id: str = "",
                    bass_mode: str = "generate", note_density: str = "normal",
                    octave: int = 2) -> dict:
    """Regenerate bass line (clear and re-generate with same or new mode).

    Args:
        track_id: ID of the bass track
        section_id: Section to regenerate (empty = entire song)
        bass_mode: Bass mode to use
        note_density: Note density
        octave: Bass octave range

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(RegenerateBassCommand(track_id, sid, bass_mode, note_density, octave))
        return _ok(message="Bass regenerated")
    except Exception as e:
        return _err("bass_regenerate_failed", str(e))


@mcp.tool()
def set_bass_pattern(track_id: str, notes: list[dict]) -> dict:
    """Directly set bass notes (manual pattern input).

    Args:
        track_id: ID of the bass track
        notes: List of note dicts with keys: pitch, start_beat, duration_beat, velocity

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetBassPatternCommand(track_id, notes))
        return _ok(message=f"Bass pattern set ({len(notes)} notes)")
    except Exception as e:
        return _err("bass_pattern_failed", str(e))


@mcp.tool()
def simplify_bass(track_id: str) -> dict:
    """Simplify the bass line (keep root notes on strong beats, remove passing tones).

    Args:
        track_id: ID of the bass track

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SimplifyBassCommand(track_id))
        return _ok(message="Bass simplified")
    except Exception as e:
        return _err("bass_simplify_failed", str(e))


@mcp.tool()
def transpose_bass(track_id: str, semitones: int) -> dict:
    """Transpose bass by semitones (positive = up, negative = down, ±12 = octave).

    Args:
        track_id: ID of the bass track
        semitones: Number of semitones to transpose

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(TransposeBassCommand(track_id, semitones))
        return _ok(message=f"Bass transposed by {semitones} semitones")
    except Exception as e:
        return _err("bass_transpose_failed", str(e))


# ═══════════════════════════ Phase 4: Drums (#63-#75) ═════════════════════


@mcp.tool()
def generate_drums(
    track_id: str = "", section_id: str = "", style: str = "rock",
) -> dict:
    """Generate a full drum pattern for a section.

    Args:
        track_id: ID of the drum track (empty = auto-create drums track)
        section_id: Section to generate for (empty = entire song)
        style: Drum style. Options: rock, pop, jazz, metal, edm, anime, latin, swing

    Returns:
        Updated song state
    """
    try:
        _begin()
        tid = track_id or None
        sid = section_id or None
        composer.execute(GenerateDrumsCommand(tid, sid, style))
        return _ok(message=f"Drums generated ({style})")
    except Exception as e:
        return _err("drums_generate_failed", str(e))


@mcp.tool()
def regenerate_drums(track_id: str, section_id: str = "", style: str = "rock") -> dict:
    """Regenerate drum pattern (clear and re-generate).

    Args:
        track_id: ID of the drum track
        section_id: Section to regenerate (empty = entire song)
        style: Drum style to use

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(RegenerateDrumsCommand(track_id, sid, style))
        return _ok(message="Drums regenerated")
    except Exception as e:
        return _err("drums_regenerate_failed", str(e))


@mcp.tool()
def set_drum_style(track_id: str, style: str, section_id: str = "") -> dict:
    """Switch drum style preset (replaces pattern in section).

    Args:
        track_id: ID of the drum track
        style: New drum style. Options: rock, pop, jazz, metal, edm, anime, latin, swing
        section_id: Section to change (empty = entire song)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(SetDrumStyleCommand(track_id, style, sid))
        return _ok(message=f"Drum style set to {style}")
    except Exception as e:
        return _err("drum_style_failed", str(e))


@mcp.tool()
def add_drum_fill(track_id: str, beat_position: float, fill_type: str = "basic") -> dict:
    """Insert a drum fill at the specified beat position.

    Args:
        track_id: ID of the drum track
        beat_position: Beat where the fill starts
        fill_type: Fill type. Options: basic, double, crescendo, tom_cascade

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(AddDrumFillCommand(track_id, beat_position, fill_type))
        return _ok(message=f"Drum fill added at beat {beat_position}")
    except Exception as e:
        return _err("drum_fill_failed", str(e))


@mcp.tool()
def add_ghost_notes(track_id: str, section_id: str = "", density: float = 0.3) -> dict:
    """Add ghost notes (low velocity snare hits on empty 16th positions).

    Args:
        track_id: ID of the drum track
        section_id: Section to add ghost notes (empty = entire song)
        density: Probability of ghost note per position (0-1, default 0.3)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(AddGhostNotesCommand(track_id, sid, density))
        return _ok(message="Ghost notes added")
    except Exception as e:
        return _err("ghost_notes_failed", str(e))


@mcp.tool()
def set_hihat_pattern(track_id: str, pattern: str, section_id: str = "") -> dict:
    """Set hi-hat pattern (replaces existing hi-hat in section).

    Args:
        track_id: ID of the drum track
        pattern: Hi-hat pattern. Options: eighths, sixteenths, offbeat, open_close
        section_id: Section to change (empty = entire song)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(SetHiHatPatternCommand(track_id, pattern, sid))
        return _ok(message=f"Hi-hat set to {pattern}")
    except Exception as e:
        return _err("hihat_failed", str(e))


@mcp.tool()
def set_kick_pattern(track_id: str, pattern: str, section_id: str = "") -> dict:
    """Set kick drum pattern (replaces existing kicks in section).

    Args:
        track_id: ID of the drum track
        pattern: Kick pattern. Options: straight, offbeat, double, four_on_floor
        section_id: Section to change (empty = entire song)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(SetKickPatternCommand(track_id, pattern, sid))
        return _ok(message=f"Kick set to {pattern}")
    except Exception as e:
        return _err("kick_failed", str(e))


@mcp.tool()
def set_snare_pattern(track_id: str, pattern: str, section_id: str = "") -> dict:
    """Set snare pattern (replaces existing snares in section).

    Args:
        track_id: ID of the drum track
        pattern: Snare pattern. Options: backbeat, ghost, rimshot
        section_id: Section to change (empty = entire song)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(SetSnarePatternCommand(track_id, pattern, sid))
        return _ok(message=f"Snare set to {pattern}")
    except Exception as e:
        return _err("snare_failed", str(e))


@mcp.tool()
def add_crash(track_id: str, beat_position: float) -> dict:
    """Add a crash cymbal at the specified beat.

    Args:
        track_id: ID of the drum track
        beat_position: Beat where the crash hits

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(AddCrashCommand(track_id, beat_position))
        return _ok(message=f"Crash added at beat {beat_position}")
    except Exception as e:
        return _err("crash_failed", str(e))


@mcp.tool()
def set_ride_pattern(track_id: str, section_id: str = "", swing: bool = False) -> dict:
    """Set ride cymbal pattern.

    Args:
        track_id: ID of the drum track
        section_id: Section to change (empty = entire song)
        swing: Whether to use swing rhythm (default False = straight)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(SetRidePatternCommand(track_id, sid, swing))
        return _ok(message=f"Ride pattern set (swing={swing})")
    except Exception as e:
        return _err("ride_failed", str(e))


@mcp.tool()
def add_tom_fill(track_id: str, beat_position: float, fill_beats: float = 1.0) -> dict:
    """Add a tom cascade fill (high tom → mid tom → low tom → floor tom).

    Args:
        track_id: ID of the drum track
        beat_position: Beat where the fill starts
        fill_beats: Duration of the fill in beats (default 1)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(AddTomFillCommand(track_id, beat_position, fill_beats))
        return _ok(message=f"Tom fill added at beat {beat_position}")
    except Exception as e:
        return _err("tom_fill_failed", str(e))


@mcp.tool()
def add_percussion(track_id: str, element: str, section_id: str = "",
                   pattern: str = "quarter") -> dict:
    """Add a percussion element (tambourine, cowbell, claves).

    Args:
        track_id: ID of the drum track
        element: Percussion element. Options: tambourine, cowbell, claves
        section_id: Section to add percussion (empty = entire song)
        pattern: Rhythm pattern. Options: quarter, eighth, sixteenth

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(AddPercussionCommand(track_id, element, sid, pattern))
        return _ok(message=f"{element} added")
    except Exception as e:
        return _err("percussion_failed", str(e))


@mcp.tool()
def clear_drum_element(track_id: str, element: str, section_id: str = "") -> dict:
    """Remove a specific drum element from a section.

    Args:
        track_id: ID of the drum track
        element: Element to clear. Options: kick, snare, hihat, crash, ride, tom, tambourine, cowbell, claves
        section_id: Section to clear from (empty = entire song)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(ClearDrumElementCommand(track_id, element, sid))
        return _ok(message=f"{element} cleared")
    except Exception as e:
        return _err("clear_element_failed", str(e))


# ═══════════════════════ Phase 5: Extended Instruments (#76-#81) ══════════


@mcp.tool()
def generate_strings(
    track_id: str = "", section_id: str = "",
    strings_mode: str = "sustained",
) -> dict:
    """Generate strings part (orchestral strings).

    Args:
        track_id: ID of target track (empty = auto-create strings track)
        section_id: Section to generate for (empty = entire song)
        strings_mode: Strings mode. Options: sustained (pad chords), melody (melodic line), counterpoint (counter melody), tremolo (rapid repetition), pizzicato (plucked)

    Returns:
        Updated song state
    """
    try:
        _begin()
        tid = track_id or None
        sid = section_id or None
        composer.execute(GenerateStringsCommand(tid, sid, strings_mode))
        return _ok(message=f"Strings generated ({strings_mode})")
    except Exception as e:
        return _err("strings_failed", str(e))


@mcp.tool()
def generate_brass(
    track_id: str = "", section_id: str = "",
    brass_mode: str = "stabs",
) -> dict:
    """Generate brass part (trumpets, trombones, horns).

    Args:
        track_id: ID of target track (empty = auto-create brass track)
        section_id: Section to generate for (empty = entire song)
        brass_mode: Brass mode. Options: stabs (short rhythmic hits), sustained (long tones), fanfare (heroic motifs), solo_line (solo melody)

    Returns:
        Updated song state
    """
    try:
        _begin()
        tid = track_id or None
        sid = section_id or None
        composer.execute(GenerateBrassCommand(tid, sid, brass_mode))
        return _ok(message=f"Brass generated ({brass_mode})")
    except Exception as e:
        return _err("brass_failed", str(e))


@mcp.tool()
def generate_woodwinds(
    track_id: str = "", section_id: str = "",
    woodwinds_mode: str = "sustained",
) -> dict:
    """Generate woodwinds part (flute, clarinet, oboe).

    Args:
        track_id: ID of target track (empty = auto-create woodwinds track)
        section_id: Section to generate for (empty = entire song)
        woodwinds_mode: Woodwinds mode. Options: stabs (short hits), sustained (long tones), solo_line (solo melody), trill (ornamental trill)

    Returns:
        Updated song state
    """
    try:
        _begin()
        tid = track_id or None
        sid = section_id or None
        composer.execute(GenerateWoodwindsCommand(tid, sid, woodwinds_mode))
        return _ok(message=f"Woodwinds generated ({woodwinds_mode})")
    except Exception as e:
        return _err("woodwinds_failed", str(e))


@mcp.tool()
def generate_synth(
    track_id: str = "", section_id: str = "",
    synth_mode: str = "pad",
) -> dict:
    """Generate synthesizer part.

    Args:
        track_id: ID of target track (empty = auto-create synth track)
        section_id: Section to generate for (empty = entire song)
        synth_mode: Synth mode. Options: pad (warm chord pad), lead (lead melody), arp (arpeggiated pattern), fx (sound effect / sweep)

    Returns:
        Updated song state
    """
    try:
        _begin()
        tid = track_id or None
        sid = section_id or None
        composer.execute(GenerateSynthCommand(tid, sid, synth_mode))
        return _ok(message=f"Synth generated ({synth_mode})")
    except Exception as e:
        return _err("synth_failed", str(e))


@mcp.tool()
def generate_piano_part(
    track_id: str = "", section_id: str = "",
    piano_mode: str = "block_chords",
) -> dict:
    """Generate advanced piano part (beyond simple notes).

    Args:
        track_id: ID of target track (empty = auto-create piano track)
        section_id: Section to generate for (empty = entire song)
        piano_mode: Piano mode. Options: block_chords (full chord voicings), broken_chords (arpeggiated chords), arpeggio (flowing arpeggios), comping (jazz-style syncopated chords)

    Returns:
        Updated song state
    """
    try:
        _begin()
        tid = track_id or None
        sid = section_id or None
        composer.execute(GeneratePianoPartCommand(tid, sid, piano_mode))
        return _ok(message=f"Piano part generated ({piano_mode})")
    except Exception as e:
        return _err("piano_part_failed", str(e))


@mcp.tool()
def generate_guitar_part(
    track_id: str = "", section_id: str = "",
    guitar_mode: str = "strum",
) -> dict:
    """Generate advanced guitar part.

    Args:
        track_id: ID of target track (empty = auto-create guitar track)
        section_id: Section to generate for (empty = entire song)
        guitar_mode: Guitar mode. Options: strum (rhythmic strumming), fingerpick (Travis picking), arpeggio (chord arpeggios), muted (palm mute percussive)

    Returns:
        Updated song state
    """
    try:
        _begin()
        tid = track_id or None
        sid = section_id or None
        composer.execute(GenerateGuitarPartCommand(tid, sid, guitar_mode))
        return _ok(message=f"Guitar part generated ({guitar_mode})")
    except Exception as e:
        return _err("guitar_part_failed", str(e))


# ═══════════════════════ Phase 5: Arrangement (#82-#92) ══════════════════


@mcp.tool()
def increase_energy(section_id: str, amount: float = 0.5) -> dict:
    """Increase energy of a section (boost velocities, add layers at high amounts).

    Args:
        section_id: ID of the target section
        amount: Amount to increase (0-1, default 0.5)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(IncreaseEnergyCommand(section_id, amount))
        return _ok(message=f"Energy increased by {amount}")
    except Exception as e:
        return _err("increase_energy_failed", str(e))


@mcp.tool()
def decrease_energy(section_id: str, amount: float = 0.5) -> dict:
    """Decrease energy of a section (reduce velocities).

    Args:
        section_id: ID of the target section
        amount: Amount to decrease (0-1, default 0.5)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(DecreaseEnergyCommand(section_id, amount))
        return _ok(message=f"Energy decreased by {amount}")
    except Exception as e:
        return _err("decrease_energy_failed", str(e))


@mcp.tool()
def increase_density(section_id: str, amount: float = 0.5) -> dict:
    """Increase note density of a section (subdivide long notes).

    Args:
        section_id: ID of the target section
        amount: Amount to increase (0-1, default 0.5)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(IncreaseDensityCommand(section_id, amount))
        return _ok(message=f"Density increased by {amount}")
    except Exception as e:
        return _err("increase_density_failed", str(e))


@mcp.tool()
def decrease_density(section_id: str, amount: float = 0.5) -> dict:
    """Decrease note density of a section (remove short notes, merge).

    Args:
        section_id: ID of the target section
        amount: Amount to decrease (0-1, default 0.5)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(DecreaseDensityCommand(section_id, amount))
        return _ok(message=f"Density decreased by {amount}")
    except Exception as e:
        return _err("decrease_density_failed", str(e))


@mcp.tool()
def add_layer(section_id: str, instrument_type: str = "") -> dict:
    """Add an instrument layer to a section (auto-recommends if no instrument specified).

    Args:
        section_id: ID of the target section
        instrument_type: Instrument to add (empty = auto-recommend). Options: piano, bass, strings, pad, lead, synth, drums, fx, brass, woodwinds, guitar, voice

    Returns:
        Updated song state
    """
    try:
        _begin()
        itype = instrument_type or None
        composer.execute(AddLayerCommand(section_id, itype))
        return _ok(message=f"Layer added ({instrument_type or 'auto'})")
    except Exception as e:
        return _err("add_layer_failed", str(e))


@mcp.tool()
def remove_layer(section_id: str, track_id: str) -> dict:
    """Remove an instrument layer from a section (clears notes in section range).

    Args:
        section_id: ID of the target section
        track_id: ID of the track to remove from this section

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(RemoveLayerCommand(section_id, track_id))
        return _ok(message="Layer removed")
    except Exception as e:
        return _err("remove_layer_failed", str(e))


@mcp.tool()
def build_up(target_beat: float, build_beats: float = 4.0) -> dict:
    """Create a build-up leading to a target beat (snare roll crescendo, velocity ramp).

    Args:
        target_beat: Beat where the build-up climaxes (e.g. start of chorus)
        build_beats: Duration of build-up in beats (default 4)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(BuildUpCommand(target_beat, build_beats))
        return _ok(message=f"Build-up created to beat {target_beat}")
    except Exception as e:
        return _err("build_up_failed", str(e))


@mcp.tool()
def break_down(section_id: str) -> dict:
    """Break down a section (strip to core instruments, reduce velocity).

    Args:
        section_id: ID of the target section

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(BreakDownCommand(section_id))
        return _ok(message="Section broken down")
    except Exception as e:
        return _err("break_down_failed", str(e))


@mcp.tool()
def add_transition(from_section_id: str, to_section_id: str) -> dict:
    """Add a transition between two sections (drum fill + crash + velocity adjustments).

    Args:
        from_section_id: ID of the departing section
        to_section_id: ID of the arriving section

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(AddTransitionCommand(from_section_id, to_section_id))
        return _ok(message="Transition added")
    except Exception as e:
        return _err("transition_failed", str(e))


@mcp.tool()
def add_fill(section_id: str, beat_position: float) -> dict:
    """Add a musical fill at the specified beat position.

    Args:
        section_id: ID of the target section
        beat_position: Beat where the fill starts

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(AddFillCommand(section_id, beat_position))
        return _ok(message=f"Fill added at beat {beat_position}")
    except Exception as e:
        return _err("fill_failed", str(e))


@mcp.tool()
def add_silence(section_id: str, track_id: str = "") -> dict:
    """Clear all notes in a section (all tracks or specific track).

    Args:
        section_id: ID of the target section
        track_id: Specific track to silence (empty = all tracks in section)

    Returns:
        Updated song state
    """
    try:
        _begin()
        tid = track_id or None
        composer.execute(AddSilenceCommand(section_id, tid))
        return _ok(message="Silence added")
    except Exception as e:
        return _err("silence_failed", str(e))


# ═══════════════════════ Phase 5: Track Advanced (#93-#95) ═══════════════


@mcp.tool()
def set_track_octave(track_id: str, octave_offset: int) -> dict:
    """Set track octave offset (-3 to +3).

    Args:
        track_id: ID of the target track
        octave_offset: Octave offset (-3 = 3 octaves down, +3 = 3 octaves up)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackOctaveCommand(track_id, octave_offset))
        return _ok(message=f"Octave offset set to {octave_offset}")
    except Exception as e:
        return _err("octave_failed", str(e))


@mcp.tool()
def set_track_density(track_id: str, density: float) -> dict:
    """Set track note density (0-1).

    Args:
        track_id: ID of the target track
        density: Density level (0 = sparse, 0.5 = normal, 1 = dense)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackDensityCommand(track_id, density))
        return _ok(message=f"Density set to {density}")
    except Exception as e:
        return _err("density_failed", str(e))


@mcp.tool()
def set_track_energy(track_id: str, energy: float) -> dict:
    """Set track energy level (0-1).

    Args:
        track_id: ID of the target track
        energy: Energy level (0 = calm, 0.5 = normal, 1 = intense)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackEnergyCommand(track_id, energy))
        return _ok(message=f"Energy set to {energy}")
    except Exception as e:
        return _err("energy_failed", str(e))


# ═══════════════════════ Phase 6: Humanize (#96-#103) ═══════════════════════


@mcp.tool()
def humanize_timing(
    track_id: str, amount: float = 0.5, section_id: str = ""
) -> dict:
    """Apply random timing offsets to notes on a track.

    Args:
        track_id: ID of the target track
        amount: Humanize intensity (0-1), default 0.5
        section_id: Optional section ID to limit scope (empty = entire track)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(HumanizeTimingCommand(track_id, amount, sid))
        return _ok(message=f"Timing humanized on track {track_id}")
    except Exception as e:
        return _err("humanize_timing_failed", str(e))


@mcp.tool()
def humanize_velocity(
    track_id: str, amount: float = 0.5, section_id: str = ""
) -> dict:
    """Apply random velocity offsets to notes on a track.

    Args:
        track_id: ID of the target track
        amount: Humanize intensity (0-1), default 0.5
        section_id: Optional section ID to limit scope (empty = entire track)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(HumanizeVelocityCommand(track_id, amount, sid))
        return _ok(message=f"Velocity humanized on track {track_id}")
    except Exception as e:
        return _err("humanize_velocity_failed", str(e))


@mcp.tool()
def apply_micro_timing(track_id: str, beat_offsets: str) -> dict:
    """Apply fixed timing offsets to notes at specific beat positions within a bar.

    Args:
        track_id: ID of the target track
        beat_offsets: JSON string mapping beat positions to offsets, e.g. '{"1.0": 0.03, "3.0": -0.02}'

    Returns:
        Updated song state
    """
    try:
        _begin()
        import json

        beat_offsets_dict = json.loads(beat_offsets)
        beat_offsets_parsed = {float(k): float(v) for k, v in beat_offsets_dict.items()}
        composer.execute(ApplyMicroTimingCommand(track_id, beat_offsets_parsed))
        return _ok(message="Micro timing applied")
    except Exception as e:
        return _err("micro_timing_failed", str(e))


@mcp.tool()
def apply_groove(
    track_id: str, groove_name: str, section_id: str = ""
) -> dict:
    """Apply a groove template to notes on a track.

    Args:
        track_id: ID of the target track
        groove_name: Groove template name (straight, swing_light, funk, etc.)
        section_id: Optional section ID to limit scope (empty = entire track)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(ApplyGrooveCommand(track_id, groove_name, sid))
        return _ok(message=f"Groove '{groove_name}' applied")
    except Exception as e:
        return _err("apply_groove_failed", str(e))


@mcp.tool()
def apply_swing(
    track_id: str = "", swing_amount: float = 0.5, section_id: str = ""
) -> dict:
    """Apply swing feel by delaying notes on even 8th-note positions.

    Args:
        track_id: ID of the target track (empty = all tracks)
        swing_amount: Swing intensity (0-1), default 0.5
        section_id: Optional section ID to limit scope (empty = entire track/section)

    Returns:
        Updated song state
    """
    try:
        _begin()
        tid = track_id or None
        sid = section_id or None
        composer.execute(ApplySwingCommand(tid, swing_amount, sid))
        target = track_id or "all tracks"
        return _ok(message=f"Swing applied to {target}")
    except Exception as e:
        return _err("apply_swing_failed", str(e))


@mcp.tool()
def push_timing(
    track_id: str, amount: float = 0.5, section_id: str = ""
) -> dict:
    """Push notes earlier in time (ahead of the beat).

    Args:
        track_id: ID of the target track
        amount: Push intensity (0-1), default 0.5
        section_id: Optional section ID to limit scope (empty = entire track)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(PushTimingCommand(track_id, amount, sid))
        return _ok(message=f"Timing pushed on track {track_id}")
    except Exception as e:
        return _err("push_timing_failed", str(e))


@mcp.tool()
def pull_timing(
    track_id: str, amount: float = 0.5, section_id: str = ""
) -> dict:
    """Pull notes later in time (behind the beat).

    Args:
        track_id: ID of the target track
        amount: Pull intensity (0-1), default 0.5
        section_id: Optional section ID to limit scope (empty = entire track)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(PullTimingCommand(track_id, amount, sid))
        return _ok(message=f"Timing pulled on track {track_id}")
    except Exception as e:
        return _err("pull_timing_failed", str(e))


@mcp.tool()
def hand_played_feel(
    track_id: str, intensity: float = 0.5, section_id: str = ""
) -> dict:
    """Apply hand-played feel with combined timing, velocity, and duration randomization.

    Args:
        track_id: ID of the target track
        intensity: Feel intensity (0-1), default 0.5
        section_id: Optional section ID to limit scope (empty = entire track)

    Returns:
        Updated song state
    """
    try:
        _begin()
        sid = section_id or None
        composer.execute(HandPlayedFeelCommand(track_id, intensity, sid))
        return _ok(message=f"Hand-played feel applied on track {track_id}")
    except Exception as e:
        return _err("hand_played_failed", str(e))


# ═══════════════════════ Phase 6: Style (#104-#109) ════════════════════════


@mcp.tool()
def set_style(style_name: str) -> dict:
    """Set a built-in style preset and apply swing/groove settings.

    Args:
        style_name: Style preset name (anime, jazz, rock, edm, lofi, etc.)

    Returns:
        Updated song state with style suggestions in data field
    """
    try:
        _begin()
        cmd = SetStyleCommand(style_name)
        composer.execute(cmd)
        return _ok(data=cmd._result, message=f"Style set to {style_name}")
    except Exception as e:
        return _err("set_style_failed", str(e))


@mcp.tool()
def mix_styles(style_a: str, style_b: str, weight_a: float = 0.5) -> dict:
    """Mix two style presets with weighted blending.

    Args:
        style_a: First style preset name
        style_b: Second style preset name
        weight_a: Weight for style_a (0-1), default 0.5

    Returns:
        Updated song state with mixed style suggestions in data field
    """
    try:
        _begin()
        cmd = MixStylesCommand(style_a, style_b, weight_a)
        composer.execute(cmd)
        return _ok(
            data=cmd._result,
            message=f"Mixed styles {style_a} + {style_b}",
        )
    except Exception as e:
        return _err("mix_styles_failed", str(e))


@mcp.tool()
def get_style_guide() -> dict:
    """Get style guide comparing current song state against the active style preset.

    Returns:
        Style guide with status, missing instruments, and suggested next actions
    """
    try:
        _begin()
        from composer_engine.generators.style_engine import StyleEngine

        engine = StyleEngine()
        guide = engine.get_style_guide(composer.song)
        return _ok(data=guide, message="Style guide generated")
    except Exception as e:
        return _err("style_guide_failed", str(e))


@mcp.tool()
def set_mood(mood: str) -> dict:
    """Set the mood tag for the current song.

    Args:
        mood: Mood tag (e.g. happy, melancholic, energetic)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetMoodCommand(mood))
        return _ok(message=f"Mood set to '{mood}'")
    except Exception as e:
        return _err("set_mood_failed", str(e))


@mcp.tool()
def set_swing(swing_amount: float) -> dict:
    """Set the global swing amount.

    Args:
        swing_amount: Swing value (0-1)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetSwingCommand(swing_amount))
        return _ok(message=f"Swing set to {swing_amount}")
    except Exception as e:
        return _err("set_swing_failed", str(e))


@mcp.tool()
def set_groove(groove_name: str) -> dict:
    """Set the global groove template name.

    Args:
        groove_name: Groove template name (straight, swing_light, funk, etc.)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetGrooveCommand(groove_name))
        return _ok(message=f"Groove set to '{groove_name}'")
    except Exception as e:
        return _err("set_groove_failed", str(e))


# ═══════════════════════ Phase 7: Analysis (#110-#128) ═══════════════════════


@mcp.tool()
def analyze_key() -> dict:
    """Detect the key and mode of the current song using pitch class distribution analysis.

    Returns:
        Analysis result with detected key, mode, confidence, and alternatives.
    """
    try:
        _begin()
        cmd = AnalyzeKeyCommand()
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Key analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_tempo() -> dict:
    """Analyze tempo stability and detect BPM from note onsets.

    Returns:
        Analysis result with BPM, stability, and detected BPM.
    """
    try:
        _begin()
        cmd = AnalyzeTempoCommand()
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Tempo analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_chords(track_id: str) -> dict:
    """Recognize chords from notes in the specified track.

    Args:
        track_id: ID of the track to analyze

    Returns:
        List of detected chords with root, quality, and position.
    """
    try:
        _begin()
        cmd = AnalyzeChordsCommand(track_id)
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Chord analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_phrases(track_id: str) -> dict:
    """Detect musical phrases in a track based on gaps and interval jumps.

    Args:
        track_id: ID of the track to analyze

    Returns:
        List of detected phrases with start/end beats and note counts.
    """
    try:
        _begin()
        cmd = AnalyzePhrasesCommand(track_id)
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Phrase analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_motifs(track_id: str) -> dict:
    """Find repeating interval patterns (motifs) in a track.

    Args:
        track_id: ID of the track to analyze

    Returns:
        List of detected motifs with pitches, rhythm, and occurrences.
    """
    try:
        _begin()
        cmd = AnalyzeMotifsCommand(track_id)
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Motif analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_rhythm(track_id: str) -> dict:
    """Analyze rhythm patterns including syncopation and duration distribution.

    Args:
        track_id: ID of the track to analyze

    Returns:
        Rhythm profile with dominant value, syncopation ratio, and complexity.
    """
    try:
        _begin()
        cmd = AnalyzeRhythmCommand(track_id)
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Rhythm analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_density(track_id: str = "") -> dict:
    """Analyze note density per beat across the song or a specific track.

    Args:
        track_id: Optional track ID (empty for all tracks)

    Returns:
        Density data with per-beat counts, average, and maximum.
    """
    try:
        _begin()
        cmd = AnalyzeDensityCommand(track_id if track_id else None)
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Density analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_energy() -> dict:
    """Analyze energy curve across bars based on density, velocity, and pitch.

    Returns:
        Energy curve with average and peak bar.
    """
    try:
        _begin()
        cmd = AnalyzeEnergyCommand()
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Energy analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_range(track_id: str) -> dict:
    """Analyze pitch range of a track.

    Args:
        track_id: ID of the track to analyze

    Returns:
        Min, max, average pitch, and span.
    """
    try:
        _begin()
        cmd = AnalyzeRangeCommand(track_id)
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Range analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_repetition(track_id: str) -> dict:
    """Detect repeating bar patterns in a track.

    Args:
        track_id: ID of the track to analyze

    Returns:
        Repetition patterns and overall repetition rate.
    """
    try:
        _begin()
        cmd = AnalyzeRepetitionCommand(track_id)
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Repetition analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_voice_leading() -> dict:
    """Check for voice leading issues such as parallel fifths and octaves.

    Returns:
        Voice leading issues with count and severity.
    """
    try:
        _begin()
        cmd = AnalyzeVoiceLeadingCommand()
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Voice leading analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_cadences() -> dict:
    """Detect cadences in the chord progression.

    Returns:
        List of cadences (authentic, plagal, half, deceptive).
    """
    try:
        _begin()
        cmd = AnalyzeCadencesCommand()
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Cadence analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_counterpoint(track_id_a: str, track_id_b: str) -> dict:
    """Analyze counterpoint motion between two tracks.

    Args:
        track_id_a: First track ID
        track_id_b: Second track ID

    Returns:
        Ratios of parallel, contrary, oblique, and similar motion.
    """
    try:
        _begin()
        cmd = AnalyzeCounterpointCommand(track_id_a, track_id_b)
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Counterpoint analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_style() -> dict:
    """Detect musical style by comparing features against style presets.

    Returns:
        Style match with confidence and scores for all presets.
    """
    try:
        _begin()
        cmd = AnalyzeStyleCommand()
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Style analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_mood() -> dict:
    """Analyze mood based on mode, tempo, and pitch range.

    Returns:
        Mood profile with valence, arousal, and tags.
    """
    try:
        _begin()
        cmd = AnalyzeMoodCommand()
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Mood analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_complexity(track_id: str = "") -> dict:
    """Analyze musical complexity across pitch, rhythm, harmony, and structure.

    Args:
        track_id: Optional track ID (empty for all tracks)

    Returns:
        Complexity scores with total and component breakdown.
    """
    try:
        _begin()
        cmd = AnalyzeComplexityCommand(track_id if track_id else None)
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Complexity analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_dynamics(track_id: str = "") -> dict:
    """Analyze velocity dynamics and per-bar contour.

    Args:
        track_id: Optional track ID (empty for all tracks)

    Returns:
        Dynamic profile with velocity range, average, contour, and trend.
    """
    try:
        _begin()
        cmd = AnalyzeDynamicsCommand(track_id if track_id else None)
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Dynamics analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def analyze_structure() -> dict:
    """Analyze song structure and identify form (ABA, AABB, etc.).

    Returns:
        Structure segments with form label.
    """
    try:
        _begin()
        cmd = AnalyzeStructureCommand()
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Structure analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


@mcp.tool()
def get_full_analysis() -> dict:
    """Run comprehensive analysis including key, tempo, energy, and per-track range.

    Returns:
        Combined analysis report with all major metrics.
    """
    try:
        _begin()
        cmd = GetFullAnalysisCommand()
        composer.execute(cmd)
        return _ok(data=cmd._result, message="Full analysis complete")
    except Exception as e:
        return _err("analyze_failed", str(e))


# ═══════════════════════ Phase 8: Automation (#129-#134) ═══════════════════════


@mcp.tool()
def add_automation(track_id: str, param: str, points: str) -> dict:
    """Add an automation curve to a track.

    Args:
        track_id: ID of the target track
        param: Automation parameter (volume, pan, expression, modulation, sustain)
        points: JSON array of {beat, value} objects

    Returns:
        Updated song state
    """
    try:
        _begin()
        import json

        pts = json.loads(points)
        composer.execute(AddAutomationCommand(track_id, param, pts))
        return _ok(message=f"Added {param} automation")
    except Exception as e:
        return _err("automation_failed", str(e))


@mcp.tool()
def remove_automation(track_id: str, param: str) -> dict:
    """Remove an automation curve from a track.

    Args:
        track_id: ID of the target track
        param: Automation parameter to remove

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(RemoveAutomationCommand(track_id, param))
        return _ok(message=f"Removed {param} automation")
    except Exception as e:
        return _err("automation_failed", str(e))


@mcp.tool()
def add_automation_point(track_id: str, param: str, beat: float, value: int) -> dict:
    """Add a control point to an automation curve.

    Args:
        track_id: ID of the target track
        param: Automation parameter
        beat: Position in beats
        value: Parameter value (0-127)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(AddAutomationPointCommand(track_id, param, beat, value))
        return _ok(message=f"Added point at beat {beat}")
    except Exception as e:
        return _err("automation_failed", str(e))


@mcp.tool()
def remove_automation_point(track_id: str, param: str, point_index: int) -> dict:
    """Remove a control point from an automation curve.

    Args:
        track_id: ID of the target track
        param: Automation parameter
        point_index: Index of the point to remove

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(RemoveAutomationPointCommand(track_id, param, point_index))
        return _ok(message=f"Removed point {point_index}")
    except Exception as e:
        return _err("automation_failed", str(e))


@mcp.tool()
def apply_automation_preset(
    track_id: str, preset_name: str, start_beat: float, end_beat: float
) -> dict:
    """Apply a preset automation curve to a track.

    Available presets: fade_in, fade_out, crescendo, decrescendo, pan_sweep_lr, pan_sweep_rl, swell

    Args:
        track_id: ID of the target track
        preset_name: Name of the preset
        start_beat: Start position
        end_beat: End position

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(
            ApplyAutomationPresetCommand(track_id, preset_name, start_beat, end_beat)
        )
        return _ok(message=f"Applied preset '{preset_name}'")
    except Exception as e:
        return _err("automation_failed", str(e))


@mcp.tool()
def clear_automation(track_id: str) -> dict:
    """Clear all automation curves from a track.

    Args:
        track_id: ID of the target track

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(ClearAutomationCommand(track_id))
        return _ok(message="Automation cleared")
    except Exception as e:
        return _err("automation_failed", str(e))


# ═══════════════════════ Phase 8: Markers (#135-#137) ═══════════════════════


@mcp.tool()
def add_marker(beat: float, label: str, color: str = "") -> dict:
    """Add a timeline marker.

    Args:
        beat: Position in beats
        label: Marker label text
        color: Optional color tag

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(AddMarkerCommand(beat, label, color))
        return _ok(message=f"Added marker '{label}' at beat {beat}")
    except Exception as e:
        return _err("marker_failed", str(e))


@mcp.tool()
def remove_marker(marker_id: str) -> dict:
    """Remove a timeline marker.

    Args:
        marker_id: ID of the marker to remove

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(RemoveMarkerCommand(marker_id))
        return _ok(message="Marker removed")
    except Exception as e:
        return _err("marker_failed", str(e))


@mcp.tool()
def list_markers() -> dict:
    """List all timeline markers.

    Returns:
        List of markers with id, beat, label, color.
    """
    try:
        _begin()
        if not composer.song:
            return _err("no_song", "No song loaded")
        markers = [m.model_dump() for m in composer.song.markers]
        return _ok(data={"markers": markers}, message=f"{len(markers)} markers")
    except Exception as e:
        return _err("marker_failed", str(e))


# ── Phase 9: Plugins (#138-#141) ─────────────────────────────────────────


@mcp.tool()
def list_plugins() -> dict:
    """List all registered plugins.

    Returns:
        List of plugins with name, version, type, description, enabled status.
    """
    try:
        _begin()
        from composer_engine.plugins.plugin_manager import PluginManager
        pm = PluginManager()
        pm.discover()
        return _ok(data={"plugins": pm.list_plugins()}, message=f"{len(pm.list_plugins())} plugins")
    except Exception as e:
        return _err("plugin_failed", str(e))


@mcp.tool()
def enable_plugin(name: str) -> dict:
    """Enable a registered plugin.

    Args:
        name: Name of the plugin to enable

    Returns:
        Success status
    """
    try:
        _begin()
        from composer_engine.plugins.plugin_manager import PluginManager
        pm = PluginManager()
        pm.discover()
        pm.enable(name)
        return _ok(message=f"Plugin '{name}' enabled")
    except Exception as e:
        return _err("plugin_failed", str(e))


@mcp.tool()
def disable_plugin(name: str) -> dict:
    """Disable a registered plugin.

    Args:
        name: Name of the plugin to disable

    Returns:
        Success status
    """
    try:
        _begin()
        from composer_engine.plugins.plugin_manager import PluginManager
        pm = PluginManager()
        pm.discover()
        pm.disable(name)
        return _ok(message=f"Plugin '{name}' disabled")
    except Exception as e:
        return _err("plugin_failed", str(e))


@mcp.tool()
def reload_plugins() -> dict:
    """Reload all plugins by re-scanning the plugins directory.

    Returns:
        List of discovered plugins.
    """
    try:
        _begin()
        from composer_engine.plugins.plugin_manager import PluginManager
        pm = PluginManager()
        plugins = pm.reload()
        return _ok(data={"plugins": [p.model_dump() for p in plugins]}, message=f"{len(plugins)} plugins loaded")
    except Exception as e:
        return _err("plugin_failed", str(e))


# ── Phase 10: MusicXML Export (#142-#143) ────────────────────────────────


@mcp.tool()
def export_musicxml(filename: str = "") -> dict:
    """Export current song as MusicXML file.

    Args:
        filename: Output file path. If empty, auto-generates based on song name.

    Returns:
        Path to the exported MusicXML file.
    """
    try:
        _begin()
        if not composer.song:
            return _err("no_song", "No song to export")
        from composer_engine.renderer.musicxml_renderer import MusicXMLRenderer
        renderer = MusicXMLRenderer()
        if not filename:
            filename = f"{composer.song.name.replace(' ', '_')}.musicxml"
        path = renderer.render_to_file(composer.song, filename)
        return _ok(data={"path": path}, message=f"MusicXML exported to {path}")
    except Exception as e:
        return _err("export_failed", str(e))


@mcp.tool()
def preview_musicxml() -> dict:
    """Preview MusicXML content of the current song.

    Returns:
        XML string preview (first 2000 characters) and total length.
    """
    try:
        _begin()
        if not composer.song:
            return _err("no_song", "No song to preview")
        from composer_engine.renderer.musicxml_renderer import MusicXMLRenderer
        renderer = MusicXMLRenderer()
        xml_str = renderer.render(composer.song)
        return _ok(
            data={"xml": xml_str[:2000], "total_length": len(xml_str)},
            message="MusicXML preview generated"
        )
    except Exception as e:
        return _err("preview_failed", str(e))


# ── Phase 11: Observability (#144-#146) ──────────────────────────────────


@mcp.tool()
def get_server_stats() -> dict:
    """Get server runtime statistics.

    Returns uptime, tool call counts, error rate, command execution count, and last tool info.

    Returns:
        Server statistics including uptime, tool_calls, tool_errors, error_rate, etc.
    """
    _begin()
    return _ok(data=stats.to_dict(), message="Server stats")


@mcp.tool()
def get_song_summary() -> dict:
    """Get a summary of the current song.

    Returns track count, total notes, sections, chords, markers, and per-track details.

    Returns:
        Song summary with counts and track details.
    """
    _begin()
    if not composer.song:
        return _err("no_song", "No song loaded")
    song = composer.song
    summary = {
        "name": song.name,
        "stage": song.stage.value,
        "tracks": len(song.tracks),
        "total_notes": sum(len(t.notes) for t in song.tracks),
        "sections": len(song.sections),
        "chords": len(song.chord_progression),
        "markers": len(song.markers),
        "tempo": song.global_settings.tempo,
        "key": f"{song.global_settings.key.value} {song.global_settings.mode.value}",
        "style": song.global_settings.style,
        "tracks_detail": [
            {
                "name": t.name,
                "instrument": t.instrument.value,
                "notes": len(t.notes),
                "muted": t.mute,
                "automation_curves": len(t.automation),
            }
            for t in song.tracks
        ],
    }
    return _ok(data=summary, message=f"Song '{song.name}': {summary['tracks']} tracks, {summary['total_notes']} notes")


@mcp.tool()
def set_log_level(level: str) -> dict:
    """Dynamically change the server log level.

    Args:
        level: Log level (DEBUG, INFO, WARN, WARNING, ERROR)

    Returns:
        Confirmation of level change.
    """
    import logging as _logging
    _begin()
    level_upper = level.upper()
    if level_upper == "WARN":
        level_upper = "WARNING"
    log_level = getattr(_logging, level_upper, None)
    if log_level is None:
        return _err("invalid_level", f"Unknown level: {level}. Use DEBUG/INFO/WARN/ERROR")
    _logging.getLogger("composer_engine").setLevel(log_level)
    log(f"Log level changed to {level_upper}", tag="SYSTEM")
    return _ok(message=f"Log level set to {level_upper}")


# ── Phase 12: Property Completion (#153-#166) ─────────────────────────────


@mcp.tool()
def set_scale(scale: str = "") -> dict:
    """Set the song scale, overriding the default Key+Mode derivation.

    Pass an empty string to reset to automatic (Key+Mode based) scale.

    Args:
        scale: Scale name (e.g. "C major pentatonic", "A blues"). Empty = auto.

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetScaleCommand(scale or None))
        return _ok(message=f"Scale set to {scale or 'auto'}")
    except Exception as e:
        return _err("set_scale_failed", str(e))


@mcp.tool()
def set_master_timing(timing: float) -> dict:
    """Set the global master timing offset.

    Positive values delay all notes, negative values push them earlier.

    Args:
        timing: Timing offset in beats (e.g. 0.05 for slight delay)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetMasterTimingCommand(timing))
        return _ok(message=f"Master timing set to {timing}")
    except Exception as e:
        return _err("set_master_timing_failed", str(e))


@mcp.tool()
def set_global_energy(energy: float) -> dict:
    """Set the global energy level.

    Affects the overall intensity of the composition.

    Args:
        energy: Energy level (0.0 = softest, 1.0 = loudest/most intense)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetGlobalEnergyCommand(energy))
        return _ok(message=f"Global energy set to {energy}")
    except Exception as e:
        return _err("set_global_energy_failed", str(e))


@mcp.tool()
def swap_sections(section_id_a: str, section_id_b: str) -> dict:
    """Swap the positions of two sections.

    Exchanges the start_beat values of the two specified sections.

    Args:
        section_id_a: ID of the first section
        section_id_b: ID of the second section

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SwapSectionsCommand(section_id_a, section_id_b))
        return _ok(message="Sections swapped")
    except Exception as e:
        return _err("swap_sections_failed", str(e))


@mcp.tool()
def split_section(section_id: str, split_beat: float) -> dict:
    """Split a section into two at the specified beat position.

    The original section is shortened, and a new section starts at split_beat.

    Args:
        section_id: ID of the section to split
        split_beat: Absolute beat position to split at (must be within the section)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SplitSectionCommand(section_id, split_beat))
        return _ok(message=f"Section split at beat {split_beat}")
    except Exception as e:
        return _err("split_section_failed", str(e))


@mcp.tool()
def merge_sections(section_id_a: str, section_id_b: str) -> dict:
    """Merge two sections into one.

    The merged section keeps the first section's type and spans from the earliest
    start to the latest end of both sections.

    Args:
        section_id_a: ID of the first section (its type is kept)
        section_id_b: ID of the second section (will be removed)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(MergeSectionsCommand(section_id_a, section_id_b))
        return _ok(message="Sections merged")
    except Exception as e:
        return _err("merge_sections_failed", str(e))


@mcp.tool()
def set_track_register(track_id: str, register: str) -> dict:
    """Set the register (pitch range category) for a track.

    Args:
        track_id: ID of the track
        register: Register category. Options: high, mid, low

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackRegisterCommand(track_id, register))
        return _ok(message=f"Track register set to {register}")
    except Exception as e:
        return _err("set_track_register_failed", str(e))


@mcp.tool()
def set_track_complexity(track_id: str, complexity: float) -> dict:
    """Set the complexity level for a track.

    Controls how intricate the musical patterns should be.

    Args:
        track_id: ID of the track
        complexity: Complexity level (0.0 = simplest, 1.0 = most complex)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackComplexityCommand(track_id, complexity))
        return _ok(message=f"Track complexity set to {complexity}")
    except Exception as e:
        return _err("set_track_complexity_failed", str(e))


@mcp.tool()
def set_track_velocity_offset(track_id: str, offset: int) -> dict:
    """Set the velocity offset for a track.

    This value is added to every note's velocity during MIDI rendering.

    Args:
        track_id: ID of the track
        offset: Velocity offset (-127 to +127, 0 = no change)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackVelocityOffsetCommand(track_id, offset))
        return _ok(message=f"Track velocity offset set to {offset}")
    except Exception as e:
        return _err("set_track_velocity_offset_failed", str(e))


@mcp.tool()
def set_track_timing_offset(track_id: str, offset: float) -> dict:
    """Set the timing offset for a track.

    This value is added to every note's start_beat during MIDI rendering.

    Args:
        track_id: ID of the track
        offset: Timing offset in beats (e.g. 0.1 = slight delay, -0.05 = push)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackTimingOffsetCommand(track_id, offset))
        return _ok(message=f"Track timing offset set to {offset}")
    except Exception as e:
        return _err("set_track_timing_offset_failed", str(e))


@mcp.tool()
def set_track_humanize(track_id: str, humanize: float) -> dict:
    """Set the per-track humanize amount.

    This is a track-level property independent of the humanize_* operation tools.

    Args:
        track_id: ID of the track
        humanize: Humanize amount (0.0 = mechanical, 1.0 = maximum humanization)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackHumanizeCommand(track_id, humanize))
        return _ok(message=f"Track humanize set to {humanize}")
    except Exception as e:
        return _err("set_track_humanize_failed", str(e))


@mcp.tool()
def set_track_groove(track_id: str, groove: str) -> dict:
    """Set the groove template for a track.

    This is a track-level property. Pass empty string to clear.

    Args:
        track_id: ID of the track
        groove: Groove template name (e.g. "funk", "shuffle"). Empty = none.

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackGrooveCommand(track_id, groove))
        return _ok(message=f"Track groove set to '{groove}'")
    except Exception as e:
        return _err("set_track_groove_failed", str(e))


@mcp.tool()
def set_track_rhythm(track_id: str, rhythm_pattern: str) -> dict:
    """Set the rhythm pattern for a track.

    Args:
        track_id: ID of the track
        rhythm_pattern: Rhythm pattern name. Empty = default.

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackRhythmCommand(track_id, rhythm_pattern))
        return _ok(message=f"Track rhythm set to '{rhythm_pattern}'")
    except Exception as e:
        return _err("set_track_rhythm_failed", str(e))


@mcp.tool()
def set_track_range(track_id: str, low: int, high: int) -> dict:
    """Set the pitch range (playable register) for a track.

    Constrains note generation to the specified MIDI pitch range.

    Args:
        track_id: ID of the track
        low: Lowest MIDI pitch (0-127, 0 = no lower limit)
        high: Highest MIDI pitch (0-127, 127 = no upper limit)

    Returns:
        Updated song state
    """
    try:
        _begin()
        composer.execute(SetTrackRangeCommand(track_id, low, high))
        return _ok(message=f"Track range set to {low}-{high}")
    except Exception as e:
        return _err("set_track_range_failed", str(e))


# ── Phase 13: MIDI Import (#167-#169) ─────────────────────────────────────

from composer_engine.importer.midi_importer import MidiImporter

_midi_importer = MidiImporter()


@mcp.tool()
def import_midi(file_path: str, song_name: str = "") -> dict:
    """Import a MIDI file as a new Song, replacing the current one.

    Parses all tracks, notes, tempo, key, and time signature from the MIDI file
    into the Song model. After import, all existing tools (editing, analysis,
    generation, export) can be used on the imported data.

    Args:
        file_path: Path to the .mid / .midi file
        song_name: Optional song name (defaults to filename without extension)

    Returns:
        Imported song state with track and note counts
    """
    try:
        _begin()
        song = _midi_importer.import_file(file_path, song_name or None)
        composer.song = song
        composer.history.clear()
        total_notes = sum(len(t.notes) for t in song.tracks)
        return _ok(
            message=f"Imported '{song.name}': {len(song.tracks)} tracks, {total_notes} notes"
        )
    except FileNotFoundError as e:
        return _err("file_not_found", str(e))
    except Exception as e:
        return _err("import_midi_failed", str(e))


@mcp.tool()
def import_midi_track(file_path: str, midi_track_index: int) -> dict:
    """Import a single track from a MIDI file into the current Song.

    Adds the specified MIDI track as a new Track in the current Song,
    preserving all existing tracks and data.

    Args:
        file_path: Path to the .mid / .midi file
        midi_track_index: Zero-based index of the track in the MIDI file
            (use get_midi_info to see available tracks)

    Returns:
        Updated song state
    """
    try:
        _begin()
        if composer.song is None:
            return _err("no_song", "No active song. Create or import a song first.")
        track = _midi_importer.import_single_track(file_path, midi_track_index)
        song = composer.song.model_copy(deep=True)
        song.tracks.append(track)
        from datetime import datetime, timezone
        song.updated_at = datetime.now(timezone.utc)
        composer.song = song
        return _ok(
            message=f"Imported track '{track.name}' ({len(track.notes)} notes) into current song"
        )
    except FileNotFoundError as e:
        return _err("file_not_found", str(e))
    except IndexError as e:
        return _err("track_index_out_of_range", str(e))
    except Exception as e:
        return _err("import_midi_track_failed", str(e))


@mcp.tool()
def get_midi_info(file_path: str) -> dict:
    """Preview MIDI file information without importing.

    Returns metadata about the MIDI file: tempo, key, time signature,
    duration, and details for each track (name, instrument, note count,
    pitch range).

    Args:
        file_path: Path to the .mid / .midi file

    Returns:
        MIDI file metadata
    """
    try:
        info = _midi_importer.get_info(file_path)
        return {"success": True, "data": info}
    except FileNotFoundError as e:
        return _err("file_not_found", str(e))
    except Exception as e:
        return _err("get_midi_info_failed", str(e))


# ──────────────────────────── Entry point ─────────────────────────────────

TOOL_COUNT = 169

if __name__ == "__main__":
    print_banner(tool_count=TOOL_COUNT)
    log(f"Registered {TOOL_COUNT} MCP tools", tag="SERVER")
    log("Pipeline stages: 5 (Inspiration → Composition → Arrangement → Production → Export)", tag="SERVER")
    log("✓ Ready — waiting for MCP connection", tag="SERVER")
    mcp.run()
