# Composer Engine 需求文档

Version: 1.4  
Last Updated: 2026-07-23

---

## 一、产品愿景

Composer Engine 是一个 **AI Native Music Composition Engine（AI 原生音乐创作引擎）**。

它不是 MIDI 编辑器。AI 不直接编辑 MIDI，而是通过 Composer 操作音乐状态，最终由 Render Engine 渲染成 MIDI。

**核心工作流**：

```
用户描述脑中的歌曲 → AI 理解并作曲 → 编曲（分配乐器、写配器）→ 输出合格小样（完整 MIDI）
```

**最终目标**：用户通过自然语言描述歌曲构思，AI 自动完成作曲与编曲，产出包含四大件（钢琴、吉他、鼓、贝斯）以及弦乐、管乐、合成器的完整小样级 MIDI。

---

## 二、设计原则

| 编号 | 原则 | 说明 |
|------|------|------|
| G1 | LLM 无关 | 支持 Cursor、Claude、GPT、Gemini 等任意 LLM，Composer 对所有模型保持一致 |
| G2 | 有状态会话 | 整个会话只维护一个 Song，AI 不需要反复读取 MIDI |
| G3 | 增量修改 | 所有修改都是增量的（修改副歌、修改 Bass、修改 Drums），而不是重新生成整首歌 |
| G4 | Song 是核心 | MIDI 永远不是核心数据，Song 才是核心 |
| G5 | 完整历史 | 支持 Undo / Redo / Version / Snapshot |
| G6 | 创作流水线 | 歌曲遵循 灵感→作曲→编曲→制作→导出 的生命周期，Pipeline 引导 AI 按阶段推进创作 |
| G7 | MCP 英文接口 | 所有 MCP Tool 的名称、参数名、参数描述、Tool 描述（docstring）**强制使用英文**，确保对所有 LLM 兼容性最佳 |

---

## 三、总体功能需求

以下是 Composer Engine 的**完整功能清单**，涵盖所有最终要实现的能力。

**状态标记说明**：

| 标记 | 含义 |
|------|------|
| ✅ | 已实现（有 MCP Tool 暴露给 AI 使用） |
| ⚠️ | 部分实现（已全部修复，不应再出现此标记） |
| 🔜 | 未来规划（尚未实现，模型字段和代码均不存在） |

### 3.1 Song 管理

| 功能 | 说明 | 状态 |
|------|------|------|
| Create Song | 创建新歌曲 | ✅ Phase 1 |
| Delete Song | 删除歌曲 | ✅ Phase 1 |
| Clone Song | 克隆歌曲 | ✅ Phase 1 |
| Save | 保存到文件 | ✅ Phase 1 |
| Load | 从文件加载 | ✅ Phase 1 |
| Import MIDI | 从 MIDI 文件导入为新 Song | ✅ Phase 13 |
| Import MIDI Track | 从 MIDI 文件导入指定音轨到当前 Song | ✅ Phase 13 |
| Get MIDI Info | 预览 MIDI 文件信息（不导入） | ✅ Phase 13 |

### 3.2 全局设置 (Global)

| 参数 | 说明 | 状态 |
|------|------|------|
| Tempo | 速度 (BPM) | ✅ `set_tempo` Phase 1 |
| Time Signature | 拍号 (4/4, 3/4, 6/8 等) | ✅ `set_time_signature` Phase 1 |
| Key | 调性 (C, D, Eb 等) | ✅ `set_key` Phase 1 |
| Mode | 调式 (Major, Minor, Dorian 等) | ✅ `set_mode` Phase 1 |
| Scale | 音阶 (覆盖 Key+Mode 默认推算) | ✅ `set_scale` Phase 12 |
| Swing | 摇摆感 (0.0 - 1.0) | ✅ `set_swing` Phase 6 |
| Groove | 律动模板 | ✅ `set_groove` Phase 6 |
| Master Humanize | 全局人性化程度 | ✅ `set_master_humanize` Phase 1 |
| Master Velocity | 全局力度基准 | ✅ `set_master_velocity` Phase 1 |
| Master Timing | 全局时值偏移 | ✅ `set_master_timing` Phase 12 |
| Global Mood | 全局情绪 | ✅ `set_mood` Phase 6 |
| Global Style | 全局风格 | ✅ `set_style` Phase 6 |
| Global Energy | 全局能量级别 | ✅ `set_global_energy` Phase 12 |
| Song Length | 歌曲总长度 | ✅ 只读计算属性，`get_song_state` 自动返回 Phase 12 |

### 3.3 段落 (Sections)

**段落类型**：Intro, Verse, Pre Chorus, Chorus, Bridge, Solo, Breakdown, Outro

**段落操作**：

| 操作 | 说明 | 状态 |
|------|------|------|
| 新增 | 添加新段落 | ✅ `add_section` Phase 1 |
| 删除 | 删除段落 | ✅ `remove_section` Phase 1 |
| 复制 | 复制段落 | ✅ `duplicate_section` Phase 1 |
| 交换 | 交换两个段落的位置 | ✅ `swap_sections` Phase 12 |
| 移动 | 移动段落到指定位置 | ✅ `move_section` Phase 1 |
| 拉长 | 增加段落长度 | ✅ `resize_section` Phase 1 |
| 缩短 | 缩短段落长度 | ✅ `resize_section` Phase 1 |
| 重复 | 重复段落 N 次 | ✅ `set_section_repeat` Phase 1 |
| Loop | 循环段落 | ✅ `set_section_repeat` Phase 1 |
| Split | 拆分段落 | ✅ `split_section` Phase 12 |
| Merge | 合并相邻段落 | ✅ `merge_sections` Phase 12 |

### 3.4 音轨 (Tracks)

**乐器类型**：Piano, Bass, Strings, Pad, Lead, Synth, Drums, FX, Brass, Woodwinds, Guitar, Voice

**音轨属性**：

| 属性 | 说明 | 状态 |
|------|------|------|
| Mute | 静音 | ✅ `mute_track` Phase 1 |
| Solo | 独奏 | ✅ `solo_track` Phase 1 |
| Volume | 音量 (0-127) | ✅ `set_track_volume` Phase 1 |
| Pan | 声像 (0-127, 64=居中) | ✅ `set_track_pan` Phase 1 |
| Octave | 八度偏移 | ✅ `set_track_octave` Phase 5 |
| Register | 音区 (high/mid/low) | ✅ `set_track_register` Phase 12 |
| Density | 音符密度 | ✅ `set_track_density` Phase 5 |
| Energy | 能量级别 | ✅ `set_track_energy` Phase 5 |
| Complexity | 复杂度 (0.0-1.0) | ✅ `set_track_complexity` Phase 12 |
| Humanize | 人性化程度 (0.0-1.0) | ✅ `set_track_humanize` Phase 12 |
| Velocity | 力度偏移 (-127~+127) | ✅ `set_track_velocity_offset` Phase 12 |
| Timing | 时值偏移 (beats) | ✅ `set_track_timing_offset` Phase 12 |
| Rhythm | 节奏模式 | ✅ `set_track_rhythm` Phase 12 |
| Groove | 律动模板 | ✅ `set_track_groove` Phase 12 |
| Pattern | 演奏模式 | 🔜 需定义演奏模式数据结构 |
| Articulation | 奏法 (连奏/断奏/重音等) | 🔜 需设计奏法映射表 |
| Range | 音域限制 (MIDI pitch 范围) | ✅ `set_track_range` Phase 12 |
| Harmony | 和声层 | 🔜 生成型功能，现有 chord 生成器已部分覆盖 |
| Counter Melody | 对位旋律 | 🔜 生成型功能，现有 melody 生成器已部分覆盖 |
| Automation | 自动化曲线 | ✅ Phase 8 (6 操作 + 7 预设) |

### 3.5 旋律 (Melody) — ✅ 全部已实现（Phase 3，15 个 MCP Tools）

| 功能 | 说明 |
|------|------|
| Generate | 基于和弦和调性生成旋律 |
| Regenerate | 保持约束条件重新生成 |
| Simplify | 简化 (减少音符、简化节奏) |
| Complexify | 复杂化 (加经过音、装饰音) |
| Transpose | 移调 |
| Invert | 音程倒影 |
| Reverse | 逆行 |
| Sequence | 模进 |
| Variation | 变奏 |
| Develop | 动机发展 |
| Extend | 延长乐句 |
| Shorten | 缩短乐句 |
| Call Response | 呼应句 |
| Hook | 生成记忆点旋律 |
| Question Answer | 问答句式 |

### 3.6 和声 (Harmony) — ✅ 全部已实现（Phase 2，13 个 MCP Tools）

| 功能 | 说明 |
|------|------|
| Generate Chords | 生成和弦进行 |
| Replace Chords | 替换指定和弦 |
| Reharmonize | 重配和声 |
| Borrow Chords | 借用和弦 (从平行调) |
| Secondary Dominant | 副属和弦 |
| Passing Chords | 经过和弦 |
| Modulation | 转调 |
| Cadence | 终止式 |
| Roman Analysis | 罗马数字级数分析 |

### 3.7 Bass — ✅ 全部已实现（Phase 4，5 个 MCP Tools）

| 功能 | 说明 |
|------|------|
| Generate | 通用 Bass 生成 |
| Walking | 行走贝斯 |
| Root | 根音贝斯 |
| Octave | 八度贝斯 |
| Syncopation | 切分贝斯 |
| Follow Chords | 跟随和弦 |
| Independent | 独立旋律线 |
| Counter Bass | 对位低音 |

### 3.8 Drums — ✅ 全部已实现（Phase 4，13 个 MCP Tools）

| 功能 | 说明 |
|------|------|
| Generate | 通用鼓生成 |
| 风格预设 | Rock, Metal, Jazz, Pop, EDM, Anime, Latin, Swing |
| Ghost Note | 幽灵音 |
| Fill | 过门 |
| Crash | 镲片 |
| Ride | 叮叮镲 |
| HiHat | 踩镲 |
| Snare | 小鼓 |
| Kick | 底鼓 |
| Tom | 嗵鼓 |
| Percussion | 打击乐 |

### 3.9 编曲 (Arrangement) — ✅ 全部已实现（Phase 5，11 个 MCP Tools）

| 功能 | 说明 |
|------|------|
| Increase Energy | 增加能量 |
| Decrease Energy | 降低能量 |
| Increase Density | 增加密度 |
| Decrease Density | 降低密度 |
| Add Layer | 添加层次 |
| Remove Layer | 移除层次 |
| Build Up | 渐进累积 |
| Break Down | 拆解 |
| Transition | 段落过渡 |
| Fill | 填充 |
| Silence | 静默 |

### 3.10 人性化 (Humanize) — ✅ 全部已实现（Phase 6，8 个 MCP Tools）

