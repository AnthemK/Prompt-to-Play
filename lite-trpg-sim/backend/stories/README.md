# Story Author Guide

Audience: authors creating or maintaining story packs.  
Not for players; player-facing information lives in the project root `README.md`.

## Purpose

This file is the onboarding guide for writing story packs that plug into `lite-trpg-sim`.

Use it to answer:

- How do I start a new story pack quickly?
- What belongs in story data and what belongs in the engine?
- What is the safest author workflow?
- What mistakes should I avoid?

If you only need field names and supported kinds, jump to [STORY_INTERFACE.md](/Users/liwenzhong/Desktop/Working/VSCode/prompt-to-play/lite-trpg-sim/backend/stories/STORY_INTERFACE.md).

## Fast Start

If you want the shortest path to a playable pack, do this:

1. create `backend/stories/your_story_id/story.json`
2. write:
   - `id`
   - `world`
   - `stat_meta`
   - `skill_meta` if the story needs a small skill layer
   - `professions`
   - `items`
   - `statuses`
   - `endings`
   - `nodes`
3. make sure one short route can reach one ending
4. run:

```bash
python3 backend/tools/story_cli.py validate --story-id your_story_id
```

Only after that, expand branches, encounters, and polish.

## Recommended Reading Order

1. this file
2. [STORY_INTERFACE.md](/Users/liwenzhong/Desktop/Working/VSCode/prompt-to-play/lite-trpg-sim/backend/stories/STORY_INTERFACE.md)
3. one existing playable story pack
4. `demo/story.json` if you want the widest mechanics coverage

## What Belongs In A Story Pack

Story packs should define:

- setting and world tone
- narrative text
- professions
- items and statuses
- nodes and branches
- encounter templates
- endings
- light rules-facing configuration

The engine should define:

- state progression
- action interpretation
- checks and resolutions
- encounter runtime behavior
- save/load behavior
- frontend view shaping

Rule of thumb:

- if it is content for one setting, keep it in story data
- if several stories would reuse it, it may belong in the system

## Safe Author Workflow

### 1. Create One Story Folder

```text
backend/stories/
  your_story_id/
    story.json
```

Supported filenames:

- `story.json`
- `story.yaml`
- `story.yml`

Optional scaffold helper:

```bash
python3 backend/tools/story_cli.py scaffold --id your_story_id
```

### 2. Build A Minimum Playable Spine

Start with these top-level fields:

- `id`
- `world`
- `stat_meta`
- `skill_meta` if you want skill-aware checks
- `professions`
- `items`
- `statuses`
- `endings`
- `nodes`

Recommended for all new stories:

- `story_interface_version: "1.1"`
- `capabilities`
- `encounters`

### 3. Write In This Order

The safest build order is:

1. `world`
2. professions
3. a short node chain that can reach one ending
4. items and statuses
5. one encounter for the highest-risk scene
6. alternate routes and additional endings

This keeps the story playable while it grows.

### 4. Validate Early And Often

Run after every meaningful edit:

```bash
python3 backend/tools/story_cli.py validate
```

Validate only one pack:

```bash
python3 backend/tools/story_cli.py validate --story-id your_story_id
```

## Minimal Structure Advice

### `world`

Use `world` for:

- story title and intro
- story-facing setup summary/detail metadata
- story-specific visible resource labels
- chapter title
- starting node
- default money
- corruption limit
- doom flavor text
- fallback ending rules
- fatal fail rules

### `stat_meta`

Keep the attribute set short and readable.  
This is a lite simulator, so a small stable stat list is usually stronger than many narrow stats.

### `skill_meta`

Use `skill_meta` only when the story benefits from a small shared skill vocabulary.

Good use:

- `潜行`
- `警觉`
- `坚忍`
- `压制`

Avoid:

- long MMO-style skill lists
- overlapping micro-skills that players cannot read at a glance

### `world.ui`

Use `world.ui` to customize the generic frontend without pushing story logic into the frontend.

Good use:

- `setup_summary`
  - one short paragraph that explains what kind of run this story offers
- `setup_details`
  - small chips such as duration, tone, or route style
- `resource_labels`
  - rename generic resources so they read naturally in the current setting

Examples:

- `shillings -> 摩拉`
- `doom -> 潮汐压力`
- `hp -> 伤势`

Avoid:

- hiding actual rules behind flavor text
- using `world.ui` for branching logic
- packing large lore dumps into the setup overlay

### `professions`

Use professions to create playstyle differences through:

- starting stats
- starting skills
- starting items
- a few meaningful bonuses
- a short identity summary

Avoid turning professions into giant subsystem bundles.

### `nodes`

