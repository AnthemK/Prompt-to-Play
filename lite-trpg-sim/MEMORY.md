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
  - Demo now includes an explicit pre-mission skill-test node for manual and automated skill coverage

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
  - Optional skill-aware checks layered on top of attributes
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
  - exit-window unlock feedback when `defeat` / `delay` / `negotiate` first become available
  - defeated enemies stop taking encounter turns until the player chooses a finish window
  - story packs can further narrow encounter exits with explicit `requires`; Demo now uses this so soft finishes disappear once the enemy is dead

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

- `V2.0 - Lite Core Polish`
  - small skill layer
    - implemented
  - effect lifecycle cleanup
    - implemented at the current V2.0 target level
  - story-facing label and metadata polish
    - implemented at the current V2.0 target level through `world.ui`
  - UX readability pass
    - implemented at the current V2.0 target level
  - Demo story refit
    - now completed at a first useful pass
    - Demo now behaves more like a short mission showcase
    - acceptance coverage has been expanded with `before_check` and true `defeat`
  - release state
    - treat current codebase as the `V2.0` stabilization baseline
    - no new major milestone should begin before this state is reviewed and accepted

## Current V2.0 Design Guardrails

- Keep the simulator lite:
  - no large skill trees
  - no secondary sub-systems just to justify the skill layer
- Prefer additive interfaces:
  - old story packs without skills should continue to run
  - skill-aware stories should only need small content edits
- Keep the frontend generic:
  - it may render skills
  - it should not know story-specific skill logic
- Keep code review-friendly:
  - small patches
  - explicit comments where new extension points appear
  - document changes whenever interfaces change

## Current Risks

- `TODO.md` previously accumulated too many large-system ambitions; this needs continuous pruning toward a lite design.
- Safari local HTTP behavior is handled by launcher workarounds, not by a true HTTPS stack.
- Safari startup can still produce edge-case UI confusion when a previous `file://` fallback snapshot is restored; frontend bootstrap now force-resets the HTTP shell state and writes a small local debug buffer.
- Launcher/frontend mitigation now also includes a project-owned no-cache static server plus a per-launch query string on `index.html` to reduce stale Safari page reuse.
- A real root-cause bug was identified in the frontend shell: `.file-mode-warning` defined `display: grid`, which overrode the element's `hidden` state in Safari. The correct fix is semantic CSS (`.file-mode-warning[hidden] { display: none; }`), not more JS fallback logic.
- The encounter framework is good enough for lite scenarios, but should not be overgrown without strong gameplay justification.
- The Demo refit is now in a good release-state place, but future system changes must keep both sides alive:
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
- The first `V2.0` rules slice is now landed:
  - optional top-level `skill_meta`
  - profession `skills`
  - `check` / `save` / `contest` may now declare an optional `skill`
  - backend meta and frontend view now expose player skills
  - Demo now uses the skill layer in its main routes
- The first effect-lifecycle cleanup slice is now landed:
  - statuses may now carry optional finite turn durations
  - `add_status` can read `duration_turns` from effects or `default_duration_turns` from the status definition
  - turn-end now expires timed statuses after their passive effects resolve
  - frontend status chips now show remaining turns when relevant
  - passive lifecycle hits now write clearer debug-trace events
  - resolution summaries for checks now carry labeled roll context such as `属性 + 技能`
  - check/save/contest config can now react to active statuses through:
    - `extra_bonus_if_statuses`
    - `dc_adjust_if_statuses`
  - action requirements can now gate on whether a status is present
  - check/save explain output now keeps a small `dc_breakdown`, so conditional DC changes are visible in debug/review output
  - story/docs guidance now explicitly separates long-lived `progress.flags` from short-lived `player.statuses`
  - `view.scene.actions[*]` now surfaces action availability, so requirement-based actions can be disabled cleanly in the frontend
  - synthetic encounter actions now preserve requirement context across both view rendering and execution
- The first story-facing metadata slice is now landed:
  - stories may define `world.ui.setup_summary`
  - stories may define `world.ui.setup_details`
  - stories may define `world.ui.resource_labels`
  - backend meta and frontend view now expose that metadata through a generic contract
  - non-demo stories now prove the interface is setting-agnostic
  - metadata remains presentation-only and is validated in the content layer
- The first UX-readability slice is now landed:
  - outcome panels are grouped into summary / resolution / change sections
  - encounter panels are grouped into battle-state / enemy / environment style sections
  - toolbar save-slot feedback now carries success/error states instead of relying on modal alerts
  - import/export feedback now includes clearer file/slot context
  - recent log styling is now more visually distinct from the latest-outcome panel
  - action failures now surface as non-modal runtime feedback near the action list
- Demo now explicitly demonstrates the newer `V2.0` story-contract features too:
  - optional skill-aware checks
  - timed status expiry
  - status-gated actions through `requires.status`
  - status-aware DC changes through `dc_adjust_if_statuses`
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
