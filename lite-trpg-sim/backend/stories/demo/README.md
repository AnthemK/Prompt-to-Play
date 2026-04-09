# Demo Story

This directory contains the long-term Demo story for `lite-trpg-sim`.

Useful companion docs:

- `WALKTHROUGH.md`
  - player-facing clear guide for the two normal professions

The Demo story now has two jobs at once:

1. act as a regression-oriented mechanics pack
2. act as a short first-play showcase for the simulator

## Current Fiction

Current mission:

- `Demo: 灰烬哨站的封匣`

Short pitch:

- You infiltrate a half-burned hilltop station at night.
- Your goal is to retrieve a sealed coffer before the situation collapses.
- You can press the attack, force a compromise, delay for control, or cut your losses and escape.

This keeps the story short and readable, while still feeling like an actual adventure instead of a pure diagnostic chamber.

## Design Target

The Demo story should stay:

- short
- replayable
- mechanically broad
- narratively brisk

Target play length:

- around 8 to 12 minutes for one ordinary route

## What The Demo Should Demonstrate

Core gameplay feel:

- a clear mission hook
- differentiated professions
- one explicit cheat profession for rapid validation
- meaningful item use
- one exploration/infiltration beat
- one compact pressure encounter
- multiple endings with different tones

Core system coverage:

1. opening setup and profession selection
2. utility item use
3. `check`
4. `save`
5. `contest`
6. `damage`
7. `healing`
8. `drain`
9. passive triggers:
   - `before_check`
   - `after_check`
   - `turn_end`
10. environment changes and environment-driven modifiers
11. encounter framework:
   - phases
   - turn rules
   - action economy
   - enemy behaviors
   - exit strategies
12. save/load round-trip inside an active encounter
13. debug trace availability

## Current Automatic Acceptance Routes

Run:

```bash
python3 backend/tools/demo_acceptance.py
```

Machine-readable output:

```bash
python3 backend/tools/demo_acceptance.py --json
```

Current routes:

1. `escape`
   - verifies the always-available retreat route
2. `negotiate`
   - verifies non-lethal resolution after real mission progress
3. `delay_load`
   - verifies save/load round-trip plus the delay ending
4. `defeat`
   - verifies the true victory route through enemy defeat
5. `prepared_entry`
   - verifies the Demo's `before_check` + `after_check` passive lifecycle
6. `mechanics_mix`
   - touches utility use, save, healing, contest, drain, damage, environment changes, and turn-end pressure
7. `fatal_death`
   - verifies explicit HP-zero fatal handling
8. `fatal_corrupt`
   - verifies explicit corruption-limit fatal handling

## Story Structure

The current Demo structure is intentionally small:

1. mission briefing on the ridge
2. one choice of entry style
3. one main encounter space
4. four successful exits:
   - defeat
   - negotiate
   - delay
   - escape
5. two failure exits:
   - death
   - corruption

## Demo-Only Cheat Role

Demo now includes one extra profession:

- `演示监察官（作弊）`

This role exists only for fast manual validation and showcase runs.

Use it when you want to:

- touch many mechanics quickly
- reach endings with less variance
- verify UI flows without being blocked by ordinary difficulty

Do not treat this role as a balance target for the wider simulator.

## Authoring Rules For Future Demo Updates

When updating Demo:

- keep the text short and playable
- do not turn it back into a pure tutorial chamber
- do not add low-value filler choices just to increase coverage
- do keep at least one route that feels like a real mission
- do keep acceptance routes stable and scriptable

## Maintenance Rule

Whenever the core system changes, evaluate whether Demo must change in one of these ways:

- add a new mechanic example
- add a new acceptance route
- update route expectations
- update this README to match the actual story and coverage

Demo should remain the project's best answer to both of these questions:

- "Does the system still work?"
- "What does this simulator feel like when it works well?"
