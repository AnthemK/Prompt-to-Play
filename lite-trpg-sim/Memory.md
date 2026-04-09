# Memory.md

## 当前项目目标

- 保持“可运行、可游玩”的轻量级跑团模拟器原型（支持多题材故事包）
- 新增并验证第二个可玩故事包（提瓦特章节）
- 优先把机制底盘提升到可承载多题材 / 多章节 / 多系统扩展的程度
- 持续强化前后端分离
- 把剧情/世界观/规则尽量外置为故事包数据，支持快速换题材
- 扩展存档体验（槽位 + 导入导出 + 自动继续）
- 持续维护代码注释、命名与分级技术文档，避免代码库失控

## 当前前后端分离方案摘要

- 启动层：
  - `launcher.py` + `launch_game.command`
  - 一键拉起后端与前端静态服务
- 前端 `frontend/`：
  - 只负责 UI、输入、渲染、按钮交互、调用 API
  - 开局支持选择故事包（调用 `/api/meta?story_id=...`）
  - 存档槽位/导入导出在前端本地实现（不定义存档结构）
- 后端 `backend/`：
  - `stories/*/story.json|yaml`：世界观 + 剧情 + 规则数据
  - `stories/STORY_INTERFACE.md`：故事包统一接口文档
  - `game/story_interface.py`：系统级故事运行时接口
  - `game/story_runtime.py`：数据故事包实现（StoryPackRuntime）
  - `game/content.py`：故事包发现与加载
  - `game/adventure.py`：通用节点解释器（执行 actions/effects）
  - `game/rules.py`：通用检定与状态/资源结算
  - `game/engine.py`：会话/存档管理（只依赖 StoryRuntime 接口）
  - `server.py`：API 边界
- 技术文档 `docs/`：
  - `ARCHITECTURE.md`：长期架构分层说明
  - `RUNTIME_STATE.md`：state/save/resolution 数据模型说明
  - `ENGINEERING.md`：代码注释、命名、文档同步与 review 规则

## 已完成事项

- 重构为故事包驱动（`backend/stories/grimweave/story.json`）
- 建立统一故事运行时接口（StoryRuntime）
- 后端新增 story repository（JSON + YAML）
- 剧情推进改为通用解释器，不再使用硬编码场景函数
- 清除系统层故事特定硬编码（结局 ID/旗标/地名）
- 检定/物品/状态规则改为数据驱动读取
- 存档结构升级到 `schema_version=3`（已保留 `1/2` 的兼容加载）
- 前端新增 5 个存档槽位
- 前端新增导入/导出 `.json`
- 前端保留自动存档（独立于手动槽）与“继续最近进度”
- 前端新增“故事包选择”下拉，开局可直切不同题材
- 新增提瓦特故事包：`backend/stories/teyvat_tide_lantern/story.json`
- 新故事包已覆盖：开场、调查、洞窟潜入、高风险终局、道德抉择、多结局
- 已重新评估系统底盘，明确“系统优先于继续扩故事”的路线
- 新增 `backend/game/resolution.py`，开始统一动作结算结果结构
- 已把检定 / 剧情动作 / 道具使用接入 `last_outcome.resolution`
- 已新增基础被动生命周期：`before_check / after_check / turn_end`
- 已兼容旧状态字段：`per_turn_effects / consume_on_check`
- 已新增最小遭遇态：状态结构 / 存档 / API / 前端展示 / effect DSL
- 已新增故事作者指南：`backend/stories/README.md`
- 已新增最小单元测试：`backend/tests/test_rules_resolution.py`
- 已新增遭遇流测试：`backend/tests/test_encounter_flow.py`
- 已为核心代码文件补充模块说明、函数 docstring 与关键注释
- 已新增分级技术文档：`docs/ARCHITECTURE.md`、`docs/RUNTIME_STATE.md`、`docs/ENGINEERING.md`
- 已新增统一结算类型：`save / contest / damage`
- 已完成伤害系统升级：`damage_type + 抗性 + 减伤 + 穿透`
- 已把 encounter 升级为通用遭遇框架雏形：
  - 阶段：`phase / phase_rules`
  - 回合规则：`turn_rules`
  - 敌方运行态：`enemy.hp/max_hp`
  - 目标进度：`objective.progress/target`
  - 阶段动作：`phases.<phase_id>.actions`
  - 敌方抗性：`enemy.resistances`
