"""Analysis commands - read-only inspection of Song data.

Phase 7: TECHNICAL.md 5.14 - populate analysis_cache without mutating song content.
"""

from composer_engine.commands.base import Command
from composer_engine.generators.analysis_engine import AnalysisEngine
from composer_engine.models.analysis import AnalysisResult
from composer_engine.models.song import Song


def _require_song(song: Song | None) -> Song:
    if song is None:
        raise ValueError("No song loaded. Create a song first.")
    return song


class AnalyzeKeyCommand(Command):
    def __init__(self):
        self._result: dict = {}

    @property
    def description(self) -> str:
        return "Analyze key"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_key(song)
        song.analysis_cache[engine._cache_key("key")] = AnalysisResult(
            type="key", data=result
        )
        self._result = result
        return song


class AnalyzeTempoCommand(Command):
    def __init__(self):
        self._result: dict = {}

    @property
    def description(self) -> str:
        return "Analyze tempo"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_tempo(song)
        song.analysis_cache[engine._cache_key("tempo")] = AnalysisResult(
            type="tempo", data=result
        )
        self._result = result
        return song


class AnalyzeChordsCommand(Command):
    def __init__(self, track_id: str):
        self.track_id = track_id
        self._result: dict = {}

    @property
    def description(self) -> str:
        return f"Analyze chords on track {self.track_id}"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_chords(song, self.track_id)
        song.analysis_cache[engine._cache_key("chords", self.track_id)] = AnalysisResult(
            type="chords", data=result, track_id=self.track_id
        )
        self._result = result
        return song


class AnalyzePhrasesCommand(Command):
    def __init__(self, track_id: str):
        self.track_id = track_id
        self._result: dict = {}

    @property
    def description(self) -> str:
        return f"Analyze phrases on track {self.track_id}"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_phrases(song, self.track_id)
        song.analysis_cache[engine._cache_key("phrases", self.track_id)] = AnalysisResult(
            type="phrases", data=result, track_id=self.track_id
        )
        self._result = result
        return song


class AnalyzeMotifsCommand(Command):
    def __init__(self, track_id: str):
        self.track_id = track_id
        self._result: dict = {}

    @property
    def description(self) -> str:
        return f"Analyze motifs on track {self.track_id}"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_motifs(song, self.track_id)
        song.analysis_cache[engine._cache_key("motifs", self.track_id)] = AnalysisResult(
            type="motifs", data=result, track_id=self.track_id
        )
        self._result = result
        return song


class AnalyzeRhythmCommand(Command):
    def __init__(self, track_id: str):
        self.track_id = track_id
        self._result: dict = {}

    @property
    def description(self) -> str:
        return f"Analyze rhythm on track {self.track_id}"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_rhythm(song, self.track_id)
        song.analysis_cache[engine._cache_key("rhythm", self.track_id)] = AnalysisResult(
            type="rhythm", data=result, track_id=self.track_id
        )
        self._result = result
        return song


class AnalyzeDensityCommand(Command):
    def __init__(self, track_id: str | None = None):
        self.track_id = track_id
        self._result: dict = {}

    @property
    def description(self) -> str:
        return "Analyze density"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_density(song, self.track_id)
        song.analysis_cache[engine._cache_key("density", self.track_id)] = AnalysisResult(
            type="density", data=result, track_id=self.track_id
        )
        self._result = result
        return song


class AnalyzeEnergyCommand(Command):
    def __init__(self):
        self._result: dict = {}

    @property
    def description(self) -> str:
        return "Analyze energy"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_energy(song)
        song.analysis_cache[engine._cache_key("energy")] = AnalysisResult(
            type="energy", data=result
        )
        self._result = result
        return song


class AnalyzeRangeCommand(Command):
    def __init__(self, track_id: str):
        self.track_id = track_id
        self._result: dict = {}

    @property
    def description(self) -> str:
        return f"Analyze range on track {self.track_id}"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_range(song, self.track_id)
        song.analysis_cache[engine._cache_key("range", self.track_id)] = AnalysisResult(
            type="range", data=result, track_id=self.track_id
        )
        self._result = result
        return song


