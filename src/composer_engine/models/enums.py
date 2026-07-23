"""All enum definitions for Composer Engine.

Aligned with TECHNICAL.md 5.1 枚举定义.
All enums inherit (str, Enum) for JSON serialization and MCP parameter passing.
"""

from enum import Enum


class Key(str, Enum):
    """Musical key signature."""

    C = "C"
    Db = "Db"
    D = "D"
    Eb = "Eb"
    E = "E"
    F = "F"
    Gb = "Gb"
    G = "G"
    Ab = "Ab"
    A = "A"
    Bb = "Bb"
    B = "B"


class Mode(str, Enum):
    """Musical mode."""

    MAJOR = "major"
    MINOR = "minor"
    DORIAN = "dorian"
    MIXOLYDIAN = "mixolydian"
    LYDIAN = "lydian"
    PHRYGIAN = "phrygian"
    LOCRIAN = "locrian"


class SectionType(str, Enum):
    """Song section type."""

    INTRO = "intro"
    VERSE = "verse"
    PRE_CHORUS = "pre_chorus"
    CHORUS = "chorus"
    BRIDGE = "bridge"
    SOLO = "solo"
    BREAKDOWN = "breakdown"
    OUTRO = "outro"


class InstrumentType(str, Enum):
    """Musical instrument type."""

    PIANO = "piano"
    BASS = "bass"
    STRINGS = "strings"
    PAD = "pad"
    LEAD = "lead"
    SYNTH = "synth"
    DRUMS = "drums"
    FX = "fx"
    BRASS = "brass"
    WOODWINDS = "woodwinds"
    GUITAR = "guitar"
    VOICE = "voice"


class Stage(str, Enum):
    """Pipeline stage for song creation lifecycle."""

    EMPTY = "empty"
    INSPIRATION = "inspiration"
    COMPOSITION = "composition"
    ARRANGEMENT = "arrangement"
    PRODUCTION = "production"
    EXPORT = "export"


# GM Program Number defaults per InstrumentType (TECHNICAL.md 5.1)
DEFAULT_GM_PROGRAMS: dict[InstrumentType, int] = {
    InstrumentType.PIANO: 0,       # Acoustic Grand Piano
    InstrumentType.GUITAR: 25,     # Acoustic Guitar (steel)
    InstrumentType.BASS: 33,       # Electric Bass (finger)
    InstrumentType.DRUMS: 0,       # Channel 9, program ignored
    InstrumentType.STRINGS: 48,    # String Ensemble 1
    InstrumentType.BRASS: 61,      # Brass Section
    InstrumentType.WOODWINDS: 73,  # Flute
    InstrumentType.PAD: 89,        # Pad 2 (warm)
    InstrumentType.LEAD: 80,       # Lead 1 (square)
    InstrumentType.SYNTH: 81,      # Lead 2 (sawtooth)
    InstrumentType.FX: 98,         # FX 3 (crystal)
    InstrumentType.VOICE: 52,      # Choir Aahs
}

# Drums default channel (TECHNICAL.md 6.4)
DRUMS_CHANNEL = 9


class BassMode(str, Enum):
    """Bass generation mode."""

    ROOT = "root"
    OCTAVE = "octave"
    WALKING = "walking"
    SYNCOPATION = "syncopation"
    FOLLOW_CHORDS = "follow_chords"
    INDEPENDENT = "independent"
    COUNTER_BASS = "counter_bass"
    GENERATE = "generate"


class DrumStyle(str, Enum):
    """Drum style preset."""

    ROCK = "rock"
    POP = "pop"
    JAZZ = "jazz"
    METAL = "metal"
    EDM = "edm"
    ANIME = "anime"
    LATIN = "latin"
    SWING = "swing"


class HiHatPattern(str, Enum):
    """Hi-hat pattern type."""

    EIGHTHS = "eighths"
    SIXTEENTHS = "sixteenths"
    OFFBEAT = "offbeat"
    OPEN_CLOSE = "open_close"


class KickPattern(str, Enum):
    """Kick drum pattern type."""

    STRAIGHT = "straight"
    OFFBEAT = "offbeat"
    DOUBLE = "double"
    FOUR_ON_FLOOR = "four_on_floor"


