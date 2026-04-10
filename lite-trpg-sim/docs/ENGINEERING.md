# Engineering Standards

Audience: developers changing code, system interfaces, tooling, or review practices.  
Not for players; player-facing instructions live in the project root `README.md`.

## Purpose

This document records long-lived engineering rules for the repository.

Use it to answer:

- What coding discipline does this project require?
- What must stay documented and commented?
- What naming patterns should we preserve?
- What should be checked before code is considered reviewable?

Do not use this file as a stage report or milestone checklist.  
Stage-specific acceptance belongs in `STAGE_DELIVERY.md`.

## Core Engineering Principles

- Build reusable system capability before scaling content.
- Keep story logic out of the frontend.
- Keep setting-specific hacks out of the engine.
- Update explanations when code changes.
- Prefer readable abstractions over clever shortcuts.
- Keep the codebase easy to review, trace, and hand off.

## Documentation Discipline

Every meaningful system change should trigger a documentation sweep.

### Code-level documentation

Keep these synchronized:

- module docstrings
- public function docstrings
- comments around complex state transitions
- comments around compatibility or migration logic
- comments at frontend/backend boundaries

### Interface-level documentation

If a change affects story-pack authoring, update:

- `backend/stories/README.md`
- `backend/stories/STORY_INTERFACE.md`

### Project-level documentation

Check the correct audience-specific file:

- `README.md`
  - player and normal-user guide
- `MEMORY.md`
  - current handoff snapshot
- `TODO.md`
  - forward roadmap only
- `docs/TECHNICAL_OVERVIEW.md`
  - technical doc index
- `docs/*.md`
  - long-lived technical reference

## Commenting Standard

### Comments are required for

- module entry files
- public functions
- state-shape mutation points
- complex resolution and effect flows
- compatibility bridges and migration logic
- backend/frontend integration points

### Good comments should explain

- why this logic exists
- what constraint it is preserving
- what the input/output contract means
- where the responsibility boundary ends

### Frontend state and visibility rule

- If a component uses the HTML `hidden` attribute for visibility, CSS must preserve that semantic.
- If the component also declares its own `display` mode, add an explicit selector such as:
  - `[hidden] { display: none; }`
  - or `.component[hidden] { display: none; }`
- Do not patch around hidden-state bugs with extra JavaScript until CSS semantics have been checked first.

### Bad comments to avoid

- comments that repeat the literal code
- comments that only narrate syntax
- stale comments that describe removed behavior

## Naming Standard

Prefer names that distinguish runtime data from static configuration.

Stable vocabulary:

- `story_id`
  - story-pack identifier
- `world_id`
  - world/save mapping identifier
- `state`
  - authoritative runtime snapshot
- `view`
  - frontend-facing read-only projection
- `resolution`
  - structured outcome payload
- `encounter_runtime`
  - active runtime encounter block
- `encounter_template`
  - static story-defined encounter template

Avoid these mistakes:

- using `encounter` for both runtime and template in the same scope
- mutating `view` as if it were authoritative state
- naming story content as if it were engine-owned system data

## State Modeling Rule

When choosing between `flags`, `statuses`, and encounter fields:

- use `progress.flags` for persistent story facts
- use `player.statuses` for temporary player conditions
- use encounter runtime fields for pressure-scene-local state

Do not use flags as a generic substitute for every short-lived condition.
If a condition mainly exists to affect the next few rolls or the current encounter, prefer a status-first model.

## Change Workflow

Recommended order for non-trivial system changes:

1. define the boundary
2. decide whether `state`, `view`, or `save_data` changes
3. decide whether the story contract changes
4. update runtime code
5. update comments and technical docs
6. add or refresh tests
7. update `MEMORY.md` and `TODO.md` if priorities or project shape changed

## Review Checklist

Before calling a change ready for review, verify:

1. no setting-specific logic leaked into system modules
2. `state`, `view`, and `save_data` still tell a coherent story
3. player-visible results remain explainable
4. story DSL complexity did not grow without clear value
5. comments and docs match implementation
6. important bugs can still be traced through `debug_trace`
7. passive lifecycle changes can be explained from trigger to state change

## Tooling Check

Run this before wrapping a meaningful code change:

```bash
python3 backend/tools/review_guard.py --doc-sync
```

Use this check to enforce that code changes are accompanied by the right documentation updates.

## Technical Debt Rule

Do not postpone all cleanup to a later "polish" pass.

Instead:

- clean nearby naming issues while touching a module
- add missing comments while context is fresh
- remove misleading compatibility leftovers when safe
- record real future work in `TODO.md`, not as hidden debt in code

## When Updating This Document

Update this file when you change:

- repository-wide review standards
- comment or naming rules
- documentation sync rules
- long-lived development workflow expectations

Do not put here:

- player instructions
- stage acceptance results
- one-off milestone conclusions
