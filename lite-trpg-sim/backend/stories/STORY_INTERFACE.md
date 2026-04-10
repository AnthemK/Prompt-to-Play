# Story Interface Reference (v1.1)

Audience: story authors and system developers who need a compact contract reference.  
Not a full writing guide; for workflow, authoring advice, and common mistakes, read `backend/stories/README.md`.

## Purpose

Use this file when you need to answer:

- Which top-level fields are expected?
- Which action kinds are supported?
- Which effect ops are supported?
- Which encounter fields are recognized?

## Validation

Run this after changing any story file:

```bash
python3 backend/tools/story_cli.py validate
```

Validate one specific story pack:

```bash
python3 backend/tools/story_cli.py validate --story-id your_story_id
```

## 1. Top-Level Story Shape

```text
story
  id
  story_interface_version
  capabilities
  world
  stat_meta
  skill_meta?     # optional
  professions
  items
  statuses
  endings
  nodes
  encounters?    # optional
```

Required top-level fields:

- `id`
- `world`
- `stat_meta`
- `professions`
- `items`
- `statuses`
- `endings`
- `nodes`

Recommended for new packs:

- `story_interface_version: "1.1"`
- `capabilities`
- `encounters`

Supported interface versions:

- `1.0`
- `1.1`

## 2. Capabilities

Recognized `capabilities` keys:

- `checks`
- `saves`
- `contests`
- `damage`
- `healing`
- `drain`
- `encounters`
- `encounter_action_economy`
- `encounter_enemy_behaviors`
- `encounter_environment`
- `debug_trace`

Notes:

- `capabilities` is descriptive, not a runtime toggle.
- If omitted, the backend can infer it from actual story content.

## 3. Core Content Blocks

### `world`

Common fields:

- `id`
- `title`
- `chapter_title`
- `tone`
- `intro`
- `start_node`
- `start_log`
- `default_shillings`
- `corruption_limit`
- `debug_trace_enabled`
- `debug_trace_limit`
- `doom_texts`
- `corruption_penalties`
- `default_ending_id`
- `fatal_rules`
- `resolve_victory`
- `ui` (optional)

Reference rules:

- `start_node` must exist in `nodes`
- `default_ending_id` must exist in `endings`

Typical `world.ui` shape:

```json
{
  "setup_summary": "短小但覆盖面广的演示任务。",
  "setup_details": [
    { "label": "时长", "value": "8-12 分钟" },
    { "label": "风格", "value": "潜入 / 多出口" }
  ],
  "resource_labels": {
    "hp": "体力",
    "shillings": "摩拉",
    "doom": "潮汐压力"
  }
}
```

Supported `resource_labels` keys:

- `hp`
- `shield`
- `corruption`
- `shillings`
- `doom`

### `stat_meta`

Purpose:

- defines the player-facing stat set and labels

Typical shape:

```json
{
  "strength": { "label": "力量" },
  "agility": { "label": "敏捷" },
  "insight": { "label": "洞察" }
}
```

### `skill_meta` (optional)

Purpose:

- defines the shared skill vocabulary used by professions and optional skill-aware checks

Typical shape:

```json
{
  "stealth": { "label": "潜行" },
  "awareness": { "label": "警觉" },
  "grit": { "label": "坚忍" }
}
```

### `professions`

Common fields per profession:

- `id`
- `name`
- `summary`
- `stats`
- `skills`
- `max_hp`
- `starting_items`
- `perks`
- `check_bonus`
- `damage_resistances`
- `trigger_effects`

### `items`

Common fields per item:

- `id`
- `name`
- `type`
- `description`
- `check_bonus`
- `use_effects`
- `trigger_effects`
- `damage_resistances`

### `statuses`

Common fields per status:

- `id`
- `name`
- `description`
- `default_duration_turns`
- `check_bonus`
- `trigger_effects`
- `damage_resistances`

Compatibility fields still recognized:

- `per_turn_effects`
- `consume_on_check`

### `endings`

Common fields:

- `id`
- `title`
- `summary`
- `detail`
- `tone`

### `nodes`

Each node usually contains:

- `title`
- `text`
- `actions`

Supported text templates:

- `{{player.xxx}}`
- `{{progress.xxx}}`
- `{{encounter.xxx}}`
- `{{world.xxx}}`
- `{{doom_text}}`

## 4. Action Model

Common action fields:

- `id`
- `label`
- `hint`
- `kind`
- `requires`
- `on_unavailable`
- `cost`
- `turn_flow`

Supported `kind` values:

- `move`
- `story`
- `check`
- `save`
- `contest`
- `damage`
- `healing`
- `drain`
- `utility`

Kinds that require a config object:

- `check` -> `check`
- `save` -> `save`
- `contest` -> `contest`
- `damage` -> `damage`
- `healing` -> `healing`
- `drain` -> `drain`

## 5. Resolution Config Blocks

### `check` / `save`

Common fields:

