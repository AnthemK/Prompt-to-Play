# MEMORY

## Purpose

This file is the fast handoff page for `lite-trpg-sim`.

Use it to answer:

- What is this project right now?
- How is it structured?
- What is stable?
- What still needs attention?

Do not use this file as a full changelog, player guide, or deep technical spec.

## Document Boundaries

- `README.md`
  - Player-facing guide only
- `MEMORY.md`
  - Current project state and handoff summary
- `TODO.md`
  - Forward-looking roadmap
- `docs/TECHNICAL_OVERVIEW.md`
  - Technical document index
- `backend/stories/README.md`
  - Story author guide

## Product Snapshot

- Project type:
  - Local browser-based lite TRPG simulator
- Current shape:
  - Playable prototype, not a throwaway demo
- Core promise:
  - Reusable front end
  - Story/system logic driven by backend story packs
- Current built-in story packs:
  - `grimweave`
  - `teyvat_tide_lantern`
  - `demo`

## What Is Already Working

- Local launcher:
  - `launcher.py`
  - `launch_game.command`
- Frontend shell:
  - Story selection
  - Character creation
  - Narrative display
  - Action buttons
  - Save/load/import/export
  - Encounter panel
- Backend systems:
  - Story pack loading
  - Session and save handling
  - Generic node/action/effect interpreter
  - Unified resolution output
  - Encounter runtime
  - Debug trace endpoint
- Story authoring support:
  - Story validation CLI
  - Story scaffold CLI
  - Story author docs

## Architecture Snapshot

### Frontend

- Location:
  - `frontend/`
- Responsibilities:
  - Render current scene
  - Render player panel and encounter panel
  - Send actions to backend
  - Manage browser-local save slots
- Non-responsibilities:
  - No hardcoded story text
  - No hardcoded branch logic

### Backend

- Location:
  - `backend/`
- Responsibilities:
  - Load story packs
  - Interpret actions and effects
  - Apply rules and resolutions
  - Manage runtime state and saves
  - Expose HTTP API for the frontend

### Story Layer

- Location:
  - `backend/stories/*`
- Responsibilities:
  - World data
  - Narrative content
  - Professions, items, statuses
  - Nodes, actions, encounters, endings

## Mechanics Snapshot

Current system is intentionally lite.

### Stable enough to build on

- `d20` checks with visible breakdown
- Unified result types:
  - `check`
  - `save`
  - `contest`
  - `damage`
  - `healing`
  - `drain`
- Items and statuses affecting checks
- Corruption / HP / shield / money tracking
- Encounter runtime with:
  - phases
  - turn rules
  - action costs
  - enemy behaviors
  - exit strategies
  - environment state

### Still intentionally shallow

- No heavy build system
- No full CRPG combat simulation
- No large progression tree
- No complicated tactical grid

## Current Strategic Direction

The next phase should improve coherence, not scale.

Priority order:

1. Keep the rules readable and lightweight
2. Improve story-author ergonomics
3. Improve encounter clarity and state consistency
4. Avoid feature sprawl that turns the project into a pseudo-CRPG

Current active milestone in `TODO.md`:

- Lite Core Polish
  - small skill layer
  - effect lifecycle cleanup
  - story-facing label and metadata polish
  - UX readability pass
  - Demo story refit
    - now completed at a first useful pass
    - Demo now behaves more like a short mission showcase
    - acceptance coverage has been expanded with `before_check` and true `defeat`

## Current Risks

- `TODO.md` previously accumulated too many large-system ambitions; this needs continuous pruning toward a lite design.
- Safari local HTTP behavior is handled by launcher workarounds, not by a true HTTPS stack.
- Safari startup can still produce edge-case UI confusion when a previous `file://` fallback snapshot is restored; frontend bootstrap now force-resets the HTTP shell state and writes a small local debug buffer.
- Launcher/frontend mitigation now also includes a project-owned no-cache static server plus a per-launch query string on `index.html` to reduce stale Safari page reuse.
- A real root-cause bug was identified in the frontend shell: `.file-mode-warning` defined `display: grid`, which overrode the element's `hidden` state in Safari. The correct fix is semantic CSS (`.file-mode-warning[hidden] { display: none; }`), not more JS fallback logic.
- Some UI labels are still partially system-generic rather than fully story-configurable.
- The encounter framework is good enough for lite scenarios, but should not be overgrown without strong gameplay justification.
- The current Demo pack is mechanically useful, but still underperforms as a showcase story:
- The Demo refit is now in a better place, but future system changes must keep both sides alive:
  - it must remain regression-friendly
  - it must remain a fun first-play sample