- README 与 Memory 同步更新
- 后端编译检查与引擎级流程自检通过

## 当前机制评估摘要

- 结论：
  - 当前底盘对“数据驱动互动小说 / 轻跑团原型”是合格的
  - 当前底盘对“接近 D&D / 神界原罪 / 博德之门3 的 RPG 系统层”还不够强
- 当前强项：
  - 故事包解耦已经成立
  - 前后端职责清楚
  - 检定、状态、物品、分支、结局都能走数据驱动
  - 存档结构已具备继续演化的基础
- 当前短板：
  - 缺少统一结算内核
  - 缺少通用遭遇/战斗框架
  - 缺少技能熟练、能力、成长系统
  - 缺少环境对象与连锁反应
  - 缺少平衡仿真与回归工具
- 战略判断：
  - 当前最该做的不是第三个大型故事包
  - 当前最该做的是完成 `M1`：统一结算 + 遭遇雏形 + 技能层 + 状态生命周期

## 当前系统设计摘要

### 代码库治理要求（新增长期约束）

- 改代码必须同步改描述：
  - 代码注释 / docstring
  - 对应技术文档
  - 必要时更新 README / Memory / TODO
- 允许为更好的系统抽象重写旧 story pack
- “兼容旧实现”不是第一优先级，系统质量与清晰边界优先
- 关键命名必须明确区分：
  - story 配置态 vs runtime 运行态
  - state vs view
  - template vs encounter

### 故事包（Story Pack）结构

`story.json` 当前关键字段：

- `id`
- `world`
  - 标题、intro、起始节点、腐化上限、末日文本、腐化惩罚、胜利解析规则
  - 系统规则：`default_ending_id/fatal_rules/resolve_victory`
- `stat_meta`
- `professions`
  - 基础属性、初始物品、职业检定加成规则
- `items`
  - 描述、检定加成、可用效果（`use_effects`）
- `statuses`
  - 描述、检定修正、每回合效果、消费触发
- `endings`
- `nodes`
  - 节点文本 + 行动列表

### 行动与效果 DSL（当前可用）

- 行动类型：`move/story/check/save/contest/damage/utility`
- 行动可配置：`requires`、`on_unavailable`、`check/save/contest/damage`、`on_success`、`on_failure`
- effect/op：
  - `goto`
  - `set_flag`
  - `adjust`
  - `add_item` / `remove_first_item`
  - `add_status` / `remove_status`
  - `damage`
  - `outcome`
  - `log`
  - `finish` / `finish_if`
  - `resolve_victory`
  - `start_encounter` / `adjust_encounter` / `end_encounter`
  - `set_encounter_flag` / `clear_encounter_flag`
  - `adjust_enemy_hp` / `adjust_objective`
  - `sync_encounter_phase`

### 统一结算结果（新增基础版）

- 结果对象入口：`state.last_outcome.resolution`
- 当前已覆盖：
  - `check`
  - `save`
  - `contest`
  - `damage`
  - `story/move`
  - `utility`
- 当前记录内容：
  - `kind/label/success/stat/dc/roll/modifier/total/tags`
  - `opponent_label/opponent_roll/opponent_modifier/opponent_total`（contest）
  - `amount/mitigated/applied`（damage）
  - `damage_type/target/target_label/penetration/resistance_flat/resistance_percent`（damage）
  - `breakdown`
  - `effects`
- 设计目的：
  - 让检定、状态变化、物品消耗、回合末被动效果都进入统一结果结构
  - 为后续扩展遭遇、伤害、豁免、社交攻防提供同一出口

### 遭遇态（新增基础版）

- 运行态入口：`state.encounter`
- 当前已接入：
  - 存档修复与新局初始化
  - API 视图输出：`view.encounter`
  - 前端面板显示
  - effect DSL：
    - `start_encounter`
    - `adjust_encounter`
    - `end_encounter`
  - 遭遇动作：`encounters.<id>.actions`