Use nodes for:

- scene text
- player choices
- lightweight checks
- route branching

### `encounters`

Use encounters when a scene should feel like a pressured situation instead of a single click.

Good encounter use cases:

- combat
- infiltration
- chase
- holding action
- negotiation under pressure

## Writing For Lite Play

The target feel is tabletop-flavored and readable, not heavy and tactical.

Good patterns:

- give one problem multiple approaches
- let failure change state instead of only blocking progress
- use statuses and resources as consequences
- keep numbers understandable
- keep action labels readable at a glance

Patterns to avoid:

- too many tiny conditional modifiers
- large profession-specific subsystems
- long combat loops with little narrative change
- many loose flags where a status or encounter field would be clearer

## Rules Authoring Heuristics

You do not need to memorize every field. Use [STORY_INTERFACE.md](/Users/liwenzhong/Desktop/Working/VSCode/prompt-to-play/lite-trpg-sim/backend/stories/STORY_INTERFACE.md) as the contract reference.

At the authoring level, the main distinction is:

- resolution config
  - how the action is judged
- effect list
  - what changes because of that judgment

Choose these action types by fiction:

- `check` / `save`
  - a clear success/failure gate
- `contest`
  - the fiction is "you vs something"
- `damage` / `healing` / `drain`
  - resource impact is itself meaningful

If a check is about a specific competence, prefer:

- `attribute + optional skill`

Example:

- `洞察 + 警觉`

If the fiction says "this is easier or harder only while a status is active", prefer:

- `extra_bonus_if_statuses`
- `dc_adjust_if_statuses`

This is usually cleaner than giving the status a broad `check_bonus` that leaks into unrelated rolls.

If you raise or lower DC conditionally, add a short `source` string when possible.

That text will surface in explain/debug output, which makes balancing and bug reports much easier to read.
- `敏捷 + 潜行`
- `意志 + 坚忍`

## `trigger_effects`

Prefer `trigger_effects` for new stories.

Use it for:

- profession passives
- item passives
- status effects
- finite-duration status loops, when a state should naturally expire after a few turns

Current trigger timings stay intentionally small:

- `before_check`
- `after_check`
- `turn_end`

This is deliberate. It keeps the system understandable for both authors and players.

Validation now treats this as a closed vocabulary, so avoid inventing new trigger names in story data unless the engine has first been extended to support them.

For lightweight timed states, you can now choose either:

- `statuses.*.default_duration_turns`
  - good when a status normally lasts a fixed number of turns
- `add_status.duration_turns`
  - good when the same status can last different lengths in different story contexts

## First Encounter Rule

If you add an encounter, keep the first version small:

- 1 clear goal
- 1 enemy or pressure source
- 1 or 2 phases
- a few readable actions
- at least 1 alternate exit strategy

Small clear encounters are better than large brittle ones.

## Common Validation Failures

The most common problems are:

- missing referenced node, item, status, ending, or encounter
- duplicated `action.id`
- action kind missing its required config object
- invalid phase reference
- invalid `effect.op`

If runtime behavior feels mysterious, validate first.

## Common Author Mistakes

- making the player read too much before every meaningful choice
- using too many booleans where a status or encounter field would be clearer
- writing a scene as plain nodes when it really wants encounter structure
- expecting frontend changes for one story-specific gimmick
- pushing setting-specific logic into the engine

## Flags vs Statuses

Use `flags` for:

- persistent discoveries
- long-term relationship facts
- route knowledge that should survive many scenes

Use `statuses` for:

- temporary tactical states
- short-lived mental or bodily conditions
- "this next check is easier/harder" style effects
- conditions that should expire, be consumed, or be removed explicitly

Rule of thumb:

- if the player should still meaningfully "have" it many scenes later, it is probably a flag
- if it mainly affects the current pressure situation or a small number of rolls, it is probably a status

## Playable Checklist

Before calling a story pack playable:

- [ ] it can start from character creation
- [ ] at least one route reaches an ending
- [ ] at least one failure path changes state meaningfully
- [ ] validation passes
- [ ] important actions have readable labels and hints
- [ ] the story does not require frontend hardcoding

## Demo Story Rule

When a new system ability lands, decide whether the `demo` story should cover it.

Use the demo story for:

- regression coverage
- mechanic explanation by example
- verifying new story-pack-facing features

## Maintenance Rule

If story-facing behavior changes, update both:

- this guide
- [STORY_INTERFACE.md](/Users/liwenzhong/Desktop/Working/VSCode/prompt-to-play/lite-trpg-sim/backend/stories/STORY_INTERFACE.md)

They serve different purposes and should stay aligned.
