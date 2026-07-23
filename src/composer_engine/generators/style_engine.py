"""Style preset engine for genre-based composition guidance.

Aligned with TECHNICAL.md 5.13 - Phase 6 StyleEngine.
"""

from composer_engine.models.enums import BassMode, DrumStyle, InstrumentType
from composer_engine.models.song import Song

STYLE_PRESETS: dict[str, dict] = {
    "anime": {
        "recommended_instruments": [
            InstrumentType.PIANO,
            InstrumentType.STRINGS,
            InstrumentType.DRUMS,
            InstrumentType.BASS,
            InstrumentType.SYNTH,
        ],
        "chord_templates": ["royal_road", "komuro", "just_the_two"],
        "tempo_range": (130, 170),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.ANIME.value,
        "bass_mode": BassMode.ROOT.value,
        "humanize_preset": "straight",
        "energy_curve": {
            "intro": 0.3,
            "verse": 0.5,
            "chorus": 0.8,
            "bridge": 0.4,
            "outro": 0.3,
        },
        "velocity_range": (70, 110),
        "swing": 0.0,
    },
    "city_pop": {
        "recommended_instruments": [
            InstrumentType.GUITAR,
            InstrumentType.BASS,
            InstrumentType.SYNTH,
            InstrumentType.DRUMS,
            InstrumentType.PIANO,
        ],
        "chord_templates": ["jazz_turnaround", "7th"],
        "tempo_range": (100, 130),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.POP.value,
        "bass_mode": BassMode.WALKING.value,
        "humanize_preset": "funk",
        "energy_curve": {
            "intro": 0.4,
            "verse": 0.5,
            "chorus": 0.6,
            "bridge": 0.5,
            "outro": 0.4,
        },
        "velocity_range": (60, 100),
        "swing": 0.2,
    },
    "jazz": {
        "recommended_instruments": [
            InstrumentType.PIANO,
            InstrumentType.BASS,
            InstrumentType.DRUMS,
        ],
        "chord_templates": ["ii-V-I", "turnaround"],
        "tempo_range": (90, 160),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.JAZZ.value,
        "bass_mode": BassMode.WALKING.value,
        "humanize_preset": "swing_heavy",
        "energy_curve": {
            "intro": 0.3,
            "verse": 0.5,
            "chorus": 0.6,
            "bridge": 0.5,
            "outro": 0.3,
        },
        "velocity_range": (50, 90),
        "swing": 0.6,
    },
    "rock": {
        "recommended_instruments": [
            InstrumentType.GUITAR,
            InstrumentType.BASS,
            InstrumentType.DRUMS,
        ],
        "chord_templates": ["I-IV-V", "power"],
        "tempo_range": (110, 150),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.ROCK.value,
        "bass_mode": BassMode.ROOT.value,
        "humanize_preset": "straight",
        "energy_curve": {
            "intro": 0.5,
            "verse": 0.6,
            "chorus": 0.9,
            "bridge": 0.5,
            "outro": 0.4,
        },
        "velocity_range": (80, 120),
        "swing": 0.0,
    },
    "metal": {
        "recommended_instruments": [
            InstrumentType.GUITAR,
            InstrumentType.BASS,
            InstrumentType.DRUMS,
        ],
        "chord_templates": ["power", "dim"],
        "tempo_range": (140, 200),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.METAL.value,
        "bass_mode": BassMode.ROOT.value,
        "humanize_preset": "straight",
        "energy_curve": {
            "intro": 0.6,
            "verse": 0.8,
            "chorus": 1.0,
            "bridge": 0.7,
            "outro": 0.5,
        },
        "velocity_range": (90, 127),
        "swing": 0.0,
    },
    "edm": {
        "recommended_instruments": [
            InstrumentType.SYNTH,
            InstrumentType.DRUMS,
            InstrumentType.BASS,
        ],
        "chord_templates": ["simple", "loop"],
        "tempo_range": (120, 140),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.EDM.value,
        "bass_mode": BassMode.ROOT.value,
        "humanize_preset": "straight",
        "energy_curve": {
            "intro": 0.3,
            "verse": 0.5,
            "chorus": 0.9,
            "bridge": 0.4,
            "outro": 0.2,
        },
        "velocity_range": (70, 110),
        "swing": 0.0,
    },
    "lofi": {
        "recommended_instruments": [
            InstrumentType.PIANO,
            InstrumentType.GUITAR,
            InstrumentType.DRUMS,
        ],
        "chord_templates": ["7th", "9th"],
        "tempo_range": (70, 95),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.SWING.value,
        "bass_mode": BassMode.ROOT.value,
        "humanize_preset": "laid_back",
        "energy_curve": {
            "intro": 0.2,
            "verse": 0.3,
            "chorus": 0.4,
            "bridge": 0.3,
            "outro": 0.2,
        },
        "velocity_range": (40, 75),
        "swing": 0.4,
    },
    "classical": {
        "recommended_instruments": [
            InstrumentType.PIANO,
            InstrumentType.STRINGS,
            InstrumentType.BRASS,
            InstrumentType.WOODWINDS,
        ],
        "chord_templates": ["diatonic"],
        "tempo_range": (60, 120),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.POP.value,
        "bass_mode": BassMode.FOLLOW_CHORDS.value,
        "humanize_preset": "human_piano",
        "energy_curve": {
            "intro": 0.2,
            "verse": 0.4,
            "chorus": 0.6,
            "bridge": 0.5,
            "outro": 0.2,
        },
        "velocity_range": (40, 100),
        "swing": 0.0,
    },
    "orchestra": {
        "recommended_instruments": [
            InstrumentType.STRINGS,
            InstrumentType.BRASS,
            InstrumentType.WOODWINDS,
        ],
        "chord_templates": ["diatonic", "rich_harmony"],
        "tempo_range": (60, 140),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.POP.value,
        "bass_mode": BassMode.FOLLOW_CHORDS.value,
        "humanize_preset": "human_piano",
        "energy_curve": {
            "intro": 0.2,
            "verse": 0.5,
            "chorus": 0.9,
            "bridge": 0.4,
            "outro": 0.3,
        },
        "velocity_range": (50, 110),
        "swing": 0.0,
    },
    "game_music": {
        "recommended_instruments": [
            InstrumentType.SYNTH,
            InstrumentType.STRINGS,
            InstrumentType.DRUMS,
        ],
        "chord_templates": ["epic", "royal_road"],
        "tempo_range": (120, 160),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.ROCK.value,
        "bass_mode": BassMode.ROOT.value,
        "humanize_preset": "straight",
        "energy_curve": {
            "intro": 0.4,
            "verse": 0.6,
            "chorus": 0.9,
            "bridge": 0.5,
            "outro": 0.4,
        },
        "velocity_range": (70, 115),
        "swing": 0.0,
    },
    "ambient": {
        "recommended_instruments": [
            InstrumentType.PAD,
            InstrumentType.SYNTH,
            InstrumentType.FX,
        ],
        "chord_templates": ["suspended", "open"],
        "tempo_range": (60, 90),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.POP.value,
        "bass_mode": BassMode.INDEPENDENT.value,
        "humanize_preset": "straight",
        "energy_curve": {
            "intro": 0.1,
            "verse": 0.2,
            "chorus": 0.3,
            "bridge": 0.2,
            "outro": 0.1,
        },
        "velocity_range": (30, 70),
        "swing": 0.0,
    },
    "synthwave": {
        "recommended_instruments": [
            InstrumentType.SYNTH,
            InstrumentType.BASS,
            InstrumentType.DRUMS,
        ],
        "chord_templates": ["minor", "retro"],
        "tempo_range": (100, 130),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.EDM.value,
        "bass_mode": BassMode.ROOT.value,
        "humanize_preset": "straight",
        "energy_curve": {
            "intro": 0.3,
            "verse": 0.5,
            "chorus": 0.8,
            "bridge": 0.4,
            "outro": 0.3,
        },
        "velocity_range": (60, 100),
        "swing": 0.0,
    },
    "future_bass": {
        "recommended_instruments": [
            InstrumentType.SYNTH,
            InstrumentType.DRUMS,
            InstrumentType.BASS,
        ],
        "chord_templates": ["7th", "add9"],
        "tempo_range": (140, 160),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.EDM.value,
        "bass_mode": BassMode.SYNCOPATION.value,
        "humanize_preset": "straight",
        "energy_curve": {
            "intro": 0.3,
            "verse": 0.5,
            "chorus": 1.0,
            "bridge": 0.4,
            "outro": 0.2,
        },
        "velocity_range": (70, 110),
        "swing": 0.0,
    },
}


