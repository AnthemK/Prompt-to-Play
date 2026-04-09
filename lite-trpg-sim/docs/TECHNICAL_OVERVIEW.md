# Technical Overview

Audience: developers, reviewers, and future agents working on `lite-trpg-sim`.  
Not for players; player-facing instructions live in the project root `README.md`.

## Purpose

This file is the technical entrypoint for the repository.

Use it to answer:

- Which document should I read first?
- Which document answers the question I have right now?
- Which file should I update if I change something important?

This file should stay short and navigational.  
It is a map, not a full specification.

## Read This First

If you are taking over the project, use this order:

1. `../MEMORY.md`
   - fast handoff
   - current priorities
   - known risks
2. `ARCHITECTURE.md`
   - layer boundaries
   - feature placement rules
3. `RUNTIME_STATE.md`
   - runtime data model
   - save and view shapes
4. `../TODO.md`
   - current milestone
   - near-term priorities

This sequence usually gives enough context to start useful work without reading every document.

## Documentation Map

### Player and product context

- `../README.md`
  - player-facing overview
  - how to launch and play
  - rules summary

### Handoff and planning

- `../MEMORY.md`
  - current project snapshot
  - what is stable
  - what still needs attention
- `../TODO.md`
  - current roadmap
  - what should be built next
  - what is intentionally deferred

### Core technical references

- `ARCHITECTURE.md`
  - module and layer responsibilities
  - frontend/backend boundary
  - story layer vs system layer
  - use this when the question is:
    - "where should this logic live?"
- `RUNTIME_STATE.md`
  - runtime `state`
  - frontend `view`
  - canonical `save_data`
  - resolution and debug-trace shapes
  - use this when the question is:
    - "what does this payload or field look like?"
- `ENGINEERING.md`
  - comment discipline
  - naming rules
  - review expectations
  - doc-sync expectations
  - use this when the question is:
    - "what repository-wide rules should this change follow?"
- `STAGE_DELIVERY.md`
  - current-stage acceptance snapshot
  - validation commands
  - Demo coverage and release boundary
  - use this when the question is:
    - "what proves the current stage is done?"

### Story author docs

- `../backend/stories/README.md`
  - story author onboarding
  - writing workflow
  - common mistakes
- `../backend/stories/STORY_INTERFACE.md`
  - story-pack contract reference
  - supported fields, kinds, and effect ops

## Task-Based Reading Paths

### I am new and need a 5-minute handoff

1. `../MEMORY.md`
2. `ARCHITECTURE.md`
3. `../TODO.md`

### I am changing backend systems

1. `ENGINEERING.md`
2. `ARCHITECTURE.md`
3. `RUNTIME_STATE.md`
4. update affected docs after the code change

### I am changing frontend rendering or UI wording

1. `../README.md`
2. `ARCHITECTURE.md`
3. `RUNTIME_STATE.md`
4. `../TODO.md` if the change affects priorities or product direction

### I am writing or reviewing a story pack

1. `../backend/stories/README.md`
2. `../backend/stories/STORY_INTERFACE.md`
3. one existing playable pack
4. `demo` story for mechanics coverage

### I am validating whether the current stage is releasable

1. `STAGE_DELIVERY.md`
2. run the listed acceptance commands
3. check `../MEMORY.md` for known risks

## Update Guidance

When a change lands, update the document that owns the changed idea:

- player-facing behavior changed
  - update `../README.md`
- current priorities changed
  - update `../MEMORY.md` and/or `../TODO.md`
- boundaries or ownership changed
  - update `ARCHITECTURE.md`
- payloads or fields changed
  - update `RUNTIME_STATE.md`
- engineering rules changed
  - update `ENGINEERING.md`
- story-pack contract changed
  - update story author docs
- stage acceptance meaning changed
  - update `STAGE_DELIVERY.md`

## Scope Rules

- Do not put player instructions here.
- Do not duplicate full content from other technical docs.
- Do not turn this into a changelog.
- Do not mix roadmap, architecture, and data-spec content together here.