| 功能 | 说明 |
|------|------|
| Timing Random | 时值随机偏移 |
| Velocity Random | 力度随机偏移 |
| Micro Timing | 微时值调整 |
| Groove | Groove 模板应用 |
| Swing | 摇摆感 |
| Push | 抢拍 |
| Pull | 拖拍 |
| Hand Played Feel | 手弹模拟 |

### 3.11 风格 (Style) — ✅ 全部已实现（Phase 6，6 个 MCP Tools）

**内置风格**：Anime, City Pop, Jazz, Rock, Metal, EDM, Lofi, Classical, Orchestra, Game Music, Ambient, Synthwave, Future Bass

**风格混合 (Style Mix)**：支持任意两种或多种风格的混合，如 Anime + Jazz, Anime + Orchestra, City Pop + Fusion 等。

### 3.12 分析 (Analysis) — ✅ 全部已实现（Phase 7，19 个 MCP Tools）

| 分析项 | 说明 |
|--------|------|
| Key | 调性检测 |
| Tempo | 速度分析 |
| Chord | 和弦识别 |
| Phrase | 乐句检测 |
| Motif | 动机识别 |
| Rhythm | 节奏模式分析 |
| Density | 密度分布 |
| Energy | 能量曲线 |
| Range | 音域分析 |
| Repetition | 重复模式 |
| Voice Leading | 声部进行 |
| Cadence | 终止式检测 |
| Counterpoint | 对位法分析 |
| Style | 风格识别 |
| Mood | 情绪检测 |
| Complexity | 复杂度评分 |
| Dynamic | 力度变化 |
| Structure | 曲式结构 |

### 3.13 创作流水线 (Pipeline) — ✅ 全部已实现（Phase 1，3 个 MCP Tools）

歌曲的创作遵循自然的生命周期，Pipeline 系统管理这个流程并引导 AI 按阶段推进。

**流水线阶段**：

| 阶段 | 名称 | 做什么 | 出口条件 |
|------|------|--------|----------|
| 1 | Inspiration（灵感） | 设定风格、情绪、速度、调性、基本构思 | 有名称 + 速度 + 调性 |
| 2 | Composition（作曲） | 设计曲式结构、生成和弦进行、创作主旋律 | 有段落 + 和弦 + 旋律 |
| 3 | Arrangement（编曲） | 分配乐器、为各 Track 生成配器 | 至少 4 轨有音符 |
| 4 | Production（制作） | 人性化、音量平衡、声像分布、打磨细节 | 用户满意 |
| 5 | Export（导出） | 导出 MIDI / MusicXML 等最终文件 | 文件生成成功 |

**流水线规则**：

- 正向推进：满足出口条件后可自动进入下一阶段
- 自由回退：可以随时回到任何前置阶段修改（如编曲时发现和弦不好，回到作曲阶段调整）
- 引导而非强制：Pipeline 提供建议和进度反馈，不阻止用户在任何阶段执行任何操作
- 每次操作后自动评估：Composer 执行 Command 后自动检查阶段进度
- AI 可查询引导：通过 `get_stage_guide` 获取当前阶段的建议操作

**每个阶段的推荐操作**：

| 阶段 | 推荐操作 |
|------|----------|
| Inspiration | 创建歌曲、设定速度/调性/拍号、选择风格、描述情绪和能量走向 |
| Composition | 设计段落结构 (Intro→Verse→Chorus→...)、生成和弦进行、创作主旋律 |
| Arrangement | 添加四大件 (Piano/Guitar/Bass/Drums)、生成各乐器配器、添加弦乐/管乐/合成器、调整层次 |
| Production | 应用人性化、调整音量平衡、设置声像分布、添加自动化、试听微调 |
| Export | 导出 MIDI、保存项目、保存快照版本 |

### 3.14 导出 (Export)

| 格式 | 状态 |
|------|------|
| MIDI | ✅ `export_midi` Phase 1 |
| MusicXML | ✅ `export_musicxml` / `preview_musicxml` Phase 10 |
| JSON | ✅ `save_song` / `load_song` Phase 1 |

---

## 四、分阶段实现需求

### 4.1 Phase 1: 核心基础 (已完成 ✅)

Phase 1 的目标是搭建完整的引擎骨架，实现从创建 Song 到导出 MIDI 的端到端流程。

#### 4.1.1 Phase 1 功能范围

**已纳入 Phase 1**：

- [x] Song 管理：Create, Delete, Clone, Save, Load
- [x] 全局设置：Tempo, Time Signature, Key, Mode, Master Velocity, Master Humanize
- [x] 段落管理：新增, 删除, 复制, 移动, 拉长/缩短, 重复/Loop
- [x] 音轨管理：添加, 删除, Mute, Solo, Volume, Pan
- [x] 音符操作：添加音符, 删除音符（逻辑音符，非 MIDI Event）
- [x] Command + Event Sourcing 系统
- [x] Undo / Redo
- [x] 快照 (Snapshot) 管理
- [x] MIDI 渲染（Song → pretty_midi → .mid）
- [x] JSON 持久化（Save / Load）
- [x] MCP Server（FastMCP v3，暴露核心 Tools）
- [x] 操作历史查看
- [x] 创作流水线 (Pipeline)：5 阶段生命周期管理、阶段自动评估、AI 引导

**未纳入 Phase 1（后续阶段）**：

- 和声/和弦系统
- 旋律生成
- Bass / Drums 生成
- 编曲智能
- 人性化
- 风格系统
- 分析引擎
- 插件架构
- MusicXML 导出

#### 4.1.2 Phase 1 MCP Tools 清单（35 个）

| # | Tool | 说明 |
|---|------|------|
| 1 | `create_song` | 创建新歌曲 |
| 2 | `delete_song` | 删除当前歌曲 |
| 3 | `clone_song` | 克隆当前歌曲 |
| 4 | `get_song_state` | 获取当前歌曲完整状态 |
| 5 | `add_track` | 添加音轨 |
| 6 | `remove_track` | 删除音轨 |
| 7 | `mute_track` | 静音/取消静音 |
| 8 | `solo_track` | 独奏/取消独奏 |
| 9 | `set_track_volume` | 设置音轨音量 |
| 10 | `set_track_pan` | 设置音轨声像 |
| 11 | `add_section` | 添加段落 |
| 12 | `remove_section` | 删除段落 |
| 13 | `duplicate_section` | 复制段落 |
| 14 | `add_notes` | 向指定音轨添加音符 |
| 15 | `set_tempo` | 设置速度 |
| 16 | `set_key` | 设置调性 |
| 17 | `set_time_signature` | 设置拍号 |
| 18 | `undo` | 撤销 |
| 19 | `redo` | 重做 |
| 20 | `save_snapshot` | 保存快照 |
| 21 | `load_snapshot` | 加载快照 |
| 22 | `list_snapshots` | 列出所有快照 |
| 23 | `save_song` | 保存歌曲到文件 |
| 24 | `load_song` | 从文件加载歌曲 |
| 25 | `export_midi` | 导出 MIDI 文件 |
| 26 | `list_history` | 查看操作历史 |
| 27 | `get_stage_guide` | 获取当前创作阶段引导信息 |
| 28 | `advance_stage` | 手动推进到下一阶段 |
| 29 | `go_back_stage` | 回退到指定阶段 |
| 30 | `move_section` | 移动段落到新位置 |
| 31 | `resize_section` | 调整段落长度 |
| 32 | `set_section_repeat` | 设置段落重复次数 |
| 33 | `set_mode` | 设置调式 |
| 34 | `set_master_velocity` | 设置全局力度基准 |
| 35 | `set_master_humanize` | 设置全局人性化程度 |

---

### 4.2 Phase 2: 和声与和弦系统 (Harmony & Chords)

**前置**：Phase 1 ✅  
**目标**：建立完整的和弦模型和和声操作体系，为旋律/Bass/编曲等后续功能提供和声基础。

#### 4.2.1 Phase 2 功能范围

**核心能力**：

- [x] 和弦数据模型：Chord（根音 + 和弦性质 + 转位 + 时位）
- [x] 和弦进行生成：基于调性 + 风格自动生成常用和弦进行
- [x] 和弦进行模板库：6 大类、15+ 个内置模板
- [x] 和弦编辑操作：替换、插入、删除单个和弦
- [x] 高级和声技法：重配和声、借用和弦、副属和弦、经过和弦、转调、终止式
- [x] 罗马数字分析：自动将和弦进行转换为罗马级数表示（I, IV, V7, vi 等）
- [x] Music Theory 基础模块：音阶计算、音程工具、和弦拼写（Phase 2 + Phase 3 共用）

**和弦性质 (ChordQuality) 支持**：

| 分类 | 和弦性质 | 说明 |
|------|---------|------|
| 三和弦 | Major, Minor, Diminished, Augmented | 大/小/减/增三和弦 |
| 七和弦 | Dom7, Maj7, Min7, HalfDim7, Dim7 | 属七/大七/小七/半减七/减七 |
| 挂留 | Sus2, Sus4 | 挂二/挂四和弦 |
| 附加音 | Add9, Add11 | 加九/加十一和弦 |
| 九和弦 | Dom9, Maj9, Min9 | 属九/大九/小九和弦 |

**内置和弦进行模板**：

| 风格 | 模板名 | 进行 | 典型用途 |
|------|--------|------|----------|
| Pop | pop_classic | I - V - vi - IV | 万能流行进行 |
| Pop | pop_50s | I - vi - IV - V | 50 年代经典 |
| Pop | pop_emotional | vi - IV - I - V | 抒情流行 |
| Pop | canon | I - V - vi - iii - IV - I - IV - V | 卡农进行 |
| Rock | rock_basic | I - IV - V - I | 基础摇滚 |
| Rock | rock_power | I - ♭VII - IV - I | 力量摇滚 |
| Rock | rock_alt | I - V - ♭VII - IV | 另类摇滚 |
| Jazz | jazz_251 | ii⁷ - V⁷ - Imaj⁷ | 爵士核心 |
| Jazz | jazz_turnaround | Imaj⁷ - vi⁷ - ii⁷ - V⁷ | 爵士回转 |
| Blues | blues_12bar | I⁷×4 - IV⁷×2 - I⁷×2 - V⁷ - IV⁷ - I⁷ - V⁷ | 12 小节蓝调 |
| Anime | royal_road | IV - V - iii - vi | 王道进行 |
| Anime | komuro | vi - V - IV - V | 小室进行 |
| Anime | just_the_two | I - V - vi - iii - IV - I - ii - V | J-Pop 经典 |
| Classical | authentic | I - IV - V - I | 正格终止式 |
| Classical | romantic | I - vi - ii - V | 浪漫派 |

**终止式 (Cadence) 类型**：

| 类型 | 进行 | 说明 |
|------|------|------|
| Authentic | V → I | 正格终止（最强结束感） |
| Plagal | IV → I | 变格终止（阿门终止） |
| Half | → V | 半终止（悬而未决） |
| Deceptive | V → vi | 欺骗终止（出人意料） |

#### 4.2.2 Phase 2 数据模型变更