def _preset_to_suggestions(preset: dict) -> dict:
    return {
        "recommended_instruments": [i.value for i in preset["recommended_instruments"]],
        "chord_templates": preset["chord_templates"],
        "tempo_range": preset["tempo_range"],
        "time_signature": preset["time_signature"],
        "drum_style": preset["drum_style"],
        "bass_mode": preset["bass_mode"],
        "energy_curve": preset["energy_curve"],
        "velocity_range": preset["velocity_range"],
    }


class StyleEngine:
    """Applies style presets and provides composition guidance."""

    def set_style(self, song: Song, style_name: str) -> dict:
        if style_name not in STYLE_PRESETS:
            raise ValueError(f"Unknown style: {style_name}")
        preset = STYLE_PRESETS[style_name]
        song.global_settings.style = style_name
        song.global_settings.swing = preset["swing"]
        song.global_settings.groove = preset["humanize_preset"]
        return {
            "style": style_name,
            "applied": {
                "swing": preset["swing"],
                "groove": preset["humanize_preset"],
            },
            "suggestions": _preset_to_suggestions(preset),
        }

    def mix_styles(
        self, song: Song, style_a: str, style_b: str, weight_a: float = 0.5
    ) -> dict:
        if style_a not in STYLE_PRESETS:
            raise ValueError(f"Unknown style: {style_a}")
        if style_b not in STYLE_PRESETS:
            raise ValueError(f"Unknown style: {style_b}")

        preset_a = STYLE_PRESETS[style_a]
        preset_b = STYLE_PRESETS[style_b]
        weight_b = 1.0 - weight_a

        avg_tempo_a = sum(preset_a["tempo_range"]) / 2
        avg_tempo_b = sum(preset_b["tempo_range"]) / 2
        mixed_tempo = avg_tempo_a * weight_a + avg_tempo_b * weight_b

        mixed_swing = preset_a["swing"] * weight_a + preset_b["swing"] * weight_b

        vel_a = preset_a["velocity_range"]
        vel_b = preset_b["velocity_range"]
        mixed_velocity = (
            int(vel_a[0] * weight_a + vel_b[0] * weight_b),
            int(vel_a[1] * weight_a + vel_b[1] * weight_b),
        )

        if weight_a >= weight_b:
            drum_style = preset_a["drum_style"]
            bass_mode = preset_a["bass_mode"]
            humanize = preset_a["humanize_preset"]
            primary_chords = preset_a["chord_templates"]
            secondary_chords = preset_b["chord_templates"]
        else:
            drum_style = preset_b["drum_style"]
            bass_mode = preset_b["bass_mode"]
            humanize = preset_b["humanize_preset"]
            primary_chords = preset_b["chord_templates"]
            secondary_chords = preset_a["chord_templates"]

        instruments_a = preset_a["recommended_instruments"]
        instruments_b = preset_b["recommended_instruments"]
        merged_instruments: list[InstrumentType] = []
        seen: set[InstrumentType] = set()
        for inst in instruments_a + instruments_b:
            if inst not in seen:
                seen.add(inst)
                merged_instruments.append(inst)

        mixed_style = f"{style_a}+{style_b}"
        song.global_settings.style = mixed_style
        song.global_settings.swing = mixed_swing
        song.global_settings.groove = humanize

        return {
            "mixed": True,
            "styles": [style_a, style_b],
            "weights": [weight_a, weight_b],
            "applied": {
                "swing": mixed_swing,
                "groove": humanize,
            },
            "suggestions": {
                "recommended_instruments": [i.value for i in merged_instruments],
                "chord_templates": list(dict.fromkeys(primary_chords + secondary_chords)),
                "tempo_range": (int(mixed_tempo - 10), int(mixed_tempo + 10)),
                "drum_style": drum_style,
                "bass_mode": bass_mode,
                "velocity_range": mixed_velocity,
                "humanize_preset": humanize,
            },
        }

    def _resolve_preset(self, style: str) -> dict | None:
        if style in STYLE_PRESETS:
            return STYLE_PRESETS[style]
        if "+" in style:
            parts = style.split("+", 1)
            if parts[0] in STYLE_PRESETS:
                return STYLE_PRESETS[parts[0]]
        return None

    def get_style_guide(self, song: Song) -> dict:
        style = song.global_settings.style
        if not style:
            return {"message": "No style set. Use set_style first."}

        preset = self._resolve_preset(style)
        if preset is None:
            return {"message": f"Unknown style: {style}"}

        current_instruments = {t.instrument for t in song.tracks}
        recommended = preset["recommended_instruments"]
        missing = [i.value for i in recommended if i not in current_instruments]

        tempo = song.global_settings.tempo
        tempo_ok = preset["tempo_range"][0] <= tempo <= preset["tempo_range"][1]
        instruments_ok = len(missing) == 0
        chords_ok = len(song.chord_progression) > 0
        swing_ok = abs(song.global_settings.swing - preset["swing"]) < 0.15
        groove_ok = song.global_settings.groove == preset["humanize_preset"]

        next_actions: list[str] = []
        if not tempo_ok:
            mid = int((preset["tempo_range"][0] + preset["tempo_range"][1]) / 2)
            next_actions.append(f"Set tempo to {mid}")
        for inst in missing[:3]:
            next_actions.append(f"Add {inst} track")
        if not chords_ok:
            next_actions.append(
                f"Generate chords using templates: {', '.join(preset['chord_templates'][:2])}"
            )
        if not groove_ok:
            next_actions.append(f"Set groove to {preset['humanize_preset']}")
        if not swing_ok:
            next_actions.append(f"Set swing to {preset['swing']}")

        return {
            "style": style,
            "status": {
                "tempo_ok": tempo_ok,
                "instruments_ok": instruments_ok,
                "chords_ok": chords_ok,
                "swing_ok": swing_ok,
                "groove_ok": groove_ok,
            },
            "missing": missing,
            "next_actions": next_actions,
            "suggestions": _preset_to_suggestions(preset),
        }
