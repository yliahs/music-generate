# Composer Engine 技术文档

Version: 2.0  
Last Updated: 2026-07-23

---

## 一、系统定位

Composer Engine 是一个 **Music State Engine（音乐状态引擎）**，而不是 MIDI Editor。

核心理念：

- AI 不直接编辑 MIDI，而是向 Composer 发送 Command
- Composer 维护完整的音乐状态（Song）
- 所有修改都是 Command，支持完整的 Undo / Redo / Replay
- MIDI 只是最终的渲染产物，不是核心数据

---

## 二、完整架构

### 2.1 系统层次

```
┌─────────────────────────────────────────────────────────┐
│                        LLM Layer                        │
│        (Cursor / Claude / GPT / Gemini / ...)           │
└────────────────────────┬────────────────────────────────┘
                         │ MCP Protocol (stdio / http)
┌────────────────────────▼────────────────────────────────┐
│                    MCP Server Layer                      │
│              FastMCP v3 (Tool Definitions)               │
│        接收 LLM 的 tool 调用，转换为 Command             │
└────────────────────────┬────────────────────────────────┘
                         │ Command
┌────────────────────────▼────────────────────────────────┐
│                   Composer Engine                        │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐  │
│  │ History  │  │ Snapshot │  │   Command Executor    │  │
│  │ Manager  │  │ Manager  │  │  execute / undo / redo│  │
│  └──────────┘  └──────────┘  └───────────────────────┘  │
│                       │                                  │
│              ┌────────▼────────┐  ┌──────────────────┐   │
│              │   Song (State)  │  │ Pipeline Manager │   │
│              │   + stage field │  │ 阶段评估 / AI引导 │   │
│              └────────┬────────┘  └──────────────────┘   │
└───────────────────────┼─────────────────────────────────┘
                        │
          ┌─────────────┼──────────────┐
          │             │              │
┌─────────▼──┐  ┌──────▼──────┐  ┌────▼────────┐
│  Renderer  │  │ Persistence │  │  Analyzer   │
│ pretty_midi│  │    JSON     │  │ (Phase 7+)  │
│  → .mid    │  │  save/load  │  │             │
└────────────┘  └─────────────┘  └─────────────┘
```

### 2.2 数据模型层次

```
Song (根聚合)
├── id: str (UUID)
├── name: str
├── stage: Stage (Inspiration/Composition/Arrangement/Production/Export)
├── created_at / updated_at: datetime
├── global_settings: GlobalSettings
│   ├── tempo: float (BPM)
│   ├── time_signature: (int, int)
│   ├── key: Key 枚举
│   ├── mode: Mode 枚举
│   ├── swing: float (0.0 - 1.0)
│   ├── groove: str ("straight")              # Phase 6 新增
│   ├── style: str ("")                       # Phase 6 新增
│   ├── mood: str ("")                        # Phase 6 新增
│   ├── master_velocity: int (0-127)
│   └── master_humanize: float (0.0 - 1.0)
├── sections: list[Section]
│   ├── id, type: SectionType, start_beat, length_beats, repeat
├── tracks: list[Track]
│   ├── id, name, instrument: InstrumentType
│   ├── program: int (GM Program), channel: int (0-15)
│   ├── notes: list[Note]
│   │   └── pitch(0-127), start_beat, duration_beat, velocity(0-127)
│   ├── mute, solo: bool
│   ├── volume(0-127), pan(0-127, 64=center)
│   ├── octave_offset: int (默认 0)          # Phase 5 新增
│   ├── density: float (0-1, 默认 0.5)       # Phase 5 新增
│   ├── energy: float (0-1, 默认 0.5)        # Phase 5 新增
│   └── automation: list[AutomationCurve] = []  # Phase 8 新增
├── chord_progression: list[Chord]           # Phase 2 新增
│   └── Chord: root(Key), quality(ChordQuality), bass(Key?),
│             start_beat, duration_beat, roman(str?)
├── analysis_cache: dict[str, AnalysisResult] = {}  # Phase 7 新增
└── markers: list[Marker] = []                      # Phase 8 新增
```

### 2.3 Command + Event Sourcing 架构

**Command 生命周期**：

```
MCP Tool 接收调用 → 创建 Command → Composer.execute(command)
    → History 保存 before_state → Command.execute(song) 修改状态
    → Pipeline.evaluate() 评估阶段 → Event Log 记录事件
    → 返回新状态给 LLM
```

**Undo 流程**：undo_stack 弹出 (command, before_state) → 当前状态压入 redo_stack → 恢复 before_state

---

## 三、当前情况

**阶段**：Phase 1-13 全部完成 ✅

**已完成**：
- ✅ Phase 1 全部交付物（数据模型 + Commands + Composer + Pipeline + Renderer + Persistence + MCP Server）
- ✅ Phase 2 全部交付物（Music Theory 模块 + Chord 模型 + ChordGenerator + 11 Commands + 13 MCP Tools）
- ✅ Phase 3 全部交付物（MelodyGenerator + 15 种操作 + 15 Commands + 15 MCP Tools）
- ✅ Phase 4 全部交付物（BassGenerator 8 模式 + DrumsGenerator 8 风格 + 18 Commands + 18 MCP Tools）
- ✅ Phase 5 全部交付物（6 种扩展乐器 + ArrangementEngine 11 操作 + 20 Commands + 20 MCP Tools）
- ✅ Phase 6 全部交付物（HumanizeEngine 8 操作 + StyleEngine 13 预设 + 13 Commands + 14 MCP Tools）
- ✅ Phase 7 全部交付物（AnalysisEngine 18 分析 + AnalysisCache + 19 Commands + 19 MCP Tools）
- ✅ Phase 8 全部交付物（AutomationEngine 7 预设 + Marker 系统 + 8 Commands + 9 MCP Tools）
- ✅ Phase 9 全部交付物（PluginManager + 5 种插件接口 + 4 MCP Tools）
- ✅ Phase 10 全部交付物（MusicXMLRenderer + 2 MCP Tools）
- ✅ Phase 11 全部交付物（日志系统 + 启动 Banner + 运行统计 + 3 MCP Tools）
- ✅ Phase 12 全部交付物（全局/段落/音轨属性补全 + 14 Commands + 14 MCP Tools）
- ✅ Phase 13 全部交付物（MidiImporter + MIDI 导入/单轨导入/预览 + 3 MCP Tools）

**远期规划**：
- 🔜 REQUIREMENTS.md §三中仅剩 4 个 🔜（Pattern、Articulation、Harmony、Counter Melody）属于远期规划

### 代码结构

```
music-gene/
├── docs/
│   ├── REQUIREMENTS.md
│   └── TECHNICAL.md
├── src/
│   └── composer_engine/
│       ├── __init__.py
│       ├── models/               # enums, note, track, section, global_settings, song
│       │   ├── chord.py          # [Phase 2] Chord, ChordQuality, CadenceType
│       │   ├── analysis.py       # [Phase 7] AnalysisResult, Phrase, Motif, etc.
│       │   └── automation.py     # [Phase 8] AutomationPoint, AutomationCurve, Marker
│       ├── theory/               # [Phase 2] 乐理基础模块（Phase 2+3 共用）
│       │   ├── scales.py         #   音阶计算
│       │   ├── intervals.py      #   音程工具
│       │   └── chord_utils.py    #   和弦拼写与分析
│       ├── generators/           # [Phase 2+] 内容生成器
│       │   ├── chord_generator.py    # [Phase 2] 和弦进行生成
│       │   ├── melody_generator.py   # [Phase 3] 旋律生成
│       │   ├── bass_generator.py     # [Phase 4] Bass 生成（8 种模式）
│       │   ├── drums_generator.py    # [Phase 4] Drums 生成（8 种风格 + 模板）
│       │   ├── instrument_generator.py  # [Phase 5] 扩展乐器生成器
│       │   ├── arrangement_engine.py    # [Phase 5] 编曲引擎
│       │   ├── humanize_engine.py       # [Phase 6] 人性化引擎 + Groove 模板
│       │   ├── style_engine.py          # [Phase 6] 风格预设引擎
│       │   ├── analysis_engine.py       # [Phase 7] 分析引擎 (18 种分析)
│       │   └── automation_engine.py     # [Phase 8] 自动化引擎 + 预设
│       ├── commands/             # base, song_commands, track_commands, section_commands, global_commands
│       │   ├── chord_commands.py     # [Phase 2] 11 个和弦命令
│       │   ├── melody_commands.py    # [Phase 3] 15 个旋律命令
│       │   ├── bass_commands.py      # [Phase 4] 5 个 Bass 命令
│       │   ├── drums_commands.py     # [Phase 4] 13 个 Drums 命令
│       │   ├── instrument_commands.py   # [Phase 5] 6 个乐器命令
│       │   ├── arrangement_commands.py  # [Phase 5] 11 个编曲命令 + 3 个 Track 命令
│       │   ├── humanize_commands.py     # [Phase 6] 8 个人性化命令
│       │   ├── style_commands.py        # [Phase 6] 5 个风格命令
│       │   ├── analysis_commands.py     # [Phase 7] 19 个分析命令
│       │   ├── automation_commands.py   # [Phase 8] 8 个自动化命令
│       │   └── marker_commands.py       # [Phase 8] 2 个标记命令
│       ├── engine/               # composer, history, snapshot
│       ├── pipeline/             # stages, pipeline_manager, evaluation
│       ├── renderer/             # midi_renderer + musicxml_renderer [Phase 10]
│       ├── persistence/          # json_store
│       ├── plugins/              # [Phase 9] 插件管理器 + 插件接口
│       │   └── plugin_manager.py
│       ├── observability/        # [Phase 11] 可观测性
│       │   ├── logger.py         # 日志初始化 + 便捷函数
│       │   ├── stats.py          # 运行统计
│       │   └── banner.py         # 启动 Banner
│       └── server/               # mcp_server (169 MCP Tools: P1:35 + P2-10:114 + P11:3 + P12:14 + P13:3)
│   ├── importer/                # MIDI 导入 (Phase 13)
├── tests/
│   ├── test_models, test_commands, test_composer, test_renderer, test_pipeline
│   ├── test_theory.py            # [Phase 2]
│   ├── test_chord_generator.py   # [Phase 2]
│   ├── test_melody_generator.py  # [Phase 3]
│   ├── test_bass_generator.py    # [Phase 4]
│   ├── test_drums_generator.py   # [Phase 4]
│   ├── test_instrument_generator.py  # [Phase 5]
│   ├── test_arrangement_engine.py    # [Phase 5]
│   ├── test_humanize_engine.py       # [Phase 6]
│   ├── test_style_engine.py          # [Phase 6]
│   ├── test_analysis_engine.py       # [Phase 7]
│   ├── test_automation.py            # [Phase 8]
│   ├── test_plugin_manager.py        # [Phase 9]
│   ├── test_musicxml_renderer.py     # [Phase 10]
│   └── test_observability.py        # [Phase 11]
├── pyproject.toml
├── .gitignore
└── README.md
```

---

## 四、技术使用

### 4.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.12+ | 主要开发语言 |
| uv | latest | 包管理器 |
| Pydantic | v2 | 数据模型、校验、JSON 序列化 |
| FastMCP | v3.4.x | MCP Server 框架 |
| pretty_midi | latest | MIDI 文件生成 |
| pytest | latest | 单元测试 |

### 4.2 技术选型理由

- **Python**：pretty_midi 生态成熟；AI/ML 生态；FastMCP 原生支持
- **Pydantic v2**：强类型 + JSON 零成本序列化 + `model_copy(deep=True)` 实现快照 + 自动 JSON Schema
- **FastMCP v3**：`@mcp.tool()` 装饰器极简 API；支持 stdio / http；内建 Client 便于测试
- **pretty_midi**：Note → MIDI 简洁 API；多轨多通道；社区成熟
- **JSON 持久化**：Pydantic 原生支持，人类可读，无额外依赖

### 4.3 依赖清单

```toml
[project]
dependencies = ["pydantic>=2.0", "fastmcp>=3.4", "pretty-midi>=0.2.10"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23"]
```

---

## 五、技术方案

### 5.1 数据模型设计

#### 核心原则

1. **Note 是逻辑音符，不是 MIDI Event** — 以 beat 为时间单位，与 Tempo 解耦，Renderer 负责转换
2. **Song 是根聚合** — 所有数据从 Song 出发；序列化 Song = 保存全部状态
3. **使用 Pydantic BaseModel** — 所有模型继承 BaseModel，自动获得校验、序列化、深拷贝能力

#### 枚举定义 (enums.py)

| 枚举 | 值 |
|------|----|
| Key | C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B |
| Mode | major, minor, dorian, mixolydian, lydian, phrygian, locrian |
| SectionType | intro, verse, pre_chorus, chorus, bridge, solo, breakdown, outro |
| InstrumentType | piano, bass, strings, pad, lead, synth, drums, fx, brass, woodwinds, guitar, voice |
| Stage | empty, inspiration, composition, arrangement, production, export |

所有枚举继承 `(str, Enum)`，枚举值为字符串（Key 首字母大写，其余小写），便于 JSON 序列化和 MCP 参数传递。

#### GM Program 默认映射

| InstrumentType | GM Program | GM Name |
|---------------|------------|---------|
| PIANO | 0 | Acoustic Grand Piano |
| GUITAR | 25 | Acoustic Guitar (steel) |
| BASS | 33 | Electric Bass (finger) |
| DRUMS | — | Channel 9 (GM Percussion) |
| STRINGS | 48 | String Ensemble 1 |
| BRASS | 61 | Brass Section |
| WOODWINDS | 73 | Flute |
| PAD | 89 | Pad 2 (warm) |
| LEAD | 80 | Lead 1 (square) |
| SYNTH | 81 | Lead 2 (sawtooth) |
| FX | 98 | FX 3 (crystal) |
| VOICE | 52 | Choir Aahs |

### 5.2 Command 系统设计

#### Command 基类

```
abstract class Command:
    property description -> str       # 操作的人类可读描述
    abstract execute(song) -> Song    # 执行命令，返回修改后的 Song
    # 注意：没有 undo 方法！采用 Snapshot 策略，由 History 管理器恢复
```

#### Undo 策略

采用 **Snapshot 策略**（非逆操作）：execute 前由 History 保存 Song 深拷贝，undo 时直接恢复。

- 优点：简单可靠，不因逆操作逻辑错误导致状态不一致；支持任意复杂操作
- 缺点：内存占用较大（每步存完整 Song），未来可优化为只存 diff

#### Phase 1 Command 清单

| 分类 | Command | 参数 |
|------|---------|------|
| Song | CreateSongCommand | name, tempo, key, mode |
| Song | DeleteSongCommand | — |
| Song | CloneSongCommand | new_name |
| Track | AddTrackCommand | name, instrument, program, channel |
| Track | RemoveTrackCommand | track_id |
| Track | MuteTrackCommand | track_id, mute |
| Track | SoloTrackCommand | track_id, solo |
| Track | SetTrackVolumeCommand | track_id, volume |
| Track | SetTrackPanCommand | track_id, pan |
| Track | AddNotesCommand | track_id, notes[] |
| Track | RemoveNotesCommand | track_id, note_indices[] |
| Section | AddSectionCommand | type, start_beat, length_beats |
| Section | RemoveSectionCommand | section_id |
| Section | DuplicateSectionCommand | section_id |
| Section | MoveSectionCommand | section_id, new_start_beat |
| Section | ResizeSectionCommand | section_id, new_length_beats |
| Section | SetSectionRepeatCommand | section_id, repeat |
| Global | SetTempoCommand | tempo |
| Global | SetKeyCommand | key |
| Global | SetModeCommand | mode |
| Global | SetTimeSignatureCommand | numerator, denominator |
| Global | SetMasterVelocityCommand | velocity (0-127) |
| Global | SetMasterHumanizeCommand | amount (0.0-1.0) |