## Files Worth Knowing First

- [README.md](/Users/liwenzhong/Desktop/Working/VSCode/prompt-to-play/lite-trpg-sim/README.md)
- [TODO.md](/Users/liwenzhong/Desktop/Working/VSCode/prompt-to-play/lite-trpg-sim/TODO.md)
- [docs/TECHNICAL_OVERVIEW.md](/Users/liwenzhong/Desktop/Working/VSCode/prompt-to-play/lite-trpg-sim/docs/TECHNICAL_OVERVIEW.md)
- [docs/ARCHITECTURE.md](/Users/liwenzhong/Desktop/Working/VSCode/prompt-to-play/lite-trpg-sim/docs/ARCHITECTURE.md)
- [docs/RUNTIME_STATE.md](/Users/liwenzhong/Desktop/Working/VSCode/prompt-to-play/lite-trpg-sim/docs/RUNTIME_STATE.md)
- [backend/stories/README.md](/Users/liwenzhong/Desktop/Working/VSCode/prompt-to-play/lite-trpg-sim/backend/stories/README.md)

## Directory Snapshot

```text
lite-trpg-sim/
  README.md
  MEMORY.md
  TODO.md
  launcher.py
  launch_game.command
  assets/icons/
  frontend/
  backend/
    server.py
    game/
    stories/
    tests/
    tools/
  docs/
    TECHNICAL_OVERVIEW.md
    ARCHITECTURE.md
    RUNTIME_STATE.md
    ENGINEERING.md
    STAGE_DELIVERY.md
```

## Recent Important Additions

- Story/system decoupling is established.
- Demo story exists as a regression story pack.
- Demo now also includes a story-local cheat profession for rapid manual acceptance and feature showcasing.
- Demo now has a separate walkthrough doc for the two normal professions, so manual QA and first-play review can follow stable human-readable routes.
- Save slots plus import/export are in place.
- Story contract and validation tooling are in place.
- Safari launcher flow has been stabilized for local play.
- Launcher icon assets now exist under `assets/icons/`.
- Technical docs are now split more cleanly:
  - `ARCHITECTURE.md` owns boundaries and layer responsibilities
  - `RUNTIME_STATE.md` owns runtime/save/view data shapes
  - `ENGINEERING.md` owns evergreen engineering rules
  - `STAGE_DELIVERY.md` owns stage-specific acceptance and release boundaries
- Root `README.md` is now structured more explicitly as:
  - quick start
  - playable content overview
  - rules summary
  - save/FAQ
  - deeper-document links
- `docs/TECHNICAL_OVERVIEW.md` now acts more clearly as:
  - a handoff reading order
  - a task-based document router
  - an update guide for which doc owns which kind of change
- `backend/stories/README.md` is now more explicitly structured as:
  - fast start
  - safe workflow
  - lite authoring principles
  - common mistakes and playable checklist
- `backend/stories/STORY_INTERFACE.md` is now more explicitly structured as:
  - top-level shape
  - action and resolution blocks
  - passive triggers and effect ops
  - encounter template reference
- Demo story has been refit from a dry acceptance chamber into:
  - a short mission at Ashwatch Station
  - a showcase for intended lite-TRPG feel
  - a broader regression pack with explicit `before_check` and `defeat` coverage

## Handoff Note

If you take over this project, start from:

1. `README.md`
2. `MEMORY.md`
3. `TODO.md`
4. `docs/TECHNICAL_OVERVIEW.md`