- `stat`
- `skill`
- `dc`
- `label`
- `tags`
- `modifier`
- `breakdown`
- `environment_bonus_rules`
- `extra_bonus_if_flags`
- `extra_bonus_if_statuses`
- `dc_adjust_if_flags`
- `dc_adjust_if_statuses`

Authoring note:

- `dc_adjust_if_flags` and `dc_adjust_if_statuses` may also include an optional `source`
- if omitted, the engine will synthesize one for explain/debug output

Expected branch locations:

- `on_success.effects`
- `on_failure.effects`

Lifecycle note:

- `add_status` may include `duration_turns`
- if omitted, the engine can fall back to `statuses.*.default_duration_turns`
- timed statuses tick down at `turn_end`

### `contest`

Common fields:

- `stat`
- `skill`
- `label`
- `opponent_label`
- `opponent_modifier`
- `active_side`
- `tie_policy`
- `failure_cost`
- `environment_bonus_rules`

Expected branch locations:

- `on_success.effects`
- `on_failure.effects`

### `damage`

Common fields:

- `target`
- `resource`
- `damage_type`
- `amount`
- `roll`
- `penetration`
- `ignore_resistance`
- `ignore_vulnerability`
- `ignore_shield`
- `source`
- `environment_impact_rules`

### `healing`

Common fields:

- `target`
- `resource`
- `amount`
- `roll`
- `damage_type`
- `source`
- `environment_impact_rules`

### `drain`

Damage side:

- same main fields as `damage`

Recovery side:

- `recover_target`
- `recover_resource`
- `recover_percent`
- `recover_flat`
- `recover_cap`
- `recover_source`

## 6. Conditions

Used by:

- `requires`
- `if`
- related rule blocks

Supported condition forms:

- `all: [ ... ]`
- `any: [ ... ]`
- atomic condition

Atomic condition fields:

- `path`
- `ctx`
- `item`
- `status`
- `op`
- `value`

Notes:

- `status` is a lightweight shortcut for "the player currently has this status"
- recommended forms:
  - `{"status": "guarded", "op": "==", "value": true}`
  - `{"status": "ash_choked", "op": "==", "value": false}`
- use `status` when the gate should follow a temporary player condition
- use `path` or progress flags for long-lived narrative facts

Supported operators:

- `==`
- `!=`
- `>=`
- `<=`
- `>`
- `<`

## 7. Passive Triggers

Current trigger timings:

- `before_check`
- `after_check`
- `turn_end`

These trigger names are validated as a closed set.

Used in:

- `professions[*].trigger_effects`
- `items[*].trigger_effects`
- `statuses[*].trigger_effects`

Special helper op:

- `remove_self`
  - mainly useful for passive status cleanup after one trigger

## 8. Effect Ops

Supported `effect.op` values:

- `goto`
- `set_flag`
- `adjust`
- `add_item`
- `remove_first_item`
- `add_status`
- `remove_status`
- `remove_self`
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
- `adjust_environment`
- `sync_encounter_phase`
- `damage`
- `healing`
- `drain`

Notes:

- Unknown `effect.op` values are rejected by validation.
- Canonical system truth lives in `backend/game/story_contract.py`.

## 9. Encounter Template

Encounters are optional, but recommended for high-risk scenes.

Common `encounters.<id>` fields:

- `id`
- `title`
- `type`
- `summary`
- `goal`
- `pressure_label`
- `pressure_max`
- `start_pressure`
- `enemy`
- `objective`
- `environment`
- `environment_rules`
- `environment_impact_rules`
- `actions`
- `phases`
- `start_phase`
- `phase_rules`
- `turn_rules`
- `action_economy`
- `enemy_behaviors`
- `enemy_behavior_selection`
- `exit_strategies`

### `enemy`

Common fields:

- `name`
- `intent`
- `hp`
- `max_hp`
- `shield`
- `resistances`
- `vulnerabilities`

### `objective`

Common fields:

- `label`
- `start`
- `target`

### `action_economy`

Common fields:

- `budget`
- `default_cost`
- `max_actions`

### `phases.<phase_id>`

Common fields:

- `label`
- `intent`
- `summary`
- `goal`
- `actions`
- `enemy_behaviors`

### `exit_strategies`

Supported `mode` values:

- `defeat`
- `escape`
- `negotiate`
- `delay`

Runtime note:

- when one configured exit window becomes available for the first time, the
  engine now emits one player-facing unlock outcome and one log entry
- example: when `defeat` first becomes true because enemy HP reaches `0`, the
  player gets immediate feedback that the encounter can now be finished via the
  defeat route
- unlock feedback does not auto-finish the encounter; the player still chooses
  the exit action

## 10. Minimum Story-Pack Checklist

Before calling a pack ready:

- [ ] top-level required fields exist
- [ ] all references resolve
- [ ] every action `id` is unique
- [ ] every action kind has its required config block
- [ ] every ending reference exists
- [ ] validation passes

## 11. If You Need More Than This File

Read next:

1. `backend/stories/README.md`
2. `backend/stories/demo/story.json`