#### Phase 12 Command 清单

| 分类 | Command | 参数 |
|------|---------|------|
| Global | SetScaleCommand | scale (音阶名称，None=自动推算) |
| Global | SetMasterTimingCommand | timing (beats，正延后/负提前) |
| Global | SetGlobalEnergyCommand | energy (0.0-1.0) |
| Section | SwapSectionsCommand | section_id_a, section_id_b |
| Section | SplitSectionCommand | section_id, split_beat |
| Section | MergeSectionsCommand | section_id_a, section_id_b |
| Track | SetTrackRegisterCommand | track_id, register (high/mid/low) |
| Track | SetTrackComplexityCommand | track_id, complexity (0.0-1.0) |
| Track | SetTrackVelocityOffsetCommand | track_id, offset (-127~+127) |
| Track | SetTrackTimingOffsetCommand | track_id, offset (beats) |
| Track | SetTrackHumanizeCommand | track_id, humanize (0.0-1.0) |
| Track | SetTrackGrooveCommand | track_id, groove (模板名称) |
| Track | SetTrackRhythmCommand | track_id, rhythm_pattern (模式名称) |
| Track | SetTrackRangeCommand | track_id, low (MIDI pitch), high (MIDI pitch) |

#### Phase 12 模型变更

**GlobalSettings 新增字段**：
```
scale: str | None = None        # 覆盖 Key+Mode 推算的音阶名称
master_timing: float = 0.0      # 全局时值偏移 (beats)
global_energy: float = 0.5      # 全局能量级别 (0.0-1.0)
```

**Track 新增字段**：
```
track_register: str = "mid"     # 音区: high / mid / low
complexity: float = 0.5         # 复杂度 (0.0-1.0)
velocity_offset: int = 0        # 力度偏移 (-127 ~ +127)
timing_offset: float = 0.0     # 时值偏移 (beats)
humanize: float = 0.0          # 轨级人性化 (0.0-1.0)
groove: str = ""               # 轨级律动模板名
rhythm_pattern: str = ""       # 节奏模式名
pitch_range_low: int = 0       # 音域下限 (0=不限)
pitch_range_high: int = 127    # 音域上限 (127=不限)
```

**Song Length 计算**：
```
song_length_beats = max(s.start_beat + s.length_beats * s.repeat for s in sections)
# 在 get_song_state 返回值中追加此计算属性，不额外存储
```

### 5.3 Composer 引擎设计

```
class Composer:
    song: Song | None
    history: History
    snapshots: SnapshotManager
    pipeline: PipelineManager

    execute(command):
        before = song.deep_copy()
        song = command.execute(song)
        history.push(command, before)
        pipeline.evaluate(song)
        return song

    undo():
        (command, before) = history.pop_undo()
        history.push_redo(command, song)
        song = before
        pipeline.evaluate(song)

    redo(): 类似 undo，方向相反

    get_state() -> { song, pipeline_info, history_info }
    get_stage_guide() -> pipeline.get_guide(song)
    save_snapshot(name) / load_snapshot(name)
```

#### History 管理器

```
class History:
    undo_stack: list[(Command, Song)]     # 最多 max_undo=100 条
    redo_stack: list[(Command, Song)]
    event_log: list[CommandEvent]          # 完整事件日志（时间戳+类型+描述+参数）

    push(command, before_state):
        undo_stack.append(...)
        redo_stack.clear()                 # 新操作清空 redo
        event_log.append(...)
        if len > max_undo: 丢弃最早的

    pop_undo() -> (Command, Song) | None
    pop_redo() -> (Command, Song) | None
```

#### Snapshot 管理器

```
class SnapshotManager:
    snapshots: dict[name -> Song deep_copy]

    save(name, song) / load(name) -> Song / list() -> [names] / delete(name)
```

### 5.4 MIDI 渲染器设计

```
class MidiRenderer:
    render(song) -> PrettyMIDI:
        1. 创建 PrettyMIDI(initial_tempo=song.tempo)
        2. 确定要渲染的 tracks:
           - 有 solo track → 只渲染 solo tracks
           - 否则 → 渲染所有 non-mute tracks
        3. 对每个 track:
           - 创建 Instrument(program, is_drum=是否Drums, name)
           - 对每个 note:
             - beat → seconds: seconds = beat * 60.0 / tempo
             - velocity 应用 master_velocity 缩放
             - 创建 MIDI Note(velocity, pitch, start, end)
           - 添加到 instrument
        4. 返回 PrettyMIDI 对象

    render_to_file(song, path) -> path:
        midi = render(song)
        midi.write(path)
```

### 5.5 MCP Server 设计

#### 设计原则

1. **全局单例 Composer** — Server 进程内维护一个 Composer 实例，所有 Tool 共享
2. **Tool 只是薄封装** — 参数校验 → 创建 Command → composer.execute() → 返回状态
3. **返回完整状态** — 每个修改操作返回 `get_state()`（含 song + pipeline + history 摘要）
4. **强制英文接口** — Tool 名称、参数名、参数描述、docstring **必须英文**（代码注释可中文）
5. **丰富的 docstring** — docstring 是 LLM 的使用说明，必须清晰完整

#### Tool 结构模式

```
每个 MCP Tool 的伪代码结构：

@mcp.tool()
def tool_name(params...) -> dict:
    """English docstring with Args and Returns."""
    cmd = XxxCommand(params)
    composer.execute(cmd)
    return composer.get_state()
```

#### get_state() 返回值结构

```
{
    "song": { Song 完整数据 },
    "pipeline": {
        "stage": "arrangement",
        "progress": 50,
        "can_advance": false
    },
    "history": {
        "undo_count": 5,
        "redo_count": 0
    }
}
```

#### MCP Server 启动方式

- **stdio 模式**：`python -m composer_engine.server.mcp_server` 或 `fastmcp run mcp_server.py:mcp`
- **Cursor 配置** (`.cursor/mcp.json`)：command=uv, args=[run, --directory, 项目路径, python, -m, composer_engine.server.mcp_server]

### 5.6 JSON 持久化设计

```
class JsonStore:
    base_dir: 默认 ~/.composer-engine/songs/

    save_song(song, filename?):
        利用 Pydantic model_dump_json(indent=2) 序列化写入文件

    load_song(filename) -> Song:
        读取文件，利用 Pydantic model_validate_json() 反序列化

    list_songs() -> [{filename, name, id}, ...]
```

### 5.7 Pipeline 流水线设计

#### 设计定位

Pipeline 是 Command 系统之上的**编排治理层**，不替代 Command，而是引导 AI 按创作流程推进。

```
Pipeline (阶段管理、引导 AI)  →  Composer (执行命令)  →  Song (数据)
```

#### Stage 定义

| Stage | 入口条件 | 出口条件 | 推荐 Tools |
|-------|----------|----------|------------|
| **Inspiration** | Song 已创建 | 有名称 + 速度 + 调性 | create_song, set_tempo, set_key, set_mode, set_time_signature, set_style, set_mood, set_swing, set_groove |
| **Composition** | 有速度 + 调性 | 有段落 + 和弦(P2+) + 旋律(P3+) | add_section, remove_section, duplicate_section, generate_chords, generate_melody, analyze_key |
| **Arrangement** | 有段落 | 至少 4 轨有音符 | add_track, add_notes, set_track_volume, set_track_pan, generate_bass, generate_drums, generate_strings, generate_brass, generate_woodwinds, generate_synth, generate_piano_part, generate_guitar_part, increase_energy, add_layer |
| **Production** | 有音轨含音符 | 用户满意 | mute_track, solo_track, set_track_volume, set_track_pan, humanize_timing, humanize_velocity, apply_groove, apply_swing, hand_played_feel, add_automation, apply_automation_preset, analyze_energy, analyze_density, get_full_analysis |
| **Export** | 有音轨含音符 | 文件导出成功 | export_midi, export_musicxml, save_song, save_snapshot |

#### PipelineManager 核心逻辑

```
class PipelineManager:
    current_stage: Stage = EMPTY
    stage_history: list[阶段转换记录]

    evaluate(song):
        if song is None → stage = EMPTY
        检查当前阶段的出口条件
        如果全部满足 → 自动推进到下一阶段，记录转换历史
        返回 StageEvaluation(stage, progress%, completed, missing, can_advance, next_stage)

    get_guide(song) -> StageGuide:
        调用 evaluate 获取评估结果
        结合 StageDefinition 的推荐操作和 Tools
        返回 { stage, description, progress, what_to_do, what_is_missing, recommended_tools, can_advance }

    advance() → 手动推进到下一阶段
    go_back(target_stage) → 回退到指定阶段（自由回退，不限制）
```

#### 阶段评估逻辑 (evaluation.py)

每个阶段有独立的检查函数，逻辑如下：

- **Inspiration 出口**：检查 song.name 非空 + tempo > 0 + key 已设
- **Composition 出口**：检查 sections 数量 > 0（Phase 2+ 加检查和弦，Phase 3+ 加检查旋律）
- **Arrangement 出口**：统计有音符的 track 数量 >= 4
- **Production 出口**：无硬性条件，由用户决定
- **Export 出口**：无条件限制

每个检查函数返回 (已满足条件列表, 未满足条件列表)，progress = 已满足 / 总条件 * 100。

#### Pipeline MCP Tools

| Tool | 说明 |
|------|------|
| `get_stage_guide` | 获取当前阶段引导（AI 在开始创作、完成一组操作、不确定下一步时调用） |
| `advance_stage` | 手动推进到下一阶段 |
| `go_back_stage(target_stage)` | 回退到指定阶段 |

### 5.8 Music Theory 基础模块设计

Phase 2 和 Phase 3 共用的乐理工具层。纯函数，无状态，无副作用。

```
theory/
├── scales.py         # 音阶计算
├── intervals.py      # 音程工具
└── chord_utils.py    # 和弦拼写与罗马分析
```

#### 音阶计算 (scales.py)

```
KEY_TO_PITCH = { C:0, Db:1, D:2, Eb:3, E:4, F:5, Gb:6, G:7, Ab:8, A:9, Bb:10, B:11 }

SCALE_INTERVALS = {
    major:      [0, 2, 4, 5, 7, 9, 11],
    minor:      [0, 2, 3, 5, 7, 8, 10],      # 自然小调
    dorian:     [0, 2, 3, 5, 7, 9, 10],
    mixolydian: [0, 2, 4, 5, 7, 9, 10],
    lydian:     [0, 2, 4, 6, 7, 9, 11],
    phrygian:   [0, 1, 3, 5, 7, 8, 10],
    locrian:    [0, 1, 3, 5, 6, 8, 10],
}

get_scale_pitches(key, mode) -> list[int]:
    base = KEY_TO_PITCH[key]
    return [(base + i) % 12 for i in SCALE_INTERVALS[mode]]

get_scale_notes_in_range(key, mode, min_pitch, max_pitch) -> list[int]:
    pitch_classes = get_scale_pitches(key, mode)
    return [p for p in range(min_pitch, max_pitch+1) if p % 12 in pitch_classes]

is_in_scale(pitch, key, mode) -> bool:
    return pitch % 12 in get_scale_pitches(key, mode)
```

#### 音程工具 (intervals.py)

```
INTERVAL_NAMES = { 0:"P1", 1:"m2", 2:"M2", 3:"m3", 4:"M3", 5:"P4",
                   6:"A4/d5", 7:"P5", 8:"m6", 9:"M6", 10:"m7", 11:"M7" }

interval_between(pitch_a, pitch_b) -> int:
    return (pitch_b - pitch_a) % 12

transpose(pitch, semitones) -> int:
    return pitch + semitones        # 不取模，保留八度
```

#### 和弦拼写与分析 (chord_utils.py)

```
CHORD_INTERVALS = {
    major: [0,4,7],    minor: [0,3,7],    dim: [0,3,6],    aug: [0,4,8],
    dom7: [0,4,7,10],  maj7: [0,4,7,11],  min7: [0,3,7,10],
    half_dim7: [0,3,6,10],  dim7: [0,3,6,9],
    sus2: [0,2,7],     sus4: [0,5,7],
    add9: [0,4,7,14],  add11: [0,4,7,17],
    dom9: [0,4,7,10,14], maj9: [0,4,7,11,14], min9: [0,3,7,10,14],
}

get_chord_pitch_classes(root, quality) -> list[int]:
    base = KEY_TO_PITCH[root]
    return [(base + i) % 12 for i in CHORD_INTERVALS[quality]]

# 自然音阶内每个级数的默认和弦性质
DIATONIC_CHORDS = {
    major: [(1,major),(2,minor),(3,minor),(4,major),(5,major),(6,minor),(7,dim)],
    minor: [(1,minor),(2,dim),(3,major),(4,minor),(5,minor),(6,major),(7,major)],
}

resolve_roman(roman_str, key, mode) -> (root_key, chord_quality):
    解析罗马数字 → 确定 scale_degree → 查表获取 root 和 quality
    示例: "V" in C major → (G, major)
          "ii7" in C major → (D, min7)
          "♭VII" in C major → (Bb, major)

roman_analysis(chord, key, mode) -> str:
    计算 chord.root 相对于 key 的 scale degree → 生成罗马标记
    示例: Chord(root=F, quality=major) in C major → "IV"
          Chord(root=E, quality=dom7) in A minor → "V7"
```

### 5.9 Phase 2 和声系统设计

#### 新增数据模型 (models/chord.py)

```
ChordQuality(str, Enum):
    MAJOR, MINOR, DIMINISHED, AUGMENTED,
    DOM7, MAJ7, MIN7, HALF_DIM7, DIM7,
    SUS2, SUS4, ADD9, ADD11, DOM9, MAJ9, MIN9

CadenceType(str, Enum):
    AUTHENTIC, PLAGAL, HALF, DECEPTIVE

Chord(BaseModel):
    root: Key                       # 根音 (C, D, Eb 等)
    quality: ChordQuality           # 和弦性质
    bass: Key | None = None         # 低音 (转位/slash chord, 如 C/E → bass=E)
    start_beat: float               # 起始拍
    duration_beat: float            # 持续拍数
    roman: str | None = None        # 罗马标记缓存 ("IV", "V7/V")
```

**Song 模型变更**：

```
Song 新增:
    chord_progression: list[Chord] = []    # 全局和弦时间线
```

#### ChordGenerator (generators/chord_generator.py)

