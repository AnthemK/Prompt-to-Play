# Story Author Guide

这个目录用于放置“故事包（story pack）”。

目标不是把题材硬编码进系统，而是让故事作者主要通过 `story.json` 或 `story.yaml` 接入世界观、剧情、规则参数和遭遇内容。

如果你准备写一个新的故事包，优先读这个文件；如果你想快速看字段列表，再看 [STORY_INTERFACE.md](/Users/liwenzhong/Desktop/Working/VSCode/prompt-to-play/lite-trpg-sim/backend/stories/STORY_INTERFACE.md)。

维护要求：

- 如果系统层新增/修改 story DSL、effect、encounter、resolution 相关接口，必须同步更新本文件
- 如果这里只写了字段，但没有写清语义/约束，默认视为文档不合格

## 一、目录约定

每个故事包一个目录：

```text
backend/stories/
  your_story_id/
    story.json
```

文件名当前支持：

- `story.json`
- `story.yaml`
- `story.yml`

## 二、设计原则

- 故事包负责：世界观、文本、职业、物品、状态、节点、遭遇、结局、规则参数
- 系统层负责：解释 story、推进状态、执行检定、处理存档、输出统一视图
- 新题材优先通过“加数据”实现，不要要求前端改 UI，不要要求后端写死专属逻辑

## 三、顶层结构

一个完整故事包当前建议包含：

- `id`
- `world`
- `stat_meta`
- `professions`
- `items`
- `statuses`
- `endings`
- `nodes`
- `encounters`（可选，推荐新故事使用）

## 四、world

`world` 负责定义故事级元数据与系统参数。

常用字段：

- `id`
- `title`
- `chapter_title`
- `tone`
- `intro`
- `start_node`
- `start_log`
- `default_shillings`
- `corruption_limit`
- `doom_texts`
- `corruption_penalties`
- `default_ending_id`
- `fatal_rules`
- `resolve_victory`

注意：

- `start_node` 必须存在于 `nodes`
- `default_ending_id` 必须存在于 `endings`
- `fatal_rules` 用于生命归零、腐化超限时的通用终止逻辑

## 五、职业 / 物品 / 状态

### professions

每个职业至少应包含：

- `id`
- `name`
- `summary`
- `stats`
- `max_hp`
- `starting_items`
- `perks`
- `check_bonus`
- `damage_resistances`（可选）

### items

物品常用字段：

- `id`
- `name`
- `type`
- `description`
- `check_bonus`
- `use_effects`
- `trigger_effects`
- `damage_resistances`（可选）

### statuses

状态常用字段：

- `id`
- `name`
- `description`
- `check_bonus`
- `trigger_effects`
- `damage_resistances`（可选）
- `per_turn_effects`（兼容旧写法）
- `consume_on_check`（兼容旧写法）

建议：

- 新故事优先使用 `trigger_effects`
- `per_turn_effects` 和 `consume_on_check` 目前仍可用，但属于兼容层

## 六、节点（nodes）

每个节点至少有：

- `title`
- `text`
- `actions`

文本支持模板变量：

- `{{player.xxx}}`
- `{{progress.xxx}}`
- `{{encounter.xxx}}`
- `{{world.xxx}}`
- `{{doom_text}}`

## 七、行动（actions）

每个行动通常包含：

- `id`
- `label`
- `hint`
- `kind`

支持的 `kind`：

- `move`
- `story`
- `check`
- `save`
- `contest`
- `damage`
- `utility`（系统自动生成，通常不手写）

常用附加字段：

- `requires`
- `on_unavailable`
- `effects`
- `check`
- `save`
- `contest`
- `damage`
- `on_success`
- `on_failure`

重要约束：

- 一个故事包内，`action.id` 最好保持全局唯一
- 因为当遭遇动作和节点动作同时出现时，它们会合并显示

## 八、条件表达式（requires / if）

当前支持：

- `all`
- `any`
- `path + op + value`
- `ctx + op + value`
- `item + op + value`

`path` 可以读取运行态，比如：

- `player.hp`
- `player.corruption`
- `progress.flags.some_flag`
- `encounter.pressure`

当前支持操作符：

- `==`
- `!=`
- `>=`
- `<=`
- `>`
- `<`

## 九、effects DSL

当前系统支持：

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

### 1) 基础效果

