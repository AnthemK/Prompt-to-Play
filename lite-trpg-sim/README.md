# 轻量级跑团模拟器（双故事包可切换）

一个可运行、可扩展的单机文字冒险/互动小说原型（前后端分离）。

- 内置故事包 A：中古战锤风格黑暗奇幻（边陲、瘟疫、邪教、鼠人传闻、旧神遗迹）
- 内置故事包 B：提瓦特冒险悬疑章节（璃月港潮汐异变、遗迹封印、道德抉择）
- 体验目标：接近单人跑团
- 单章时长：约 15–30 分钟
- 核心目标：后端数据驱动剧情，前端保持通用 UI 框架

## 项目定位与特色

- 纯本地运行：Python 标准库后端 + 静态前端
- 明确分层：
  - 前端只负责显示/输入/交互流程
  - 后端负责剧情、规则、分支、结局、存档结构
- 内容完整可玩：
  - 4 职业、属性/生命/腐化/状态/物品
  - d20 检定（可见拆解）
  - 调查/潜入/强攻/交涉多路线
  - 道德抉择与多结局（含失败/堕落）

## 当前架构（前后端分离）

```text
launcher.py             # 一键启动器
launch_game.command     # macOS 双击启动入口

frontend/
  index.html            # 通用 UI 结构
  styles.css            # 视觉样式
  app.js                # 渲染、交互、API 调用、存档槽位与导入导出

backend/
  server.py             # HTTP API
  stories/
    README.md           # 故事作者指南（详细接口、写作约束、遭遇与效果说明）
    grimweave/
      story.json        # 世界观、职业、物品、状态、结局、节点与行动（数据驱动）
    teyvat_tide_lantern/
      story.json        # 提瓦特单章节故事包（同接口直接接入）
    STORY_INTERFACE.md  # 故事包统一接口/字段约定
  game/
    story_interface.py  # 统一故事运行时接口（引擎只依赖它）
    story_runtime.py    # StoryPackRuntime：数据故事包实现
    content.py          # story pack 发现/加载（JSON + YAML）
    adventure.py        # 通用剧情解释器（执行节点/行动/effects）
    rules.py            # 通用检定与资源/状态结算
    resolution.py       # 统一结算结果结构与变化记录
    engine.py           # 会话/存档管理（不含具体故事逻辑）

backend/tests/
  test_rules_resolution.py  # 统一结算与规则回归测试
  test_encounter_flow.py    # 遭遇框架回归测试

docs/
  ARCHITECTURE.md          # 系统 / 内容 / 前后端分层说明
  RUNTIME_STATE.md         # state / save / resolution / encounter 数据模型
  ENGINEERING.md           # 代码注释、命名、文档同步与 review 约束
```

## API 概览

- `GET /api/meta[?story_id=...]`：返回当前故事包元数据
- `POST /api/game/new`：创建新局（支持 `story_id`）
- `GET /api/game/{session_id}/view`：获取当前视图
- `POST /api/game/{session_id}/action`：执行行动
- `POST /api/game/{session_id}/save`：导出后端定义的存档结构
- `POST /api/game/load`：加载存档结构
- `DELETE /api/game/{session_id}`：删除会话

## 统一故事接口

- 系统通过 `StoryRuntime` 接口运行故事（见 `backend/game/story_interface.py`）
- 当前数据故事包实现为 `StoryPackRuntime`（`backend/game/story_runtime.py`）
- 故事包字段约定见：`backend/stories/STORY_INTERFACE.md`
- `GameEngine` 仅处理会话/存档/聚合视图，不包含具体故事常量

## 技术文档分层（新增）

- `README.md`
  - 面向使用者与协作者的总览、运行方式、架构概览
- `Memory.md`
  - 面向当前迭代的工作记忆与状态摘要
- `docs/ARCHITECTURE.md`
  - 面向长期维护的架构分层说明
- `docs/RUNTIME_STATE.md`
  - 面向状态结构、结算结构、存档结构的精确说明
- `docs/ENGINEERING.md`
  - 面向代码风格、注释纪律、文档同步要求
- `backend/stories/README.md`
  - 面向故事作者的 story pack 写作与接入说明

当前维护约束：

- 改运行时代码时，必须同步更新代码注释与相关技术文档
- 改 story DSL / story 接口时，必须同步更新 `backend/stories/README.md` 与 `STORY_INTERFACE.md`
- 允许为了更好的系统抽象重写旧故事包；兼容性不应成为阻碍底层质量的借口