```
CHORD_TEMPLATES = {
    "pop": [
        {"name":"pop_classic",   "roman": ["I","V","vi","IV"]},
        {"name":"pop_50s",       "roman": ["I","vi","IV","V"]},
        {"name":"pop_emotional", "roman": ["vi","IV","I","V"]},
        {"name":"canon",         "roman": ["I","V","vi","iii","IV","I","IV","V"]},
    ],
    "rock": [
        {"name":"rock_basic", "roman": ["I","IV","V","I"]},
        {"name":"rock_power", "roman": ["I","bVII","IV","I"]},
        {"name":"rock_alt",   "roman": ["I","V","bVII","IV"]},
    ],
    "jazz": [
        {"name":"jazz_251",       "roman": ["ii7","V7","Imaj7"]},
        {"name":"jazz_turnaround","roman": ["Imaj7","vi7","ii7","V7"]},
    ],
    "blues": [
        {"name":"blues_12bar",    "roman": ["I7","I7","I7","I7","IV7","IV7","I7","I7","V7","IV7","I7","V7"]},
    ],
    "anime": [
        {"name":"royal_road",    "roman": ["IV","V","iii","vi"]},
        {"name":"komuro",        "roman": ["vi","V","IV","V"]},
        {"name":"just_the_two",  "roman": ["I","V","vi","iii","IV","I","ii","V"]},
    ],
    "classical": [
        {"name":"authentic", "roman": ["I","IV","V","I"]},
        {"name":"romantic",  "roman": ["I","vi","ii","V"]},
    ],
}

class ChordGenerator:
    generate(key, mode, style, length_beats, beats_per_chord=4) -> list[Chord]:
        1. 根据 style 从 CHORD_TEMPLATES 选取模板（可随机或指定 template_name）
        2. 用 resolve_roman() 将每个罗马标记解析为 (root, quality)
        3. 按 beats_per_chord 分配 start_beat 和 duration_beat
        4. 如果总长度 < length_beats → 循环模板
        5. 如果总长度 > length_beats → 截断
        6. 用 roman_analysis() 缓存 roman 字段
        7. 返回 list[Chord]

    reharmonize(chords, key, mode, target_style) -> list[Chord]:
        1. 分析每个和弦的和声功能（主功能T / 属功能D / 下属功能S）
        2. 在 target_style 的和弦语汇中寻找同功能替代
        3. 保持和声节奏(start/duration)不变
        4. 返回新的 list[Chord]

    borrow_chord(chord, source_mode) -> Chord:
        从 source_mode (如 parallel minor) 获取同级数和弦
        例: key=C, mode=major, degree=4 → 从 C minor 借 Fm

    secondary_dominant(target_chord) -> Chord:
        返回目标和弦的属和弦 (V/x)
        例: target = Am (vi in C) → E or E7

    passing_chord(chord_a, chord_b) -> Chord:
        计算两和弦根音之间的半音 → 插入中间和弦
        规则: 优先使用半音经过（如 C-Db-D 或 C-C#-D）

    set_cadence(chords, section_end_beat, cadence_type) -> list[Chord]:
        修改段落结尾的最后 2 个和弦:
        - authentic: ... → V → I
        - plagal: ... → IV → I
        - half: ... → V
        - deceptive: ... → V → vi
```

#### Phase 2 Command 清单

| 分类 | Command | 参数 |
|------|---------|------|
| Chord | GenerateChordsCommand | section_id?, style, template_name?, beats_per_chord |
| Chord | SetChordsCommand | chords[] |
| Chord | ReplaceChordCommand | chord_index, new_root, new_quality |
| Chord | InsertChordCommand | position_beat, root, quality, duration_beat |
| Chord | RemoveChordCommand | chord_index |
| Chord | ReharmonizeCommand | section_id?, target_style |
| Chord | BorrowChordCommand | chord_index, source_mode |
| Chord | SecondaryDominantCommand | target_chord_index |
| Chord | PassingChordCommand | chord_index_a, chord_index_b |
| Chord | ModulateCommand | target_key, target_mode?, pivot_beat |
| Chord | SetCadenceCommand | section_id, cadence_type |

#### Pipeline 阶段评估更新

Phase 2 完成后，Composition 阶段出口条件追加：
```
check_composition_exit 新增:
    - has_chord_progression: len(song.chord_progression) > 0
```

### 5.10 Phase 3 旋律生成设计

#### MelodyGenerator (generators/melody_generator.py)

```
class MelodyGenerator:

    generate(
        chord_progression: list[Chord],
        key: Key, mode: Mode,
        start_beat: float, end_beat: float,
        note_density: "sparse"|"normal"|"dense" = "normal",
        pitch_range: (int, int) = (60, 84),        # C4 - C6
        contour: "arch"|"ascending"|"descending"|"wave"|"flat" = "arch",
        chord_tone_weight: float = 0.7,
        rhythm_complexity: "simple"|"moderate"|"complex" = "moderate"
    ) -> list[Note]:

        算法核心流程:

        1. 准备音阶
           scale_notes = get_scale_notes_in_range(key, mode, pitch_range)

        2. 规划旋律轮廓 (contour → 每个 beat 的 target_pitch_center)
           - arch: 中间高两边低，peak 在 60-70% 处
           - ascending: 线性从 range_low 到 range_high
           - descending: 线性从 range_high 到 range_low
           - wave: 正弦曲线起伏
           - flat: 固定在 range_center

        3. 确定节奏网格
           - sparse: 步进 = 2.0 拍（半音符为主）
           - normal: 步进 = 1.0 拍（四分音符为主）
           - dense:  步进 = 0.5 拍（八分音符为主）
           - complex 模式: 混入附点(1.5)、切分(0.75+0.25)、十六分(0.25)

        4. 逐位置生成 pitch
           for each beat_position:
               current_chord = 查找当前和弦
               chord_tones = get_chord_pitch_classes(chord.root, chord.quality)
               target_center = contour 计算的目标中心音高

               if 强拍(beat_position % beats_per_bar < 0.01):
                   # 强拍偏好和弦音
                   candidates = chord_tones 附近的 scale_notes
                   weights: chord_tone × chord_tone_weight, scale × (1-weight)
               else:
                   # 弱拍可用经过音
                   candidates = scale_notes

               选择最接近 target_center 的候选音
               避免与前一个音距离 > 7（完全五度），优先级位移
               避免连续 3 个同音

        5. 后处理
           - 乐句末尾（section 最后 2 拍）倾向落在稳定音(1, 3, 5 级)
           - 检查全部 pitch 在 pitch_range 内
           - 将相邻同 pitch 音符合并为长音（如果密度允许）

    simplify(notes, strength=0.5) -> list[Note]:
        1. 按 strength 移除最短的 N% 音符
        2. 合并相邻同音
        3. 保留强拍上的音符

    complexify(notes, key, mode, chord_progression, strength=0.5) -> list[Note]:
        1. 在长音符（> 1拍）之间添加经过音
        2. 在强拍和弦音前添加倚音（半音下方）
        3. strength 控制添加比例

    transpose(notes, semitones) -> list[Note]:
        每个 note.pitch += semitones

    invert(notes, pivot_pitch) -> list[Note]:
        每个 note.pitch = 2 * pivot_pitch - note.pitch

    reverse(notes) -> list[Note]:
        total = max(n.start_beat + n.duration_beat for n in notes) - min(n.start_beat)
        base = min(n.start_beat)
        每个 note: new_start = base + total - (note.start_beat - base + note.duration_beat)

    sequence(notes, interval, count) -> list[Note]:
        原始长度 = max_end - min_start
        for i in 1..count:
            复制 notes，每个 pitch += interval * i
            每个 start_beat += 原始长度 * i
        拼接返回

    variation(notes, chord_progression, key, mode) -> list[Note]:
        1. 标记强拍和弦音为"骨架"（保留不动）
        2. 弱拍音符: 在 scale_notes 中随机替换为邻音
        3. 随机微调节奏（±0.25 拍偏移）

    develop_motif(notes, motif_beats=4, key, mode) -> list[Note]:
        1. 取 notes 前 motif_beats 拍作为"动机"
        2. 发展手段（依次应用）:
           a. 原样陈述
           b. 移高二度模进
           c. 倒影
           d. 节奏变奏 + 移调
        3. 拼接所有发展片段

    extend(notes, extra_beats, chord_progression, key, mode) -> list[Note]:
        分析末尾 4 拍的音型特征（密度、走向、平均 pitch）
        用 generate() 按相同特征续写 extra_beats

    shorten(notes, cut_beats) -> list[Note]:
        移除 end_beat > (max_end - cut_beats) 的音符
        截短跨界音符

    call_response(notes, response_style) -> list[Note]:
        response 放在原始乐句之后，等长
        - "mirror": 倒影（invert）
        - "echo": 复制 + 随机变化 20% 音符
        - "complement": 密→疏 or 疏→密，高→低 or 低→高

    generate_hook(chord_progression, key, mode, hook_beats=4) -> list[Note]:
        特点: 音域窄(≤8度), 重复性强, 节奏鲜明
        1. 选择 1-2 个核心音程（如纯四/大三）
        2. 生成 2 拍动机
        3. 重复或微变重复填满 hook_beats

    question_answer(chord_progression, key, mode, phrase_beats=4) -> list[Note]:
        1. 生成 question (phrase_beats 拍)，结尾在不稳定音(2,5,7 级)
        2. 生成 answer (phrase_beats 拍)，节奏相似，结尾在稳定音(1,3,5 级)
        3. 拼接返回
```

#### Phase 3 Command 清单

| 分类 | Command | 参数 |
|------|---------|------|
| Melody | GenerateMelodyCommand | track_id, section_id?, params(密度/音域/轮廓/权重/复杂度) |
| Melody | RegenerateMelodyCommand | track_id, section_id? |
| Melody | SimplifyMelodyCommand | track_id, strength |
| Melody | ComplexifyMelodyCommand | track_id, strength |
| Melody | TransposeMelodyCommand | track_id, semitones |
| Melody | InvertMelodyCommand | track_id, pivot_pitch |
| Melody | ReverseMelodyCommand | track_id |
| Melody | SequenceMelodyCommand | track_id, interval, count |
| Melody | VariationMelodyCommand | track_id |
| Melody | DevelopMotifCommand | track_id, motif_beats |
| Melody | ExtendMelodyCommand | track_id, extra_beats |
| Melody | ShortenMelodyCommand | track_id, cut_beats |
| Melody | CallResponseCommand | track_id, response_style |
| Melody | GenerateHookCommand | track_id, hook_beats |
| Melody | QuestionAnswerCommand | track_id, phrase_beats |

#### Pipeline 阶段评估更新

Phase 3 完成后，Composition 阶段出口条件追加：
```
check_composition_exit 最终版:
    - has_sections: len(song.sections) > 0
    - has_chord_progression: len(song.chord_progression) > 0  # Phase 2+
    - has_melody: 至少 1 个 track 有音符                        # Phase 3+
```

### 5.11 Phase 4 Bass & Drums 设计

#### 新增枚举与常量 (models/enums.py)

```
BassMode(str, Enum):
    ROOT, OCTAVE, WALKING, SYNCOPATION,
    FOLLOW_CHORDS, INDEPENDENT, COUNTER_BASS, GENERATE

DrumStyle(str, Enum):
    ROCK, POP, JAZZ, METAL, EDM, ANIME, LATIN, SWING

HiHatPattern(str, Enum):
    EIGHTHS, SIXTEENTHS, OFFBEAT, OPEN_CLOSE

KickPattern(str, Enum):
    STRAIGHT, OFFBEAT, DOUBLE, FOUR_ON_FLOOR

SnarePattern(str, Enum):
    BACKBEAT, GHOST, RIMSHOT
```

```
GM_PERCUSSION (常量字典):
    KICK      = 36    # Bass Drum 1
    SNARE     = 38    # Acoustic Snare
    SIDE_STICK = 37
    CLAP      = 39
    CLOSED_HH = 42    # Closed Hi-Hat
    OPEN_HH   = 46    # Open Hi-Hat
    PEDAL_HH  = 44    # Pedal Hi-Hat
    CRASH_1   = 49
    CRASH_2   = 57
    RIDE      = 51
    RIDE_BELL = 53
    LOW_TOM   = 45
    MID_TOM   = 47
    HIGH_TOM  = 50
    FLOOR_TOM = 41
    TAMBOURINE = 54
    COWBELL   = 56
    CLAVES    = 75
```

#### BassGenerator (generators/bass_generator.py)

```
class BassGenerator:
    BASS_RANGE = (28, 55)       # E1 到 G3

    generate(
        chords: list[Chord],
        key: Key, mode: Mode,
        start_beat: float, end_beat: float,
        bass_mode: BassMode = GENERATE,
        note_density: str = "normal",
        octave: int = 2               # 1=低(28-40), 2=中(36-48), 3=高(43-55)
    ) -> list[Note]:

        根据 bass_mode 分发到具体算法:

    _root(chords, octave_range) -> list[Note]:
        对每个 chord:
            pitch = 根音的 MIDI（在 octave_range 内）
            start = chord.start_beat
            duration = chord.duration_beat
        最简单模式：一个和弦一个音

    _octave(chords, octave_range) -> list[Note]:
        对每个 chord:
            root_pitch = 根音 MIDI
            半拍: root, root+12 交替
            如果 chord.duration >= 4:
                [root(1拍), root+12(1拍), root(1拍), root+12(1拍)]
            如果 chord.duration >= 2:
                [root(1拍), root+12(1拍)]

    _walking(chords, key, mode, octave_range) -> list[Note]:
        经典行走贝斯算法:
        1. 每拍一个音（四分音符节奏）
        2. 每个和弦的第 1 拍 = 根音
        3. 中间拍 = 和弦音或音阶经过音（级进优先）
        4. 最后一拍 = 半音或全音趋向下一和弦根音
        5. 避免连续重复音
        6. 音域控制在 octave_range 内

    _syncopation(chords, octave_range) -> list[Note]:
        切分节奏:
        1. 根音放在 offbeat（如 0.5, 1.5, 2.5 拍）
        2. 部分音符跨拍连线（duration 1.5 拍）
        3. 强拍留空或短促
        4. 休止符穿插（density 控制）

    _follow_chords(chords, octave_range) -> list[Note]:
        分解和弦式:
        1. 取和弦音(root, third, fifth, seventh?)
        2. 在 bass 音域内逐音分解
        3. 模式: 上行(1-3-5) 或 下行(5-3-1) 或 混合
        4. 每拍一个音或半拍一个音（由 density 控制）

    _independent(chords, key, mode, octave_range) -> list[Note]:
        独立旋律线:
        1. 类似 MelodyGenerator 但限制在 bass 音域
        2. 以和弦音为骨架，音阶音为经过
        3. 节奏自由（不严格跟和弦节奏）
        4. 有自己的旋律轮廓

    _counter_bass(chords, melody_notes, key, mode, octave_range) -> list[Note]:
        对位低音:
        1. 分析 melody_notes 的走向
        2. 反向运动：旋律上行 → bass 下行，反之亦然
        3. 节奏互补：旋律密 → bass 疏，反之亦然
        4. 以和弦音为骨架确保和声正确

    _generate(chords, key, mode, octave_range, density) -> list[Note]:
        综合模式:
        1. 默认以 root 为基础
        2. 在和弦切换处加入经过音
        3. 偶尔加入八度跳跃
        4. density 控制装饰音数量

    simplify(notes) -> list[Note]:
        移除经过音、保留根音、合并短音符

    transpose(notes, semitones) -> list[Note]:
        每个 note.pitch += semitones（保持在 bass 音域）
```

#### DrumsGenerator (generators/drums_generator.py)