这些用于普通剧情推进：

- `goto`
- `set_flag`
- `adjust`
- `add_item`
- `remove_first_item`
- `add_status`
- `remove_status`
- `log`

### 2) 结果输出

如果你希望行动结束后展示明确结果，使用：

- `outcome`

`outcome` 字段常用：

- `summary`
- `detail`
- `changes`（可选）

即使不写 `changes`，系统也会根据统一结算结果自动补一部分变化提示。

### 3) 终止类

- `finish`
- `finish_if`
- `resolve_victory`

### 4) 遭遇类（新增）

#### `start_encounter`

启动一个遭遇模板：

```json
{ "op": "start_encounter", "encounter": "dock_ambush" }
```

可选字段：

- `round`
- `pressure`

#### `adjust_encounter`

当前最小实现支持修改遭遇压力：

```json
{ "op": "adjust_encounter", "amount": 1 }
```

可选字段：

- `field`：当前仅支持 `pressure`

#### `set_encounter_flag` / `clear_encounter_flag`

写入或清理遭遇局部 flag：

```json
{ "op": "set_encounter_flag", "flag": "bridge_cut", "value": true }
```

```json
{ "op": "clear_encounter_flag", "flag": "bridge_cut" }
```

#### `adjust_enemy_hp`

调整遭遇内敌方生命（自动夹在 `0..max_hp`）：

```json
{ "op": "adjust_enemy_hp", "amount": -2 }
```

#### `adjust_objective`

调整遭遇目标进度（自动夹在 `0..target`）：

```json
{ "op": "adjust_objective", "amount": 1 }
```

#### `sync_encounter_phase`

手动触发一次阶段规则重算：

```json
{ "op": "sync_encounter_phase" }
```

#### `end_encounter`

结束当前遭遇：

```json
{ "op": "end_encounter" }
```

### 5) 伤害类

#### `damage`

执行伤害结算并写入统一 `resolution`：

```json
{
  "op": "damage",
  "target": "player",
  "resource": "hp",
  "damage_type": "physical",
  "amount": 2,
  "penetration": 1,
  "source": "伏击者刀伤"
}
```

也支持骰伤害：

```json
{
  "op": "damage",
  "damage": {
    "target": "enemy",
    "resource": "hp",
    "damage_type": "fire",
    "roll": { "dice": 1, "sides": 6, "bonus": 1 },
    "source": "坍塌冲击"
  }
}
```

字段说明：

- `target`：`player`（默认）或 `enemy`
- `resource`：当前常用为 `hp`
- `damage_type`：伤害类型（如 `physical/fire/poison`）
- `amount`：固定伤害
- `roll`：骰伤害配置（可与 `amount` 叠加）
- `penetration`：穿透值（先抵消平减伤）
- `ignore_resistance`：为 `true` 时忽略抗性
- `source`：结果解释来源

### 6) 抗性规则

抗性规则可写在：

- `professions[].damage_resistances`
- `items.<id>.damage_resistances`
- `statuses.<id>.damage_resistances`
- `encounters.<id>.enemy.resistances`

规则对象：

- `type`：单一伤害类型，`any` 表示全类型
- `type_in`：类型列表（可选）
- `reduce`：平减伤
- `percent`：百分比减伤
- `source`：显示来源（可选）

## 十、encounters（推荐新故事使用）

`encounters` 是可选顶层字典。

一个最小遭遇模板示例：