## 当前机制判断（只看系统，不看故事）

- 作为“数据驱动文字冒险 / 轻跑团引擎”，当前底子是好的
- 作为“接近 D&D / 神界原罪 / 博德之门3 的可扩展 RPG 机制底层”，当前还不够强
- 当前强项：
  - 故事与系统已经解耦
  - 检定、物品、状态、分支、结局都可由后端数据驱动
  - 前后端职责清晰，适合继续演化
- 当前短板：
  - 统一结算内核仍在演进中（已接入 check/save/contest/damage，仍需继续扩伤害类型与对抗语义）
  - 遭遇框架已从最小状态块升级为阶段化模型，但仍未达到完整战术层深度
  - 还没有技能熟练、能力、成长、环境反应这些 RPG 核心底盘
  - 还缺少平衡仿真与机制回归工具

因此，后续开发原则是：

- 先补系统，再扩内容
- 先做通用机制模块，再让故事包调用
- 在 `M1` 完成前，不把“继续快速堆新故事包”作为主方向

目前已经开始落地的 `M1` 基础：

- 统一结算结果结构：动作结果现在带有 `last_outcome.resolution`
- 统一结算新增：`check / save / contest / damage`
- `damage` 已支持：`damage_type / penetration / resistances / mitigated`
- 基础被动效果生命周期：`before_check / after_check / turn_end`
- 旧故事字段仍兼容：`per_turn_effects / consume_on_check`
- 遭遇框架已升级：运行态 / 存档 / API / 前端面板均支持，且新增阶段、阶段规则、回合规则、敌方生命、目标进度
- 已补最小单元测试，开始处理机制层技术债

## 运行方式（macOS + VS Code）

需要：`python3`

### 推荐：一键启动（最简单）

在 `VSCode/prompt-to-play/lite-trpg-sim` 下执行：

```bash
python3 launcher.py
```

或双击：

- `launch_game.command`

启动器会自动启动：

1. 后端 `127.0.0.1:8787`
2. 前端 `127.0.0.1:5173`
3. 浏览器打开游戏页面

### 手动启动（调试）

终端 A：

```bash
python3 backend/server.py
```

终端 B（在 `VSCode` 目录）：

```bash
python3 -m http.server 5173 -d prompt-to-play/lite-trpg-sim/frontend
```

访问：`http://127.0.0.1:5173/index.html`

## 如何开始游戏

1. 在开局面板选择故事包
2. 输入角色名，选择职业
3. 点击“开始冒险”
4. 通过行动按钮推进剧情
5. 查看检定明细、状态变化、日志与后果
6. 使用存档槽位进行多路线尝试

## 内置故事包

### 1) `grimweave`

- 标题：灰织边陲：腐月下的誓言
- 气质：中古战锤风格黑暗奇幻
- 章节：泥沼村邪教与墓穴仪式

### 2) `teyvat_tide_lantern`

- 标题：提瓦特：潮汐下的无名星灯
- 气质：提瓦特世界冒险悬疑
- 章节：璃月港失踪潮声
- 角色出场：夜兰、钟离、胡桃、那维莱特、派蒙
- 关键体验：港区调查、海蚀洞潜入、遗迹核心对抗、先救人还是先封控的道德抉择

## 如何开始游戏（提瓦特章节示例）

1. 启动后在“选择故事包”里选 `提瓦特：潮汐下的无名星灯`
2. 选择职业并开始
3. 在“核心前区”做道德抉择，再在“潮汐核心井”完成终局对抗

## 核心玩法说明

### 角色系统

- 属性：力量、敏捷、洞察、意志、交涉
- 资源：生命、腐化、先令、末日进度
- 状态：负伤/染疫/受祝/惊惧/背负难民（不同故事包可定义不同状态）
- 职业差异：初始属性、初始物品、检定标签加成

### 检定系统

- 机制：`d20 + 修正 >= DC`
- 修正来源：
  - 属性修正
  - 职业加成（标签驱动）
  - 装备/状态加成（数据驱动）
  - 腐化惩罚
  - 场景内消耗品与旗标加成
- 前端可见：骰值、DC、总修正、分项来源

当前说明：

- 当前已支持 4 类统一结算：`check / save / contest / damage`
- `contest` 支持玩家与对手双投掷对抗（同一条结果链路）
- `damage` 支持固定值与骰伤害、伤害类型、平减伤、百分比减伤、穿透，并统一落入 `resolution.effects`
- 后续仍需继续扩展为更完整的伤害类型、抗性与行动经济系统