```
# 鼓模板: 每个 bar 的打击列表
# 格式: list[tuple(pitch, beat_offset, duration, velocity)]
# beat_offset 是 bar 内的偏移（0-based）

DRUM_TEMPLATES = {
    "rock": {
        "kick":   [(36, 0.0, 0.5, 100), (36, 2.0, 0.5, 100)],
        "snare":  [(38, 1.0, 0.5, 100), (38, 3.0, 0.5, 100)],
        "hihat":  [(42, i*0.5, 0.5, 80) for i in range(8)],  # 8分音符
        "crash":  [],   # 段首手动添加
    },
    "pop": {
        "kick":   [(36, 0.0, 0.5, 90), (36, 2.0, 0.5, 85)],
        "snare":  [(38, 1.0, 0.5, 95), (38, 3.0, 0.5, 95)],
        "hihat":  [(42, i*0.5, 0.5, 70) for i in range(8)],
        "crash":  [],
    },
    "jazz": {
        "kick":   [(36, 0.0, 0.5, 60), (36, 2.5, 0.5, 50)],    # 轻柔不规则
        "snare":  [(38, 1.0, 0.5, 60), (37, 3.0, 0.5, 50)],    # Side Stick
        "ride":   [(51, 0.0, 1.0, 75), (51, 1.0, 0.5, 60),
                   (51, 1.5, 0.5, 70), (51, 2.0, 1.0, 75),
                   (51, 3.0, 0.5, 60), (51, 3.5, 0.5, 70)],    # Swing Ride
        "hihat":  [(44, 1.0, 0.5, 50), (44, 3.0, 0.5, 50)],    # Pedal
    },
    "metal": {
        "kick":   [(36, i*0.25, 0.25, 110) for i in range(16)], # 16分双踩
        "snare":  [(38, 1.0, 0.5, 120), (38, 3.0, 0.5, 120)],
        "hihat":  [(42, i*0.25, 0.25, 90) for i in range(16)],  # 16分踩镲
        "crash":  [],
    },
    "edm": {
        "kick":   [(36, i, 0.5, 110) for i in range(4)],         # Four-on-floor
        "snare":  [(39, 1.0, 0.5, 100), (39, 3.0, 0.5, 100)],   # Clap
        "hihat":  [(46, i*0.5+0.25, 0.25, 80) for i in range(8)],# Offbeat Open HH
        "crash":  [],
    },
    "anime": {
        "kick":   [(36, 0.0, 0.5, 95), (36, 2.0, 0.5, 90)],
        "snare":  [(38, 1.0, 0.5, 100), (38, 3.0, 0.5, 100)],
        "hihat":  [(42, i*0.5, 0.5, 75) for i in range(8)],
        "crash":  [],
    },
    "latin": {
        "kick":   [(36, 0.0, 0.5, 90), (36, 2.5, 0.5, 85)],
        "snare":  [(38, 2.0, 0.5, 90)],
        "hihat":  [],
        "conga":  [(63, 0.0, 0.5, 80), (63, 1.0, 0.5, 75),      # 使用 GM Conga
                   (64, 1.5, 0.5, 70), (63, 2.0, 0.5, 80),
                   (64, 3.0, 0.5, 75), (63, 3.5, 0.5, 70)],
        "clave":  [(75, 0.0, 0.5, 85), (75, 1.5, 0.5, 85),      # Son Clave
                   (75, 2.0, 0.5, 85)],
    },
    "swing": {
        "kick":   [(36, 0.0, 0.5, 65), (36, 2.0, 0.5, 60)],
        "snare":  [(38, 1.0, 0.5, 55), (38, 3.0, 0.5, 55)],     # 刷奏
        "ride":   [(51, 0.0, 1.0, 80), (51, 1.0, 0.33, 65),
                   (51, 1.67, 0.33, 75), (51, 2.0, 1.0, 80),
                   (51, 3.0, 0.33, 65), (51, 3.67, 0.33, 75)],  # Shuffle
        "hihat":  [(44, 1.0, 0.5, 50), (44, 3.0, 0.5, 50)],
    },
}

FILL_TEMPLATES = {
    "basic":    在最后 1 拍: [Snare×2, Tom_High, Tom_Low],
    "double":   在最后 2 拍: [Snare×4, Tom 下行],
    "crescendo": 渐强 16 分 Snare roll → Crash,
    "tom_cascade": Tom 从高到低级联,
}

class DrumsGenerator:

    generate(
        style: DrumStyle,
        start_beat: float, end_beat: float,
        time_sig: (int, int) = (4, 4)
    ) -> list[Note]:
        1. 从 DRUM_TEMPLATES[style] 获取模板
        2. 计算 bar 数: bars = (end - start) / beats_per_bar
        3. 对每个 bar:
            offset = start_beat + bar_index * beats_per_bar
            对模板中每个元素:
                Note(pitch=元素.pitch,
                     start_beat=offset + 元素.beat_offset,
                     duration_beat=元素.duration,
                     velocity=元素.velocity)
        4. 返回所有 Note

    set_style(notes, new_style, start_beat, end_beat) -> list[Note]:
        1. 移除 [start, end) 范围内的所有鼓音符
        2. 用新 style 重新生成
        3. 返回新 notes

    add_fill(notes, beat_position, fill_type="basic") -> list[Note]:
        1. 从 FILL_TEMPLATES 选模板
        2. 移除 fill 覆盖范围内的原有鼓音符
        3. 插入 fill 音符
        4. 添加 Crash (beat_position + fill_length) 作为 fill 结尾
        5. 返回修改后的 notes

    add_ghost_notes(notes, start_beat, end_beat, density=0.3) -> list[Note]:
        1. 找到所有没有 snare 的 16 分音符位置
        2. 以 density 概率添加低力度 Snare (velocity 20-40)
        3. 返回新 notes

    set_hihat_pattern(notes, pattern, start_beat, end_beat) -> list[Note]:
        1. 清除范围内所有 HiHat 音符 (pitch 42/44/46)
        2. 按 pattern 类型生成:
           - eighths:    每 0.5 拍 Closed HH(42)
           - sixteenths: 每 0.25 拍 Closed HH(42)
           - offbeat:    每 0.5+0.25 拍 Open HH(46)
           - open_close: 交替 Closed(42) 和 Open(46)
        3. 返回修改后 notes

    set_kick_pattern(notes, pattern, start_beat, end_beat) -> list[Note]:
        类似 hihat，清除旧 kick 后按模板生成:
        - straight:      拍 1, 3
        - offbeat:       拍 0.5, 2.5
        - double:        拍 1, 1.5, 3, 3.5
        - four_on_floor: 每拍

    set_snare_pattern(notes, pattern, start_beat, end_beat) -> list[Note]:
        - backbeat: 拍 2, 4
        - ghost:    拍 2, 4 + 低力度装饰
        - rimshot:  拍 2, 4 用 Side Stick(37)

    add_crash(notes, beat_position) -> list[Note]:
        插入 Crash(49) 在指定位置

    set_ride_pattern(notes, start_beat, end_beat, swing=False) -> list[Note]:
        清除旧 Ride，生成新 Ride 模式（直 or Swing）

    add_tom_fill(notes, beat_position, fill_beats=1) -> list[Note]:
        从 High Tom → Mid Tom → Low Tom 级联

    add_percussion(notes, element, start_beat, end_beat, pattern) -> list[Note]:
        添加 Tambourine / Cowbell / Claves 等
        element 映射到 GM pitch

    clear_element(notes, element, start_beat, end_beat) -> list[Note]:
        移除指定 pitch 范围的音符（如只清 hihat 或只清 kick）
```

#### Phase 4 Command 清单

| 分类 | Command | 参数 |
|------|---------|------|
| Bass | GenerateBassCommand | track_id?, section_id?, bass_mode, note_density, octave |
| Bass | RegenerateBassCommand | track_id |
| Bass | SetBassPatternCommand | track_id, notes[] |
| Bass | SimplifyBassCommand | track_id |
| Bass | TransposeBassCommand | track_id, semitones |
| Drums | GenerateDrumsCommand | track_id?, section_id?, style |
| Drums | RegenerateDrumsCommand | track_id |
| Drums | SetDrumStyleCommand | track_id, style, section_id? |
| Drums | AddDrumFillCommand | track_id, beat_position, fill_type? |
| Drums | AddGhostNotesCommand | track_id, section_id?, density |
| Drums | SetHiHatPatternCommand | track_id, pattern, section_id? |
| Drums | SetKickPatternCommand | track_id, pattern, section_id? |
| Drums | SetSnarePatternCommand | track_id, pattern, section_id? |
| Drums | AddCrashCommand | track_id, beat_position |
| Drums | SetRidePatternCommand | track_id, section_id?, swing |
| Drums | AddTomFillCommand | track_id, beat_position, fill_beats |
| Drums | AddPercussionCommand | track_id, element, section_id?, pattern |
| Drums | ClearDrumElementCommand | track_id, element, section_id? |

#### Pipeline 阶段评估更新

Phase 4 不新增出口条件。Bass/Drums 生成的 notes 已经计入 Arrangement 阶段的 "至少 4 轨有音符" 检查。

### 5.12 Phase 5 扩展乐器与编曲设计

#### 新增枚举 (models/enums.py)

```
StringsMode(str, Enum):
    SUSTAINED, MELODY, COUNTERPOINT, TREMOLO, PIZZICATO

BrassMode(str, Enum):
    STABS, SUSTAINED, FANFARE, SOLO_LINE

WoodwindsMode(str, Enum):
    STABS, SUSTAINED, SOLO_LINE, TRILL

SynthMode(str, Enum):
    PAD, LEAD, ARP, FX

PianoMode(str, Enum):
    BLOCK_CHORDS, BROKEN_CHORDS, ARPEGGIO, COMPING

GuitarMode(str, Enum):
    STRUM, FINGERPICK, ARPEGGIO, MUTED
```

#### Track 模型变更

```
Track 新增字段:
    octave_offset: int = 0          # 八度偏移 (-3 ~ +3)
    density: float = 0.5            # 密度 (0.0 ~ 1.0)
    energy: float = 0.5             # 能量 (0.0 ~ 1.0)
```

#### 扩展乐器生成器架构 (generators/instrument_generator.py)

```
class InstrumentGenerator:
    """所有扩展乐器生成器的基类/工具类"""

    # 各乐器默认音域
    INSTRUMENT_RANGES = {
        "strings":   (55, 88),    # G3 - E6
        "brass":     (53, 82),    # F3 - Bb5
        "woodwinds": (60, 96),    # C4 - C7
        "synth":     (36, 96),    # C2 - C7
        "piano":     (36, 96),    # C2 - C7
        "guitar":    (40, 84),    # E2 - C6
    }

    generate_strings(
        chords, key, mode,
        start_beat, end_beat,
        strings_mode: StringsMode = SUSTAINED
    ) -> list[Note]:
        分发到子算法:

        _sustained(chords) -> list[Note]:
            # 持续和弦铺底
            1. 对每个 chord，生成和弦音 (3-4 音)
            2. 每个音 = 长音（duration = chord.duration_beat）
            3. 音域分布在弦乐中高区
            4. velocity 柔和 (60-80)

        _melody(chords, key, mode) -> list[Note]:
            # 弦乐旋律线
            类似 MelodyGenerator.generate()
            但音色特征：更多连音 (legato)，较少跳进
            pitch_range 限制在弦乐音域

        _counterpoint(chords, key, mode, reference_melody?) -> list[Note]:
            # 对位
            1. 分析 reference_melody 的节奏和走向
            2. 生成反向运动 + 节奏互补的旋律
            3. 保持和声正确（优先和弦音+音阶音）
            4. 如果没有 reference，生成独立对位线

        _tremolo(chords) -> list[Note]:
            # 震音
            1. 取和弦音
            2. 将长音拆为 32 分音符快速重复
            3. velocity 起伏（模拟弓压变化）

        _pizzicato(chords) -> list[Note]:
            # 拨弦
            1. 短促音符 (duration = 0.25)
            2. 和弦分解式
            3. 力度中等偏强 (80-100)
            4. 节奏灵活（与其他乐器互补）

    generate_brass(chords, key, mode, start_beat, end_beat,
                   brass_mode: BrassMode = STABS) -> list[Note]:

        _stabs(chords) -> list[Note]:
            # 短音型打击
            1. 在重拍位置放置短促和弦音
            2. duration = 0.25-0.5，velocity 强 (100-120)
            3. 节奏与鼓组呼应

        _sustained(chords) -> list[Note]:
            # 持续音
            类似 strings_sustained 但力度更强
            渐强/渐弱（velocity 曲线）

        _fanfare(chords, key, mode) -> list[Note]:
            # 号角式
            1. 短小有力的旋律片段
            2. 以和弦音为主（根音、五度、八度）
            3. 附点节奏特征
            4. velocity 强 (110-127)

        _solo_line(chords, key, mode) -> list[Note]:
            # 铜管独奏旋律
            类似 MelodyGenerator 但铜管音域 + 大跳音程更多

    generate_woodwinds(chords, key, mode, start_beat, end_beat,
                       woodwinds_mode) -> list[Note]:

        _stabs / _sustained / _solo_line: 类似 brass 但音域更高、力度更轻

        _trill(chords, key, mode) -> list[Note]:
            # 颤音
            1. 在长音处交替两个相邻音阶音
            2. 速度: 32 分音符交替
            3. 常用于乐句结尾或高潮

    generate_synth(chords, key, mode, start_beat, end_beat,
                   synth_mode: SynthMode = PAD) -> list[Note]:

        _pad(chords) -> list[Note]:
            # 铺底
            类似 strings_sustained
            和弦长音 + 慢渐入 (velocity ramp)

        _lead(chords, key, mode) -> list[Note]:
            # 合成器主奏
            类似 MelodyGenerator 但 velocity 更均匀
            音域宽，允许大跳

        _arp(chords) -> list[Note]:
            # 琶音器
            1. 取和弦音
            2. 按模式排列: up / down / up-down / random
            3. 以 16 分或 8 分音符速度循环
            4. velocity 带微弱起伏

        _fx(chords, start_beat, end_beat) -> list[Note]:
            # 音效
            1. 上升扫描: pitch 从低到高渐变
            2. 下降扫描: pitch 从高到低
            3. 噪音突刺: 随机 pitch + 短 duration
            4. 适用于过渡/段落连接

    generate_piano_part(chords, key, mode, start_beat, end_beat,
                        piano_mode: PianoMode = BLOCK_CHORDS) -> list[Note]:

        _block_chords(chords) -> list[Note]:
            # 柱式和弦
            同时弹奏和弦所有音（3-4 音）
            每和弦一次或每拍一次

        _broken_chords(chords) -> list[Note]:
            # 分解和弦
            和弦音逐个弹奏（低→高 或 高→低）
            每拍 2-4 个音

        _arpeggio(chords) -> list[Note]:
            # 琶音
            类似 synth_arp 但在钢琴音域
            上行/下行/混合模式

        _comping(chords) -> list[Note]:
            # 爵士即兴伴奏
            1. 和弦声位(voicing)变化
            2. 切分节奏
            3. 力度变化
            4. 留白（不是每拍都弹）

    generate_guitar_part(chords, key, mode, start_beat, end_beat,
                         guitar_mode: GuitarMode = STRUM) -> list[Note]:

        _strum(chords) -> list[Note]:
            # 扫弦
            1. 和弦所有音略有时差（模拟手指扫过）
            2. 下扫(低→高) / 上扫(高→低)
            3. 节奏模式: 下-下-上-下-上-下-上-上 等
            4. 闷音/延音交替

        _fingerpick(chords) -> list[Note]:
            # 指弹
            1. 低音(拇指) + 高音(食/中/无名指) 分层
            2. 低音跟随 bass 线
            3. 高音走和弦分解
            4. 典型模式: Travis Picking

        _arpeggio(chords) -> list[Note]:
            # 琶音分解
            类似 piano_arpeggio 但限制在吉他音域
            更多使用开放弦音域

        _muted(chords) -> list[Note]:
            # 闷音
            1. 短促音符 (duration 0.1-0.2)
            2. velocity 中等 (60-80)
            3. 节奏密集（16 分或 8 分）
            4. pitch = 和弦根音为主
```

