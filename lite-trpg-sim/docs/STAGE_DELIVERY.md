# Stage Delivery Snapshot (2026-04-09)

Audience: reviewers, collaborators, and future agents validating the current completed stage.  
Not for players; player-facing instructions live in the project root `README.md`.

## Purpose

This file is the delivery snapshot for the current finished stage.

Use it to answer:

- What was considered done at this stage?
- Which checks should be run for acceptance?
- What does the Demo story currently prove?
- Which limitations are known but not blocking release?

Do not use this file as a general engineering policy document.  
Long-lived development rules belong in `ENGINEERING.md`.

## Stage Summary

This stage is considered complete with the following outcomes:

- frontend/backend separation is established
- story packs are decoupled from core system code
- unified resolution output exists across the core action types
- encounter runtime is integrated into `state`, `view`, and saves
- debug trace support is available for diagnosis
- Demo story exists as a regression-oriented acceptance pack

## Acceptance Commands

Run these from the project root `lite-trpg-sim`:

```bash
python3 backend/tools/story_cli.py validate
python3 -m unittest discover -s backend/tests
python3 backend/tools/demo_acceptance.py
python3 launcher.py --no-browser --smoke-test-seconds 2
python3 backend/tools/review_guard.py --doc-sync
```

Expected outcome:

- every command exits with code `0`
- `demo_acceptance.py` reports `PASS`

## Demo Acceptance Coverage

`backend/tools/demo_acceptance.py` currently covers these routes:

1. `escape`
2. `negotiate`
3. `delay_load`
4. `mechanics_mix`
5. `fatal_death`
6. `fatal_corrupt`

These routes collectively verify:

- starting a new game
- advancing through actions
- reaching multiple endings
- saving and loading during play
- exercising checks, saves, contests, utility use, healing, drain, and damage
- reading debug trace output for diagnosis

## Release Boundary For This Stage

Included in this stage:

- launcher flow usable for local browser play
- story-pack loading and validation
- save slots plus import/export
- generic node/action/effect interpreter
- encounter framework suitable for lite scenarios
- canonical resolution payloads
- Demo story as a system regression pack

Not included in this stage:

- deep character progression
- heavy tactical combat
- advanced AI behavior trees
- large-scale metagame systems

## Known Non-Blocking Limits

- the system is still intentionally pre-skill-layer
- enemy behavior remains lightweight and template-driven
- environment rules are useful but not yet deeply chain-reactive
- Safari local launching still relies on compatibility handling rather than local HTTPS

## Next-Stage Starting Point

The next stage should begin from these priorities:

1. keep the system lite and readable
2. improve effect lifecycle coherence
3. add only small, high-value differentiation systems
4. keep Demo aligned with all new core mechanics

For roadmap detail, read `../TODO.md`.

## When Updating This Document

Update this file when:

- a stage is declared complete
- acceptance commands change
- Demo acceptance coverage changes
- the release boundary for the current stage changes

Do not use this file as:

- a changelog for every tiny change
- a permanent rules document
- a player guide
