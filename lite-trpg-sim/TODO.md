# TODO

> Scope: this file is for development planning only.  
> Player-facing information belongs in `README.md`.  
> Technical document navigation starts from `docs/TECHNICAL_OVERVIEW.md`.

## Planning Rule

`lite-trpg-sim` should evolve as a lite tabletop simulator.

This file should help answer:

- What should we improve next?
- Why is that improvement worth doing?
- What should we explicitly delay?

This file should not become:

- a changelog
- a player rules reference
- a pile of equal-priority feature wishes

## Direction Filters

Before adding a new task, test it against these filters:

- Does it improve decision quality, readability, or replay value?
- Does it stay reusable across different story settings?
- Does it keep the play loop fast?
- Can it be explained to players without creating rules bloat?

If the answer is mostly "no", it should not enter the near-term roadmap.

## Current Product Read

### Strong enough to build on

- Story/system separation is real
- Story packs drive content through a shared contract
- Unified resolution payloads are in place
- Encounter runtime is usable for lite scenarios
- Save slots plus import/export are working
- Story author tooling and validation exist
- Demo story already serves as a regression pack

### Still limiting quality

- Checks are still too attribute-heavy
- Effect/status lifecycle is not coherent enough yet
- Story-driven UI labels are not flexible enough everywhere
- Encounter readability can improve without adding more combat bulk
- Some frontend feedback remains functional but not elegant

## Active Milestone: Lite Core Polish

This is the current highest-priority milestone.

Success means:

- the system feels more like a tabletop ruleset
- story authors get more leverage without more complexity
- the UI explains results more clearly
- the project stays lite

## Priority 1: Small Skill Layer

Goal: improve character differentiation and check expression without turning the simulator into a spreadsheet game.

Tasks:

- [ ] Introduce a small reusable skill list above raw attributes
- [ ] Let checks read `attribute + optional skill`
- [ ] Allow professions and content to reference the same skill vocabulary
- [ ] Surface the tested skill clearly in frontend result panels
- [ ] Keep the total skill count intentionally small

Why now:

- This is the cleanest way to improve TRPG feel
- It helps new stories express different approaches to the same problem
- It strengthens replay value without adding heavy subsystems

Done when:

- Authors can define checks with attribute plus skill
- Players can see what kind of competence was tested
- Demo story covers at least one skill-driven route

## Priority 2: Effect Lifecycle Cleanup

Goal: make statuses, passives, and encounter-driven effects follow one readable lifecycle.

Tasks:

- [ ] Define a concise trigger vocabulary for ongoing effects
- [ ] Add lightweight duration/expiry support where it clearly helps play
- [ ] Reduce reliance on loose flags for effect behavior
- [ ] Make resolution output explain effect-driven modifiers consistently
- [ ] Update story author docs with the lifecycle model

Why now:

- This is the biggest remaining coherence gap in the rules layer
- Future stories will become messy if this stays vague
- It improves debugging and story-author confidence at the same time

Done when:

- Common status patterns no longer need ad hoc handling
- Effect timing is understandable from docs and debug trace
- Demo story covers at least one timed or triggered effect path

## Priority 3: Story-Facing UI Labels And Metadata

Goal: make new settings feel more native without requiring frontend rewrites.

Tasks:

- [ ] Allow story packs to configure visible resource labels
- [ ] Improve story selection metadata shown at setup
- [ ] Audit hardcoded generic labels that should be story-driven
- [ ] Tighten validation around missing metadata and inconsistent labels

Why now:

- This directly supports the "swap stories without rewriting the UI" promise
- It raises perceived quality for every new story pack

Done when:

- At least one story can rename visible resources cleanly
- Setup screen metadata feels specific rather than placeholder-generic

## Priority 4: UX Readability Pass

Goal: improve the feel of play without increasing rules weight.

Tasks:

- [ ] Make action outcomes easier to scan
- [ ] Make encounter state easier to read at a glance
- [ ] Improve save-slot feedback and confidence
- [ ] Improve import/export error clarity
- [ ] Review whether recent log and last outcome are visually distinct enough

Why now:

- Presentation quality is a multiplier on every existing mechanic
- This improves playability faster than adding another half-system

Done when:

- A fresh player can read results and encounter state with less hesitation
- Save/load actions feel trustworthy and understandable

## Priority 5: Demo Story Refit

Goal: turn `demo` from a pure testbed into a short, adventure-flavored showcase that still works as a regression pack.

Tasks:

- [x] Reframe the Demo fiction from "test chamber" to a compact field mission with clear stakes
- [x] Keep the playtime short, ideally around 8 to 12 minutes for one route
- [x] Preserve explicit coverage of the current core mechanics
- [x] Add one `before_check` trigger example so Demo matches current coverage claims
- [x] Add one true `defeat` victory route to acceptance coverage
- [x] Ensure both professions demonstrate meaningfully different openings or advantages
- [x] Ensure items and environment-manipulation actions are part of at least one recommended route
- [x] Keep the text brisk and readable, but not dry or purely diagnostic

Why now:

- Demo is currently useful for regression, but weak as a showcase of the simulator's appeal
- Future system work needs one story that is both testable and representative
- A good Demo helps validate not just correctness, but also whether the game feels fun

Planned shape:

1. A concise mission hook
2. One preparation step with profession or item texture
3. One exploration or infiltration beat
4. One pressure encounter with multiple exits
5. Multiple endings:
   - defeat
   - negotiate
   - delay
   - escape
   - death
   - corruption

Coverage targets:

- opening character setup
- utility item use
- `check/save/contest/damage/healing/drain`
- passive triggers:
  - `before_check`
  - `after_check`
  - `turn_end`
- environment changes and environment-driven modifiers
- action economy, turn rules, enemy behaviors, phase sync
- save/load round-trip inside an encounter
- debug trace availability

Done when:

- [x] Demo is fun enough to use as a first-play sample
- [x] Demo acceptance still passes
- [x] Demo README clearly explains both showcase routes and acceptance coverage
- [x] A reviewer can point to Demo as both:
  - a system regression pack
  - a compact example of the game's intended feel

## Deferred On Purpose

These are not "never" items. They are deliberately not near-term priorities.

- [ ] Large character progression trees
- [ ] Complex equipment rarity and loot systems
- [ ] Full tactical-grid combat
- [ ] Heavy faction or campaign metagame layers
- [ ] Broad story-count expansion as the main goal

Reason:

- Each of these can easily bloat the simulator before the lite core is mature

## Later Candidates, Only If The Core Holds

### Medium-term

- [ ] Advantage / disadvantage support
- [ ] Partial-success support for selected checks
- [ ] A very small specialization or perk layer
- [ ] Better encounter history and filtering in the UI
- [ ] Better story-pack metadata browsing

### Long-term

- [ ] Story graph inspection tools
- [ ] Stronger debug-mode visual panels
- [ ] Balancing and simulation helpers for authors

These only matter after the active milestone is complete.

## Exit Criteria For The Current Milestone

Do not call the next phase "done" unless:

- [ ] the simulator still feels fast to play
- [ ] new mechanics remain explainable in a short rules summary
- [ ] story authors can use the new mechanics without hacks
- [ ] Demo story still covers the important system paths
- [ ] docs remain in sync:
  - `MEMORY.md`
  - `docs/TECHNICAL_OVERVIEW.md`
  - story author docs
  - any affected technical references

## Maintenance Rule

When finishing a task from this file:

- remove or reword completed items
- keep only the current milestone near the top
- move distant ideas downward or out entirely
- prune anything that no longer fits the lite direction