#### ArrangementEngine (generators/arrangement_engine.py)

```
class ArrangementEngine:
    """编曲智能控制 — 批量修改多轨的高级操作"""

    increase_energy(song, section_id, amount=0.5) -> Song:
        对 section 范围内的所有 track:
        1. 提升 velocity（amount × 20）
        2. 如果 amount > 0.5: 添加缺失的乐器层（推荐顺序: drums > bass > strings > brass）
        3. 如果 amount > 0.7: 加密度（插入经过音/装饰音）
        返回修改后的 Song

    decrease_energy(song, section_id, amount=0.5) -> Song:
        1. 降低 velocity
        2. 如果 amount > 0.5: mute 非核心轨（strings, brass, fx 先 mute）
        3. 如果 amount > 0.7: 简化音符（移除装饰音）

    increase_density(song, section_id, amount=0.5) -> Song:
        1. 对所有有音符的 track:
           - 在长音间隙插入经过音
           - 将长音拆为重复短音
           - amount 控制插入比例

    decrease_density(song, section_id, amount=0.5) -> Song:
        1. 合并相邻短音符为长音
        2. 移除装饰音/经过音
        3. 保留骨架（强拍和弦音）

    add_layer(song, section_id, instrument_type?) -> Song:
        1. 如果指定 instrument_type → 创建该乐器 Track
        2. 否则 → 智能推荐:
           分析已有 tracks → 推荐缺失的乐器
           推荐优先级: drums > bass > piano > strings > synth_pad
        3. 自动调用对应 Generator 生成音符
        4. 返回新增 Track 后的 Song

    remove_layer(song, section_id, track_id) -> Song:
        1. 移除指定 track 在 section 范围内的所有音符
        2. 如果整个 track 无音符 → 可选删除 track

    build_up(song, target_beat, build_beats=4) -> Song:
        从 target_beat - build_beats 到 target_beat 渐进:
        1. Drums: 加 snare roll (16分音符) + crescendo
        2. Bass: 上行音阶连接
        3. 其他: velocity 线性递增
        4. 最后 1 拍加 cymbal swell
        适用于 Chorus 前/Drop 前

    break_down(song, section_id) -> Song:
        1. 保留 1-2 个核心 track (通常 melody + piano 或 melody + pad)
        2. mute 其他所有 track
        3. 降低保留 track 的 velocity
        适用于 Bridge、Breakdown 段

    add_transition(song, from_section_id, to_section_id) -> Song:
        1. 在两段之间（最后 2 拍 + 最初 2 拍）:
           - Drums: fill
           - Bass: 经过音连接
           - Crash: 新段落第一拍
           - Strings/Synth: 尾音延长到新段
        2. 自动根据能量差选择过渡类型

    add_fill(song, section_id, beat_position) -> Song:
        1. 对所有有音符的 track 在 beat_position 附近添加 fill:
           - Drums: drum fill
           - Bass: bass fill (快速音阶连接)
           - 其他: 维持原样或加装饰

    add_silence(song, section_id, track_id?) -> Song:
        1. 如果指定 track_id: 清除该 track 在 section 的音符
        2. 否则: 清除 section 内所有音符（全段静默）
```

#### Phase 5 Command 清单

| 分类 | Command | 参数 |
|------|---------|------|
| Instrument | GenerateStringsCommand | track_id?, section_id?, strings_mode |
| Instrument | GenerateBrassCommand | track_id?, section_id?, brass_mode |
| Instrument | GenerateWoodwindsCommand | track_id?, section_id?, woodwinds_mode |
| Instrument | GenerateSynthCommand | track_id?, section_id?, synth_mode |
| Instrument | GeneratePianoPartCommand | track_id?, section_id?, piano_mode |
| Instrument | GenerateGuitarPartCommand | track_id?, section_id?, guitar_mode |
| Arrangement | IncreaseEnergyCommand | section_id, amount |
| Arrangement | DecreaseEnergyCommand | section_id, amount |
| Arrangement | IncreaseDensityCommand | section_id, amount |
| Arrangement | DecreaseDensityCommand | section_id, amount |
| Arrangement | AddLayerCommand | section_id, instrument_type? |
| Arrangement | RemoveLayerCommand | section_id, track_id |
| Arrangement | BuildUpCommand | target_beat, build_beats |
| Arrangement | BreakDownCommand | section_id |
| Arrangement | AddTransitionCommand | from_section_id, to_section_id |
| Arrangement | AddFillCommand | section_id, beat_position |
| Arrangement | AddSilenceCommand | section_id, track_id? |
| Track | SetTrackOctaveCommand | track_id, octave_offset |
| Track | SetTrackDensityCommand | track_id, density |
| Track | SetTrackEnergyCommand | track_id, energy |

#### Pipeline 阶段评估更新

Phase 5 完成后，Arrangement 阶段的建议 Tools 更新:
```
Arrangement 推荐 Tools 追加:
    generate_strings, generate_brass, generate_woodwinds, generate_synth,
    generate_piano_part, generate_guitar_part,
    increase_energy, decrease_energy, add_layer, build_up, add_transition
```

出口条件不变（至少 4 轨有音符），但引导信息增强：建议使用扩展乐器丰富编配。

### 5.13 Phase 6 人性化与风格设计

#### 新增枚举 (models/enums.py)

```
HumanizeType(str, Enum):
    TIMING_RANDOM, VELOCITY_RANDOM, MICRO_TIMING, GROOVE,
    SWING, PUSH, PULL, HAND_PLAYED

GrooveName(str, Enum):
    STRAIGHT, SWING_LIGHT, SWING_HEAVY, FUNK, BOSSA,
    SHUFFLE, HUMAN_PIANO, HUMAN_GUITAR, HUMAN_DRUMS, LAID_BACK

StylePreset(str, Enum):
    ANIME, CITY_POP, JAZZ, ROCK, METAL, EDM, LOFI,
    CLASSICAL, ORCHESTRA, GAME_MUSIC, AMBIENT, SYNTHWAVE, FUTURE_BASS
```

#### GlobalSettings 模型变更

```
GlobalSettings 新增字段:
    swing: float = 0.0            # 全局摇摆 (0.0 - 1.0)
    groove: str = "straight"      # 全局 Groove 模板名
    style: str = ""               # 当前风格标签（空=未设置）
    mood: str = ""                # 当前情绪标签
```

#### Groove 模板数据结构 (generators/humanize_engine.py)

```
# 每个 Groove 模板定义每拍子分位(sub-beat)的 timing 和 velocity 偏移
# 一个 4/4 拍 bar 有 16 个 16 分音符位置 (index 0-15)

GrooveTemplate = {
    "timing_offsets": list[float],    # 16 个位置的 timing 偏移（beat 单位）
    "velocity_offsets": list[int],    # 16 个位置的 velocity 偏移
}

GROOVE_TEMPLATES = {
    "straight": {
        "timing_offsets":  [0]*16,
        "velocity_offsets": [0]*16,
    },
    "swing_light": {
        "timing_offsets":  [0,0, 0.04,0, 0,0, 0.04,0, 0,0, 0.04,0, 0,0, 0.04,0],
        "velocity_offsets": [0,0, -5,0, 0,0, -5,0, 0,0, -5,0, 0,0, -5,0],
    },
    "swing_heavy": {
        "timing_offsets":  [0,0, 0.08,0, 0,0, 0.08,0, 0,0, 0.08,0, 0,0, 0.08,0],
        "velocity_offsets": [0,0, -10,0, 0,0, -10,0, 0,0, -10,0, 0,0, -10,0],
    },
    "funk": {
        "timing_offsets":  [0,0.02, -0.02,0.03, 0,-0.02, 0.02,0, 0,0.02, -0.02,0.03, 0,-0.02, 0.02,0],
        "velocity_offsets": [5,-3, 3,-5, 5,-3, 3,-5, 5,-3, 3,-5, 5,-3, 3,-5],
    },
    "bossa": {
        "timing_offsets":  [0,0, 0.03,0, -0.02,0, 0.03,0, 0,0, 0.03,0, -0.02,0, 0.03,0],
        "velocity_offsets": [3,-2, 0,-3, 3,-2, 0,-3, 3,-2, 0,-3, 3,-2, 0,-3],
    },
    "shuffle": {
        "timing_offsets":  [0,0, 0.1,0, 0,0, 0.1,0, 0,0, 0.1,0, 0,0, 0.1,0],
        "velocity_offsets": [0,0, -8,0, 0,0, -8,0, 0,0, -8,0, 0,0, -8,0],
    },
    "human_piano": 随机化(timing ±0.02, velocity ±5),
    "human_guitar": 随机化(timing ±0.03, velocity ±7),
    "human_drums": 随机化(timing ±0.015, velocity ±10),
    "laid_back": 全局偏移(timing +0.03, velocity -5),
}
```

#### HumanizeEngine (generators/humanize_engine.py)

```
class HumanizeEngine:
    """直接修改 Note 的 start_beat / velocity / duration_beat"""

    humanize_timing(notes, amount=0.5, start_beat?, end_beat?) -> list[Note]:
        max_offset = amount * 0.05         # 最大偏移 0.05 beat ≈ 30ms @120BPM
        for note in notes (在范围内):
            note.start_beat += random.uniform(-max_offset, max_offset)
            确保 start_beat >= 0
        返回修改后的 notes

    humanize_velocity(notes, amount=0.5, start_beat?, end_beat?) -> list[Note]:
        max_offset = int(amount * 15)      # 最大偏移 ±15
        for note in notes:
            note.velocity += random.randint(-max_offset, max_offset)
            clamp(note.velocity, 1, 127)
        返回 notes

    apply_micro_timing(notes, beat_offsets: dict[float, float]) -> list[Note]:
        # beat_offsets = { 拍位: 偏移量 }，如 { 1.0: 0.03, 3.0: -0.02 }
        for note in notes:
            for target_beat, offset in beat_offsets:
                if abs(note.start_beat % beats_per_bar - target_beat) < 0.01:
                    note.start_beat += offset
        返回 notes

    apply_groove(notes, groove_name, start_beat?, end_beat?) -> list[Note]:
        template = GROOVE_TEMPLATES[groove_name]
        beats_per_bar = 4  # 默认 4/4
        for note in notes:
            bar_pos = note.start_beat % beats_per_bar
            sub_beat_index = round(bar_pos / 0.25) % 16
            note.start_beat += template.timing_offsets[sub_beat_index]
            note.velocity += template.velocity_offsets[sub_beat_index]
            clamp(note.velocity, 1, 127)
        返回 notes

    apply_swing(notes, swing_amount, start_beat?, end_beat?) -> list[Note]:
        # 将弱拍(偶数8分音符位)延迟
        delay = swing_amount * 0.1         # 最大延迟 0.1 beat
        for note in notes:
            bar_pos = note.start_beat % beats_per_bar
            eighth_pos = round(bar_pos / 0.5)
            if eighth_pos % 2 == 1:        # 弱拍
                note.start_beat += delay
        返回 notes

    push_timing(notes, amount, start_beat?, end_beat?) -> list[Note]:
        offset = -(amount * 0.05)          # 提前，负偏移
        for note in notes:
            note.start_beat += offset
            确保 start_beat >= 0
        返回 notes

    pull_timing(notes, amount, start_beat?, end_beat?) -> list[Note]:
        offset = amount * 0.05             # 推迟，正偏移
        for note in notes:
            note.start_beat += offset
        返回 notes

    hand_played_feel(notes, intensity, start_beat?, end_beat?) -> list[Note]:
        # 综合 timing + velocity + duration 随机化
        t_max = intensity * 0.04
        v_max = int(intensity * 10)
        d_factor = intensity * 0.1
        for note in notes:
            note.start_beat += random.uniform(-t_max, t_max)
            note.velocity += random.randint(-v_max, v_max)
            note.duration_beat *= random.uniform(1 - d_factor, 1 + d_factor)
            clamp(velocity, 1, 127)
            确保 start_beat >= 0, duration > 0
        返回 notes
```

#### StyleEngine (generators/style_engine.py)

```
# 每个风格预设的完整配置
STYLE_PRESETS = {
    "anime": {
        "recommended_instruments": [PIANO, STRINGS, DRUMS, BASS, SYNTH],
        "chord_templates": ["royal_road", "komuro", "just_the_two"],
        "tempo_range": (130, 170),
        "time_signature": (4, 4),
        "drum_style": DrumStyle.ANIME,
        "bass_mode": BassMode.ROOT,
        "humanize_preset": "straight",
        "energy_curve": {"intro":0.3, "verse":0.5, "chorus":0.8, "bridge":0.4, "outro":0.3},
        "velocity_range": (70, 110),
        "swing": 0.0,
    },
    "city_pop": {
        "recommended_instruments": [GUITAR, BASS, SYNTH, DRUMS, PIANO],
        "chord_templates": ["jazz_turnaround"],
        "tempo_range": (100, 130),
        "drum_style": DrumStyle.POP,
        "bass_mode": BassMode.WALKING,
        "humanize_preset": "funk",
        "energy_curve": {"intro":0.4, "verse":0.5, "chorus":0.6, "bridge":0.5, "outro":0.4},
        "velocity_range": (60, 100),
        "swing": 0.2,
    },
    # jazz / rock / metal / edm / lofi / classical / orchestra /
    # game_music / ambient / synthwave / future_bass 同理...
    # 省略其余 11 种，结构相同
}

class StyleEngine:

    set_style(song, style_name: str) -> dict:
        """设置风格预设，返回建议操作而非直接修改音符"""
        preset = STYLE_PRESETS[style_name]
        song.global_settings.style = style_name
        # 自动应用数值型设置
        song.global_settings.swing = preset["swing"]
        song.global_settings.groove = preset["humanize_preset"]
        # 返回建议（不自动创建轨道，由 AI 决定）
        return {
            "style": style_name,
            "applied": {
                "swing": preset["swing"],
                "groove": preset["humanize_preset"],
            },
            "suggestions": {
                "recommended_instruments": preset["recommended_instruments"],
                "chord_templates": preset["chord_templates"],
                "tempo_range": preset["tempo_range"],
                "drum_style": preset["drum_style"].value,
                "bass_mode": preset["bass_mode"].value,
                "energy_curve": preset["energy_curve"],
                "velocity_range": preset["velocity_range"],
            },
        }

    mix_styles(song, style_a: str, style_b: str, weight_a: float = 0.5) -> dict:
        """混合两种风格，返回融合后的建议"""
        preset_a = STYLE_PRESETS[style_a]
        preset_b = STYLE_PRESETS[style_b]
        weight_b = 1.0 - weight_a

        # 数值型加权平均
        mixed_tempo = (avg(preset_a.tempo_range) * weight_a +
                       avg(preset_b.tempo_range) * weight_b)
        mixed_swing = preset_a.swing * weight_a + preset_b.swing * weight_b
        mixed_velocity = 加权平均(velocity_range)

        # 离散型: 按权重选择
        instruments = 合并去重(preset_a.instruments * weight_a优先 +
                              preset_b.instruments)
        drum_style = preset_a.drum_style if weight_a >= 0.5 else preset_b.drum_style
        humanize = preset_a.humanize if weight_a >= 0.5 else preset_b.humanize

        song.global_settings.style = f"{style_a}+{style_b}"
        song.global_settings.swing = mixed_swing
        # 返回混合建议
        return { "mixed": True, "styles": [style_a, style_b], "weights": [...], "suggestions": {...} }

    get_style_guide(song) -> dict:
        """获取当前风格的建议操作清单"""
        if not song.global_settings.style:
            return {"message": "No style set. Use set_style first."}
        style = song.global_settings.style
        preset = STYLE_PRESETS.get(style)
        # 分析当前 song 状态 vs 风格建议的差距
        missing_instruments = [i for i in preset.instruments if i not in current_instruments]
        tempo_ok = preset.tempo_range[0] <= song.tempo <= preset.tempo_range[1]
        return {
            "style": style,
            "status": { "tempo_ok", "instruments_ok", "chords_ok", ... },
            "missing": missing_instruments,
            "next_actions": ["Add drums track", "Set tempo to 140", ...],
        }
```

