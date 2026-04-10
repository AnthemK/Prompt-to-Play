# V2.0 Delivery Snapshot (2026-04-10)

Audience: reviewers, collaborators, and future agents validating the current stable release target.  
Not for players; player-facing instructions live in the project root `README.md`.

## Purpose

This file is the delivery snapshot for the current completed version target.

Use it to answer:

- What is included in `V2.0`?
- Which checks should be run before calling this build stable?
- What does the Demo story currently prove?
- Which limits are still known but non-blocking?

Do not use this file as a roadmap or evergreen engineering policy document.  
Long-lived rules belong in `ENGINEERING.md`. Future roadmap work belongs in `TODO.md`.

## Version Summary

`V2.0 - Lite Core Polish` is considered implemented with these outcomes:

- optional skill-aware checks are part of the shared story contract
- effect lifecycle is clearer and more consistent
- stories can provide presentation-only setup metadata and visible resource labels
- frontend readability is improved without adding rules weight
- Demo remains both:
  - a regression pack
  - a short showcase mission

## Included In V2.0

- launcher flow usable for local browser play
- story-pack loading and validation
- save slots plus import/export
- generic node/action/effect interpreter
- optional `attribute + skill` check layer
- timed statuses and closed passive trigger vocabulary
- clearer action availability in scene views
- encounter framework suitable for lite scenarios
- canonical resolution payloads with richer explain/debug output
- `world.ui` metadata for:
  - setup summary
  - setup detail chips
  - story-facing resource labels
- UI readability pass for:
  - outcome sections
  - encounter sections
  - save/load/import/export feedback
- Demo story as both acceptance pack and playable short mission

## Acceptance Commands

Run these from the project root `lite-trpg-sim`:

```bash
python3 backend/tools/story_cli.py validate
python3 -m unittest discover -s backend/tests
python3 backend/tools/demo_acceptance.py --json
python3 launcher.py --no-browser --smoke-test-seconds 2
python3 backend/tools/review_guard.py --doc-sync
```

Expected outcome:

- every command exits with code `0`
- `demo_acceptance.py --json` reports `"ok": true`

## Demo Acceptance Coverage

`backend/tools/demo_acceptance.py` currently covers these routes:

1. `escape`
2. `negotiate`
3. `delay_load`
4. `defeat`
5. `prepared_entry`
6. `mechanics_mix`
7. `guarded_window`
8. `fatal_death`
9. `fatal_corrupt`

These routes collectively verify:

- starting a new game
- advancing through actions
- reaching multiple endings
- saving and loading during play
- exercising:
  - `check`
  - `save`
  - `contest`
  - `damage`
  - `healing`
  - `drain`
  - utility item use
- passive timing coverage:
  - `before_check`
  - `after_check`
  - `turn_end`
- status-gated action visibility through `requires.status`
- status-aware DC adjustment through `dc_adjust_if_statuses`
- debug trace availability for diagnosis

## Release Boundary

This build is intentionally a stable lite TRPG simulator, not a heavy CRPG rules engine.

Included:

- reusable frontend/backend split
- story-driven content packs
- lite but extensible rules core
- enough tooling and docs for authoring and review

Explicitly not included:

- deep character progression
- tactical-grid combat
- heavy behavior-tree AI
- large campaign metagame systems
- broad feature expansion beyond the `V2.0` scope

## Known Non-Blocking Limits

- Safari local launching still relies on compatibility handling rather than local HTTPS
- encounter AI remains lightweight and template-driven by design
- environment systems are useful, but intentionally not deeply simulation-heavy
- the current UI is much clearer than `V1.x`, but still favors readability over flashy presentation

## Stabilization Rule

After `V2.0`, only do these before starting a new milestone:

- bug fixes
- acceptance fixes
- documentation cleanup
- release review work

Do not begin a broader `V3.0` roadmap until this snapshot is treated as the accepted stable baseline.

## When Updating This Document

Update this file when:

- a version target is declared complete
- acceptance commands change
- Demo acceptance coverage changes
- the version boundary changes

Do not use this file as:

- a full changelog
- a player guide
- a feature wishlist
