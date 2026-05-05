# Bead Pattern Converter

Convert a color image into a bead-art pattern with a fixed grid, palette-matched color codes, and a materials summary.

For a user-facing quick-start guide, see [USER_GUIDE.md](/Users/liwenzhong/Desktop/Working/VSCode/prompt-to-play/vibe-kit/bead-pattern-converter/USER_GUIDE.md).

## Purpose

This tool is designed for turning an input image into a practical bead-art plan instead of a generic pixel-art preview.

The first version should help a user:

- upload one source image
- choose a target size, defaulting to `48 x 48`
- choose a palette
- optionally switch to a full production palette such as `Mard 221`
- choose an optimization preset or switch to custom tuning
- optionally limit colors and smooth noisy fragments
- optionally remove only the outer edge-connected background color, regardless of whether that background is white, gray, or another solid edge color
- automatically trim large blank margins around the subject before mapping
- generate a bead-art preview
- optionally overlay removed-background reference marks on the source preview
- generate a numbered or coded grid for assembly
- see the required bead colors and counts
- inspect a lightweight diagnostics panel for top mapped colors, optimization impact, and background-removal stats

## Planned Outputs

The MVP is expected to produce:

- a final preview image
- a raw palette-match preview for comparison
- preview canvases with a visible inset frame so white beads do not disappear into the page background
- a grid view with per-cell color codes
- a palette legend with color name and standard code
- a bead count summary per color
- a total bead count
- exportable preview PNG
- exportable pure-grid PNG
- exportable one-page summary PNG
- exportable materials CSV with optimization metadata

## Available Palettes

- `Default Bead Palette (18 Colors)`: fast iteration and rough testing
- `Portrait Plus (24 Colors)`: extra warm and portrait-friendly tones
- `Mard 221 Standard Palette`: imported from the public `pindou.online` Mard color chart for high-fidelity matching

## Usage Direction

This tool will be built as a local browser app first.

The intended workflow is:

1. Open the tool in a browser.
2. Upload a source image.
3. Set the target grid size.
4. Choose a palette or keep the default palette.
5. Choose an optimization preset, or switch to custom tuning.
6. Optionally tune cleanup settings such as max colors and cleanup passes.
7. Optionally enable outer-background removal if you want empty cells around the subject instead of filled background beads.
8. Generate the bead pattern. The converter first trims obvious empty margins, then samples each target cell directly from the cropped source so small subjects do not get washed out during downscaling.
9. Compare the raw palette match with the optimized preview.
10. Optionally turn on source-preview cut reference to inspect which outer cells will become empty.
11. Review the grid and material summary.
12. Export the preview, pure grid, one-page sheet, or materials list.

## Current Local Run

The current MVP is a static browser app with a built-in launcher.

Recommended startup options:

1. Double-click `start.command`
2. Or run the launcher directly from Terminal

Terminal example:

```bash
cd vibe-kit/bead-pattern-converter
python3 launcher.py
```

The launcher will:

- start the local server
- bind the server locally and open the tool in your browser by default
- prefer a `localhost` launch URL to avoid Safari loopback restrictions
- disable local HTTP caching so Safari reloads fresh JS/CSS after tool updates
- use fixed port `8765` by default for predictable manual testing
- fail clearly if `8765` is already occupied

Optional:

```bash
python3 launcher.py --no-browser
```

If port `8765` is already busy and you explicitly want a fallback port:

```bash
python3 launcher.py --allow-port-fallback
```

## V1 Status

The current repository state should be treated as the first deliverable `V1`.

V1 is considered complete because it now provides:

- one-step local launch
- palette guidance and cleanup presets
- raw and optimized preview comparison
- build grid and materials summary
- export presets for build, sharing, and materials use cases
- regression and smoke-test coverage
- documented limits, including why `128 x 128` remains the V1 maximum

## Smoke Test

A repeatable command-line smoke test is included for validating the conversion
pipeline with a real image.

Example:

```bash
/Users/liwenzhong/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  scripts/smoke-test.mjs \
  /absolute/path/to/source-image.jpg \
  48 \
  48
```

The smoke test uses the same core mapping logic as the browser app and prints a
JSON summary with:

- source image size
- target grid size
- total bead count
- number of colors used
- active optimization settings
- the top mapped colors by count

## Maintainability Notes

The current codebase is organized around small modules instead of one large browser script:

- `src/main.js`: UI wiring and event flow
- `src/optimization-presets.js`: preset definitions and lookup helpers
- `src/diagnostics.js`: diagnostics panel rendering
- `src/canvas-utils.js`: shared canvas drawing and wrapped-text helpers
- `src/controls-view.js`: control-panel rendering and form-value helpers
- `src/color-math.js`: reusable color distance and color-space helpers
- `src/pattern-ops.js`: reusable cell-level cleanup, reduction, and background-removal logic
- `src/palette.js`: palette manifest access and lazy payload loading
- `src/processing-contract.js`: stable request/result shape for processing adapters
- `src/browser-processing-adapter.js`: current canvas-based implementation of that processing contract
- `src/convert.js`: browser-side image loading and conversion orchestration
- `src/sampling-core.js`: shared subject detection and cell-sampling logic used by both browser and smoke test
- `src/pattern-core.js`: palette matching, cleanup, counting, and background removal
- `src/render.js`: canvas and table rendering
- `src/export.js`: PNG and CSV export helpers

This split keeps browser-only code, shared pipeline code, and rendering/export code separate, so future features can be added without continuing to grow `main.js`.

The browser now reads lightweight palette summaries first and only loads the
full color payload when a pattern is generated. This keeps heavy sets such as
`Mard 221` out of the initial UI cost.

Palette selection in the control panel now also includes built-in guidance:

- a recommendation badge
- a “best for” summary
- a tradeoff note

This is part of the V1 goal of making palette choice understandable without
requiring external docs.

Diagnostics now go beyond a compact summary and include:

- a longer ranked final color list
- changed-cell ratio
- removed-background share
- top raw-to-optimized remap pairs after cleanup / reduction

This is intended to make the generated result easier to trust and debug.

Sheet export now supports three presets:

- `Build sheet`: grid-first reference for actual assembly
- `Share sheet`: cleaner overview for sending or posting
- `Materials sheet`: procurement-focused summary with a longer materials table

The UI also talks to a processing adapter contract instead of calling browser
conversion code directly. The current adapter is browser-canvas based, but this
boundary is the intended insertion point for a future Python-backed processor.

The exported materials CSV now also includes:

- palette and palette id
- optimization preset and numeric settings
- raw vs optimized color counts
- changed-cell statistics
- background-removal metadata

## Regression Fixtures

A deterministic fixture-based regression check is also included for guarding the
core mapping rules during refactors.

Run:

```bash
/Users/liwenzhong/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  scripts/regression-test.mjs
```

The current fixtures cover:

- yellow-family mapping staying inside yellow palette entries
- outer-background removal preserving enclosed same-color holes
- isolated-pixel cleanup rewriting a lonely noisy cell
- non-white edge background removal
- portrait-palette warm-tone separation
- `Mard 221` major color-family separation

## Performance Notes

The current product limit remains `128 x 128` for V1.

This is not only a compute decision. It is also a readability decision.

Measured synthetic benchmark results from `scripts/perf-benchmark.mjs`:

- `Default 18` at `128 x 128`: about `67 ms`
- `Mard 221` at `128 x 128`: about `630 ms`
- `Mard 221` at true `256 x 256`: about `2581 ms`

Why `256 x 256` is not enabled for V1:

- the raw matching cost grows roughly with cell count, so `256 x 256` is much heavier than `128 x 128`
- the preview canvases are `480 x 480`, which leaves only about `1.73 px` per cell at `256`
- the build grid canvas is `960 x 960`, which leaves only `3 px` per cell at `256`
- code labels become unreadable long before `256`; the current UI already hides them below a practical threshold
- export sheets are currently single-page layouts, so a `256 x 256` build grid would need tiling or pagination to stay useful

Practical V1 interpretation:

- `48 x 48` is easy
- `96 x 96` and `128 x 128` are still usable, especially with small palettes
- `256 x 256` would require a new rendering/export strategy, not just a higher input max

The one-page PNG export includes:

- the optimized build grid
- finished preview
- palette and preset summary
- optimization and comparison stats
- top material rows in one printable/shareable sheet

## MVP Scope

The first implementation should focus on:

- stable image loading
- subject-first trimming before target-size downscaling
- fixed-size pixel conversion
- mapping every pixel to a standard bead color
- optional color reduction and isolated-pixel cleanup
- raw-vs-optimized comparison preview
- easier preset-based cleanup tuning
- diagnostics that expose palette usage and background-removal behavior
- clear visual output
- accurate material counting
- basic local exports for practical use

The MVP should not depend on a backend.

## Future Extensions

Planned expansion areas include:

- image beautification for bead-art readability
- configurable palette packs for different brands
- background removal or transparency handling
- export to PNG, PDF, or CSV
- optional Python-based processing for heavier image workflows

## Folder Layout

```text
bead-pattern-converter/
  README.md
  launcher.py
  start.command
  index.html
  styles.css
  scripts/
  src/
  docs/
    DESIGN.md
  data/
    palettes.js
  samples/
```