#### Phase 6 Command 清单

| 分类 | Command | 参数 |
|------|---------|------|
| Humanize | HumanizeTimingCommand | track_id, amount, section_id? |
| Humanize | HumanizeVelocityCommand | track_id, amount, section_id? |
| Humanize | ApplyMicroTimingCommand | track_id, beat_offsets |
| Humanize | ApplyGrooveCommand | track_id, groove_name, section_id? |
| Humanize | ApplySwingCommand | track_id?, swing_amount, section_id? |
| Humanize | PushTimingCommand | track_id, amount, section_id? |
| Humanize | PullTimingCommand | track_id, amount, section_id? |
| Humanize | HandPlayedFeelCommand | track_id, intensity, section_id? |
| Style | SetStyleCommand | style_name |
| Style | MixStylesCommand | style_a, style_b, weight_a |
| Style | SetMoodCommand | mood |
| Style | SetSwingCommand | swing_amount |
| Style | SetGrooveCommand | groove_name |

> `GetStyleGuideCommand` 不需要 — `get_style_guide` 是只读查询，直接在 MCP Tool 中调用 StyleEngine，无需 Command。

#### Pipeline 阶段评估更新

Phase 6 完成后，Production 阶段建议 Tools 更新：
```
Production 推荐 Tools 追加:
    humanize_timing, humanize_velocity, apply_groove, apply_swing,
    hand_played_feel, set_style, mix_styles, set_mood, set_swing, set_groove
```

出口条件不变（Production 阶段无硬性条件，由用户/AI 决定）。

### 5.14 Phase 7 分析引擎设计

#### 新增数据模型 (models/analysis.py)

```
class AnalysisResult(BaseModel):
    """通用分析结果容器"""
    type: str                           # 分析类型 ("key", "tempo", "chord" 等)
    data: dict                          # 分析数据（各类型结构不同）
    timestamp: datetime                 # 分析时间
    track_id: str | None = None         # 针对特定 track 的分析（None=全局）

class Phrase(BaseModel):
    start_beat: float
    end_beat: float

class Motif(BaseModel):
    pitches: list[int]                  # 音高序列
    rhythm: list[float]                 # 节奏序列（duration_beat 列表）
    occurrences: list[float]            # 出现位置（start_beat 列表）

class RhythmProfile(BaseModel):
    dominant_value: float               # 主导音符时值（如 0.5=八分）
    syncopation_ratio: float            # 切分音比例 (0-1)
    complexity: float                   # 节奏复杂度 (0-100)

class VoiceLeadingIssue(BaseModel):
    beat: float
    type: str                           # "parallel_fifth", "parallel_octave", etc.
    description: str
    track_a: str                        # track_id
    track_b: str

class CounterpointReport(BaseModel):
    parallel_ratio: float               # 平行运动比例
    contrary_ratio: float               # 反向运动比例
    oblique_ratio: float                # 斜向运动比例
    similar_ratio: float                # 同向运动比例
    issues: list[VoiceLeadingIssue]

class StyleMatch(BaseModel):
    style: str                          # 最匹配的风格名
    confidence: float                   # 置信度 (0-100)
    scores: dict[str, float]            # 各风格的匹配分

class MoodProfile(BaseModel):
    valence: float                      # 情感效价 (-1=悲伤, +1=欢快)
    arousal: float                      # 激活度 (-1=平静, +1=激动)
    tags: list[str]                     # 情绪标签 ["happy", "energetic", ...]

class DynamicProfile(BaseModel):
    velocity_range: tuple[int, int]     # (min, max)
    avg_velocity: float
    contour: list[tuple[float, float]]  # [(beat, avg_velocity_at_beat), ...]

class StructureSegment(BaseModel):
    type: str                           # "verse", "chorus", etc.
    start_beat: float
    end_beat: float
    similarity_to: list[str]            # 与哪些段相似（section_id 列表）
```

#### Song 模型变更

```
Song 新增字段:
    analysis_cache: dict[str, AnalysisResult] = {}
    # key 格式: "{analysis_type}" 或 "{analysis_type}:{track_id}"
```

#### AnalysisEngine (generators/analysis_engine.py)

```
class AnalysisEngine:
    """18 种分析功能的入口。所有方法均为纯函数（只读 Song 数据）。"""

    # ---- 缓存管理 ----

    _cache_key(analysis_type, track_id=None) -> str:
        if track_id:
            return f"{analysis_type}:{track_id}"
        return analysis_type

    _get_cached(song, analysis_type, track_id=None) -> AnalysisResult | None:
        key = _cache_key(analysis_type, track_id)
        return song.analysis_cache.get(key)

    _set_cache(song, result: AnalysisResult) -> None:
        key = _cache_key(result.type, result.track_id)
        song.analysis_cache[key] = result

    invalidate_cache(song) -> None:
        """Command 执行后调用，清空全部缓存"""
        song.analysis_cache.clear()

    # ---- 18 种分析 ----

    analyze_key(song) -> dict:
        """调性检测：基于 Krumhansl-Schmuckler 算法简化版"""
        1. 统计所有音符的 pitch_class 分布（12 维直方图）
        2. 与 24 个调性模板（12 key × major/minor）做相关系数
        3. 返回 { "key": 相关最高的调, "mode": major/minor,
                 "confidence": 最高相关系数 * 100, "alternatives": 前 3 候选 }

    analyze_tempo(song) -> dict:
        """速度稳定性分析"""
        1. 分析所有音符的 onset 间隔
        2. 计算 IOI (Inter-Onset Interval) 的标准差
        3. stability = 1 - (std / mean) * 100
        返回 { "bpm": song.global_settings.tempo,
               "stability": stability%,
               "detected_bpm": 从 IOI 推算的 BPM }

    analyze_chords(song, track_id) -> dict:
        """从音符推断和弦"""
        1. 按 beat 切片（每拍或每半拍）
        2. 取每个切片内的 pitch_class 集合
        3. 与 CHORD_INTERVALS 匹配，选择最佳匹配
        4. 合并相邻相同和弦
        返回 { "chords": [{ "root", "quality", "start_beat", "duration_beat" }, ...] }

    analyze_phrases(song, track_id) -> dict:
        """乐句边界检测"""
        1. 检测音符间的间隙（duration gap > 阈值 = 乐句边界）
        2. 长音后的大跳(>P5) = 乐句边界
        3. 节奏密度突变 = 乐句边界
        返回 { "phrases": [{ "start_beat", "end_beat", "note_count" }, ...] }

    analyze_motifs(song, track_id) -> dict:
        """动机识别：滑动窗口 + 音程序列匹配"""
        1. 将旋律转为音程序列 (intervals)
        2. 滑动窗口(3-8 音)扫描所有子序列
        3. 统计相似子序列出现次数（允许移调匹配: 比较 interval 而非 pitch）
        4. 出现 >= 2 次的子序列 = motif
        返回 { "motifs": [{ "pitches", "rhythm", "occurrences", "count" }, ...] }

    analyze_rhythm(song, track_id) -> dict:
        """节奏模式分析"""
        1. 统计各音符时值分布
        2. dominant_value = 占比最高的时值
        3. 检测切分音: start_beat 不在整拍上的比例
        4. complexity = 基于时值种类数 + 切分比 + 附点比 计算
        返回 { "dominant_value", "syncopation_ratio", "complexity",
               "distribution": { 0.25: 15%, 0.5: 40%, 1.0: 30%, ... } }

    analyze_density(song, track_id?) -> dict:
        """密度分布图"""
        1. 按 beat 或按 bar 统计音符数量
        2. 可针对单轨或全局
        返回 { "resolution": "beat", "data": [(beat, note_count), ...],
               "avg": 平均密度, "max": 最高密度 }

    analyze_energy(song) -> dict:
        """能量曲线：综合密度 + 力度 + 音高"""
        1. 按 bar 统计: energy = w1*密度 + w2*平均velocity + w3*平均pitch
        2. 归一化到 0-1
        返回 { "curve": [(bar, energy_level), ...],
               "avg": 平均能量, "peak_bar": 最高能量位置 }

    analyze_range(song, track_id) -> dict:
        """音域分析"""
        1. 统计 min/max/avg pitch
        2. span = max - min (半音数)
        3. 与乐器标准音域比较
        返回 { "lowest": pitch, "highest": pitch, "span": semitones,
               "avg": 平均音高, "in_standard_range": bool }

    analyze_repetition(song, track_id) -> dict:
        """重复模式检测"""
        1. 按 bar 提取音符 pattern（pitch + rhythm 指纹）
        2. 比较所有 bar pair，相似度 > 阈值 = 重复
        3. 统计重复组
        返回 { "patterns": [{ "pattern_id", "bar_indices", "count" }, ...],
               "repetition_rate": 重复 bar 占比 }

    analyze_voice_leading(song) -> dict:
        """声部进行检查"""
        1. 取所有非打击乐 track 的两两组合
        2. 逐拍分析两声部的音程关系
        3. 检测: 平行五度/八度, 隐伏五度/八度, 声部交错
        返回 { "issues": [{ "beat", "type", "description", "tracks" }, ...],
               "issue_count": N, "severity": "low"|"medium"|"high" }

    analyze_cadences(song) -> dict:
        """终止式检测"""
        1. 分析 chord_progression
        2. 在每个 section 末尾检测和弦模式:
           V→I = authentic, IV→I = plagal, →V = half, V→vi = deceptive
        返回 { "cadences": [{ "beat", "type", "section_id" }, ...] }

    analyze_counterpoint(song, track_id_a, track_id_b) -> dict:
        """对位法分析"""
        1. 逐拍提取两 track 的旋律走向 (上行/下行/持续)
        2. 分类: 平行(同向同程)/同向(同向不同程)/反向/斜向
        3. 统计各类型比例
        返回 CounterpointReport 序列化

    analyze_style(song) -> dict:
        """风格识别"""
        1. 提取特征向量: 乐器组合 + 和弦复杂度 + 节奏模式 + 速度 + 力度范围
        2. 与 STYLE_PRESETS 的特征做相似度匹配
        返回 { "style": 最匹配风格, "confidence": %,
               "scores": { "rock": 80, "pop": 60, ... } }

    analyze_mood(song) -> dict:
        """情绪检测"""
        1. valence: major=+, minor=-, 高音域=+, 低音域=-
        2. arousal: 快tempo=+, 高velocity=+, 高density=+
        3. 映射到情绪标签
        返回 { "valence", "arousal", "tags": ["happy", "energetic", ...] }

    analyze_complexity(song, track_id?) -> dict:
        """复杂度评分"""
        维度:
        - 音高复杂度: 不同 pitch_class 数 + 平均音程大小
        - 节奏复杂度: 时值种类 + 切分比 + 连音比
        - 和声复杂度: 和弦种类 + 非自然音和弦比 + 转调次数
        - 结构复杂度: section 种类数 + track 数
        score = 加权综合 (0-100)
        返回 { "total": score, "pitch": N, "rhythm": N, "harmony": N, "structure": N }

    analyze_dynamics(song, track_id?) -> dict:
        """力度变化分析"""
        1. 统计 velocity: min, max, avg, std
        2. 按 bar 计算 velocity 曲线
        3. 检测渐强(crescendo)/渐弱(decrescendo) 段
        返回 { "range": (min,max), "avg": N, "contour": [(bar, avg_vel), ...],
               "crescendos": [...], "decrescendos": [...] }

    analyze_structure(song) -> dict:
        """曲式结构分析"""
        1. 基于 sections 信息 + 音符内容相似度
        2. 相似度: 两 section 范围内音符指纹的相关系数
        3. 识别: ABA, AABB, ABAB, Verse-Chorus 等模式
        返回 { "segments": [{ "type", "start_beat", "end_beat", "similar_to" }, ...],
               "form": "ABA" | "AABB" | "Verse-Chorus" | "Through-composed" }

    # ---- 综合报告 ----

    get_full_analysis(song) -> dict:
        """生成全维度分析报告"""
        report = {}
        report["key"] = analyze_key(song)
        report["tempo"] = analyze_tempo(song)
        report["energy"] = analyze_energy(song)
        report["density"] = analyze_density(song)
        report["complexity"] = analyze_complexity(song)
        report["structure"] = analyze_structure(song)
        report["dynamics"] = analyze_dynamics(song)
        report["mood"] = analyze_mood(song)
        if song.chord_progression:
            report["cadences"] = analyze_cadences(song)
        for track in song.tracks:
            report[f"range_{track.id}"] = analyze_range(song, track.id)
        return report
```

#### 缓存失效策略

```
# 在 Composer.execute() 中，Command 执行后清空缓存:

class Composer:
    execute(command):
        before = song.deep_copy()
        song = command.execute(song)
        # Phase 7: 任何修改都清空分析缓存
        song.analysis_cache.clear()
        history.push(command, before)
        pipeline.evaluate(song)
        return song
```

> **设计决策**：采用最简单的缓存失效策略（全清），避免复杂的依赖追踪。未来可优化为按 analysis_type 和修改的 track_id 精细失效。

#### Phase 7 Command 清单

| 分类 | Command | 参数 |
|------|---------|------|
| Analysis | AnalyzeKeyCommand | — |
| Analysis | AnalyzeTempoCommand | — |
| Analysis | AnalyzeChordsCommand | track_id |
| Analysis | AnalyzePhrasesCommand | track_id |
| Analysis | AnalyzeMotifsCommand | track_id |
| Analysis | AnalyzeRhythmCommand | track_id |
| Analysis | AnalyzeDensityCommand | track_id? |
| Analysis | AnalyzeEnergyCommand | — |
| Analysis | AnalyzeRangeCommand | track_id |
| Analysis | AnalyzeRepetitionCommand | track_id |
| Analysis | AnalyzeVoiceLeadingCommand | — |
| Analysis | AnalyzeCadencesCommand | — |
| Analysis | AnalyzeCounterpointCommand | track_id_a, track_id_b |
| Analysis | AnalyzeStyleCommand | — |
| Analysis | AnalyzeMoodCommand | — |
| Analysis | AnalyzeComplexityCommand | track_id? |
| Analysis | AnalyzeDynamicsCommand | track_id? |
| Analysis | AnalyzeStructureCommand | — |
| Analysis | GetFullAnalysisCommand | — |

