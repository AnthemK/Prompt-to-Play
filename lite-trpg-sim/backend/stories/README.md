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

### `professions`

Use professions to create playstyle differences through:

- starting stats
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

## `trigger_effects`

Prefer `trigger_effects` for new stories.

Use it for:

- profession passives
- item passives
- status effects

Current trigger timings stay intentionally small:

- `before_check`
- `after_check`
- `turn_end`

This is deliberate. It keeps the system understandable for both authors and players.

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
