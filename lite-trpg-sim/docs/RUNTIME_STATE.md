# Runtime State And Save Model

Audience: developers debugging runtime behavior, save compatibility, and frontend payload shape.  
Not for players; player-facing instructions live in the project root `README.md`.

## Purpose

This document is the data-model reference for the live game session.

Use it to answer:

- What does backend runtime `state` contain?
- What does the frontend `view` contain?
- What does a canonical save payload contain?
- Which fields are runtime-only, saveable, or presentation-only?

If you need module ownership and feature-placement guidance, read `ARCHITECTURE.md`.

## Data Model Overview

There are three main shapes:

1. `state`
   - authoritative backend runtime
2. `view`
   - frontend-facing projection returned by the engine
3. `save_data`
   - canonical import/export payload

The frontend should render `view` and persist `save_data`.  
The frontend should not mutate `state` directly.

## 1. Runtime State `state`

Top-level shape:

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
  debug_trace
  last_outcome
  game_over
  ending
```

Field notes:

- `schema_version`
  - backend-owned migration version for runtime/save compatibility
- `session_id`
  - local runtime id used by API paths
- `story_id`
  - active story pack id
- `log`
  - rolling narrative/event history
- `encounter`
  - active encounter runtime, or `None`
- `last_outcome`
  - latest structured result summary shown after one action
- `ending`
  - ending payload after game over, or `None`

## 2. Player Block `player`

```text
player
  name
  profession_id
  profession_name
  stats
  max_hp
  hp
  shield
  corruption
  shillings
  inventory
  statuses
```

Field notes:

- `stats`
  - current stat dictionary used by checks and contests
- `shield`
  - temporary buffer that absorbs compatible damage before `hp`
- `inventory`
  - authoritative storage, currently `{item_id: qty}`
- `statuses`
  - currently `status_id[]`; story/runtime lookup resolves their details

## 3. Progress Block `progress`

```text
progress
  chapter
  node_id
  doom
  turns
  flags
```

Field notes:

- `node_id`
  - current narrative node id
- `doom`
  - global pressure/campaign stress value
- `turns`
  - coarse global turn counter
- `flags`
  - lightweight persistent facts used for branching

## 4. Encounter Runtime `encounter`

`encounter` is runtime state, not the original story template.

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
  environment
  environment_meta
  environment_rules
  environment_impact_rules
  flags
  economy
  last_enemy_behavior
  enemy_behavior_cooldowns
```

Key runtime meanings:

- `round`
  - current encounter round counter
- `phase`
  - current phase id
- `pressure`
  - shared encounter pressure meter when configured
- `enemy`
  - active enemy runtime block
- `objective`
  - progress data for non-kill goals
- `environment`
  - current mutable environment values
- `economy`
  - action-spend data for the player turn

### `enemy`

Common runtime fields:

```text
enemy
  id
  name
  hp
  max_hp
  shield
  resistances
  vulnerabilities
  intent
```

Notes:

- `resistances` and `vulnerabilities` are consulted by the unified damage pipeline.
- `shield` follows the same absorb-first pattern as player shield.

### `economy`

```text
economy
  budget
  spent
  actions_taken
```

Notes:

- `budget` tracks available action resources for the round.
- `spent` tracks what the player has already consumed.
- `actions_taken` supports turn-flow and cap logic.

## 5. Last Outcome `last_outcome`

```text
last_outcome
  summary
  detail
  roll
  resolution
  changes
```

Field notes:

- `summary`
  - short outcome line for the main panel
- `detail`
  - longer explanation text
- `roll`
  - legacy compatibility field for older frontend rendering
- `resolution`
  - canonical structured result payload
- `changes`
  - compact human-readable change list for quick scanning

## 6. Debug Trace `debug_trace`

Backend-only diagnostics:

```text
debug_trace
  enabled
  max_entries
  entries[]
    ts
    level
    event
    message
    payload
```

Notes:

- Not intended for the player UI.
- Used to diagnose rule execution, state drift, and encounter bugs.
- Exposed through `GET /api/game/{session_id}/debug?limit=200`.

## 7. Unified Resolution `resolution`

Current canonical fields:

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
  amplified
  shield_absorbed
  shield_before
  shield_after
  impact_kind
  drain_recovered
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
  active_side
  passive_side
  tie
  tie_policy
  margin
  explain
  system
  effects
```

This structure is shared by:

- `check`
- `save`
- `contest`
- `damage`
- `healing`
- `drain`
- system-generated encounter transitions

### `explain`

```text
explain
  summary
  fragments[]
    code
    text
    data
```

Notes:

- `summary`
  - one-line readable explanation
- `fragments`
  - explanation atoms suitable for debug or richer frontend rendering later

### `effects`

Current common effect kinds pushed into `resolution.effects`:

- `resource`
- `status`
- `item`
- `flag`
- `encounter`
- `damage`

### Damage pipeline order

Current damage application order:

1. declare raw damage
2. apply resistance mitigation
3. apply vulnerability amplification
4. absorb with shield
5. apply remaining loss to the target resource

## 8. Frontend View `view`

The engine projects runtime `state` into one frontend-facing payload:

```text
view
  session_id
  story_id
  world
  scene
  player
  inventory
  statuses
  encounter
  progress
  recent_log
  last_outcome
  game_over
  ending
```

Important distinction:

- `view.player`
  - presentation-safe subset of player state
- `view.scene`
  - current node text and actions after runtime interpretation
- `view.encounter`
  - copied runtime block safe for rendering
- `view.recent_log`
  - truncated recent history, not the full backend log

The frontend should treat `view` as read-only render input.

## 9. Canonical Save Payload `save_data`

Backend-generated save shape:

```text
save_data
  schema_version
  saved_at
  story_id
  world_id
  state
```

Notes:

- `state` is the authoritative snapshot.
- `schema_version` belongs to backend migration logic.
- Story selection during load should be inferred from `story_id`, then `state.story_id`, then `world_id`.

## 10. Frontend Local Save Store

The browser stores save slots separately from the backend runtime:

```text
saveStore
  version
  slots
  autosave
```

Notes:

- Each slot caches display metadata for fast setup-screen rendering.
- The authoritative imported/exported content is still the backend `save_data`.
- Frontend-local save layout may change without changing backend runtime shape, as long as `save_data` stays intact.

## 11. Update Rules

Update this document when you change:

- runtime field names
- save payload shape
- view payload shape
- resolution fields
- debug trace contract

Do not use this document as:

- a feature roadmap
- a system-boundary guide
- a player rules reference
