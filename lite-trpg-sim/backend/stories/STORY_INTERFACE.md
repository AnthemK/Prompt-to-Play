# Story Interface (v1)

这个文件定义“故事包如何无缝接入系统”的统一接口约定。

更详细的写作指南见：

- `backend/stories/README.md`

维护要求：

- 每次 story DSL 或运行时接口调整后，都必须同步更新本文件
- 本文件偏字段清单，语义解释应补充到 `backend/stories/README.md`

## 目标

- 新故事应尽量只改 `backend/stories/<story_id>/story.json|yaml`
- `backend/game/*` 不应再写入具体题材的地名、角色、结局 ID
- 引擎通过统一 `StoryRuntime` 接口运行故事

## 必需顶层字段

- `id`: 故事唯一标识
- `world`: 世界元数据与系统规则
- `stat_meta`: 属性定义
- `professions`: 职业模板列表
- `items`: 物品字典
- `statuses`: 状态字典
- `endings`: 结局字典
- `nodes`: 剧情节点字典
- `encounters`: 遭遇模板字典（可选）

## world 关键字段

- `id`, `title`, `chapter_title`, `intro`
- `start_node`, `start_log`
- `default_shillings`, `corruption_limit`
- `doom_texts`: 根据 doom 显示文本
- `corruption_penalties`: 腐化惩罚段
- `default_ending_id`: 通用回退结局
- `fatal_rules`:
  - `on_hp_zero`: `{ ending, summary }`
  - `on_corruption_limit`: `{ ending, summary }`
- `resolve_victory`:
  - `default`: `{ ending, summary }`
  - `rules`: 条件规则数组

## 节点模型

`nodes.<node_id>`:

- `title`
- `text`（支持 `{{player.xxx}}`、`{{progress.xxx}}`、`{{doom_text}}`）
- `actions`: 行动列表

## 行动模型

通用字段：

- `id`, `label`, `hint`, `kind`
- `requires`（可选）
- `on_unavailable`（可选）

`kind=check` 时：

- `check`: 检定配置
- `on_success.effects`
- `on_failure.effects`

`kind=save` 时：

- `save`: 豁免配置（字段结构与 `check` 基本一致）
- `on_success.effects`
- `on_failure.effects`

`kind=contest` 时：

- `contest`: 对抗配置
  - 常用字段：`stat`, `label`, `opponent_label`, `opponent_modifier`
- `on_success.effects`
- `on_failure.effects`

`kind=damage` 时：

- `damage`: 伤害配置
  - 常用字段：`target`, `resource`, `damage_type`, `amount`, `roll`, `penetration`, `ignore_resistance`, `source`
- `on_success.effects`（可选）
- `on_failure.effects`（可选）

`kind=story/move` 时：

- `effects`

遭遇激活时：

- `encounters.<id>.actions` 会与当前节点动作一起展示

## 条件表达式（requires / if）

支持：

- `all: [cond...]`
- `any: [cond...]`
- 原子条件：
  - `path + op + value`
  - `ctx + op + value`
  - `item + op + value`

`op` 当前支持：`== != >= <= > <`

## effects DSL（当前支持）

- `goto`
- `set_flag`
- `adjust`
- `add_item`
- `remove_first_item`
- `add_status`
- `remove_status`
- `outcome`
- `log`
- `finish`
- `finish_if`
- `resolve_victory`
- `start_encounter`
- `adjust_encounter`
- `end_encounter`
- `set_encounter_flag`
- `clear_encounter_flag`
- `adjust_enemy_hp`
- `adjust_objective`
- `sync_encounter_phase`
- `damage`

## 遭遇模板（encounters）扩展字段

`encounters.<id>` 目前常用字段：

- `id`, `title`, `type`, `summary`, `goal`
- `pressure_label`, `pressure_max`, `start_pressure`
- `enemy`: `{name, intent, hp, max_hp}`
- `enemy.resistances`: 抗性规则（可选）
- `objective`: `{label, start, target}`
- `actions`: 全局遭遇动作
- `phases`: 阶段字典，`phases.<phase_id>` 可含：
  - `label`, `intent`, `summary`, `goal`, `actions`
- `start_phase`
- `phase_rules`: 条件触发的阶段切换规则
- `turn_rules`: 每回合推进时执行的 effect 列表规则

说明：

- 当前遭遇动作会合并 `encounters.<id>.actions` 与 `phases.<phase_id>.actions`
- 动作可通过 `phase` / `phase_in` / `phase_not_in` 控制显示

## 伤害抗性规则（damage_resistances / resistances）

支持在这些位置定义抗性规则：

- `professions[].damage_resistances`
- `items.<id>.damage_resistances`
- `statuses.<id>.damage_resistances`
- `encounters.<id>.enemy.resistances`

规则对象常用字段：

- `type`: 伤害类型（如 `physical`, `fire`, `poison`；`any` 表示通用）
- `type_in`: 类型列表（可选）
- `reduce`: 平减伤
- `percent`: 百分比减伤（总和会被系统限制）
- `source`: 解释文本（可选）

## 被动效果生命周期（新增约定）

以下对象可定义 `trigger_effects`：

- `professions`
- `items`
- `statuses`

每个 `trigger_effects` 元素是一个 effect 对象，额外包含：

- `trigger`
- `match`（可选）

当前已接入的触发时机：

- `before_check`
- `after_check`
- `turn_end`

`match` 当前常用字段：

- `stat`
- `stat_in`
- `success`
- `tags_any`
- `tags_all`

被动 effect 当前建议使用的 op：

- `adjust`
- `set_flag`
- `add_item`
- `remove_first_item`
- `add_status`
- `remove_status`
- `log`

兼容字段：

- `statuses.<id>.per_turn_effects` 仍兼容，等价于 `trigger=turn_end`
- `statuses.<id>.consume_on_check` 仍兼容，等价于 `trigger=after_check` 的自移除效果

## 兼容性建议

- 新增字段尽量“只增不改”
- 避免删除现有字段语义
- 新增机制优先扩展 DSL，再改引擎