class SnarePattern(str, Enum):
    """Snare drum pattern type."""

    BACKBEAT = "backbeat"
    GHOST = "ghost"
    RIMSHOT = "rimshot"


# GM Percussion Map (REQUIREMENTS.md 4.4, TECHNICAL.md 5.11)
GM_PERCUSSION = {
    "KICK": 36,
    "SNARE": 38,
    "SIDE_STICK": 37,
    "CLAP": 39,
    "CLOSED_HH": 42,
    "OPEN_HH": 46,
    "PEDAL_HH": 44,
    "CRASH_1": 49,
    "CRASH_2": 57,
    "RIDE": 51,
    "RIDE_BELL": 53,
    "LOW_TOM": 45,
    "MID_TOM": 47,
    "HIGH_TOM": 50,
    "FLOOR_TOM": 41,
    "TAMBOURINE": 54,
    "COWBELL": 56,
    "CLAVES": 75,
}


class StringsMode(str, Enum):
    """Strings generation mode."""

    SUSTAINED = "sustained"
    MELODY = "melody"
    COUNTERPOINT = "counterpoint"
    TREMOLO = "tremolo"
    PIZZICATO = "pizzicato"


class BrassMode(str, Enum):
    """Brass generation mode."""

    STABS = "stabs"
    SUSTAINED = "sustained"
    FANFARE = "fanfare"
    SOLO_LINE = "solo_line"


class WoodwindsMode(str, Enum):
    """Woodwinds generation mode."""

    STABS = "stabs"
    SUSTAINED = "sustained"
    SOLO_LINE = "solo_line"
    TRILL = "trill"


class SynthMode(str, Enum):
    """Synth generation mode."""

    PAD = "pad"
    LEAD = "lead"
    ARP = "arp"
    FX = "fx"


class PianoMode(str, Enum):
    """Piano part generation mode."""

    BLOCK_CHORDS = "block_chords"
    BROKEN_CHORDS = "broken_chords"
    ARPEGGIO = "arpeggio"
    COMPING = "comping"


class GuitarMode(str, Enum):
    """Guitar part generation mode."""

    STRUM = "strum"
    FINGERPICK = "fingerpick"
    ARPEGGIO = "arpeggio"
    MUTED = "muted"


class HumanizeType(str, Enum):
    """Humanize operation type."""

    TIMING_RANDOM = "timing_random"
    VELOCITY_RANDOM = "velocity_random"
    MICRO_TIMING = "micro_timing"
    GROOVE = "groove"
    SWING = "swing"
    PUSH = "push"
    PULL = "pull"
    HAND_PLAYED = "hand_played"


class GrooveName(str, Enum):
    """Groove template name."""

    STRAIGHT = "straight"
    SWING_LIGHT = "swing_light"
    SWING_HEAVY = "swing_heavy"
    FUNK = "funk"
    BOSSA = "bossa"
    SHUFFLE = "shuffle"
    HUMAN_PIANO = "human_piano"
    HUMAN_GUITAR = "human_guitar"
    HUMAN_DRUMS = "human_drums"
    LAID_BACK = "laid_back"


class StylePreset(str, Enum):
    """Built-in style preset."""

    ANIME = "anime"
    CITY_POP = "city_pop"
    JAZZ = "jazz"
    ROCK = "rock"
    METAL = "metal"
    EDM = "edm"
    LOFI = "lofi"
    CLASSICAL = "classical"
    ORCHESTRA = "orchestra"
    GAME_MUSIC = "game_music"
    AMBIENT = "ambient"
    SYNTHWAVE = "synthwave"
    FUTURE_BASS = "future_bass"


class AutomationParam(str, Enum):
    """Automation parameter type (MIDI CC)."""

    VOLUME = "volume"
    PAN = "pan"
    EXPRESSION = "expression"
    MODULATION = "modulation"
    SUSTAIN = "sustain"


AUTOMATION_CC = {
    "volume": 7,
    "pan": 10,
    "expression": 11,
    "modulation": 1,
    "sustain": 64,
}