| 新增模型 | 说明 |
|----------|------|
| `ChordQuality` 枚举 | 和弦性质（major, minor, dom7, maj7 等 16 种） |
| `CadenceType` 枚举 | 终止式类型（authentic, plagal, half, deceptive） |
| `Chord` | 单个和弦（root, quality, bass, start_beat, duration_beat, roman） |

| 已有模型变更 | 说明 |
|-------------|------|
| `Song` 新增字段 | `chord_progression: list[Chord]` — 全局和弦时间线 |

> **设计决策**：和弦进行存储在 Song 级别（非 Section 级别），因为每个 Chord 自带 start_beat，自然与 Section 的时间范围对应。`generate_chords` 可通过 section_id 定位生成范围。

#### 4.2.3 Phase 2 MCP Tools 清单

| # | Tool | 说明 |
|---|------|------|
| 30 | `generate_chords` | 为指定段落/全曲生成和弦进行（基于 key/mode/style/template） |
| 31 | `set_chords` | 直接设置和弦进行（手动输入或整体替换） |
| 32 | `replace_chord` | 替换指定位置的和弦 |
| 33 | `insert_chord` | 在指定位置插入和弦 |
| 34 | `remove_chord` | 删除指定位置的和弦 |
| 35 | `reharmonize` | 对指定范围重配和声（自动寻找风格内替代和弦） |
| 36 | `borrow_chord` | 在指定位置插入借用和弦（来自平行调） |
| 37 | `secondary_dominant` | 在目标和弦前插入副属和弦 (V/x) |
| 38 | `add_passing_chord` | 在两个和弦之间插入经过和弦 |
| 39 | `modulate` | 转调到新的调性（从指定位置开始） |
| 40 | `set_cadence` | 设置段落结尾的终止式类型 |
| 41 | `get_roman_analysis` | 获取当前和弦进行的罗马数字级数分析 |
| 42 | `get_chord_progression` | 获取当前和弦进行详情（含和弦名、位置、Roman） |

---

### 4.3 Phase 3: 旋律生成 (Melody Generation)

**前置**：Phase 2  
**目标**：基于和弦进行生成旋律，支持 15 种旋律操作技法，覆盖从生成到变换到发展的完整旋律创作流程。

#### 4.3.1 Phase 3 功能范围

**核心能力**：

- [x] 旋律生成：基于和弦进行 + 调性 + 约束条件自动生成旋律
- [x] 旋律重生成：保持相同约束重新随机生成
- [x] 旋律变换操作（6 种）：简化、复杂化、移调、倒影、逆行、模进
- [x] 旋律发展操作（4 种）：变奏、动机发展、延长、缩短
- [x] 乐句结构操作（3 种）：呼应句、Hook/记忆点、问答句式

**旋律生成参数**：

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| track_id | str | 目标音轨 | 必填 |
| section_id | str? | 目标段落 | 可选 |
| note_density | str | 音符密度 | "normal" |
| pitch_range_low | int | 最低音 MIDI (如 60=C4) | 60 |
| pitch_range_high | int | 最高音 MIDI (如 84=C6) | 84 |
| contour | str | 旋律轮廓 | "arch" |
| chord_tone_weight | float | 和弦音偏好权重 (0-1) | 0.7 |
| rhythm_complexity | str | 节奏复杂度 | "moderate" |

**生成参数选项**：

| 参数 | 选项 | 说明 |
|------|------|------|
| note_density | sparse / normal / dense | 稀疏(多长音) / 正常 / 密集(多短音) |
| contour | arch / ascending / descending / wave / flat | 拱形 / 上行 / 下行 / 波浪 / 平坦 |
| rhythm_complexity | simple / moderate / complex | 简单(四分音符为主) / 中等 / 复杂(含切分/附点/十六分) |

**15 种旋律操作详解**：

| # | 操作 | 说明 | 关键参数 |
|---|------|------|----------|
| 1 | Generate | 基于和弦+调性+约束自动生成旋律 | 生成参数（上表） |
| 2 | Regenerate | 保持约束重新随机生成（清除旧音符、重新生成） | track_id |
| 3 | Simplify | 减少音符、简化节奏（去装饰音、合并短音符） | strength (0-1) |
| 4 | Complexify | 增加经过音、装饰音、倚音 | strength (0-1) |
| 5 | Transpose | 按指定半音数移调 | semitones (int) |
| 6 | Invert | 以参考音为轴进行音程倒影 | pivot_pitch (int) |
| 7 | Reverse | 逆行（时间轴翻转所有音符） | — |
| 8 | Sequence | 将乐句按指定音程逐次模进 | interval (半音), count (次数) |
| 9 | Variation | 保持骨架音（强拍和弦音），变化经过音和节奏 | — |
| 10 | Develop | 取前 N 拍为动机，通过变形/扩展发展为更长乐句 | motif_beats (float) |
| 11 | Extend | 在末尾延长乐句（基于已有素材外推） | extra_beats (float) |
| 12 | Shorten | 从末尾截短乐句 | cut_beats (float) |
| 13 | Call Response | 基于已有乐句生成应答乐句 | response_style |
| 14 | Hook | 生成简短、重复、有记忆点的旋律片段 | hook_beats (float) |
| 15 | Question Answer | 生成"问-答"两段式旋律 | phrase_beats (float) |

**Call Response 响应风格**：

| 风格 | 说明 |
|------|------|
| mirror | 倒影呼应 |
| echo | 稍作变化的重复 |
| complement | 互补（高→低，密→疏） |

#### 4.3.2 Phase 3 MCP Tools 清单

| # | Tool | 说明 |
|---|------|------|
| 43 | `generate_melody` | 为指定音轨/段落生成旋律 |
| 44 | `regenerate_melody` | 保持约束重新生成旋律 |
| 45 | `simplify_melody` | 简化旋律 |
| 46 | `complexify_melody` | 复杂化旋律（加经过音/装饰音） |
| 47 | `transpose_melody` | 移调 |
| 48 | `invert_melody` | 音程倒影 |
| 49 | `reverse_melody` | 逆行 |
| 50 | `sequence_melody` | 模进 |
| 51 | `variation_melody` | 变奏 |
| 52 | `develop_motif` | 动机发展 |
| 53 | `extend_melody` | 延长乐句 |
| 54 | `shorten_melody` | 缩短乐句 |
| 55 | `call_response` | 呼应句 |
| 56 | `generate_hook` | 生成 Hook（记忆点旋律） |
| 57 | `question_answer` | 问答句式 |

---

### 4.4 Phase 4: Bass 与 Drums 生成 (Rhythm Section) (已完成 ✅)

**前置**：Phase 2 ✅  
**目标**：生成完整的节奏组，支持多种风格。Phase 4 结束即可产出「四大件小样」（钢琴+吉他+鼓+贝斯）。

#### 4.4.1 Phase 4 功能范围

**Bass 核心能力**：

- [ ] BassGenerator：基于和弦进行自动生成 Bass 线
- [ ] 8 种 Bass 模式，覆盖从简单到复杂的低音编配

**8 种 Bass 模式详解**：

| # | 模式 | 说明 | 典型风格 |
|---|------|------|----------|
| 1 | Root | 根音贝斯：每拍/每和弦只弹根音 | Pop, Rock 基础 |
| 2 | Octave | 八度贝斯：根音 + 八度交替 | Rock, Motown |
| 3 | Walking | 行走贝斯：半音/全音阶梯连接和弦音 | Jazz, Blues |
| 4 | Syncopation | 切分贝斯：弱拍/反拍强调 | Funk, R&B |
| 5 | Follow Chords | 跟随和弦：琶音式分解和弦音 | Pop Ballad |
| 6 | Independent | 独立旋律线：低音区独立旋律 | Progressive |
| 7 | Counter Bass | 对位低音：与主旋律反向运动 | Classical, Jazz |
| 8 | Generate | 通用模式：综合以上特征，根据风格自动选择 | 通用 |

**Bass 生成参数**：

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| track_id | str? | 目标音轨（空则自动创建 Bass 轨） | 可选 |
| section_id | str? | 目标段落 | 可选 |
| bass_mode | str | Bass 模式 | "generate" |
| note_density | str | 密度 (sparse/normal/dense) | "normal" |
| octave | int | 八度 (1=低, 2=中, 3=高) | 2 |

**Drums 核心能力**：

- [ ] DrumsGenerator：基于风格生成完整鼓组节奏
- [ ] 8 种鼓风格预设，完整覆盖主流音乐风格
- [ ] 细粒度鼓元素控制：逐元素设置/替换/删除
- [ ] 过门(Fill)和装饰(Ghost Note)智能插入

**8 种鼓风格预设**：

| 风格 | Kick 特征 | Snare 特征 | HiHat 特征 | 附加元素 |
|------|-----------|-----------|-----------|----------|
| Rock | 1,3 拍 | 2,4 拍 | 8分音符 | Crash 段首 |
| Pop | 1,3 拍（轻） | 2,4 拍 | 8分音符/闭合 | — |
| Jazz | 弱、随机 | 刷奏感 | — | Ride 主导 |
| Metal | 双踩、16分 | 2,4 拍（重） | 16分/开合 | Double Kick |
| EDM | Four-on-floor | Clap 2,4 | Offbeat 开踩镲 | 合成打击 |
| Anime | 1,3 拍（清晰） | 2,4 拍 | 8分音符 | 轻快节奏 |
| Latin | Tumbao 节奏 | 交替 | — | Conga/Clave/Cowbell |
| Swing | Shuffle 感 | 2,4 拍（刷） | — | Ride Swing |

**GM Percussion Map（Phase 4 使用的打击乐 MIDI Pitch）**：

| Pitch | 名称 | 分类 |
|-------|------|------|
| 35 | Acoustic Bass Drum | Kick |
| 36 | Bass Drum 1 | Kick |
| 37 | Side Stick | Snare |
| 38 | Acoustic Snare | Snare |
| 39 | Hand Clap | Snare |
| 40 | Electric Snare | Snare |
| 41 | Low Floor Tom | Tom |
| 42 | Closed Hi-Hat | HiHat |
| 43 | High Floor Tom | Tom |
| 44 | Pedal Hi-Hat | HiHat |
| 45 | Low Tom | Tom |
| 46 | Open Hi-Hat | HiHat |
| 47 | Low-Mid Tom | Tom |
| 48 | Hi-Mid Tom | Tom |
| 49 | Crash Cymbal 1 | Crash |
| 50 | High Tom | Tom |
| 51 | Ride Cymbal 1 | Ride |
| 53 | Ride Bell | Ride |
| 54 | Tambourine | Percussion |
| 56 | Cowbell | Percussion |
| 57 | Crash Cymbal 2 | Crash |
| 75 | Claves | Percussion |

**鼓细节控制**：