> **注意**：Analysis Commands 是只读操作，不修改 Song 数据。它们的 execute() 返回原始 song（不修改），但将结果缓存到 song.analysis_cache 中。History 不为只读 Command 保存快照（优化）。

#### Pipeline 阶段评估更新

Phase 7 完成后，所有阶段的建议 Tools 中追加分析工具：
```
所有阶段推荐 Tools 追加:
    analyze_key, analyze_energy, analyze_complexity, get_full_analysis
    （AI 可随时调用分析来辅助决策）
```

出口条件不变。分析功能是辅助工具，不构成出口条件。

### 5.15 Phase 8 Track 自动化设计

#### 新增枚举与模型 (models/enums.py + models/automation.py)

```
AutomationParam(str, Enum):
    VOLUME = "volume"           # CC 7
    PAN = "pan"                 # CC 10
    EXPRESSION = "expression"   # CC 11
    MODULATION = "modulation"   # CC 1
    SUSTAIN = "sustain"         # CC 64

# CC 编号映射
AUTOMATION_CC = {
    "volume": 7,
    "pan": 10,
    "expression": 11,
    "modulation": 1,
    "sustain": 64,
}
```

```
class AutomationPoint(BaseModel):
    """单个控制点"""
    beat: float               # 时间位置（beat 单位）
    value: int                # 参数值 (0-127)

class AutomationCurve(BaseModel):
    """自动化曲线 — 一个参数的完整曲线"""
    param: AutomationParam
    points: list[AutomationPoint] = []

    get_value_at(beat) -> int | None:
        """线性插值：在指定 beat 位置获取值"""
        if not points: return None
        sorted_pts = sorted(points, key=lambda p: p.beat)
        if beat <= sorted_pts[0].beat: return sorted_pts[0].value
        if beat >= sorted_pts[-1].beat: return sorted_pts[-1].value
        # 二分查找相邻两点 → 线性插值
        for i in range(len(sorted_pts) - 1):
            if sorted_pts[i].beat <= beat <= sorted_pts[i+1].beat:
                ratio = (beat - sorted_pts[i].beat) / (sorted_pts[i+1].beat - sorted_pts[i].beat)
                return round(sorted_pts[i].value + ratio * (sorted_pts[i+1].value - sorted_pts[i].value))

class Marker(BaseModel):
    """时间轴标记"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    beat: float
    label: str
    color: str = ""
```

#### Track / Song 模型变更

```
Track 新增字段:
    automation: list[AutomationCurve] = []

Song 新增字段:
    markers: list[Marker] = []
```

#### AutomationEngine (generators/automation_engine.py)

```
# 预设自动化模板
AUTOMATION_PRESETS = {
    "fade_in": {
        "param": "volume",
        "curve": lambda start, end, track_vol:
            [(start, 0), (end, track_vol or 100)],
    },
    "fade_out": {
        "param": "volume",
        "curve": lambda start, end, track_vol:
            [(start, track_vol or 100), (end, 0)],
    },
    "crescendo": {
        "param": "expression",
        "curve": lambda start, end, _:
            [(start, 40), (end, 120)],
    },
    "decrescendo": {
        "param": "expression",
        "curve": lambda start, end, _:
            [(start, 120), (end, 40)],
    },
    "pan_sweep_lr": {
        "param": "pan",
        "curve": lambda start, end, _:
            [(start, 0), (end, 127)],
    },
    "pan_sweep_rl": {
        "param": "pan",
        "curve": lambda start, end, _:
            [(start, 127), (end, 0)],
    },
    "swell": {
        "param": "expression",
        "curve": lambda start, end, _:
            [(start, 40), ((start+end)/2, 120), (end, 40)],
    },
}

class AutomationEngine:

    add_automation(track, param, points: list[(beat, value)]) -> None:
        """添加/替换自动化曲线"""
        # 查找已有同 param 的曲线，替换；否则新建
        curve = AutomationCurve(param=param, points=[AutomationPoint(b, v) for b, v in points])
        移除 track.automation 中同 param 的旧曲线
        track.automation.append(curve)

    remove_automation(track, param) -> None:
        """移除指定参数的自动化曲线"""
        track.automation = [c for c in track.automation if c.param != param]

    add_point(track, param, beat, value) -> None:
        """向已有曲线添加控制点"""
        找到 param 对应的 curve
        如果不存在 → 创建新 curve
        curve.points.append(AutomationPoint(beat, value))
        按 beat 排序 points

    remove_point(track, param, point_index) -> None:
        """移除指定索引的控制点"""
        找到 param 对应的 curve
        del curve.points[point_index]

    apply_preset(track, preset_name, start_beat, end_beat) -> None:
        """应用预设自动化"""
        preset = AUTOMATION_PRESETS[preset_name]
        param = AutomationParam(preset["param"])
        point_data = preset["curve"](start_beat, end_beat, track.volume)
        add_automation(track, param, point_data)

    clear_all(track) -> None:
        """清除音轨所有自动化"""
        track.automation.clear()
```

#### MIDI 渲染器更新

```
MidiRenderer.render(song) 追加:
    对每个 track 的 automation curves:
        对每个 curve:
            cc_number = AUTOMATION_CC[curve.param.value]
            对每个相邻点对 → 按 16 分音符粒度插值（CC_INTERPOLATION_STEP = 0.25）
            → 线性插值生成 MIDI CC 事件
```

#### Phase 8 Command 清单

| 分类 | Command | 参数 |
|------|---------|------|
| Automation | AddAutomationCommand | track_id, param, points[] |
| Automation | RemoveAutomationCommand | track_id, param |
| Automation | AddAutomationPointCommand | track_id, param, beat, value |
| Automation | RemoveAutomationPointCommand | track_id, param, point_index |
| Automation | ApplyAutomationPresetCommand | track_id, preset_name, start_beat, end_beat |
| Automation | ClearAutomationCommand | track_id |
| Marker | AddMarkerCommand | beat, label, color? |
| Marker | RemoveMarkerCommand | marker_id |

> `list_markers` 是只读查询，不需要 Command。

#### Phase 8 MCP Tools 映射

```
MCP Tools (#129-#137):
    add_automation          → AddAutomationCommand
    remove_automation       → RemoveAutomationCommand
    add_automation_point    → AddAutomationPointCommand
    remove_automation_point → RemoveAutomationPointCommand
    apply_automation_preset → ApplyAutomationPresetCommand
    clear_automation        → ClearAutomationCommand
    add_marker              → AddMarkerCommand
    remove_marker           → RemoveMarkerCommand
    list_markers            → 直接查询 song.markers（只读）
```

### 5.16 Phase 9 插件架构设计

#### 新增枚举与模型

```
PluginType(str, Enum):
    GENERATOR = "generator"
    ANALYZER = "analyzer"
    PATTERN = "pattern"
    STYLE = "style"
    RENDERER = "renderer"

class PluginInfo(BaseModel):
    """插件元信息"""
    name: str
    version: str
    type: PluginType
    entry: str                  # 入口文件路径
    class_name: str             # 入口类名
    description: str = ""
    enabled: bool = True
```

#### 插件接口定义

```
# 所有插件必须实现的基类（ABC）

class GeneratorPlugin(ABC):
    """自定义生成器插件"""
    @abstractmethod
    def generate(self, chords, key, mode, start_beat, end_beat, **kwargs) -> list[Note]:
        ...

class AnalyzerPlugin(ABC):
    """自定义分析器插件"""
    @abstractmethod
    def analyze(self, song, **kwargs) -> dict:
        ...

class PatternPlugin(ABC):
    """自定义模式库插件"""
    @abstractmethod
    def get_pattern(self, style, **kwargs) -> list[Note]:
        ...

class StylePlugin(ABC):
    """自定义风格预设插件"""
    @abstractmethod
    def get_preset(self) -> dict:
        ...

class RendererPlugin(ABC):
    """自定义渲染器插件"""
    @abstractmethod
    def render(self, song, **kwargs) -> str | bytes:
        ...
```

#### PluginManager (plugins/plugin_manager.py)

```
class PluginManager:
    plugins_dir: Path = Path.home() / ".composer-engine" / "plugins"
    registry: dict[str, PluginInfo] = {}    # name → info
    instances: dict[str, object] = {}       # name → loaded plugin instance

    discover() -> list[PluginInfo]:
        """扫描 plugins_dir 下所有子目录"""
        for subdir in plugins_dir.iterdir():
            plugin_json = subdir / "plugin.json"
            if plugin_json.exists():
                info = PluginInfo.model_validate_json(plugin_json.read_text())
                registry[info.name] = info
        return list(registry.values())

    load(name) -> object:
        """按需加载插件实例"""
        info = registry[name]
        if name in instances:
            return instances[name]
        # importlib 动态加载
        spec = importlib.util.spec_from_file_location(
            info.name, plugins_dir / info.name / info.entry)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls = getattr(module, info.class_name)
        instance = cls()
        instances[name] = instance
        return instance

    enable(name) -> None:
        registry[name].enabled = True

    disable(name) -> None:
        registry[name].enabled = False
        if name in instances:
            del instances[name]

    reload() -> list[PluginInfo]:
        """重新扫描并清空加载缓存"""
        instances.clear()
        registry.clear()
        return discover()

    list_plugins() -> list[dict]:
        return [info.model_dump() for info in registry.values()]
```

#### Phase 9 Command 清单

Phase 9 的 MCP Tools 均为查询/管理类，不涉及 Song 修改，可不使用 Command 模式，直接在 MCP Tool 中调用 PluginManager。

#### Phase 9 MCP Tools 映射

```
MCP Tools (#138-#141):
    list_plugins    → PluginManager.list_plugins()
    enable_plugin   → PluginManager.enable(name)
    disable_plugin  → PluginManager.disable(name)
    reload_plugins  → PluginManager.reload()
```

### 5.17 Phase 10 MusicXML 导出设计

#### MusicXMLRenderer (renderer/musicxml_renderer.py)

```
class MusicXMLRenderer:
    """将 Song 转换为 MusicXML 格式"""

    # velocity → 力度标记映射
    VELOCITY_TO_DYNAMIC = [
        (0, 20, "ppp"), (21, 40, "pp"), (41, 55, "p"),
        (56, 70, "mp"), (71, 85, "mf"), (86, 100, "f"),
        (101, 115, "ff"), (116, 127, "fff"),
    ]

    # beat 时值 → MusicXML duration type 映射
    BEAT_TO_TYPE = [
        (4.0, "whole"), (3.0, "half", dotted=True),
        (2.0, "half"), (1.5, "quarter", dotted=True),
        (1.0, "quarter"), (0.75, "eighth", dotted=True),
        (0.5, "eighth"), (0.25, "16th"), (0.125, "32nd"),
    ]

    render(song) -> str:
        """生成完整 MusicXML 字符串"""
        root = ET.Element("score-partwise", version="4.0")

        # 1. Part list
        part_list = ET.SubElement(root, "part-list")
        for i, track in enumerate(tracks_to_render):
            score_part = ET.SubElement(part_list, "score-part", id=f"P{i+1}")
            ET.SubElement(score_part, "part-name").text = track.name

        # 2. 对每个 track → part
        for i, track in enumerate(tracks_to_render):
            part = ET.SubElement(root, "part", id=f"P{i+1}")

            # 3. 按小节切分音符
            beats_per_bar = song.global_settings.time_signature[0]
            total_beats = 计算歌曲总拍数
            measures = ceil(total_beats / beats_per_bar)

            for m in range(measures):
                measure = ET.SubElement(part, "measure", number=str(m+1))

                # 首小节写入 attributes
                if m == 0:
                    _write_attributes(measure, song)

                # 该小节内的音符
                bar_start = m * beats_per_bar
                bar_end = bar_start + beats_per_bar
                bar_notes = [n for n in track.notes
                             if bar_start <= n.start_beat < bar_end]

                # 排序 + 补休止符
                bar_notes.sort(key=lambda n: n.start_beat)
                current_beat = bar_start
                for note in bar_notes:
                    if note.start_beat > current_beat:
                        _write_rest(measure, note.start_beat - current_beat)
                    _write_note(measure, note, track.instrument == DRUMS)
                    current_beat = note.start_beat + note.duration_beat
                # 小节末补休止符
                if current_beat < bar_end:
                    _write_rest(measure, bar_end - current_beat)

        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    _write_attributes(measure, song):
        """写入调号、拍号、速度"""
        attrs = ET.SubElement(measure, "attributes")
        # divisions (每拍的最小单位数，通常 4 = 支持 16 分音符)
        ET.SubElement(attrs, "divisions").text = "4"
        # key
        key_el = ET.SubElement(attrs, "key")
        fifths = KEY_TO_FIFTHS[song.global_settings.key]
        ET.SubElement(key_el, "fifths").text = str(fifths)
        # time
        time_el = ET.SubElement(attrs, "time")
        ET.SubElement(time_el, "beats").text = str(song.global_settings.time_signature[0])
        ET.SubElement(time_el, "beat-type").text = str(song.global_settings.time_signature[1])
        # clef
        clef = ET.SubElement(attrs, "clef")
        ET.SubElement(clef, "sign").text = "G"
        ET.SubElement(clef, "line").text = "2"
        # direction (tempo)
        direction = ET.SubElement(measure, "direction")
        sound = ET.SubElement(direction, "sound", tempo=str(int(song.global_settings.tempo)))

    _write_note(measure, note, is_drum):
        """写入单个音符"""
        note_el = ET.SubElement(measure, "note")
        pitch_el = ET.SubElement(note_el, "pitch")
        if is_drum:
            # 打击乐使用 unpitched
            unpitched = ET.SubElement(note_el, "unpitched")
            ET.SubElement(unpitched, "display-step").text = pitch_to_step(note.pitch)
            ET.SubElement(unpitched, "display-octave").text = str(pitch_to_octave(note.pitch))
        else:
            step, alter, octave = midi_to_musicxml_pitch(note.pitch)
            ET.SubElement(pitch_el, "step").text = step
            if alter: ET.SubElement(pitch_el, "alter").text = str(alter)
            ET.SubElement(pitch_el, "octave").text = str(octave)
        # duration (in divisions: 1 beat = 4 divisions)
        duration = quantize_duration(note.duration_beat)
        ET.SubElement(note_el, "duration").text = str(round(duration * 4))
        ET.SubElement(note_el, "type").text = beat_to_type(duration)
        # dynamics
        dynamics_el = ET.SubElement(note_el, "dynamics")
        ET.SubElement(dynamics_el, velocity_to_dynamic(note.velocity))

    _write_rest(measure, duration_beats):
        """写入休止符"""
        note_el = ET.SubElement(measure, "note")
        ET.SubElement(note_el, "rest")
        quantized = quantize_duration(duration_beats)
        ET.SubElement(note_el, "duration").text = str(round(quantized * 4))
        ET.SubElement(note_el, "type").text = beat_to_type(quantized)

    quantize_duration(beats) -> float:
        """量化为最近的标准时值"""
        standard = [4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.25, 0.125]
        return min(standard, key=lambda s: abs(s - beats))

    midi_to_musicxml_pitch(midi_pitch) -> (step, alter, octave):
        """MIDI pitch → (step, alter, octave)"""
        PITCH_MAP = {0:("C",0), 1:("C",1), 2:("D",0), 3:("D",1),
                     4:("E",0), 5:("F",0), 6:("F",1), 7:("G",0),
                     8:("G",1), 9:("A",0), 10:("A",1), 11:("B",0)}
        pc = midi_pitch % 12
        octave = (midi_pitch // 12) - 1
        step, alter = PITCH_MAP[pc]
        return step, alter, octave

    render_to_file(song, path) -> str:
        """渲染并写入文件"""
        xml_str = render(song)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        return path
```

