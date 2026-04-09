# Architecture Guide

Audience: developers maintaining system boundaries, backend/frontend responsibilities, and story-pack integration.  
Not for players; player-facing instructions live in the project root `README.md`.

## Purpose

This document answers structural questions:

- Which layer owns which responsibility?
- How do frontend, backend, and story packs collaborate?
- Where should a new feature be implemented?

If you need field-level data shapes, read `RUNTIME_STATE.md` instead.

## Design Principles

- Keep the frontend story-agnostic.
- Keep the backend engine setting-agnostic.
- Keep story packs data-driven.
- Add reusable mechanics to the system layer before using them in one story.
- Avoid turning the project into a heavy CRPG stack.

## Repository Layout

```text
lite-trpg-sim/
  README.md
  MEMORY.md
  TODO.md
  launcher.py
  launch_game.command
  frontend/
  backend/
    server.py
    game/
    stories/
    tests/
    tools/
  docs/
```

## Layer Model

### 1. Launcher layer

Files:

- `launcher.py`
- `launch_game.command`

Responsibilities:

- Start the backend HTTP server and frontend static server.
- Open the local browser in a player-friendly way.
- Absorb macOS/Safari local-launch quirks.

Non-responsibilities:

- No game rules.
- No story interpretation.
- No save mutation.

### 2. Frontend layer

Location:

- `frontend/`

Responsibilities:

- Render setup UI, scene text, actions, logs, and side panels.
- Render the backend-provided `view` payload.
- Trigger API requests.
- Keep browser-local save slots plus import/export UX.

Non-responsibilities:

- No hardcoded world lore.
- No hardcoded branching rules.
- No authoritative state transitions.

### 3. API boundary layer

File:

- `backend/server.py`

Responsibilities:

- Expose HTTP endpoints.
- Validate request shape at the transport layer.
- Translate exceptions into API responses.
- Hand off all game work to `GameEngine`.

Non-responsibilities:

- No story-specific rules.
- No direct node/effect execution logic.

### 4. Engine layer

Location:

- `backend/game/engine.py`
- `backend/game/story_interface.py`

Responsibilities:

- Own in-memory sessions.
- Own canonical save/load structure.
- Resolve story ids to runtime adapters.
- Project runtime state into the frontend `view` model.

Important rule:

- `GameEngine` must stay story-agnostic. It can know the interface, but not the setting.

### 5. Runtime and rules layer

Location:

- `backend/game/story_runtime.py`
- `backend/game/adventure.py`
- `backend/game/rules.py`
- `backend/game/resolution.py`

Responsibilities:

- Interpret story-pack nodes, actions, and effects.
- Run checks, saves, contests, damage, healing, and drain.
- Maintain encounter runtime.
- Write unified outcome payloads and debug trace events.

Internal split:

- `story_runtime.py`
  - Story-runtime adapter used by the engine
  - State bootstrap, repair, and high-level projections
- `adventure.py`
  - Generic node/action/effect interpreter
  - Encounter flow, action economy, exit strategies, enemy behavior templates
- `rules.py`
  - Reusable rules math and state mutation helpers
  - Status/item/resource interactions
  - Encounter environment modifiers
- `resolution.py`
  - Canonical explanation and effect payload shape

### 6. Content layer

Location:

- `backend/game/content.py`
- `backend/stories/*`

Responsibilities:

- Load and normalize story packs.
- Validate story-pack shape.
- Keep world data, nodes, professions, items, statuses, endings, and encounter templates in `story.json` or `story.yaml`.

Non-responsibilities:

- No per-story Python runtime logic unless the whole system contract changes.
- No frontend rendering decisions.

## Story-System Boundary

The intended boundary is simple:

- System layer:
  - knows how the game works
- Story layer:
  - knows what happens in one setting

Story packs may configure:

- world metadata
- professions
- items and statuses
- nodes and actions
- endings
- encounters and their templates
- story-specific numbers and text

Story packs should not define:

- HTTP behavior
- browser UI behavior
- save-slot implementation
- custom one-off Python hooks for a single setting

## Frontend-Backend Flow

### New game flow

1. Frontend requests `GET /api/meta`
2. Player selects a story pack, name, and profession
3. Frontend sends `POST /api/game/new`
4. Backend creates a runtime `state`
5. Engine returns a rendered `view`
6. Frontend renders only that `view`

### Action flow

1. Frontend sends `POST /api/game/{session_id}/action`
2. Engine resolves the correct story runtime
3. Runtime interprets the action through the generic system
4. Backend returns an updated `view`
5. Frontend rerenders and updates local autosave

### Save/load flow

1. Frontend requests save export from the backend
2. Backend returns canonical `save_data`
3. Frontend stores or exports the whole payload
4. Load/import returns the same payload to the backend
5. Backend repairs state shape if needed, then re-renders a `view`

## Feature Placement Guide

Put a change in the system layer when it adds a reusable capability:

- a new action kind
- a new effect op
- a new encounter rule
- a new resolution field
- a new save migration rule
- a new frontend view section used across stories

Put a change in the story layer when it only changes content:

- new narrative text
- new professions or items
- new branches and endings
- new encounter templates using existing mechanics
- new setting-specific labels and values

Pause and reconsider the design if a feature would require:

- hardcoding one setting into frontend labels or logic
- adding a Python special case for one story pack
- adding heavy CRPG subsystems that the current lite scope does not need

## Current Architecture Strengths

- Frontend is largely content-agnostic.
- Engine is largely setting-agnostic.
- Story packs are hot-swappable through one contract.
- Save/load stays backend-owned.
- Encounter runtime is now a first-class part of `state`, `save`, and `view`.

## Current Pressure Points

- Story-level labels are not yet fully configurable everywhere in the UI.
- Encounter depth must stay intentionally lite to avoid complexity creep.
- Schema tooling is useful but should continue improving before the content library grows much larger.

## When Updating This Document

Update this file when you change:

- responsibility boundaries
- new major layers or modules
- engine/runtime/story integration rules
- feature placement guidance

Do not use this file as:

- a changelog
- a field-by-field data dictionary
- a player manual