### 分支与后果

- 同一目标可通过不同路径处理（战斗/潜行/仪式/交涉/撤离）
- 失败会导致资源损失、状态恶化、路线变化
- 终局与前置选择、资源状态、腐化和关键检定相关

### 遭遇框架（M1 进行中）

- 遭遇运行态已支持：
  - `phase / phase_label / intent`
  - `enemy.hp/max_hp/resistances`
  - `objective.progress/target`
  - `turn_rules`（回合规则）
  - `phase_rules`（阶段切换规则）
- 遭遇动作可来自：
  - `encounters.<id>.actions`
  - `encounters.<id>.phases.<phase_id>.actions`
- 动作可按阶段显示：`phase / phase_in / phase_not_in`

### 物品与状态

- 物品可拥有：
  - 常驻检定加成（`check_bonus`）
  - 主动使用效果（`use_effects`）
- 状态可拥有：
  - 检定修正
  - 每回合效果（`per_turn_effects`）
  - 检定后消耗规则（`consume_on_check`）

当前新增能力：

- `professions/items/statuses` 可定义 `trigger_effects`
- 当前已接入触发时机：
  - `before_check`
  - `after_check`
  - `turn_end`
- 这让状态与被动效果开始脱离“散落特判”，逐步向统一 effect 生命周期演进

## 存档系统（已扩展）

- 5 个手动存档槽位（前端本地管理）
- 自动存档（独立于手动槽）
- 导出槽位为 `.json`
- 导入 `.json` 并校验后读档
- 存档结构由后端定义（含 `schema_version/story_id/state`）
- 刷新页面后可继续（“继续最近进度”）

## 数据驱动剧情（已扩展）

当前剧情由故事包驱动，包括：

- `backend/stories/grimweave/story.json`
- `backend/stories/teyvat_tide_lantern/story.json`

每个故事包都可独立定义：

- 世界观元数据
- 属性元数据
- 职业模板
- 物品定义
- 状态定义
- 结局定义
- 剧情节点与行动
- 遭遇模板（可选）
- 行动效果（`effects`）和检定分支（`on_success/on_failure`）

后端解释器执行的常见 effect/op：

- `goto` / `set_flag` / `adjust`
- `add_item` / `remove_first_item`
- `add_status` / `remove_status`
- `outcome` / `log`
- `finish` / `finish_if`
- `resolve_victory`
- `start_encounter` / `adjust_encounter` / `end_encounter`

系统层（`engine/content/adventure/rules`）现在不再硬编码具体故事包的地名、角色名、结局 ID 或关键旗标。

## 如何快速替换故事背景（尽量只改后端）

1. 新建故事包目录：`backend/stories/<your_story>/`
2. 放入 `story.json`（或 `story.yaml/.yml`）
3. 保持与现有字段结构兼容：`world/stat_meta/professions/items/statuses/endings/nodes`
4. 前端通常无需改动（开局面板直接选择故事包）
5. 也可通过 `POST /api/game/new` 传 `story_id` 启动指定故事

建议做法：

- 新题材优先改故事包数据
- 仅当需要新增通用机制时，再扩展 `adventure.py/rules.py` 的解释能力
- 新故事作者可先阅读 `backend/stories/README.md`

## 当前完成度

- 双故事包可切换游玩（黑暗奇幻 + 提瓦特冒险章节）
- 完整可玩单章节流程（每个故事包均含开场、调查、高风险冲突、道德抉择、多个结局）
- 前后端分离稳定运行
- 一键启动
- 存档槽位 + 自动存档 + 导入导出
- JSON/YAML 故事包加载 + 节点数据驱动执行
- 前端开局支持故事包选择
- 当前机制底盘适合继续扩展，但尚未达到 CRPG 级系统深度
- 已完成统一结算与基础生命周期的第一步落地
- 已完成遭遇态最小基础设施与故事作者指南

## 测试

可运行最小机制测试：

```bash
python3 -m unittest discover -s backend/tests
```

## 后续扩展方向

1. 先补系统底盘：统一结算、遭遇框架、状态生命周期、技能熟练
2. 再做角色成长、阵营关系、章节链
3. 补齐工具链：schema 校验、仿真、平衡性与回归测试
4. 在系统稳定后，再继续扩更多故事包（克苏鲁/赛博朋克/废土）