| 操作 | 说明 |
|------|------|
| set_hihat_pattern | 设置踩镲模式：8ths / 16ths / offbeat / open_close |
| set_kick_pattern | 设置底鼓模式：straight / offbeat / double / four_on_floor |
| set_snare_pattern | 设置小鼓模式：backbeat / ghost / rimshot |
| add_ghost_notes | 在小鼓上添加幽灵音（低力度装饰） |
| add_drum_fill | 在指定位置插入过门 |
| add_crash | 在段首/重拍添加镲片 |
| set_ride_pattern | 设置叮叮镲模式 |
| add_tom_fill | 添加嗵鼓过门 |
| add_percussion | 添加打击乐（Tambourine/Cowbell/Claves 等） |
| clear_drum_element | 清除特定鼓元素 |

#### 4.4.2 Phase 4 数据模型变更

| 新增模型/枚举 | 说明 |
|--------------|------|
| `BassMode` 枚举 | root, octave, walking, syncopation, follow_chords, independent, counter_bass, generate |
| `DrumStyle` 枚举 | rock, pop, jazz, metal, edm, anime, latin, swing |
| `HiHatPattern` 枚举 | eighths, sixteenths, offbeat, open_close |
| `KickPattern` 枚举 | straight, offbeat, double, four_on_floor |
| `SnarePattern` 枚举 | backbeat, ghost, rimshot |
| `GM_PERCUSSION` 常量 | Kick/Snare/HiHat/Tom/Crash/Ride/Percussion 的 MIDI pitch 映射 |

> **无 Song 模型变更**：Bass 和 Drums 的输出都是 Note（pitch + start_beat + duration_beat + velocity），直接写入 Track.notes。鼓使用 GM Percussion pitch。

#### 4.4.3 Phase 4 MCP Tools 清单

