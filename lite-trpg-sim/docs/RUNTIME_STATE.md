# Runtime State And Save Model

本文档记录当前系统层最重要的数据模型，方便 review、调试和后续扩展。

## 1. 运行态 `state`

运行态由后端持有，前端不会直接修改。

```text
state
  schema_version
  session_id
  story_id
  created_at
  player
  progress
  log
  encounter
  last_outcome
  game_over
  ending
```

## 2. `player`

```text
player
  name
  profession_id
  profession_name
  stats
  max_hp
  hp
  corruption
  shillings
  inventory
  statuses
```

说明：

- `stats` 是当前的基础属性字典
- `inventory` 是 `{item_id: qty}`
- `statuses` 目前是 `status_id[]`

## 3. `progress`

```text
progress
  chapter
  node_id
  doom
  turns
  flags
```

说明：

- `node_id` 是当前剧情节点
- `doom` 是全局压力值
- `turns` 是统一回合计数
- `flags` 是临时的轻量全局事实记录

## 4. `encounter`

当前遭遇态已经是正式字段：

```text
encounter
  id
  title
  type
  summary
  goal
  round
  phase
  phase_label
  intent
  pressure
  pressure_label
  pressure_max
  enemy
  objective
  flags
```

说明：

- 这是运行态，不是故事模板
- 遭遇模板来自 `story.json` 顶层 `encounters`
- 当前关键动态字段：`round / pressure / phase / enemy.hp / objective.progress`
- 当前敌方支持：`enemy.resistances`（伤害抗性规则）

## 5. `last_outcome`

```text
last_outcome
  summary
  detail
  roll
  resolution
  changes
```

说明：

- `roll` 是旧前端兼容字段
- `resolution` 是统一结算结构，未来会逐步成为主字段
- `changes` 是展示层的短摘要列表

## 6. `resolution`

统一结算结构当前关键字段：

```text
resolution
  kind
  label
  success
  stat
  dc
  roll
  modifier
  total
  tags
  breakdown
  amount
  applied
  mitigated
  damage_type
  target
  target_label
  penetration
  resistance_flat
  resistance_percent
  opponent_label
  opponent_roll
  opponent_modifier
  opponent_total
  effects
```

### `effects`

当前已支持的 effect kind：

- `resource`
- `status`
- `item`
- `flag`
- `encounter`
- `damage`

## 7. 存档结构

后端导出的 canonical save payload：

```text
save_data
  schema_version
  saved_at
  story_id
  world_id
  state
```

说明：

- 前端只存取整个 `save_data`
- 前端不应自行拼装 `state`
- 兼容迁移应该在后端完成

## 8. 前端本地槽位结构

前端 `localStorage` 中保存：

```text
saveStore
  version
  slots
  autosave
```

槽位条目除了 `save_data` 之外，还缓存标题、角色名、回合数等展示信息，便于 setup overlay 快速显示。

## 9. 后续扩展建议

如果继续扩 encounter / growth / faction 等系统，建议优先：

1. 先在本文件登记 state/save/view 的目标形态
2. 再修改代码和 story DSL
3. 最后补测试与作者文档
