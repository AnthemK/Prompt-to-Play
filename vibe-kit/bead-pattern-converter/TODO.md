# Bead Pattern Converter V1 Plan

## V1 Status

`V1` is now complete.

The items in this file are kept as a release record and as a boundary between
finished `V1` work and post-`V1` expansion work.

## V1 Goal

Deliver the first complete local-use version of the bead pattern converter.

`V1` means the tool is:

- usable end-to-end by a real user without reading source code
- stable enough that refactors do not silently break core behavior
- structured so new palettes, exports, and processing backends can be added without rewriting the UI

This is not the final product vision. It is the first version that forms a
closed, reliable workflow.

## V1 User Workflow

To count as `V1`, a user must be able to:

1. launch the tool locally with one step
2. upload an image
3. choose grid size and palette
4. choose cleanup settings or a preset
5. optionally remove the outer background
6. inspect source preview, raw match, optimized preview, build grid, and materials
7. export:
   - preview PNG
   - pure grid PNG
   - one-page sheet PNG
   - materials CSV
8. trust that the basic matching and cleanup behavior is stable across updates

## Current Status

The following foundation work is already complete and should be treated as part
of the V1 baseline:

- shared sampling core for browser and CLI smoke test
- modular rendering, export, diagnostics, and control-panel code
- perceptual color matching and cleanup pipeline
- outer-background removal with perimeter-only behavior
- palette manifest / payload split with lazy loading for large palettes
- processing adapter contract for future Python integration
- smoke test command
- deterministic regression fixtures

That means the remaining work should no longer be “keep refactoring forever”.
It should now focus on closing the product loop for a first release.

## V1 Closed-Loop Tasks

### 1. Palette Guidance and Selection UX

Status: done

Goal:

- make palette choice understandable for non-developers

Tasks:

- add a recommendation label or helper text for each palette
- explain when to use:
  - starter palette
  - portrait palette
  - `Mard 221`
- add a default recommendation based on image type heuristics later if lightweight enough

Done when:

- a user can choose a palette without reading external docs
- the UI explains tradeoffs between speed, style, and fidelity

### 2. Diagnostics Upgrade for Trust

Status: done

Goal:

- help users understand why the output looks the way it does

Tasks:

- expand diagnostics beyond the current compact summary
- show:
  - full ranked color usage list or at least a longer list than the current top slice
  - removed-background share
  - raw vs optimized color counts
  - changed-cell count and ratio
  - top remapped colors after cleanup if available

Done when:

- a user can inspect the output and understand the main palette and cleanup decisions
- diagnostics are informative without overwhelming the main workflow

### 3. Export Presets for Real Use Cases

Status: done

Goal:

- make export outputs fit actual usage contexts instead of one generic layout

Tasks:

- support export layout presets:
  - `build sheet`
  - `share sheet`
  - `materials sheet`
- keep current one-page export as one preset if suitable
- ensure pure grid export remains available as a separate output

Done when:

- users can export a layout appropriate for assembly, sharing, or purchasing

### 4. Regression Coverage Expansion

Status: done

Goal:

- protect the V1 workflow from behavioral drift

Tasks:

- add more regression fixtures for:
  - bright icon / emoji-like subjects
  - portrait-like color cleanup
  - non-white solid background removal
  - high-color `Mard 221` mapping sanity
- keep fixtures synthetic and deterministic where possible

Done when:

- core matching, cleanup, and background behavior are covered by a small but meaningful fixture suite

### 5. V1 Performance Pass

Status: done

Goal:

- ensure the tool stays usable at practical sizes such as `96x96` and `128x128`

Tasks:

- reduce unnecessary redraws
- ensure large palettes do not block the UI excessively
- evaluate whether preview/grid redraws can be localized or memoized lightly
- optimize only where measurements show real pain

Done when:

- the tool remains responsive enough for manual use on larger grids
- no major UI freeze is observed during ordinary local testing

Current findings:

- synthetic benchmarks show `Default 18` at `128x128` around `67 ms`
- synthetic benchmarks show `Mard 221` at `128x128` around `630 ms`
- true `Mard 221` at `256x256` is already around `2581 ms`
- the first hard V1 limit is not only compute cost but readability:
  - preview cells become about `1.73 px` at `256x256`
  - build-grid cells become about `3 px` at `256x256`
  - code labels and single-page exports stop being practically usable

V1 decision:

- keep the user-facing max at `128x128`
- treat `256x256` as post-V1 work that requires tiled rendering, paged export, or zoom-first grid UX

### 6. Release Hardening

Status: done

Goal:

- make V1 feel finished rather than “developer demo plus source code”

Tasks:

- do a final pass on:
  - empty / invalid input messaging
  - export button states
  - palette loading errors
  - launcher instructions
- confirm README matches actual behavior
- document the supported workflow and known limits

Done when:

- the repo can be handed to a user and they can operate it with minimal guidance

Release notes:

- generate flow now prevents duplicate submits while processing
- export buttons stay disabled until a successful result exists
- invalid non-image file selection reports a clear error
- launcher behavior and manual fallback URL are documented
- user-facing quick-start guide now lives in `USER_GUIDE.md`

## V1 Acceptance Criteria

`V1` is complete only if all conditions below are true:

- the full local workflow works end-to-end
- palette choice is understandable
- diagnostics provide enough trust and explainability
- exports cover the main real-world use cases
- regression tests and smoke tests pass
- performance is acceptable for practical grids
- docs describe the actual product rather than intentions

## Post-V1 Work

These are valuable, but should not block V1:

- Python processing backend
- advanced beautification / style modules
- more aggressive subject-aware cleanup
- additional palette packs
- tiled rendering architecture if the performance pass shows it is needed
- richer interactive inspection such as per-cell near-miss colors
- true `256x256` support with paged build-grid export and zoom-first inspection
- palette-aware heuristics that suggest a starting palette automatically
- larger diagnostics views for deep color-family analysis on high-color outputs
- optional materials export variants for shopping, inventory, and print packing slips

## Recommended Execution Order

1. Palette guidance and selection UX
2. Diagnostics upgrade
3. Export presets
4. Regression coverage expansion
5. V1 performance pass
6. Release hardening