**Bass Tools (#58-#62)**：

| # | Tool | 说明 |
|---|------|------|
| 58 | `generate_bass` | 生成 Bass 线（bass_mode: root/walking/octave/syncopation/follow_chords/independent/counter_bass/generate） |
| 59 | `regenerate_bass` | 重新生成 Bass（保持当前模式） |
| 60 | `set_bass_pattern` | 直接设置 Bass 音符序列 |
| 61 | `simplify_bass` | 简化 Bass（减少经过音） |
| 62 | `transpose_bass` | Bass 移调（+/- 八度或半音） |

**Drums Tools (#63-#75)**：

| # | Tool | 说明 |
|---|------|------|
| 63 | `generate_drums` | 生成完整鼓组（style: rock/pop/jazz/metal/edm/anime/latin/swing） |
| 64 | `regenerate_drums` | 重新生成鼓组 |
| 65 | `set_drum_style` | 切换鼓风格预设 |
| 66 | `add_drum_fill` | 在指定位置插入过门 |
| 67 | `add_ghost_notes` | 添加幽灵音 |
| 68 | `set_hihat_pattern` | 设置踩镲模式 |
| 69 | `set_kick_pattern` | 设置底鼓模式 |
| 70 | `set_snare_pattern` | 设置小鼓模式 |
| 71 | `add_crash` | 添加镲片 |
| 72 | `set_ride_pattern` | 设置叮叮镲模式 |
| 73 | `add_tom_fill` | 添加嗵鼓过门 |
| 74 | `add_percussion` | 添加打击乐元素 |
| 75 | `clear_drum_element` | 清除指定鼓元素 |

---

### 4.5 Phase 5: 扩展乐器与编曲 (Extended Instruments & Arrangement) (已完成 ✅)

**前置**：Phase 3 ✅ + Phase 4 ✅  
**目标**：补齐弦乐、管乐、合成器等扩展乐器，加入编曲智能控制。Phase 5 结束即可产出「合格小样」。

#### 4.5.1 Phase 5 功能范围

**扩展乐器生成器（6 种）**：

| 乐器 | 模式 | 音域 (MIDI) | 说明 |
|------|------|-----------|------|
| Strings | sustained / melody / counterpoint / tremolo / pizzicato | 55-88 (G3-E6) | 弦乐组 |
| Brass | stabs / sustained / fanfare / solo_line | 53-82 (F3-Bb5) | 铜管组 |
| Woodwinds | stabs / sustained / solo_line / trill | 60-96 (C4-C7) | 木管组 |
| Synth | pad / lead / arp / fx | 36-96 | 合成器 |
| Piano (高级) | block_chords / broken_chords / arpeggio / comping | 36-96 | 钢琴配器 |
| Guitar (高级) | strum / fingerpick / arpeggio / muted | 40-84 (E2-C6) | 吉他配器 |

**各乐器模式详解**：

**Strings 弦乐**：

| 模式 | 说明 |
|------|------|
| sustained | 持续和弦：长音和弦铺底（Pad 效果） |
| melody | 旋律线：弦乐主旋律或副旋律 |
| counterpoint | 对位：与主旋律形成对位关系 |
| tremolo | 震音：快速重复同音（紧张/激动） |
| pizzicato | 拨弦：短促弹奏（轻快/俏皮） |

**Brass 铜管**：

| 模式 | 说明 |
|------|------|
| stabs | 短音型：节奏性重音打击 |
| sustained | 持续音：长音铺底或渐强 |
| fanfare | 号角：宣告式旋律片段 |
| solo_line | 独奏线：铜管独奏旋律 |

**Synth 合成器**：

| 模式 | 说明 |
|------|------|
| pad | 铺底：长音和弦垫底 |
| lead | 主奏：合成器主旋律 |
| arp | 琶音：自动琶音器效果 |
| fx | 音效：噪音扫描/上升/下降特效 |

**Piano 钢琴高级模式**：

| 模式 | 说明 |
|------|------|
| block_chords | 柱式和弦：同时弹奏和弦所有音 |
| broken_chords | 分解和弦：逐音弹奏和弦 |
| arpeggio | 琶音：上行/下行琶音 |
| comping | 即兴伴奏：爵士式节奏化和弦 |

**Guitar 吉他高级模式**：

| 模式 | 说明 |
|------|------|
| strum | 扫弦：节奏吉他 |
| fingerpick | 指弹：分指拨弦 |
| arpeggio | 分解和弦：琶音式 |
| muted | 闷音：Palm Mute 效果 |

**编曲操作（11 种）**：

| # | 操作 | 说明 | 关键参数 |
|---|------|------|----------|
| 1 | Increase Energy | 增加能量（添加乐器层/加密度/提力度） | section_id, amount(0-1) |
| 2 | Decrease Energy | 减少能量（简化/降力度/减层） | section_id, amount(0-1) |
| 3 | Increase Density | 增加音符密度（加细分/装饰音） | section_id, amount(0-1) |
| 4 | Decrease Density | 减少音符密度（简化/合并） | section_id, amount(0-1) |
| 5 | Add Layer | 添加乐器层（智能推荐乐器） | section_id, instrument_type? |
| 6 | Remove Layer | 移除乐器层 | section_id, track_id |
| 7 | Build Up | 渐进累积（从简到繁，适合段落前过渡） | target_beat, build_beats |
| 8 | Break Down | 拆解（从繁到简，只留核心） | section_id |
| 9 | Transition | 段落过渡（自动生成段间连接） | from_section_id, to_section_id |
| 10 | Fill | 段内填充（鼓/贝斯/旋律 fill） | section_id, beat_position |
| 11 | Silence | 静默（清空指定段落指定音轨） | section_id, track_id? |

**Track 高级属性（Phase 5 新增）**：

| 属性 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| octave_offset | int | 八度偏移 (-3 到 +3) | 0 |
| density | float | 音符密度 (0-1) | 0.5 |
| energy | float | 能量级别 (0-1) | 0.5 |

#### 4.5.2 Phase 5 数据模型变更

| 新增模型/枚举 | 说明 |
|--------------|------|
| `StringsMode` 枚举 | sustained, melody, counterpoint, tremolo, pizzicato |
| `BrassMode` 枚举 | stabs, sustained, fanfare, solo_line |
| `WoodwindsMode` 枚举 | stabs, sustained, solo_line, trill |
| `SynthMode` 枚举 | pad, lead, arp, fx |
| `PianoMode` 枚举 | block_chords, broken_chords, arpeggio, comping |
| `GuitarMode` 枚举 | strum, fingerpick, arpeggio, muted |

| 已有模型变更 | 说明 |
|-------------|------|
| `Track` 新增字段 | `octave_offset: int = 0`, `density: float = 0.5`, `energy: float = 0.5` |

#### 4.5.3 Phase 5 MCP Tools 清单

**Extended Instruments (#76-#81)**：

| # | Tool | 说明 |
|---|------|------|
| 76 | `generate_strings` | 弦乐生成（strings_mode: sustained/melody/counterpoint/tremolo/pizzicato） |
| 77 | `generate_brass` | 铜管生成（brass_mode: stabs/sustained/fanfare/solo_line） |
| 78 | `generate_woodwinds` | 木管生成（woodwinds_mode: stabs/sustained/solo_line/trill） |
| 79 | `generate_synth` | 合成器生成（synth_mode: pad/lead/arp/fx） |
| 80 | `generate_piano_part` | 钢琴配器（piano_mode: block_chords/broken_chords/arpeggio/comping） |
| 81 | `generate_guitar_part` | 吉他配器（guitar_mode: strum/fingerpick/arpeggio/muted） |

**Arrangement (#82-#92)**：

| # | Tool | 说明 |
|---|------|------|
| 82 | `increase_energy` | 增加段落能量 |
| 83 | `decrease_energy` | 减少段落能量 |
| 84 | `increase_density` | 增加音符密度 |
| 85 | `decrease_density` | 减少音符密度 |
| 86 | `add_layer` | 添加乐器层 |
| 87 | `remove_layer` | 移除乐器层 |
| 88 | `build_up` | 渐进累积 |
| 89 | `break_down` | 拆解简化 |
| 90 | `add_transition` | 段落过渡 |
| 91 | `add_fill` | 填充 |
| 92 | `add_silence` | 静默 |

**Track Advanced (#93-#95)**：

| # | Tool | 说明 |
|---|------|------|
| 93 | `set_track_octave` | 设置音轨八度偏移 |
| 94 | `set_track_density` | 设置音轨密度 |
| 95 | `set_track_energy` | 设置音轨能量级别 |

---

### 4.6 Phase 6: 人性化与风格 (Humanize & Style)

**前置**：Phase 5 ✅  
**目标**：让机械的 MIDI 听起来更像真人演奏，支持一键应用风格预设。Phase 6 结束即可产出「高品质小样」。

#### 4.6.1 Phase 6 功能范围

**人性化系统 (Humanize) — 8 种操作**：

| # | 操作 | 说明 | 关键参数 |
|---|------|------|----------|
| 1 | Timing Random | 时值随机偏移：每个音符 start_beat ± 随机偏移 | amount (0-1), track_id, section_id? |
| 2 | Velocity Random | 力度随机偏移：每个音符 velocity ± 随机偏移 | amount (0-1), track_id, section_id? |
| 3 | Micro Timing | 微时值调整：对特定拍位施加固定偏移 | beat_offsets: dict[拍位→偏移量] |
| 4 | Groove Template | 应用 Groove 模板：预设的 timing/velocity 偏移模式 | groove_name, track_id, section_id? |
| 5 | Swing | 摇摆感：弱拍（偶数8分）延迟，形成 shuffle 效果 | swing_amount (0-1), track_id, section_id? |
| 6 | Push | 抢拍：所有音符提前微量 | amount (0-1), track_id, section_id? |
| 7 | Pull | 拖拍：所有音符推迟微量 | amount (0-1), track_id, section_id? |
| 8 | Hand Played Feel | 手弹模拟：综合应用微量 timing + velocity + duration 随机化 | intensity (0-1), track_id, section_id? |

**Groove 模板库**：

| 模板名 | 说明 | Timing 特征 | Velocity 特征 |
|--------|------|------------|--------------|
| straight | 直拍（无偏移，基准参照） | 无偏移 | 均匀 |
| swing_light | 轻微摇摆 | 弱拍延迟 10-20ms | 弱拍 -5 |
| swing_heavy | 重摇摆 | 弱拍延迟 30-50ms | 弱拍 -10 |
| funk | 放克律动 | 16分音符错位 | 强拍+重音交替 |
| bossa | Bossa Nova | 切分拍位微偏 | 轻重交替 |
| shuffle | 洗牌感 | 三连音化弱拍 | 弱拍轻 |
| human_piano | 手弹钢琴 | ±5-15ms 随机 | ±3-8 随机 |
| human_guitar | 手弹吉他 | ±8-20ms 随机 | ±5-10 随机 |
| human_drums | 手打鼓 | ±5-10ms 随机 | ±5-15 随机 |
| laid_back | 慵懒/延迟感 | 整体延迟 10-20ms | 较轻 -5 |

**风格系统 (Style Engine) — 13 种内置风格**：

| 风格 | 推荐乐器 | 和弦倾向 | 节奏特征 | Humanize 预设 | 能量曲线 |
|------|---------|---------|---------|-------------|---------|
| Anime | Piano, Strings, Drums, Bass | royal_road, komuro | 8ths HH, 明快 | straight | 中-高-中 |
| City Pop | Guitar, Bass, Synth, Drums | jazz_turnaround, 7th | Funk groove | funk | 中稳 |
| Jazz | Piano, Bass, Drums | ii-V-I, turnaround | Swing | swing_heavy | 中 |
| Rock | Guitar, Bass, Drums | I-IV-V, power | Straight 8ths | straight | 高 |
| Metal | Guitar, Bass, Drums | power, dim | Double kick | straight | 极高 |
| EDM | Synth, Drums, Bass | simple, loop | Four-on-floor | straight | 构建-释放 |
| Lofi | Piano, Guitar, Drums | 7th, 9th | Swing shuffle | laid_back | 低稳 |
| Classical | Piano, Strings, Brass, Woodwinds | diatonic | 自由节奏 | human_piano | 渐变 |
| Orchestra | Strings, Brass, Woodwinds | 丰富 | 指挥弹性 | human_piano | 大起伏 |
| Game Music | Synth, Strings, Drums | epic | 进行曲/战斗 | straight | 高 |
| Ambient | Pad, Synth, FX | suspended, open | 无节拍 | straight | 极低 |
| Synthwave | Synth, Bass, Drums | minor, retro | 4-on-floor | straight | 中-高 |
| Future Bass | Synth, Drums, Bass | 7th, add9 | 切分/sidechained | straight | 构建-drop |

**风格预设包含的配置项**：

| 配置项 | 说明 |
|--------|------|
| recommended_instruments | 推荐乐器列表（按优先级排序） |
| chord_templates | 推荐使用的和弦进行模板 |
| tempo_range | 建议 BPM 范围 (min, max) |
| time_signature | 建议拍号 |
| drum_style | 推荐鼓风格（映射到 DrumStyle 枚举） |
| bass_mode | 推荐 Bass 模式（映射到 BassMode 枚举） |
| humanize_preset | 推荐 Groove 模板 |
| energy_curve | 能量曲线模板 [段落→能量级别] |
| velocity_range | 建议力度范围 (min, max) |
| swing | 建议 swing 值 |

**Style Mix（风格混合）**：

- 支持混合 2 种风格，按权重融合
- 混合规则：取两个风格的配置加权平均（数值型）或随机选择（离散型）
- 示例：`Anime + Jazz (0.6:0.4)` → 60% Anime 乐器/和弦 + 40% Jazz Groove/Humanize

#### 4.6.2 Phase 6 数据模型变更

| 新增模型/枚举 | 说明 |
|--------------|------|
| `HumanizeType` 枚举 | timing_random, velocity_random, micro_timing, groove, swing, push, pull, hand_played |
| `GrooveName` 枚举 | straight, swing_light, swing_heavy, funk, bossa, shuffle, human_piano, human_guitar, human_drums, laid_back |
| `StylePreset` 枚举 | anime, city_pop, jazz, rock, metal, edm, lofi, classical, orchestra, game_music, ambient, synthwave, future_bass |

| 已有模型变更 | 说明 |
|-------------|------|
| `GlobalSettings` 新增字段 | `swing: float = 0.0`, `groove: str = "straight"`, `style: str = ""`, `mood: str = ""` |

> **设计决策**：Humanize 操作直接修改 Note 的 start_beat / velocity / duration_beat，是不可逆的（但可 Undo）。Style 是元数据，影响 AI 的生成建议但不直接修改音符。

#### 4.6.3 Phase 6 MCP Tools 清单

**Humanize (#96-#103)**：

| # | Tool | 说明 |
|---|------|------|
| 96 | `humanize_timing` | 时值随机偏移 |
| 97 | `humanize_velocity` | 力度随机偏移 |
| 98 | `apply_micro_timing` | 微时值调整 |
| 99 | `apply_groove` | 应用 Groove 模板 |
| 100 | `apply_swing` | 应用摇摆感 |
| 101 | `push_timing` | 抢拍 |
| 102 | `pull_timing` | 拖拍 |
| 103 | `hand_played_feel` | 手弹模拟 |

**Style (#104-#109)**：

| # | Tool | 说明 |
|---|------|------|
| 104 | `set_style` | 设置/应用风格预设 |
| 105 | `mix_styles` | 混合两种风格 |
| 106 | `get_style_guide` | 获取当前风格的建议操作 |
| 107 | `set_mood` | 设置情绪标签 |
| 108 | `set_swing` | 设置全局 Swing 值 |
| 109 | `set_groove` | 设置全局 Groove 模板 |

---

### 4.7 Phase 7: 分析引擎 (Analysis Engine)

**前置**：Phase 2 ✅ + Phase 3 ✅  
**目标**：为歌曲提供多维度分析能力，支撑 AI 的智能编辑决策。

#### 4.7.1 Phase 7 功能范围

**18 种分析功能**：

| # | 分析项 | 输入 | 输出 | 说明 |
|---|--------|------|------|------|
| 1 | Key Detection | Song | Key + Mode + confidence | 检测歌曲实际调性（基于音符统计） |
| 2 | Tempo Analysis | Song | BPM + stability% | 分析节奏稳定性 |
| 3 | Chord Recognition | Track notes | list[Chord] | 从音符推断和弦进行 |
| 4 | Phrase Detection | Track | list[Phrase(start, end)] | 检测旋律乐句边界 |
| 5 | Motif Detection | Track | list[Motif(pitches, rhythm, occurrences)] | 识别重复出现的短旋律动机 |
| 6 | Rhythm Analysis | Track | RhythmProfile(dominant_value, syncopation%, complexity) | 分析节奏模式特征 |
| 7 | Density Map | Song/Track | list[(beat, note_count)] | 音符密度随时间的分布 |
| 8 | Energy Curve | Song | list[(beat, energy_level)] | 能量曲线（基于密度+力度+音高） |
| 9 | Range Analysis | Track | (lowest_pitch, highest_pitch, span, avg_pitch) | 音域分析 |
| 10 | Repetition Detection | Track | list[RepeatPattern(pattern, count, positions)] | 检测重复模式 |
| 11 | Voice Leading | Song | list[VoiceLeadingIssue(beat, description)] | 声部进行检查（平行五/八度等） |
| 12 | Cadence Detection | Song | list[(beat, CadenceType)] | 检测终止式 |
| 13 | Counterpoint | Song (2 tracks) | CounterpointReport(parallel%, contrary%, oblique%) | 对位法分析 |
| 14 | Style Detection | Song | StyleMatch(style, confidence%) | 风格识别 |
| 15 | Mood Detection | Song | MoodProfile(valence, arousal, tags[]) | 情绪检测（基于调性/速度/音域） |
| 16 | Complexity Score | Song/Track | float (0-100) | 复杂度评分 |
| 17 | Dynamic Analysis | Song/Track | DynamicProfile(range, avg, contour) | 力度变化分析 |
| 18 | Structure Analysis | Song | list[StructureSegment(type, start, end, similarity_to[])] | 曲式结构分析 |

**AnalysisCache**：

- 每次分析结果缓存在 Song 中，避免重复计算
- 当 Song 被修改（任何 Command 执行后），对应缓存自动失效
- 缓存策略：以 `(analysis_type, track_id?)` 为 key

**综合分析报告 (Full Report)**：

- 一键生成歌曲的全维度分析
- 包含：调性、节奏、和弦、密度、能量、音域、复杂度、结构
- 输出 JSON 格式，适合 LLM 读取和决策

#### 4.7.2 Phase 7 数据模型变更

| 新增模型 | 说明 |
|----------|------|
| `AnalysisResult` | 通用分析结果容器 (type, data, timestamp) |
| `Phrase` | 乐句 (start_beat, end_beat) |
| `Motif` | 动机 (pitches, rhythm, occurrences) |
| `RhythmProfile` | 节奏特征 (dominant_value, syncopation_ratio, complexity) |
| `VoiceLeadingIssue` | 声部进行问题 (beat, type, description) |
| `CounterpointReport` | 对位分析报告 |
| `StyleMatch` | 风格匹配结果 |
| `MoodProfile` | 情绪分析结果 |
| `DynamicProfile` | 力度分析结果 |
| `StructureSegment` | 曲式结构段 |

| 已有模型变更 | 说明 |
|-------------|------|
| `Song` 新增字段 | `analysis_cache: dict[str, AnalysisResult] = {}` |

#### 4.7.3 Phase 7 MCP Tools 清单

**Individual Analysis (#110-#127)**：

| # | Tool | 说明 |
|---|------|------|
| 110 | `analyze_key` | 调性检测 |
| 111 | `analyze_tempo` | 速度/节奏稳定性分析 |
| 112 | `analyze_chords` | 从音符推断和弦 |
| 113 | `analyze_phrases` | 乐句边界检测 |
| 114 | `analyze_motifs` | 动机识别 |
| 115 | `analyze_rhythm` | 节奏模式分析 |
| 116 | `analyze_density` | 密度分布图 |
| 117 | `analyze_energy` | 能量曲线 |
| 118 | `analyze_range` | 音域分析 |
| 119 | `analyze_repetition` | 重复模式检测 |
| 120 | `analyze_voice_leading` | 声部进行检查 |
| 121 | `analyze_cadences` | 终止式检测 |
| 122 | `analyze_counterpoint` | 对位法分析 |
| 123 | `analyze_style` | 风格识别 |
| 124 | `analyze_mood` | 情绪检测 |
| 125 | `analyze_complexity` | 复杂度评分 |
| 126 | `analyze_dynamics` | 力度变化分析 |
| 127 | `analyze_structure` | 曲式结构分析 |

**Report (#128)**：

| # | Tool | 说明 |
|---|------|------|
| 128 | `get_full_analysis` | 生成综合分析报告 |

---

## 五、Roadmap

> 详细功能规格见第四章各 Phase 子节。本章为概览。

### Phase 1: 核心基础 (Core Foundation) ✅

**MCP Tools**：35 个 | **状态**：已完成

**交付物**：数据模型 + Command 系统 + Composer 引擎 + Pipeline + MIDI 渲染器 + JSON 持久化 + MCP Server + 单元测试

> 详见 4.1 节

---

### Phase 2: 和声与和弦系统 (Harmony & Chords) ✅

**前置**：Phase 1 ✅ | **新增 MCP Tools**：13 个（#30-#42）

**交付物**：
- Music Theory 基础模块（音阶计算 + 音程工具 + 和弦拼写 — Phase 2/3 共用）
- Chord / ChordQuality / CadenceType 数据模型
- ChordGenerator（基于调性和风格生成常用和弦进行 + 15 个内置模板）
- 11 个 Chord Commands + 13 个 MCP Tools
- 和声操作：Generate, Set, Replace, Insert, Remove, Reharmonize, Borrow, Secondary Dominant, Passing, Modulate, Cadence
- Roman Analysis（罗马数字级数分析）

> 详见 4.2 节

---

### Phase 3: 旋律生成 (Melody Generation) ✅

**前置**：Phase 2 | **新增 MCP Tools**：15 个（#43-#57）

**交付物**：
- MelodyGenerator（基于和弦 + 调性 + 多维约束条件自动生成旋律）
- 15 种旋律操作：Generate, Regenerate, Simplify, Complexify, Transpose, Invert, Reverse, Sequence, Variation, Develop, Extend, Shorten, Call Response, Hook, Question Answer
- 15 个 Melody Commands + 15 个 MCP Tools

> 详见 4.3 节

---

### Phase 4: Bass 与 Drums 生成 (Rhythm Section) ✅

**前置**：Phase 2 ✅ | **新增 MCP Tools**：18 个（#58-#75） | **状态**：已完成

**交付物**：
- BassGenerator：8 种 Bass 模式（Generate, Walking, Root, Octave, Syncopation, Follow Chords, Independent, Counter Bass）
- DrumsGenerator + 鼓模板系统
- BassMode / DrumStyle / HiHatPattern / KickPattern / SnarePattern 枚举 + GM_PERCUSSION 常量
- 8 种鼓风格预设（Rock, Pop, Jazz, Metal, EDM, Anime, Latin, Swing）
- 鼓细节控制：Ghost Note, Fill, Crash, Ride, HiHat, Snare, Kick, Tom, Percussion
- 5 个 Bass Commands + 13 个 Drums Commands + 18 个 MCP Tools

> 详见 4.4 节

**里程碑**：四大件小样可用

---

### Phase 5: 扩展乐器与编曲 (Extended Instruments & Arrangement) ✅

**前置**：Phase 3 ✅ + Phase 4 ✅ | **新增 MCP Tools**：20 个（#76-#95） | **状态**：已完成

**交付物**：
- 6 种扩展乐器生成器：Strings(5模式), Brass(4模式), Woodwinds(4模式), Synth(4模式), Piano高级(4模式), Guitar高级(4模式)
- StringsMode / BrassMode / WoodwindsMode / SynthMode / PianoMode / GuitarMode 枚举
- ArrangementEngine：11 种编曲操作（Increase/Decrease Energy/Density, Add/Remove Layer, Build Up, Break Down, Transition, Fill, Silence）
- Track 高级属性：octave_offset, density, energy
- 6 个乐器 Commands + 11 个编曲 Commands + 3 个 Track Commands + 20 个 MCP Tools

> 详见 4.5 节

**里程碑**：合格小样可用（四大件 + 弦乐 + 管乐 + 合成器 + 编曲控制）

---

### Phase 6: 人性化与风格 (Humanize & Style) ✅

**前置**：Phase 5 ✅ | **新增 MCP Tools**：14 个（#96-#109） | **状态**：已完成

**交付物**：
- HumanizeEngine：8 种人性化操作（Timing Random, Velocity Random, Micro Timing, Groove, Swing, Push, Pull, Hand Played Feel）
- StyleEngine：13 种内置风格预设 + Style Mix（风格混合） + Style Guide
- 10 种 Groove 模板（straight, swing_light, swing_heavy, funk, bossa, shuffle, human_piano, human_guitar, human_drums, laid_back）
- HumanizeType / GrooveName / StylePreset 枚举
- GlobalSettings 新增字段：swing, groove, style, mood
- 8 个 Humanize Commands + 5 个 Style Commands + 14 个 MCP Tools

> 详见 4.6 节

**里程碑**：高品质小样可用

---

### Phase 7: 分析引擎 (Analysis Engine) ✅

**前置**：Phase 2 ✅ + Phase 3 ✅ | **新增 MCP Tools**：19 个（#110-#128） | **状态**：已完成

**交付物**：
- AnalysisEngine：18 种分析功能（Key, Tempo, Chord, Phrase, Motif, Rhythm, Density, Energy, Range, Repetition, Voice Leading, Cadence, Counterpoint, Style, Mood, Complexity, Dynamic, Structure）
- AnalysisCache（Song 级缓存，Command 执行后自动失效）
- 综合分析报告（get_full_analysis）
- 10 种分析结果模型（AnalysisResult, Phrase, Motif, RhythmProfile, VoiceLeadingIssue, CounterpointReport, StyleMatch, MoodProfile, DynamicProfile, StructureSegment）
- Song 新增 analysis_cache 字段
- 19 个 Analysis Commands + 19 个 MCP Tools

> 详见 4.7 节

**里程碑**：智能分析可用

---

### Phase 8: Track 自动化 (Automation) ✅

**前置**：Phase 5 ✅ | **新增 MCP Tools**：9 个（#129-#137）

**交付物**：
- AutomationEngine：6 种自动化操作 + 7 种预设自动化
- AutomationParam / AutomationPoint / AutomationCurve / Marker 数据模型
- Track 新增 automation 字段 + Song 新增 markers 字段
- Marker 标记系统（3 种操作）
- 6 个 Automation Commands + 3 个 Marker Commands + 9 个 MCP Tools

> 详见 4.8 节

**里程碑**：精细控制可用

---

### Phase 9: 插件架构 (Plugin System) ✅

**前置**：Phase 1-8 核心功能稳定 | **新增 MCP Tools**：4 个（#138-#141）

**交付物**：
- PluginManager：插件发现、注册、加载、调用、卸载
- 5 种插件类型：Generator, Analyzer, Pattern, Style, Renderer
- 插件清单文件 (plugin.json) 规范
- PluginType / PluginInfo 数据模型
- 4 个 MCP Tools

> 详见 4.9 节

**里程碑**：第三方扩展可用

---

### Phase 10: MusicXML 导出 (MusicXML Export) ✅

**前置**：Phase 1 ✅ | **新增 MCP Tools**：2 个（#142-#143）

**交付物**：
- MusicXMLRenderer：Note/Track/Section → MusicXML 转换 + 节奏量化 + 力度映射
- 2 个 MCP Tools（导出 + 预览）

> 详见 4.10 节

**里程碑**：MIDI + MusicXML 双格式

---

### Phase 11: 可观测性 (Observability) ✅

**前置**：Phase 1 ✅ | **新增 MCP Tools**：3 个（#150-#152）

**交付物**：
- 结构化日志系统（Server/Engine/System 三层）
- 启动 Banner + 加载摘要
- Tool 调用日志（名称、参数摘要、耗时、结果）
- Command 执行日志 + 错误 traceback
- 运行统计（uptime、调用次数、Song 摘要）
- 环境变量控制（日志级别、文件输出、Banner 开关）
- 3 个 MCP Tools（统计查询 + Song 摘要 + 动态日志级别）

> 详见 4.11 节

**里程碑**：运行状态可观测

---

### Phase 12: 属性补全 (Property Completion) ✅

**前置**：Phase 1 ✅ | **新增 MCP Tools**：14 个（#153-#166）

**交付物**：
- 全局设置补全：Scale、Master Timing、Global Energy 属性 + Song Length 计算属性
- 段落操作补全：交换、拆分、合并 3 个新操作
- 音轨属性补全：Register、Complexity、Velocity Offset、Timing Offset、Humanize、Groove、Rhythm、Range 8 个新属性
- 14 个 MCP Tools

> 详见 4.12 节

**里程碑**：全属性可控

---

### Phase 13: MIDI 导入 (MIDI Import) ✅

**前置**：Phase 1 ✅ | **新增 MCP Tools**：3 个（#167-#169）

**交付物**：
- MidiImporter 模块：MIDI 文件解析 → Song 模型
- GM Program → InstrumentType 反向映射
- Seconds → Beats 时间转换
- 全量导入 / 单轨导入 / 预览 三种模式
- 3 个 MCP Tools

> 详见 4.13 节

**里程碑**：可导入已有 MIDI

---

### Roadmap 总览

| Phase | 名称 | 新增 Tools | 累计 | 里程碑 |
|-------|------|-----------|------|--------|
| 1 | 核心基础 | 35 | 35 | 引擎可用 ✅ |
| 2 | 和声系统 | 13 | 48 | 和弦进行可生成 ✅ |
| 3 | 旋律生成 | 15 | 63 | 旋律可生成 ✅ |
| 4 | 节奏组 | 18 | 81 | **四大件小样** ✅ |
| 5 | 扩展乐器与编曲 | 20 | 101 | **合格小样** ✅ |
| 6 | 人性化与风格 | 14 | 115 | 高品质小样 ✅ |
| 7 | 分析引擎 | 19 | 134 | 智能分析可用 ✅ |
| 8 | 自动化 | 9 | 143 | 精细控制可用 ✅ |
| 9 | 插件架构 | 4 | 147 | 第三方扩展可用 ✅ |
| 10 | MusicXML 导出 | 2 | 149 | MIDI + MusicXML ✅ |
| 11 | 可观测性 | 3 | 152 | 运行状态可观测 ✅ |
| 12 | 属性补全 | 14 | 166 | 全属性可控 ✅ |
| 13 | MIDI 导入 | 3 | 169 | 可导入已有 MIDI ✅ |

> §三 中仍有 4 个 🔜 条目（Pattern、Articulation、Harmony、Counter Melody）属于远期规划。

---

*本文档随项目进展持续更新。Phase 1-13 全部完成，169 个 MCP Tools 已注册。§三中仅剩 4 个 🔜 条目（Pattern、Articulation、Harmony、Counter Melody）属于远期规划。*

---

### 4.8 Phase 8: Track 自动化 (Automation)

**前置**：Phase 5 ✅  
**目标**：精细控制音轨参数随时间的变化，让 MIDI 更具表现力。

#### 4.8.1 Phase 8 功能范围

**自动化参数类型 (AutomationParam)**：

| 参数 | CC编号 | 范围 | 说明 |
|------|--------|------|------|
| volume | CC 7 | 0-127 | 音量自动化 |
| pan | CC 10 | 0-127 (64=中) | 声像自动化 |
| expression | CC 11 | 0-127 | 表情控制 |
| modulation | CC 1 | 0-127 | 调制轮 |
| sustain | CC 64 | 0/127 | 延音踏板 |

**自动化曲线 (AutomationCurve)**：

- 每条曲线由一系列控制点（breakpoint）组成：`(beat, value)`
- 支持线性插值（两点之间平滑过渡）
- 每个 Track 可有多条曲线（每个参数一条）

**自动化操作 — 6 种**：

| # | 操作 | 说明 | 关键参数 |
|---|------|------|----------|
| 1 | Add Automation | 添加自动化曲线 | track_id, param, points[] |
| 2 | Remove Automation | 移除自动化曲线 | track_id, param |
| 3 | Add Point | 添加控制点 | track_id, param, beat, value |
| 4 | Remove Point | 移除控制点 | track_id, param, point_index |
| 5 | Apply Preset | 应用预设自动化 | track_id, preset_name, start_beat, end_beat |
| 6 | Clear All Automation | 清除音轨所有自动化 | track_id |

**预设自动化**：

| 预设名 | 说明 | 效果 |
|--------|------|------|
| fade_in | 渐强 | volume: 0 → 目标值 |
| fade_out | 渐弱 | volume: 当前值 → 0 |
| crescendo | 渐强(expression) | expression: 低 → 高 |
| decrescendo | 渐弱(expression) | expression: 高 → 低 |
| pan_sweep_lr | 声像左→右 | pan: 0 → 127 |
| pan_sweep_rl | 声像右→左 | pan: 127 → 0 |
| swell | 鼓胀(先强后弱) | expression: 低→高→低 |

**Marker 标记系统**：

- Marker 是时间轴上的标注点，标记重要位置
- 属性：`beat` (位置)、`label` (文本)、`color` (可选颜色标签)
- 用途：标记段落入口、排练标记、关键变化点

**Marker 操作 — 3 种**：

| # | 操作 | 说明 |
|---|------|------|
| 1 | Add Marker | 添加标记 |
| 2 | Remove Marker | 移除标记 |
| 3 | List Markers | 列出所有标记 |

#### 4.8.2 Phase 8 数据模型变更

| 新增模型 | 说明 |
|----------|------|
| `AutomationParam` 枚举 | volume, pan, expression, modulation, sustain |
| `AutomationPoint` | 控制点 (beat: float, value: int) |
| `AutomationCurve` | 自动化曲线 (param: AutomationParam, points: list[AutomationPoint]) |
| `Marker` | 标记 (id: str, beat: float, label: str, color: str = "") |

| 已有模型变更 | 说明 |
|-------------|------|
| `Track` 新增字段 | `automation: list[AutomationCurve] = []` |
| `Song` 新增字段 | `markers: list[Marker] = []` |

#### 4.8.3 Phase 8 MCP Tools 清单

**Automation (#129-#134)**：

| # | Tool | 说明 |
|---|------|------|
| 129 | `add_automation` | 添加自动化曲线 |
| 130 | `remove_automation` | 移除自动化曲线 |
| 131 | `add_automation_point` | 添加控制点 |
| 132 | `remove_automation_point` | 移除控制点 |
| 133 | `apply_automation_preset` | 应用预设自动化 |
| 134 | `clear_automation` | 清除音轨所有自动化 |

**Marker (#135-#137)**：

| # | Tool | 说明 |
|---|------|------|
| 135 | `add_marker` | 添加标记 |
| 136 | `remove_marker` | 移除标记 |
| 137 | `list_markers` | 列出所有标记 |

---

### 4.9 Phase 9: 插件架构 (Plugin System)

**前置**：Phase 1-8 核心功能稳定  
**目标**：支持第三方扩展，使 Composer Engine 可通过插件扩展新的生成器、分析器、模式库和风格。

#### 4.9.1 Phase 9 功能范围

**5 种插件类型**：

| 类型 | 接口 | 说明 | 示例 |
|------|------|------|------|
| Generator | `generate(chords, key, mode, ...) -> list[Note]` | 自定义乐器/模式生成器 | 中国民乐生成器、R&B 节奏生成器 |
| Analyzer | `analyze(song, ...) -> dict` | 自定义分析器 | 和声张力分析、情感弧线分析 |
| Pattern | `get_pattern(style, ...) -> list[Note]` | 节奏/旋律模式库 | Bossa Nova 钢琴 voicing 库 |
| Style | `get_preset() -> dict` | 自定义风格预设 | Kawaii Future Bass 预设 |
| Renderer | `render(song, ...) -> bytes/str` | 自定义渲染器 | 音频预览渲染、ABC 记谱法 |

**插件生命周期**：

| 阶段 | 说明 |
|------|------|
| 发现 (Discovery) | 扫描指定目录（默认 `~/.composer-engine/plugins/`）发现插件 |
| 注册 (Register) | 验证插件接口 → 注册到 PluginManager |
| 加载 (Load) | 按需加载插件（懒加载） |
| 调用 (Invoke) | 通过 PluginManager 统一调用 |
| 卸载 (Unload) | 卸载/禁用插件 |

**插件清单文件 (plugin.json)**：

```json
{
  "name": "my-generator",
  "version": "1.0.0",
  "type": "generator",
  "entry": "my_plugin.py",
  "class": "MyGenerator",
  "description": "A custom generator for ..."
}
```

#### 4.9.2 Phase 9 数据模型变更

| 新增模型 | 说明 |
|----------|------|
| `PluginType` 枚举 | generator, analyzer, pattern, style, renderer |
| `PluginInfo` | 插件元信息 (name, version, type, entry, class_name, description, enabled) |

#### 4.9.3 Phase 9 MCP Tools 清单

**Plugin (#138-#141)**：

| # | Tool | 说明 |
|---|------|------|
| 138 | `list_plugins` | 列出所有已注册插件 |
| 139 | `enable_plugin` | 启用插件 |
| 140 | `disable_plugin` | 禁用插件 |
| 141 | `reload_plugins` | 重新扫描并加载插件 |

---

### 4.10 Phase 10: MusicXML 导出 (MusicXML Export)

**前置**：Phase 1 ✅  
**目标**：在 MIDI 基础上增加 MusicXML 导出，支持在 MuseScore、Finale 等乐谱软件中查看和编辑。

#### 4.10.1 Phase 10 功能范围

**MusicXML 渲染**：

| 功能 | 说明 |
|------|------|
| Note → MusicXML | 将 Note(pitch, start_beat, duration_beat) 转换为 MusicXML 音符元素 |
| Track → Part | 每个 Track 映射为 MusicXML Part |
| Section → Measure | 根据拍号将 beat 切分为小节 |
| Chord Symbols | 和弦进行输出为和弦标记 |
| Key/Time/Tempo | 全局设置输出到 MusicXML 头部 |
| Dynamics | velocity 映射为力度标记 (pp, p, mp, mf, f, ff) |

**渲染约束**：

- 节奏量化：将 beat 时值量化为最近的标准时值（全音符/二分/四分/八分/十六分/附点）
- Drums Track 使用打击乐记谱（percussion clef）
- 支持连音线（tie）和休止符自动补齐

#### 4.10.2 Phase 10 MCP Tools 清单

**MusicXML (#142-#143)**：

| # | Tool | 说明 |
|---|------|------|
| 142 | `export_musicxml` | 导出为 MusicXML 文件 |
| 143 | `preview_musicxml` | 预览 MusicXML 内容（返回 XML 字符串片段） |

---

### 4.11 Phase 11: 可观测性 (Observability)

**前置**：Phase 1 ✅  
**目标**：让引擎运行状态透明可见——启动时看得到、运行中追踪得了、出错时定位得快。

#### 4.11.1 Phase 11 功能范围

**当前问题**：

| 场景 | 现状 | 目标 |
|------|------|------|
| MCP Server 启动 | 无任何输出，不知道加载了几个 Tool、是否就绪 | 打印 Banner + 加载摘要 + 就绪确认 |
| Tool 被调用 | 无日志，不知道哪个 Tool 被调了、耗时多少 | 每次调用记录 tool 名、参数摘要、耗时、结果 |
| Command 执行 | 无日志，不知道 Song 发生了什么变更 | 记录 Command 类型、描述、Song 变更摘要 |
| 出错 | 异常被 try/except 吞掉，只返回 JSON error | 同时写日志 + 打印 traceback |
| 运行状态 | 无法知道当前 Song 有几个 Track、几个 Note | 提供 status 查询 Tool |

**日志系统 — 3 层**：

| 层 | 模块 | 日志内容 |
|----|------|---------|
| **Server 层** | `mcp_server.py` | Tool 调用日志：`[TOOL] create_song(name="Demo") → OK (23ms)` |
| **Engine 层** | `composer.py` | Command 执行日志：`[CMD] CreateSongCommand → Song "Demo" created` |
| **System 层** | 全局 | 启动/关闭/错误/警告 |

**日志格式**：

```
[2026-07-23 17:00:00] [INFO]  [SERVER] MCP Server starting...
[2026-07-23 17:00:00] [INFO]  [SERVER] Registered 143 tools
[2026-07-23 17:00:00] [INFO]  [SERVER] ✓ Composer Engine ready
[2026-07-23 17:00:05] [INFO]  [TOOL]   create_song(name="Demo", tempo=120) → OK (12ms)
[2026-07-23 17:00:05] [INFO]  [CMD]    CreateSongCommand → Song "Demo" created (1 tracks, 0 notes)
[2026-07-23 17:00:06] [WARN]  [TOOL]   remove_track(track_id="xxx") → FAIL: Track not found (3ms)
[2026-07-23 17:00:10] [ERROR] [CMD]    GenerateMelodyCommand failed: No chord progression
```

**日志级别控制**：

| 级别 | 输出内容 | 适用场景 |
|------|---------|---------|
| `ERROR` | 仅错误和异常 | 生产环境 |
| `WARN` | 错误 + 警告（操作失败等） | 日常使用 |
| `INFO` | 上述 + Tool 调用 + Command 执行 | **默认级别** |
| `DEBUG` | 上述 + 参数细节 + Song 状态快照 | 调试开发 |

**日志输出**：

| 目标 | 说明 |
|------|------|
| stderr | 默认输出到 stderr（不干扰 MCP 的 stdout 通信） |
| 文件 | 可选，通过环境变量 `COMPOSER_LOG_FILE` 指定路径 |

**启动 Banner**：

```
╔══════════════════════════════════════════╗
║   🎵 Composer Engine v0.1.0             ║
║   MCP Tools: 143 | Phases: 10           ║
║   Python: 3.12.x | Pydantic: 2.x        ║
╚══════════════════════════════════════════╝
[INFO] Registered 143 MCP tools
[INFO] Pipeline stages: 5 (Inspiration → Export)
[INFO] Plugin directory: ~/.composer-engine/plugins/
[INFO] Log level: INFO
[INFO] ✓ Ready — waiting for MCP connection
```

**运行统计 (Stats)**：

引擎维护运行时统计，通过 MCP Tool 查询：

| 统计项 | 说明 |
|--------|------|
| `uptime` | 启动至今的时间 |
| `tool_calls` | Tool 总调用次数 |
| `tool_errors` | Tool 错误次数 |
| `commands_executed` | Command 执行次数 |
| `undo_count` | Undo 操作次数 |
| `song_summary` | 当前 Song 摘要（tracks/notes/chords/sections 计数） |
| `last_tool` | 最近一次 Tool 调用的名称和时间 |

#### 4.11.2 Phase 11 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `COMPOSER_LOG_LEVEL` | `INFO` | 日志级别 (DEBUG/INFO/WARN/ERROR) |
| `COMPOSER_LOG_FILE` | (空 = 不写文件) | 日志文件路径 |
| `COMPOSER_NO_BANNER` | (空 = 显示) | 设为 `1` 时不打印启动 Banner |

#### 4.11.3 Phase 11 MCP Tools 清单

**Observability (#144-#146)**：

| # | Tool | 说明 |
|---|------|------|
| 150 | `get_server_stats` | 获取服务器运行统计 |
| 151 | `get_song_summary` | 获取当前 Song 的概要统计 |
| 152 | `set_log_level` | 动态调整日志级别 |

---

### 4.12 Phase 12: 属性补全 (Property Completion) ✅

**前置**：Phase 1 ✅  
**目标**：补全 §三 总体功能需求中剩余的简单/中等属性字段和操作，消灭大部分 🔜 标记。

#### 4.12.1 Phase 12 功能范围

**全局设置补全 — 3 个新属性 + 1 个计算属性**：

| # | 属性 | 字段 | 类型 | 默认值 | 说明 |
|---|------|------|------|--------|------|
| 1 | Scale | `GlobalSettings.scale` | `Optional[str]` | `None` | 覆盖 Key+Mode 默认推算的音阶名称，`None` 时由 theory 模块自动计算 |
| 2 | Master Timing | `GlobalSettings.master_timing` | `float` | `0.0` | 全局时值偏移（beats），正值延后、负值提前 |
| 3 | Global Energy | `GlobalSettings.global_energy` | `float` | `0.5` | 全局能量级别 (0.0 最弱 ~ 1.0 最强) |
| 4 | Song Length | 只读计算 | — | — | 由所有 Sections 的 `start_beat + length_beats * repeat` 的最大值自动计算，在 `get_song_state` 中返回 |

**段落操作补全 — 3 个新操作**：

| # | 操作 | Command | 参数 | 说明 |
|---|------|---------|------|------|
| 5 | 交换 | `SwapSectionsCommand` | `section_id_a`, `section_id_b` | 交换两个段落的 `start_beat` |
| 6 | 拆分 | `SplitSectionCommand` | `section_id`, `split_beat` | 在指定 beat 处将段落一分为二 |
| 7 | 合并 | `MergeSectionsCommand` | `section_id_a`, `section_id_b` | 合并两个段落为一个，长度相加 |

**音轨属性补全 — 7 个新属性**：

| # | 属性 | 字段 | 类型 | 默认值 | 说明 |
|---|------|------|------|--------|------|
| 8 | Register | `Track.register` | `str` | `"mid"` | 音区：`high` / `mid` / `low` |
| 9 | Complexity | `Track.complexity` | `float` | `0.5` | 音轨复杂度 (0.0 极简 ~ 1.0 极复杂) |
| 10 | Velocity Offset | `Track.velocity_offset` | `int` | `0` | 力度偏移 (-127 ~ +127)，渲染时叠加到每个音符的 velocity |
| 11 | Timing Offset | `Track.timing_offset` | `float` | `0.0` | 时值偏移 (beats)，渲染时叠加到每个音符的 start_beat |
| 12 | Humanize | `Track.humanize` | `float` | `0.0` | 轨级人性化程度 (0.0-1.0)，与 humanize_* 操作独立 |
| 13 | Groove | `Track.groove` | `str` | `""` | 轨级律动模板名称（空字符串=不应用），与 apply_groove 操作独立 |
| 14 | Rhythm | `Track.rhythm_pattern` | `str` | `""` | 节奏模式名称（空字符串=默认） |
| 15 | Range | `Track.pitch_range_low` / `Track.pitch_range_high` | `int` | `0` / `127` | 音域限制（MIDI pitch 范围），0/127 表示不限制 |

#### 4.12.2 Phase 12 MCP Tools 清单（14 个）

**Global (#153-#155)**：

| # | Tool | 说明 |
|---|------|------|
| 153 | `set_scale` | 设置音阶（覆盖 Key+Mode 推算） |
| 154 | `set_master_timing` | 设置全局时值偏移 |
| 155 | `set_global_energy` | 设置全局能量级别 |

**Section (#156-#158)**：

| # | Tool | 说明 |
|---|------|------|
| 156 | `swap_sections` | 交换两个段落的位置 |
| 157 | `split_section` | 在指定 beat 处拆分段落 |
| 158 | `merge_sections` | 合并两个段落 |

**Track (#159-#166)**：

| # | Tool | 说明 |
|---|------|------|
| 159 | `set_track_register` | 设置音轨音区 (high/mid/low) |
| 160 | `set_track_complexity` | 设置音轨复杂度 |
| 161 | `set_track_velocity_offset` | 设置音轨力度偏移 |
| 162 | `set_track_timing_offset` | 设置音轨时值偏移 |
| 163 | `set_track_humanize` | 设置音轨人性化程度 |
| 164 | `set_track_groove` | 设置音轨律动模板 |
| 165 | `set_track_rhythm` | 设置音轨节奏模式 |
| 166 | `set_track_range` | 设置音轨音域限制 |

---

### 4.13 Phase 13: MIDI 导入 (MIDI Import) ✅

**前置**：Phase 1 ✅  
**目标**：从已有 MIDI 文件导入数据到 Song 模型，使 AI 能基于已有作品继续编曲、分析或重新编排。

#### 4.13.1 Phase 13 功能范围

**核心价值**：

| 场景 | 说明 |
|------|------|
| 导入已有作品 | 将 MIDI 文件解析为 Song，用现有 152+ 工具继续编辑 |
| 分析参考曲 | 导入参考 MIDI，用 Phase 7 分析引擎进行和声/旋律/节奏分析 |
| 部分导入 | 只导入 MIDI 中的某一轨（如只要鼓或只要旋律），融合到当前创作中 |
| 预览 | 先查看 MIDI 文件信息（轨道数、时长、乐器等），再决定是否/如何导入 |

**MIDI 解析能力**：

| 项目 | 解析方式 | 映射 |
|------|---------|------|
| Tempo | `pretty_midi.get_tempo_changes()` 取首个 | → `GlobalSettings.tempo` |
| Time Signature | `pretty_midi.time_signature_changes` 取首个 | → `GlobalSettings.time_signature` |
| Key Signature | `pretty_midi.key_signature_changes` 取首个 | → `GlobalSettings.key` + `GlobalSettings.mode` |
| Instrument Track | `pretty_midi.Instrument` (非 drum) | → `Track` (自动映射 `InstrumentType`) |
| Drum Track | `pretty_midi.Instrument(is_drum=True)` | → `Track(instrument=DRUMS, channel=9)` |
| Notes | `instrument.notes` (seconds → beats) | → `Note(pitch, start_beat, duration_beat, velocity)` |
| Track Name | `instrument.name` 或 `"Track N"` | → `Track.name` |
| Program | `instrument.program` | → `Track.program` + 反向推断 `InstrumentType` |

**GM Program → InstrumentType 反向映射规则**：

| Program 范围 | InstrumentType | 说明 |
|-------------|---------------|------|
| 0-7 | PIANO | Piano 族 |
| 8-15 | PIANO | Chromatic Percussion → 归入 Piano |
| 16-23 | PIANO | Organ → 归入 Piano |
| 24-31 | GUITAR | Guitar 族 |
| 32-39 | BASS | Bass 族 |
| 40-47 | STRINGS | Strings (弓弦) |
| 48-55 | STRINGS | String Ensemble + Choir → Strings/Voice |
| 56-63 | BRASS | Brass 族 |
| 64-79 | WOODWINDS | Reed + Pipe (管乐) |
| 80-87 | LEAD | Lead Synth |
| 88-95 | PAD | Pad Synth |
| 96-103 | FX | FX |
| 104-111 | GUITAR | Ethnic → 归入 Guitar |
| 112-119 | FX | Percussive → FX |
| 120-127 | FX | Sound Effects |
| is_drum | DRUMS | 打击乐通道 |

**Seconds → Beats 转换**：

```
beat = seconds * tempo / 60.0
```

使用 MIDI 文件中的首个 tempo 值，将所有 Note 的 `start`/`end`（秒）转换为 `start_beat`/`duration_beat`（拍）。

**导入模式 — 2 种**：

| 模式 | Tool | 说明 |
|------|------|------|
| 全量导入 | `import_midi` | 解析整个 MIDI 文件，创建全新 Song（替换当前） |
| 单轨导入 | `import_midi_track` | 只导入 MIDI 文件中指定的一轨，追加到当前 Song |

**预览功能**：

| Tool | 说明 |
|------|------|
| `get_midi_info` | 不导入，仅返回 MIDI 文件的元信息（轨道列表、tempo、时长、音符数等） |

#### 4.13.2 Phase 13 MCP Tools 清单（3 个）

| # | Tool | 参数 | 说明 |
|---|------|------|------|
| 167 | `import_midi` | `file_path`, `song_name` (可选) | 从 MIDI 文件创建新 Song |
| 168 | `import_midi_track` | `file_path`, `midi_track_index` | 从 MIDI 文件导入指定轨到当前 Song |
| 169 | `get_midi_info` | `file_path` | 预览 MIDI 文件信息（不导入） |