- 当前通用雏形字段：
  - `id/title/type/summary/goal`
  - `round/pressure/pressure_label/pressure_max`
  - `phase/phase_label/intent`
  - `enemy(name/intent/hp/max_hp/resistances)`
  - `objective(label/progress/target)`
  - `flags`
- 当前语义：
  - 遭遇动作 = 全局动作 + 当前阶段动作
  - 每回合推进时：`encounter.round +1`，然后执行 `turn_rules`
  - 每次关键变动后可触发 `phase_rules` 重算并切阶段

### 检定系统（通用）

- `d20 + modifier >= DC`
- modifier 来源：
  - 属性修正
  - 职业 `check_bonus`
  - 物品 `check_bonus`
  - 状态 `check_bonus`
  - 世界腐化惩罚
  - 行动内旗标加成 + 消耗品加成
- DC 动态调整：
  - `dc_adjust_by_doom`
  - `dc_adjust_if_flags`

### 机制演化方向（新增）

- 以“统一结算内核”替代单一检定中心
- 让状态、装备、职业、环境都以统一 effect 形式进入结算
- 在 state / save 中预留遭遇态、成长态、阵营态
- 后续故事包只消费这些系统能力，不新增题材特化逻辑
- 当前已完成第一步：effect 生命周期基础钩子已接入 rules 层

## 前端负责什么 / 后端负责什么

### 前端职责（当前约束）

- 显示剧情、选项、检定结果、角色面板、日志
- 触发 API：`meta/new/action/save/load`
- 管理本地存档槽位与导入导出
- 不硬编码剧情节点逻辑与分支判断

### 后端职责（当前约束）

- 解释故事包数据并推进状态
- 执行检定、资源变化、状态变化
- 结局判定与死亡/腐化终止
- 定义与校验存档结构
- 暴露稳定视图给前端
- 通过 `StoryRuntime` 接口对接引擎，避免引擎耦合故事细节
- 未来继续承载：统一结算、遭遇、成长、环境交互等通用机制层

## 关键接口与数据流摘要

- `GET /api/meta?story_id=...`
  - 返回故事包元数据（world/stats/professions/items）
- `POST /api/game/new`
  - 输入 `player_name/profession_id/story_id`
- `POST /api/game/{id}/action`
  - 输入 `action_id`
- `POST /api/game/{id}/save`
  - 输出后端定义存档
- `POST /api/game/load`
  - 输入存档并恢复会话

数据流：

1. 前端获取 `meta`
2. 开局切换故事包 -> 再取对应 `meta`
3. 创建新局 -> `view`
4. 行动循环：`action` -> `view`
5. 行动后自动存档（autosave）
6. 手动槽位保存/读取 + 导入/导出

## 剧情设定摘要（当前故事包）

- 地点：帝国边陲泥沼村
- 主冲突：失踪、瘟疫、邪教祭仪、墓穴异端
- 场景链：村口 -> 村内调查 -> 林地/暗渠 -> 墓穴 -> 祭坑
- 关键抉择：
  - 林中孩子（救助/安息/抛弃）
  - 囚牢处理（放行/封死/净化）
- 结局：
  - 黎明、惨胜、黑雨、堕落、塌方、死亡
- 新增故事包：
  - `teyvat_tide_lantern`（璃月港潮汐异变）
  - 角色出场：夜兰、钟离、胡桃、那维莱特、派蒙
  - 主冲突：失踪潮声、走私遗迹、深渊核心泄漏
  - 关键抉择：先救人还是先封核心
  - 结局覆盖：协作止灾、带伤封印、港区失守、低语堕落、战斗阵亡

## 数据结构 / 状态结构 / 存档结构简述

### 运行态 state

- `schema_version`
- `session_id`
- `story_id`
- `player`
  - `name/profession_id/profession_name/stats`
  - `hp/max_hp/corruption/shillings`
  - `inventory/statuses`
- `progress`
  - `chapter/node_id/doom/turns/flags`
- `log`
- `last_outcome`
- `game_over`
- `ending`
- `encounter`
  - `id/title/type/summary/goal`
  - `round/pressure/pressure_label/pressure_max`
  - `phase/phase_label/intent`
  - `enemy/objective/flags`