class AnalyzeRepetitionCommand(Command):
    def __init__(self, track_id: str):
        self.track_id = track_id
        self._result: dict = {}

    @property
    def description(self) -> str:
        return f"Analyze repetition on track {self.track_id}"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_repetition(song, self.track_id)
        song.analysis_cache[engine._cache_key("repetition", self.track_id)] = AnalysisResult(
            type="repetition", data=result, track_id=self.track_id
        )
        self._result = result
        return song


class AnalyzeVoiceLeadingCommand(Command):
    def __init__(self):
        self._result: dict = {}

    @property
    def description(self) -> str:
        return "Analyze voice leading"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_voice_leading(song)
        song.analysis_cache[engine._cache_key("voice_leading")] = AnalysisResult(
            type="voice_leading", data=result
        )
        self._result = result
        return song


class AnalyzeCadencesCommand(Command):
    def __init__(self):
        self._result: dict = {}

    @property
    def description(self) -> str:
        return "Analyze cadences"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_cadences(song)
        song.analysis_cache[engine._cache_key("cadences")] = AnalysisResult(
            type="cadences", data=result
        )
        self._result = result
        return song


class AnalyzeCounterpointCommand(Command):
    def __init__(self, track_id_a: str, track_id_b: str):
        self.track_id_a = track_id_a
        self.track_id_b = track_id_b
        self._result: dict = {}

    @property
    def description(self) -> str:
        return f"Analyze counterpoint between {self.track_id_a} and {self.track_id_b}"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_counterpoint(song, self.track_id_a, self.track_id_b)
        self._result = result
        return song


class AnalyzeStyleCommand(Command):
    def __init__(self):
        self._result: dict = {}

    @property
    def description(self) -> str:
        return "Analyze style"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_style(song)
        song.analysis_cache[engine._cache_key("style")] = AnalysisResult(
            type="style", data=result
        )
        self._result = result
        return song


class AnalyzeMoodCommand(Command):
    def __init__(self):
        self._result: dict = {}

    @property
    def description(self) -> str:
        return "Analyze mood"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_mood(song)
        song.analysis_cache[engine._cache_key("mood")] = AnalysisResult(
            type="mood", data=result
        )
        self._result = result
        return song


class AnalyzeComplexityCommand(Command):
    def __init__(self, track_id: str | None = None):
        self.track_id = track_id
        self._result: dict = {}

    @property
    def description(self) -> str:
        return "Analyze complexity"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_complexity(song, self.track_id)
        song.analysis_cache[engine._cache_key("complexity", self.track_id)] = AnalysisResult(
            type="complexity", data=result, track_id=self.track_id
        )
        self._result = result
        return song


class AnalyzeDynamicsCommand(Command):
    def __init__(self, track_id: str | None = None):
        self.track_id = track_id
        self._result: dict = {}

    @property
    def description(self) -> str:
        return "Analyze dynamics"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_dynamics(song, self.track_id)
        song.analysis_cache[engine._cache_key("dynamics", self.track_id)] = AnalysisResult(
            type="dynamics", data=result, track_id=self.track_id
        )
        self._result = result
        return song


class AnalyzeStructureCommand(Command):
    def __init__(self):
        self._result: dict = {}

    @property
    def description(self) -> str:
        return "Analyze structure"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.analyze_structure(song)
        song.analysis_cache[engine._cache_key("structure")] = AnalysisResult(
            type="structure", data=result
        )
        self._result = result
        return song


class GetFullAnalysisCommand(Command):
    def __init__(self):
        self._result: dict = {}

    @property
    def description(self) -> str:
        return "Get full analysis report"

    def execute(self, song: Song | None) -> Song:
        song = _require_song(song)
        engine = AnalysisEngine()
        result = engine.get_full_analysis(song)
        song.analysis_cache[engine._cache_key("full")] = AnalysisResult(
            type="full", data=result
        )
        self._result = result
        return song