#### 辅助映射

```
# Key → MusicXML fifths 映射 (升降号数)
KEY_TO_FIFTHS = {
    Key.C: 0, Key.G: 1, Key.D: 2, Key.A: 3, Key.E: 4, Key.B: 5,
    Key.Gb: -6, Key.F: -1, Key.Bb: -2, Key.Eb: -3, Key.Ab: -4, Key.Db: -5,
}
```

#### Phase 10 无需 Command

MusicXML 导出是只读操作（不修改 Song），直接在 MCP Tool 中调用 `MusicXMLRenderer`：

```
@mcp.tool()
def export_musicxml(filename: str = "") -> dict:
    xml_str = MusicXMLRenderer().render(composer.song)
    path = MusicXMLRenderer().render_to_file(composer.song, filename)
    return _ok(data={"path": path}, message="MusicXML exported")

@mcp.tool()
def preview_musicxml() -> dict:
    xml_str = MusicXMLRenderer().render(composer.song)
    # 截取前 2000 字符作为预览
    return _ok(data={"xml": xml_str[:2000], "total_length": len(xml_str)})
```

### 5.18 Phase 11 可观测性设计

#### 日志模块 (observability/logger.py)

```
import logging, sys, os, time

# 自定义格式
LOG_FORMAT = "[%(asctime)s] [%(levelname)-5s] [%(tag)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class TagFilter(logging.Filter):
    """为 log record 注入 tag 字段"""
    def __init__(self, tag="SYSTEM"):
        self.tag = tag
    def filter(self, record):
        if not hasattr(record, 'tag'):
            record.tag = self.tag
        return True

def setup_logger() -> logging.Logger:
    """初始化全局 logger"""
    logger = logging.getLogger("composer_engine")

    # 级别：从环境变量读取
    level_name = os.environ.get("COMPOSER_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    # Handler: stderr（不干扰 MCP 的 stdout）
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    stderr_handler.addFilter(TagFilter())
    logger.addHandler(stderr_handler)

    # Handler: 文件（可选）
    log_file = os.environ.get("COMPOSER_LOG_FILE", "")
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        file_handler.addFilter(TagFilter())
        logger.addHandler(file_handler)

    return logger

def log(msg, level="INFO", tag="SYSTEM"):
    """便捷日志函数"""
    logger = logging.getLogger("composer_engine")
    logger.log(
        getattr(logging, level.upper(), logging.INFO),
        msg,
        extra={"tag": tag}
    )
```

#### 运行统计 (observability/stats.py)

```
class ServerStats:
    """运行时统计收集器"""

    start_time: float       # time.time() at startup
    tool_calls: int = 0     # 总 tool 调用次数
    tool_errors: int = 0    # tool 错误次数
    commands_executed: int = 0
    undo_count: int = 0
    last_tool: str = ""     # 最近调用的 tool
    last_tool_time: str = "" # ISO 格式时间

    def record_tool_call(self, tool_name, success, elapsed_ms):
        self.tool_calls += 1
        if not success:
            self.tool_errors += 1
        self.last_tool = f"{tool_name} ({'OK' if success else 'FAIL'}) {elapsed_ms}ms"
        self.last_tool_time = datetime.now().isoformat()

    def record_command(self):
        self.commands_executed += 1

    def record_undo(self):
        self.undo_count += 1

    def get_uptime(self) -> str:
        elapsed = time.time() - self.start_time
        h, m, s = int(elapsed // 3600), int(elapsed % 3600 // 60), int(elapsed % 60)
        return f"{h}h {m}m {s}s"

    def to_dict(self) -> dict:
        return {
            "uptime": self.get_uptime(),
            "tool_calls": self.tool_calls,
            "tool_errors": self.tool_errors,
            "commands_executed": self.commands_executed,
            "undo_count": self.undo_count,
            "last_tool": self.last_tool,
            "last_tool_time": self.last_tool_time,
            "error_rate": f"{(self.tool_errors / max(1, self.tool_calls) * 100):.1f}%",
        }
```

#### 启动 Banner (observability/banner.py)

```
import sys, platform
from composer_engine import __version__  # 或 fallback "0.1.0"

def print_banner(tool_count: int = 146):
    if os.environ.get("COMPOSER_NO_BANNER"):
        return
    pydantic_ver = 从 pydantic.VERSION 获取
    python_ver = platform.python_version()
    banner = f"""
╔══════════════════════════════════════════╗
║   🎵 Composer Engine v{__version__:<18s}║
║   MCP Tools: {tool_count:<4d}| Phases: 11          ║
║   Python: {python_ver:<8s}| Pydantic: {pydantic_ver:<8s}║
╚══════════════════════════════════════════╝"""
    print(banner, file=sys.stderr)
```

#### Composer 引擎日志集成

```
Composer.execute() 追加:
    log(f"{command.__class__.__name__} → {command.description}", tag="CMD")
    stats.record_command()

Composer.undo() 追加:
    log(f"Undo: {command.description}", tag="CMD")
    stats.record_undo()
```

#### MCP Server 日志集成

```
# 在每个 @mcp.tool() 函数中，用 wrapper/decorator 统一：

def tool_log(func):
    """装饰器：自动记录 Tool 调用日志"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - t0) * 1000
            success = result.get("success", True)
            params = _summarize_params(kwargs)
            log(f"{func.__name__}({params}) → {'OK' if success else 'FAIL'} ({elapsed:.0f}ms)",
                tag="TOOL",
                level="INFO" if success else "WARN")
            stats.record_tool_call(func.__name__, success, elapsed)
            return result
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            log(f"{func.__name__} → ERROR: {e} ({elapsed:.0f}ms)",
                tag="TOOL", level="ERROR")
            stats.record_tool_call(func.__name__, False, elapsed)
            raise
    return wrapper

def _summarize_params(kwargs, max_len=80) -> str:
    """参数摘要：截断长字符串，隐藏大型 JSON"""
    parts = []
    for k, v in kwargs.items():
        sv = str(v)
        if len(sv) > 30:
            sv = sv[:27] + "..."
        parts.append(f'{k}={sv}')
    summary = ", ".join(parts)
    return summary[:max_len]
```

注意：由于 143 个现有 tool 已经写好，不逐个加装饰器。改为在 `_ok()` 和 `_err()` 中统一记录。

实际方案（最小侵入）：

```
# _ok / _err 已是所有 tool 的出口，在此统一记录

_current_tool_name: str = ""
_current_tool_start: float = 0.0

def _ok(data=None, message="OK") -> dict:
    elapsed = (time.perf_counter() - _current_tool_start) * 1000
    log(f"{_current_tool_name}() → OK ({elapsed:.0f}ms): {message}",
        tag="TOOL")
    stats.record_tool_call(_current_tool_name, True, elapsed)
    result = {"success": True, "message": message}
    result.update(composer.get_state())
    if data:
        result["data"] = data
    return result

def _err(error, message="") -> dict:
    elapsed = (time.perf_counter() - _current_tool_start) * 1000
    log(f"{_current_tool_name}() → FAIL ({elapsed:.0f}ms): {error} {message}",
        tag="TOOL", level="WARN")
    stats.record_tool_call(_current_tool_name, False, elapsed)
    return {"success": False, "error": error, "message": message}
```

`_current_tool_name` 和 `_current_tool_start` 在每个 tool 函数入口处设置：

```
# 注入方式：给 MCP 注册一个 middleware/hook
# 或在每个 tool 函数开头加一行：
_begin_tool("create_song")
```

#### Song 摘要函数

```
def get_song_summary(song: Song | None) -> dict:
    if not song:
        return {"status": "no_song"}
    return {
        "name": song.name,
        "stage": song.stage.value,
        "tracks": len(song.tracks),
        "total_notes": sum(len(t.notes) for t in song.tracks),
        "sections": len(song.sections),
        "chords": len(song.chord_progression),
        "markers": len(song.markers),
        "tempo": song.global_settings.tempo,
        "key": f"{song.global_settings.key.value} {song.global_settings.mode.value}",
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
```

#### Phase 11 MCP Tools 映射

```
MCP Tools (#144-#146):
    get_server_stats    → stats.to_dict()（只读）
    get_song_summary    → get_song_summary(composer.song)（只读）
    set_log_level       → logging.getLogger("composer_engine").setLevel(level)
```

#### 代码结构更新

```
src/composer_engine/
    ├── observability/          # [Phase 11] 新增
    │   ├── __init__.py
    │   ├── logger.py           # 日志初始化 + 便捷函数
    │   ├── stats.py            # 运行统计
    │   └── banner.py           # 启动 Banner
    └── server/
        └── mcp_server.py       # 集成日志 + 统计 + Banner

tests/
    └── test_observability.py   # [Phase 11] 新增
```

---

## 六、实现细节

### 6.1 ID 生成

所有实体使用 UUID4，通过 Pydantic `Field(default_factory=lambda: str(uuid4()))` 自动生成。

### 6.2 深拷贝

Undo/Redo 快照使用 Pydantic 内置方法 `song.model_copy(deep=True)`。

### 6.3 时间单位

| 层次 | 单位 | 说明 |
|------|------|------|
| 逻辑层 (Note) | beat | start_beat, duration_beat |
| 渲染层 (MIDI) | 秒 | 转换公式: `seconds = beats * 60.0 / tempo` |

### 6.4 Drums Channel

遵循 GM 标准：Drums Track 固定 Channel 9；pitch 对应 GM Percussion Map (Kick=36, Snare=38, HiHat=42 等)。

### 6.5 Solo/Mute 优先级

1. 存在 `solo=True` 的 Track → 只渲染这些 Track
2. 否则 → 渲染所有 `mute=False` 的 Track
3. solo 优先于 mute

### 6.6 错误处理

统一响应格式：

```
成功: { success: true, data: {...}, message: "..." }
失败: { success: false, error: "错误类型", message: "详细描述" }
```

常见错误：无 Song 时操作 / ID 不存在 / 参数越界(Pydantic 自动校验) / undo 栈空

### 6.7 测试策略

- `test_models`: 模型创建、字段校验、JSON 序列化/反序列化
- `test_commands`: 每个 Command 的 execute 正确性
- `test_composer`: execute → undo → redo 完整流程；snapshot save/load
- `test_renderer`: Song 渲染为 MIDI 的基本正确性
- `test_pipeline`: 阶段评估、自动推进、手动 advance/go_back

---

---

### 5.19 Phase 13: MIDI 导入技术方案

#### 模块设计

新增 `importer/midi_importer.py` 模块，与 `renderer/midi_renderer.py` 对称：

```
src/composer_engine/
├── importer/
│   ├── __init__.py
│   └── midi_importer.py    # MidiImporter 类
```

#### MidiImporter 类

```
class MidiImporter:
    def import_file(file_path: str, song_name: str = None) -> Song
        # 解析完整 MIDI 文件 → Song
        # 1. pm = pretty_midi.PrettyMIDI(file_path)
        # 2. 提取 tempo, time_sig, key_sig → GlobalSettings
        # 3. 遍历 pm.instruments → Track + Notes
        # 4. 返回完整 Song

    def import_single_track(file_path: str, track_index: int) -> Track
        # 解析单轨 → Track
        # 1. pm = pretty_midi.PrettyMIDI(file_path)
        # 2. instrument = pm.instruments[track_index]
        # 3. 转换 → Track + Notes
        # 4. 返回 Track

    def get_info(file_path: str) -> dict
        # 返回 MIDI 文件元信息（不创建 Song）
        # tempo, time_sig, key_sig, duration, track_count
        # 每轨: name, program, is_drum, note_count, pitch_range

    # 内部方法
    def _seconds_to_beat(seconds, tempo) -> float
    def _program_to_instrument_type(program, is_drum) -> InstrumentType
    def _parse_key_signature(key_sig) -> (Key, Mode)
    def _parse_notes(instrument, tempo) -> list[Note]
```

#### GM Program 反向映射

```
GM_PROGRAM_TO_INSTRUMENT: dict[range, InstrumentType] = {
    range(0, 24):   PIANO,
    range(24, 32):  GUITAR,
    range(32, 40):  BASS,
    range(40, 56):  STRINGS,
    range(56, 64):  BRASS,
    range(64, 80):  WOODWINDS,
    range(80, 88):  LEAD,
    range(88, 96):  PAD,
    range(96, 104): FX,
    range(104, 112): GUITAR,     # Ethnic → Guitar
    range(112, 128): FX,         # Percussive + SFX → FX
}
# is_drum=True → DRUMS（优先级最高）
```

#### Seconds → Beats 转换

```
def _seconds_to_beat(seconds: float, tempo: float) -> float:
    return seconds * tempo / 60.0
```

这是 `midi_renderer._beat_to_seconds()` 的精确逆运算。

#### Key Signature 解析

`pretty_midi.KeySignature` 包含 `key_number`:
- 0-11: C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B (Major)
- 12-23: 同上对应的 Minor

```
KEY_MAP = [Key.C, Key.Db, Key.D, Key.Eb, Key.E, Key.F,
           Key.Gb, Key.G, Key.Ab, Key.A, Key.Bb, Key.B]

def _parse_key_signature(ks):
    idx = ks.key_number % 12
    mode = Mode.MINOR if ks.key_number >= 12 else Mode.MAJOR
    return KEY_MAP[idx], mode
```

#### Command 设计

无新 Command。导入操作直接在 MCP Tool 中调用 `MidiImporter`，然后通过 `composer.song = imported_song` 设置（或对于单轨导入，使用现有 `AddTrackCommand` 模式）。这与 `load_song` 的实现一致。

#### MCP Tool 设计

```
@mcp.tool()
def import_midi(file_path: str, song_name: str = "") -> dict:
    # MidiImporter().import_file(file_path, song_name) → Song
    # composer.song = song; composer.history.clear()
    # return _ok(...)

@mcp.tool()
def import_midi_track(file_path: str, midi_track_index: int) -> dict:
    # track = MidiImporter().import_single_track(file_path, midi_track_index)
    # song.tracks.append(track); song.updated_at = now()
    # return _ok(...)

@mcp.tool()
def get_midi_info(file_path: str) -> dict:
    # info = MidiImporter().get_info(file_path)
    # return _ok(data=info)
```

#### 错误处理

| 场景 | 处理 |
|------|------|
| 文件不存在 | 返回 `file_not_found` 错误 |
| 非 MIDI 文件 | 返回 `invalid_midi` 错误 |
| track_index 越界 | 返回 `track_index_out_of_range` 错误 |
| 空 MIDI（无音轨） | 返回空 Song（0 tracks） |
| 无 tempo/key 信息 | 使用默认值（120 BPM / C Major） |

---

*本文档随项目进展持续更新。当前版本覆盖 Phase 1-13（全部完成，169 MCP Tools）。*