### 存档结构（后端定义）

- `schema_version`
- `saved_at`
- `story_id`
- `world_id`
- `state`（完整快照）

补充说明：

- `state.last_outcome` 现在可包含 `resolution`
- `state.encounter` 现在是正式保留字段
- 该字段已进入运行态和存档快照，需要保持向后兼容

### 前端本地存储结构（槽位）

- `SAVE_STORE_KEY=lite_trpg_sim_save_store_v2`
- `ACTIVE_SLOT_KEY=lite_trpg_sim_active_slot_v2`
- `slots[1..5]`
  - 元信息 + `save_data`
- `autosave`
  - 最近自动存档 + `save_data`

## 已知问题

- 沙箱环境下无法稳定做完整 HTTP 端到端压测（部分本地 socket 受限）
- 前端槽位仍是轻量管理（无重命名、标签、排序）
- YAML 支持依赖本机是否安装 PyYAML（JSON 不受影响）
- 前端资源栏文案仍是通用固定项（如“先令/腐化”），未按故事包自定义显示名映射
- 当前机制仍偏“单次检定驱动”，尚未形成真正的遭遇与构筑系统
- 当前 flags 使用会在机制复杂化后快速膨胀，需要逐步转向统一 effect / encounter 模型
- 代码注释已补到核心模块，但仍需在后续每次迭代持续维护，不能回退到“代码改了文档没改”
- 当前遭遇框架仍是雏形：尚未实现完整行动经济、抗性/伤害类型、敌方 AI 行为树
- 当前抗性系统已支持平减伤与百分比减伤，但尚未引入元素反应和分层护甲系统

## 待办事项

1. 扩展伤害与对抗语义（伤害类型、抗性、护甲、减伤）
2. 遭遇系统补齐行动经济与敌方行为（不仅是 phase/turn_rule）
3. 引入技能层与熟练机制，和属性解耦
4. 为资源标签增加故事包可配置显示名（例如“先令 -> 摩拉”）
5. 增加故事包 schema 文档、校验脚本与仿真工具

## 文件夹内容快照（2026-04-08 同步）

- `backend/game/`
  - `engine.py`：会话、视图、存档
  - `content.py`：story pack 加载/归一化
  - `story_interface.py`：统一运行时接口
  - `story_runtime.py`：数据故事包运行时实现
  - `adventure.py`：节点解释器 + 遭遇框架（phase/turn_rule/objective/enemy）
  - `rules.py`：check/save/contest/damage（含抗性/减伤/穿透）+ 资源/状态/被动效果
  - `resolution.py`：统一结算结构与效果行
- `backend/stories/`
  - `grimweave/story.json`：黑暗奇幻故事包
  - `teyvat_tide_lantern/story.json`：提瓦特故事包
  - `README.md`：故事作者详细指南
  - `STORY_INTERFACE.md`：字段/接口速查
- `backend/tests/`
  - `test_rules_resolution.py`：规则与结算回归
  - `test_encounter_flow.py`：遭遇框架回归
- `frontend/`
  - `app.js`：通用渲染与 API 协作（含扩展结算/遭遇展示）
  - `index.html` / `styles.css`：界面结构与样式
- `docs/`
  - `ARCHITECTURE.md`：分层架构
  - `RUNTIME_STATE.md`：状态与存档模型
  - `ENGINEERING.md`：工程与文档维护规范

## 后续扩展必须遵守的约束

- 前端不硬编码具体剧情文本与剧情分支条件
- 新题材优先改 `backend/stories/*` 数据文件
- 若扩展逻辑，优先在解释器层做“通用能力”而非写死单故事
- 存档结构必须由后端主导定义，前端仅存取与展示
- 检定结果始终可解释（骰值、修正来源、DC、成败）
- 在 `M1` 前，优先系统建设，不把新增大型内容包当成主线任务
- 改动系统接口时，必须同步更新：
  - `backend/stories/README.md`
  - `backend/stories/STORY_INTERFACE.md`
  - `docs/*.md`
  - 必要时 `README.md / Memory.md / TODO.md`