```json
{
  "dock_ambush": {
    "id": "dock_ambush",
    "title": "码头伏击",
    "type": "hostile",
    "summary": "敌人试图包抄你。",
    "goal": "脱离包围",
    "pressure_label": "警戒",
    "pressure_max": 3,
    "start_phase": "opening",
    "enemy": {
      "name": "伏击者",
      "intent": "压迫并逼退",
      "hp": 6,
      "max_hp": 6,
      "resistances": [
        { "type": "fire", "reduce": 1, "source": "敌方：防火披肩" }
      ]
    },
    "objective": {
      "label": "稳控进度",
      "start": 0,
      "target": 2
    },
    "phases": {
      "opening": {
        "label": "压制阶段",
        "intent": "试图包围"
      },
      "critical": {
        "label": "破防阶段",
        "intent": "准备总攻",
        "actions": [
          {
            "id": "encounter_save",
            "label": "稳住心志",
            "kind": "save",
            "save": { "stat": "will", "dc": 11, "label": "惊惧豁免" },
            "on_success": { "effects": [{ "op": "adjust_objective", "amount": 1 }] },
            "on_failure": { "effects": [{ "op": "damage", "amount": 1, "source": "惊惧反噬" }] }
          }
        ]
      }
    },
    "phase_rules": [
      { "if": { "path": "encounter.pressure", "op": ">=", "value": 2 }, "phase": "critical" }
    ],
    "turn_rules": [
      {
        "if": { "path": "encounter.phase", "op": "==", "value": "opening" },
        "effects": [{ "op": "adjust_encounter", "amount": 1 }]
      }
    ],
    "actions": [
      {
        "id": "encounter_hold",
        "label": "稳住阵线",
        "kind": "contest",
        "contest": {
          "stat": "agility",
          "label": "阵线对抗",
          "opponent_label": "伏击者",
          "opponent_modifier": 1
        },
        "on_success": {
          "effects": [
            { "op": "adjust_encounter", "amount": 1 },
            { "op": "adjust_objective", "amount": 1 },
            { "op": "outcome", "summary": "你顶住了冲击。", "detail": "局势仍在拉扯。" }
          ]
        },
        "on_failure": {
          "effects": [{ "op": "damage", "amount": 2, "source": "伏击者刀伤" }]
        }
      }
    ]
  }
}
```

说明：

- 遭遇动作会与当前节点动作一起显示
- 遭遇当前状态会出现在前端“当前遭遇”面板
- `turn_end` 时会自动让 `encounter.round +1`
- 当前遭遇框架支持阶段切换、阶段动作、回合规则、敌方生命和目标进度

## 十一、trigger_effects（新增推荐写法）

`professions / items / statuses` 都可以定义 `trigger_effects`。

每个 effect 额外带：

- `trigger`
- `match`（可选）

当前触发时机：

- `before_check`
- `after_check`
- `turn_end`

`match` 常用字段：

- `stat`
- `stat_in`
- `success`
- `tags_any`
- `tags_all`

示例：

```json
{
  "trigger_effects": [
    {
      "trigger": "after_check",
      "match": { "stat": "will", "success": true },
      "op": "remove_status"
    }
  ]
}
```

## 十二、统一结算结果（系统会自动生成）

玩家每次行动后，后端会生成 `last_outcome.resolution`。

当前常见字段：

- `kind`
- `label`
- `success`
- `stat`
- `dc`
- `roll`
- `modifier`
- `total`
- `tags`
- `breakdown`
- `effects`
- `amount/applied/mitigated`（damage）
- `damage_type/target/target_label`（damage）

故事作者通常不需要手写它，但应理解：

- 物品消耗
- 状态获得/移除
- 资源变化
- 遭遇进入/离开/压力变化
- 遭遇阶段变化
- 伤害生效结果

都会被记录进这个统一结果对象。

## 十三、编写故事时的注意事项

- 优先通过配置表达规则，不要依赖系统层专门给你的故事开后门
- `flag` 用于剧情分支很方便，但不要把复杂系统都堆成一堆布尔值
- 高风险事件优先写成 `encounter`，不要全靠节点文本硬模拟
- 结局判定尽量通过 `resolve_victory` 或统一状态来表达
- 尽量让失败也有后果路线，而不是只有“什么都没发生”
- 行动标签、职业加成、物品加成、状态效果之间要能互相解释

## 十四、常见坑

- `start_node` 指向不存在的节点
- `default_ending_id` 不存在
- `action.id` 重名，导致节点动作和遭遇动作冲突
- `requires` 读取了不存在的路径
- 使用大量专用 `flag` 去模拟本应成为系统对象的内容
- 把题材特有逻辑写进系统需求，而不是写进 story 数据

## 十五、建议的开发流程

1. 先写世界观与职业框架
2. 再写核心节点链
3. 再补状态、物品、结局
4. 高风险段落优先改为 `encounters`
5. 最后跑校验、冒烟路线与仿真

## 十六、文档维护约定

这个 README 不是一次性说明书。

当系统新增以下能力时，应同步更新这里：

- 顶层字段变化
- effect DSL 变化
- trigger 生命周期变化
- 遭遇系统变化
- 存档结构变化
- 编写建议与坑点
