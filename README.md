# 🎵 Composer Engine — AI 原生作曲引擎

> 用自然语言描述你脑中的音乐，AI 帮你完成从灵感到小样的全流程。

Composer Engine 是一个面向 AI 的音乐创作中间件。它通过 **MCP (Model Context Protocol)** 暴露 **143 个工具**，让大语言模型（如 Claude、GPT）能够以结构化方式完成：

**描述 → 作曲 → 编曲 → 制作 → 导出**

最终输出合格的 MIDI 小样和 MusicXML 乐谱。

---

## 📋 目录

- [快速开始](#-快速开始)
- [核心概念](#-核心概念)
- [创作流程指南](#-创作流程指南)
- [MCP Tools 速查](#-mcp-tools-速查)
- [风格预设](#-风格预设)
- [工程结构](#-工程结构)
- [配置与运行](#-配置与运行)
- [开发指南](#-开发指南)
- [FAQ](#-faq)

---

## 🚀 快速开始

### 环境要求

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) 包管理器（推荐）

### 安装

```bash
# 克隆项目
git clone <repo-url> && cd music-gene

# 安装依赖
uv sync

# 运行测试，确认一切正常
uv run python -m pytest tests/ -q
# 预期输出：331 passed
```

### 启动 MCP Server

```bash
uv run python -m composer_engine.server.mcp_server
```

服务启动后，将以下配置添加到你的 AI 客户端（如 Cursor、Claude Desktop）的 MCP 设置中：

```json
{
  "mcpServers": {
    "composer-engine": {
      "command": "uv",
      "args": ["run", "python", "-m", "composer_engine.server.mcp_server"],
      "cwd": "<你的项目路径>/music-gene"
    }
  }
}
```

### 30 秒体验

连接 MCP 后，对 AI 说：

> "帮我创建一首 Anime 风格的歌，C 大调，BPM 140，4/4 拍。先写一段 8 小节的副歌和弦进行，然后生成旋律、贝斯和鼓。"

AI 会依次调用 `create_song` → `set_tempo` → `set_key` → `set_style` → `add_section` → `generate_chords` → `generate_melody` → `generate_bass` → `generate_drums` → `export_midi`，最终输出一个 `.mid` 文件。

---

## 💡 核心概念

### Song 数据模型

所有音乐信息都存储在一个 `Song` 对象中：

```
Song
├── name: "My Song"
├── global_settings
│   ├── tempo: 120.0        # BPM
│   ├── key: C              # 调性
│   ├── mode: major         # 调式
│   ├── time_signature: (4, 4)
│   ├── style: "anime"      # 风格预设
│   └── mood: "happy"       # 情绪标签
├── sections[]               # 段落：Intro, Verse, Chorus...
├── tracks[]                 # 音轨（每个乐器一轨）
│   ├── notes[]             # 音符 (pitch, start_beat, duration_beat, velocity)
│   └── automation[]        # 自动化曲线 (volume, pan, expression...)
├── chord_progression[]      # 和弦进行
└── markers[]                # 时间轴标记
```

### Command 模式

所有对 Song 的修改都通过 **Command** 执行，自动支持：

- ✅ **Undo / Redo** — 随时撤销和重做
- ✅ **Snapshot** — 保存/加载任意版本
- ✅ **历史记录** — 查看所有操作记录

### Pipeline 五阶段

引擎内置创作流水线，引导 AI 按阶段推进：

```
Inspiration → Composition → Arrangement → Production → Export
  (灵感)        (作曲)         (编曲)        (制作)      (导出)
```

每个阶段有推荐工具、入口条件和出口条件。调用 `get_stage_guide` 可查看当前阶段的指引。

---

## 🎼 创作流程指南

### 第一步：灵感 (Inspiration)

设定歌曲基础方向。

```
你可以对 AI 说：
"创建一首歌叫《星空》，120 BPM，G 大调，Jazz 风格"
```

涉及工具：
| 工具 | 作用 |
|------|------|
| `create_song` | 创建歌曲 |
| `set_tempo` | 设置速度 (BPM) |
| `set_key` | 设置调性 (C/D/E/F/G/A/B + 升降) |
| `set_mode` | 设置调式 (major/minor/dorian 等) |
| `set_time_signature` | 设置拍号 (4/4, 3/4, 6/8...) |
| `set_style` | 设置风格预设 |
| `set_mood` | 设置情绪标签 |

### 第二步：作曲 (Composition)

构建歌曲骨架：段落结构 + 和弦进行 + 旋律。

```
"添加 Intro(4小节) + Verse(8小节) + Chorus(8小节) 的结构"
"为 Chorus 生成一段流行风格的和弦进行"
"在和弦基础上生成主旋律"
```

涉及工具：
| 工具 | 作用 |
|------|------|
| `add_section` | 添加段落 (intro/verse/chorus/bridge...) |
| `generate_chords` | 自动生成和弦进行 |
| `generate_melody` | 自动生成旋律 |
| `simplify_melody` / `complexify_melody` | 调节旋律复杂度 |
| `transpose_melody` | 旋律移调 |

### 第三步：编曲 (Arrangement)

为骨架填充乐器声部。

```
"添加贝斯、鼓、钢琴伴奏和弦乐铺底"
"鼓用 Rock 风格，贝斯用 Walking 模式"
"加一段弦乐长音铺底"
```

**四大件（节奏组）：**
| 工具 | 作用 |
|------|------|
| `generate_bass` | 生成贝斯线（8 种模式） |
| `generate_drums` | 生成鼓模式（8 种风格） |
| `generate_piano_part` | 钢琴伴奏（4 种模式） |
| `generate_guitar_part` | 吉他声部（4 种模式） |

**扩展乐器：**
| 工具 | 作用 |
|------|------|
| `generate_strings` | 弦乐（sustain/tremolo/pizzicato/arco/divisi） |
| `generate_brass` | 铜管（fanfare/sustain/staccato/swell） |
| `generate_woodwinds` | 木管（melody/sustain/trill/run） |
| `generate_synth` | 合成器（pad/arp/lead/bass） |

**编曲控制：**
| 工具 | 作用 |
|------|------|
| `increase_energy` / `decrease_energy` | 调节能量 |
| `add_layer` / `remove_layer` | 添加/移除声部层次 |
| `add_build_up` | 添加渐进（副歌前） |
| `add_transition` | 添加过渡 |

### 第四步：制作 (Production)

润色和精细调整。

```
"给所有音轨加一点人性化"
"鼓加 Swing 感"
"给弦乐做一个渐强自动化，从第 8 拍到第 16 拍"
"分析一下整首歌的能量分布"
```

**人性化：**
| 工具 | 作用 |
|------|------|
| `humanize_timing` | 时值微调（更自然） |
| `humanize_velocity` | 力度微调 |
| `apply_groove` | 应用 Groove 模板 |
| `apply_swing` | 添加 Swing 感 |
| `hand_played_feel` | 手弹感模拟 |

**自动化：**
| 工具 | 作用 |
|------|------|
| `add_automation` | 添加自动化曲线 (volume/pan/expression...) |
| `apply_automation_preset` | 应用预设（fade_in/fade_out/crescendo/swell 等） |

**分析（辅助决策）：**
| 工具 | 作用 |
|------|------|
| `get_full_analysis` | 综合分析报告 |
| `analyze_energy` | 能量分布分析 |
| `analyze_mood` | 情绪分析 |
| `analyze_style` | 风格匹配分析 |

### 第五步：导出 (Export)

```
"导出 MIDI 文件"
"同时导出一份 MusicXML 乐谱"
"保存一个快照叫 v1.0"
```

| 工具 | 作用 |
|------|------|
| `export_midi` | 导出 `.mid` 文件 |
| `export_musicxml` | 导出 `.musicxml` 乐谱文件 |
| `save_song` | 保存工程 (JSON) |
| `save_snapshot` | 保存版本快照 |

---

## 📖 MCP Tools 速查

共 **143 个** MCP 工具，按功能分组：

| 分组 | 数量 | 编号 | 说明 |
|------|------|------|------|
| 核心基础 | 29 | #1-#29 | 歌曲/段落/音轨/音符 CRUD + 导出/持久化/Pipeline |
| 和声系统 | 13 | #30-#42 | 和弦生成/替换/借用/副属/终止式 |
| 旋律生成 | 15 | #43-#57 | 旋律生成/变奏/发展/倒影/逆行/扩展 |
| Bass & Drums | 18 | #58-#75 | 贝斯 8 模式 + 鼓 8 风格 + 细节控制 |
| 扩展乐器 & 编曲 | 20 | #76-#95 | 6 种乐器 + 11 种编曲操作 |
| 人性化 & 风格 | 14 | #96-#109 | 8 种人性化 + 13 种风格预设 |
| 分析引擎 | 19 | #110-#128 | 18 种分析 + 综合报告 |
| 自动化 & 标记 | 9 | #129-#137 | 自动化曲线 + 7 种预设 + Marker |
| 插件系统 | 4 | #138-#141 | 插件管理 (发现/启用/禁用/重载) |
| MusicXML 导出 | 2 | #142-#143 | MusicXML 导出 + 预览 |

> 完整 Tool 清单详见 [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md)

---

## 🎨 风格预设

内置 **13 种**风格预设，通过 `set_style` 设置：

| 风格 | 说明 | 典型特征 |
|------|------|---------|
| `anime` | 日系动画 | 明亮和弦、强旋律、弦乐铺底 |
| `city_pop` | 城市流行 | 7th/9th 和弦、Funk 律动 |
| `jazz` | 爵士 | 复杂和声、Swing 节奏 |
| `rock` | 摇滚 | 强力和弦、直拍鼓 |
| `metal` | 金属 | 低音 Riff、双踩 |
| `edm` | 电子舞曲 | Four-on-floor、Synth Lead |
| `lofi` | Lo-Fi | 低保真质感、Jazz 和弦 |
| `classical` | 古典 | 对位法、动态对比 |
| `orchestra` | 管弦乐 | 大编制、层次丰富 |
| `game_music` | 游戏音乐 | 循环结构、情绪驱动 |
| `ambient` | 氛围 | Pad 铺底、空间感 |
| `synthwave` | 合成器浪潮 | 80s Synth、Arp |
| `future_bass` | Future Bass | Supersaw、侧链压缩感 |

可通过 `mix_styles` 混合两种风格，如 `mix_styles("jazz", "lofi", 0.6)` = 60% Jazz + 40% Lo-Fi。

---

## 📁 工程结构

```
music-gene/
├── docs/
│   ├── REQUIREMENTS.md          # 完整需求文档（10 个 Phase）
│   └── TECHNICAL.md             # 技术架构文档
├── src/composer_engine/
│   ├── models/                  # 数据模型 (Pydantic v2)
│   │   ├── note.py              #   音符
│   │   ├── track.py             #   音轨
│   │   ├── section.py           #   段落
│   │   ├── song.py              #   歌曲（顶层容器）
│   │   ├── chord.py             #   和弦
│   │   ├── automation.py        #   自动化/标记
│   │   ├── analysis.py          #   分析结果
│   │   ├── global_settings.py   #   全局设置
│   │   └── enums.py             #   所有枚举 + 常量
│   ├── commands/                # Command 模式（所有变更操作）
│   │   ├── base.py              #   Command 抽象基类
│   │   ├── song_commands.py     #   歌曲操作
│   │   ├── track_commands.py    #   音轨/音符操作
│   │   ├── chord_commands.py    #   和弦操作
│   │   ├── melody_commands.py   #   旋律操作
│   │   ├── bass_commands.py     #   贝斯操作
│   │   ├── drums_commands.py    #   鼓操作
│   │   ├── instrument_commands.py  # 扩展乐器
│   │   ├── arrangement_commands.py # 编曲
│   │   ├── humanize_commands.py #   人性化
│   │   ├── style_commands.py    #   风格
│   │   ├── analysis_commands.py #   分析
│   │   └── automation_commands.py  # 自动化/标记
│   ├── engine/                  # 核心引擎
│   │   ├── composer.py          #   Composer（主引擎）
│   │   ├── history.py           #   Undo/Redo 历史栈
│   │   └── snapshot.py          #   快照管理
│   ├── generators/              # 生成器/引擎
│   │   ├── chord_generator.py   #   和弦生成器
│   │   ├── melody_generator.py  #   旋律生成器
│   │   ├── bass_generator.py    #   贝斯生成器
│   │   ├── drums_generator.py   #   鼓生成器
│   │   ├── instrument_generator.py # 扩展乐器生成器
│   │   ├── arrangement_engine.py   # 编曲引擎
│   │   ├── humanize_engine.py   #   人性化引擎
│   │   ├── style_engine.py      #   风格引擎
│   │   ├── analysis_engine.py   #   分析引擎
│   │   └── automation_engine.py #   自动化引擎
│   ├── theory/                  # 乐理基础
│   │   ├── scales.py            #   音阶计算
│   │   ├── intervals.py         #   音程工具
│   │   └── chord_utils.py       #   和弦拼写
│   ├── pipeline/                # 创作流水线
│   │   ├── stages.py            #   阶段定义
│   │   ├── pipeline_manager.py  #   流水线管理
│   │   └── evaluation.py        #   条件评估
│   ├── renderer/                # 渲染器
│   │   ├── midi_renderer.py     #   MIDI 渲染
│   │   └── musicxml_renderer.py #   MusicXML 渲染
│   ├── persistence/             # 持久化
│   │   └── json_store.py        #   JSON 存储
│   ├── plugins/                 # 插件系统
│   │   └── plugin_manager.py    #   插件管理器
│   └── server/
│       └── mcp_server.py        #   MCP Server（143 Tools）
└── tests/                       # 测试（331 个）
    ├── test_models.py
    ├── test_commands.py
    ├── test_composer.py
    ├── test_renderer.py
    ├── test_pipeline.py
    ├── test_theory.py
    ├── test_chord_generator.py
    ├── test_melody_generator.py
    ├── test_bass_generator.py
    ├── test_drums_generator.py
    ├── test_instrument_generator.py
    ├── test_arrangement_engine.py
    ├── test_humanize_engine.py
    ├── test_style_engine.py
    ├── test_analysis_engine.py
    ├── test_automation.py
    ├── test_plugin_manager.py
    └── test_musicxml_renderer.py
```

---

## ⚙️ 配置与运行

### 依赖

| 包 | 版本 | 用途 |
|----|------|------|
| `pydantic` | ≥ 2.0 | 数据模型与验证 |
| `fastmcp` | ≥ 3.4 | MCP Server 框架 |
| `pretty-midi` | ≥ 0.2.10 | MIDI 渲染与输出 |
| `pytest` | ≥ 8.0 | 测试框架 (dev) |

### 快捷脚本

项目提供 `scripts/` 目录下的启动脚本，自动处理依赖安装：

| 脚本 | Windows | macOS/Linux | 作用 |
|------|---------|-------------|------|
| 启动服务 | `scripts\start.bat` | `scripts/start.sh` | 安装依赖 + 启动 MCP Server |
| 运行测试 | `scripts\test.bat` | `scripts/test.sh` | 安装依赖 + 运行全部测试 |

```bash
# Windows — 双击或命令行
scripts\start.bat          # 启动 MCP Server
scripts\test.bat           # 运行全部测试
scripts\test.bat -q        # 简洁输出
scripts\test.bat tests/test_automation.py -v   # 指定测试文件

# macOS / Linux
./scripts/start.sh
./scripts/test.sh
./scripts/test.sh -q
./scripts/test.sh tests/test_automation.py -v
```

### 手动命令

```bash
# 运行全部测试
uv run python -m pytest tests/ -q

# 运行特定 Phase 测试
uv run python -m pytest tests/test_automation.py -v

# 启动 MCP Server
uv run python -m composer_engine.server.mcp_server
```

### 插件目录

插件默认放在 `~/.composer-engine/plugins/` 目录下。每个插件是一个子目录，包含 `plugin.json` 清单文件：

```json
{
  "name": "my-generator",
  "version": "1.0.0",
  "type": "generator",
  "entry": "my_plugin.py",
  "class_name": "MyGenerator",
  "description": "自定义生成器"
}
```

支持 5 种插件类型：`generator`、`analyzer`、`pattern`、`style`、`renderer`。

---

## 🛠️ 开发指南

### 技术栈

- **Python 3.12+** — 类型提示 + match/case
- **Pydantic v2** — 数据模型、验证、JSON 序列化
- **FastMCP v3** — MCP Server 框架
- **pretty_midi** — MIDI 渲染
- **xml.etree.ElementTree** — MusicXML 渲染（标准库）

### 架构原则

1. **Command 模式**：所有对 Song 的修改必须通过 Command，保证 Undo/Redo 安全
2. **逻辑音符**：音符以 `beat` 为单位存储，渲染时才转换为秒
3. **AI-First**：所有 MCP Tool 的名称、参数、文档全部英文，方便 LLM 理解
4. **Pipeline 引导**：五阶段流水线为 AI 提供创作方向建议，但不强制线性

### 添加新功能的流程

1. 在 `REQUIREMENTS.md` 中定义需求
2. 在 `TECHNICAL.md` 中写技术设计（伪代码）
3. 实现代码：Model → Generator → Command → MCP Tool
4. 编写测试
5. 对齐验证（确保文档 ↔ 代码一致）

### 测试

```bash
# 全部测试
uv run python -m pytest tests/ -q
# 预期：331 passed

# 带详细输出
uv run python -m pytest tests/ -v --tb=short
```

---

## ❓ FAQ

### Q: 需要什么 AI 才能使用？

任何支持 MCP 的 AI 客户端都可以，包括：
- **Cursor**（内置 MCP 支持）
- **Claude Desktop**（通过 MCP 配置）
- 其他支持 MCP 协议的工具

### Q: 输出的 MIDI 质量如何？

引擎输出的是**合格的小样级 MIDI**，包含：
- 多轨编曲（旋律/和弦/贝斯/鼓/弦乐/管乐/合成器）
- 人性化处理（时值/力度微调、Groove、Swing）
- 自动化（音量/声像/表情渐变）
- GM 标准乐器映射

可直接导入 DAW（如 Logic Pro、Ableton、FL Studio）进一步编辑。

### Q: 支持哪些调性？

12 个调性 × 7 种调式 = 84 种组合：
- 调性：C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B
- 调式：Major, Minor, Dorian, Mixolydian, Lydian, Phrygian, Locrian

### Q: 可以撤销操作吗？

可以。所有通过 MCP Tool 执行的操作都支持：
- `undo` — 撤销上一步
- `redo` — 重做
- `save_snapshot` / `load_snapshot` — 保存/恢复任意版本

### Q: 如何扩展新乐器或风格？

通过插件系统：
1. 在 `~/.composer-engine/plugins/` 下创建插件目录
2. 编写插件类（实现对应接口）
3. 创建 `plugin.json` 清单
4. 调用 `reload_plugins` 加载

---

## 📄 文档

| 文档 | 说明 |
|------|------|
| [REQUIREMENTS.md](docs/REQUIREMENTS.md) | 完整需求文档（10 个 Phase、143 个 Tool 详细定义） |
| [TECHNICAL.md](docs/TECHNICAL.md) | 技术架构文档（数据模型、伪代码、设计决策） |

---

## 📊 项目状态

| Phase | 名称 | Tools | 状态 |
|-------|------|-------|------|
| 1 | 核心基础 | 29 | ✅ 完成 |
| 2 | 和声系统 | 13 | ✅ 完成 |
| 3 | 旋律生成 | 15 | ✅ 完成 |
| 4 | Bass & Drums | 18 | ✅ 完成 |
| 5 | 扩展乐器 & 编曲 | 20 | ✅ 完成 |
| 6 | 人性化 & 风格 | 14 | ✅ 完成 |
| 7 | 分析引擎 | 19 | ✅ 完成 |
| 8 | 自动化 & 标记 | 9 | ✅ 完成 |
| 9 | 插件系统 | 4 | ✅ 完成 |
| 10 | MusicXML 导出 | 2 | ✅ 完成 |
| **合计** | | **143** | **🎉 全部完成** |

**测试**：331 passed ✅

---

*Made with ♪ by Composer Engine*
