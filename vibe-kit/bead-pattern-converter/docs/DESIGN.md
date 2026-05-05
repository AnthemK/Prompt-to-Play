# Bead Pattern Converter Design

## Goal

Build a small local tool that converts a source image into a bead-art assembly plan with three core deliverables:

- a finished preview
- a build grid with per-cell color identifiers
- a materials summary with counts by standard bead color

The first version should run fully in the browser while keeping a clean extension point for optional Python-based image processing later.

## Product Requirements

### Inputs

- source image file
- target width and height
- default target size: `48 x 48`
- palette selection, initially a single default palette
- optimization preset selection
- optional max-color limit
- optional cleanup passes for isolated-pixel smoothing
- optional outer-background removal

### Core Outputs

- bead-art preview image
- raw palette-match preview for comparison
- assembly grid image or canvas
- per-cell color code mapping
- palette legend
- per-color bead counts
- total bead count

### Non-Goals For MVP

- account system
- cloud storage
- backend service
- advanced beautification
- multi-image batch processing

## Proposed Tech Stack

### Frontend MVP

- `HTML`
- `CSS`
- vanilla `JavaScript`
- browser `Canvas` API for image processing and rendering

This choice keeps the tool easy to open, easy to modify, and aligned with the lightweight purpose of `vibe-kit`.

### Deferred Processing Layer

Reserve a processing adapter boundary so the current browser implementation and a future Python implementation can share the same pipeline contract.

Suggested high-level modules:

- `ui/` or UI layer: file input, controls, status, and rendering targets
- `pipeline/`: orchestrates the conversion flow
- `render/`: preview grid and legend rendering
- `palette/`: manifest access and lazy color-payload loading
- `export/`: later support for PNG, PDF, and CSV
- `adapters/`: browser adapter now, Python adapter later

Current practical split:

- `main.js`: DOM wiring and state transitions
- `optimization-presets.js`: reusable preset registry
- `diagnostics.js`: non-critical inspection UI
- `canvas-utils.js`: shared canvas drawing and text-layout primitives
- `controls-view.js`: control-panel population, summaries, and form reading
- `color-math.js`: perceptual color math and nearest-color search
- `pattern-ops.js`: reusable cell-grid transforms such as cleanup and background removal
- `palette.js`: manifest-first palette access with lazy payload loading for heavy sets
- `processing-contract.js`: normalized request/result contract for processing adapters
- `browser-processing-adapter.js`: current browser implementation of the processing contract
- `convert.js`: browser adapter around the shared conversion pipeline
- `sampling-core.js`: shared trim-and-sample helpers used in browser and CLI smoke test
- `pattern-core.js`: palette matching, cleanup, background removal, and counting
- `render.js`: on-screen rendering
- `export.js`: export rendering and file download helpers

## Data Model

### Palette Entry

Each standard bead color should be represented by a structured record similar to:

```js
{
  id: "H2",
  name: "White",
  hex: "#F5F5F2",
  rgb: [245, 245, 242],
  brand: "default",
  aliases: []
}
```

Notes:

- `id` is the standard bead code shown in the grid and counts
- `name` is user-facing
- `hex` and `rgb` support rendering and color-distance comparison
- `brand` allows future palette packs

Current palette strategy:

- starter palettes stay small and fixed for quick iteration
- larger production palettes, such as the `Mard 221` set, live as separate data files
- matching quality should be improved by the sampling and distance algorithm, not by silently mutating a palette to fit one test image
- palette manifests also carry user-facing recommendation guidance so selection UX does not depend on hardcoded UI copy

### Pattern Cell

Each cell in the generated bead pattern can be represented as:

```js
{
  x: 0,
  y: 0,
  paletteId: "H2",
  rgb: [245, 245, 242]
}
```

### Conversion Result

The main pipeline output can be normalized into:

```js
{
  source: {
    width: 1024,
    height: 1024
  },
  target: {
    width: 48,
    height: 48
  },
  palette: {
    id: "default-1",
    name: "Default Bead Palette"
  },
  grid: [],
  counts: [
    {
      paletteId: "H2",
      name: "White",
      count: 2174
    }
  ],
  totalBeads: 2304
}
```

## Processing Pipeline

### Step 1: Load Source Image

- accept image file input
- decode image in browser
- normalize orientation if needed later

Adapter note:

- the UI now creates a normalized processing request
- a processing adapter returns a normalized result with `conversion` and `cropBounds`
- today that adapter is browser-canvas based, but the contract is designed so a future Python adapter can slot in without rewriting UI orchestration

### Step 2: Fit To Target Grid

- detect and trim obvious empty margins around the subject first
- scale the remaining content to target dimensions
- choose a deterministic resizing strategy

Initial recommendation:

- preserve the whole detected subject by default
- add light padding after trimming so the result does not feel over-cropped
- keep letterboxing only after content trimming, not before

### Step 3: Sample Pixels

- read one color value per target cell
- sample each target cell directly from the cropped source region
- prefer foreground-weighted averaging so white background does not dominate small subjects

Maintainability note:

- subject detection and cell sampling now live in a shared `sampling-core.js`
- the browser app and CLI smoke test both use the same implementation so algorithm changes stay consistent across manual and automated testing

### Step 4: Map To Standard Palette

- compute the nearest palette color for each sampled pixel
- store both original sampled RGB and mapped palette entry

Current algorithm:

- foreground-aware direct cell sampling
- perceptual `CIEDE2000` color distance

Planned upgrade path:

- CIEDE2000 or other stronger perceptual color distance
- configurable color reduction constraints

### Step 5: Optional Optimization Passes

- optionally keep only the top N colors actually used in the draft pattern
- optionally smooth isolated single-cell fragments into the local dominant color
- optionally remove only the edge-connected outer background after initial mapping

Current implementation notes:

- color reduction runs before cleanup
- outer-background removal runs from perimeter-connected cells only, using similarity to the detected edge background color, so enclosed islands of the same color remain intact
- cleanup focuses on obvious isolated noise, not aggressive shape rewriting
- the goal is readability for bead placement, not full artistic restyling

### Regression Safety

The project now includes fixture-based regression checks for algorithmic
behavior that is easy to break during refactors:

- yellow-vs-red family mapping
- perimeter-only background removal
- isolated-noise cleanup
- non-white background removal
- portrait-style warm-tone separation
- large-palette family separation sanity

These are intentionally synthetic fixtures, not visual snapshots, so the tests
stay fast and deterministic.

### Step 6: Aggregate Counts

- count the number of cells for each palette color
- sort materials by frequency or palette order

### Step 7: Render Outputs

- preview canvas using the mapped palette colors
- assembly grid canvas using code labels
- legend and materials summary panel

## Current Performance Envelope

The V1 limit stays at `128 x 128`.

Measured synthetic benchmarks show that the pipeline is still comfortable at
practical V1 sizes, but the next jump is not just a small extension:

- `Default 18` at `128 x 128`: about `67 ms`
- `Mard 221` at `128 x 128`: about `630 ms`
- true `Mard 221` at `256 x 256`: about `2581 ms`

The larger issue is output density:

- preview canvases are `480 x 480`
- build grid canvas is `960 x 960`
- export sheets are single-page compositions

That means:

- `128 x 128` preview cells are already only about `3.47 px`
- `256 x 256` preview cells would drop to about `1.73 px`
- `256 x 256` build-grid cells would drop to about `3 px`
- code labels are therefore no longer practically readable

Conclusion for V1:

- performance at `96 x 96` and `128 x 128` is acceptable
- lifting the max to `256 x 256` would require tiled grid rendering, paged exports, or zoom-first interaction
- therefore `256 x 256` is a post-V1 product change, not a safe constant tweak

## Rendering Strategy

### Preview

Show the finished bead-art look:

- colored square per cell
- optional bead-circle effect later
- scalable zoom for inspection

### Comparison Preview

Show the unoptimized palette match beside the optimized result so the user can:

- see how many cells changed
- judge whether cleanup improved readability
- compare color-count reduction against visual fidelity

### Assembly Grid

Show a practical build sheet:

- coordinate labels on rows and columns
- one visible cell per bead
- background fill from mapped color
- text label using palette code
- contrast-aware label color for readability

### Materials Summary

Show:

- palette code
- color swatch
- color name

### Export Presets

The printable/shareable export layer now supports multiple compositions:

- `build sheet`: emphasizes grid and build context
- `share sheet`: emphasizes finished preview and concise summary
- `materials sheet`: emphasizes procurement and color counts

Pure grid export remains a separate direct output rather than an export preset.

### Diagnostics Panel

Show lightweight inspection data without cluttering the main workflow:

- ranked mapped colors
- raw vs optimized color counts
- changed-cell count
- changed-cell ratio
- placed-bead count vs full grid cells
- background-removal metadata
- background-removal share
- top raw-to-optimized remap pairs

This panel is intentionally separate from export output so the app can grow more debugging and tuning aids without polluting the printable pattern sheet.
- bead count
- overall total

## Accuracy Considerations

MVP quality depends on two things:

- palette correctness
- readable color mapping

Important design choice:

- do not hardcode the entire application around one vendor-specific numbering scheme
- instead, load palette data from a dedicated data file so the palette can be replaced or expanded later

## Python Extension Boundary

The frontend should call a single conversion interface, even in the MVP.

Suggested browser-side contract:

```js
async function convertImageToPattern(input, options) {
  return {
    preview,
    grid,
    counts,
    totalBeads,
    meta
  };
}
```

Later, a Python-backed path can implement the same logical contract:

- browser-only adapter: current default
- Python adapter: optional future path for better image operations

### Reasons To Reserve Python Support

- more advanced image cleanup
- stronger quantization libraries
- optional background removal
- more complex beautification steps
- export pipelines such as PDF generation

### Integration Strategy

Do not build Python into the MVP runtime.

Instead:

- keep the conversion pipeline modular
- isolate palette matching and image transformation steps
- define data contracts that can be serialized as JSON

This allows a future architecture such as:

```text
UI -> conversion adapter -> browser pipeline
UI -> conversion adapter -> Python pipeline
```

## Future Beautification Module

This module should sit after initial resizing and before final palette rendering.

Potential operations:

- remove isolated noise pixels
- simplify edge transitions
- preserve face or outline readability
- reduce color count while keeping the subject recognizable

Possible modes:

- faithful
- bead-friendly
- high-contrast
- soft merge

## File Plan For Implementation

Recommended first implementation layout:

```text
bead-pattern-converter/
  README.md
  index.html
  styles.css
  app.js
  data/
    palette.default.json
  docs/
    DESIGN.md
  samples/
```

If the browser code grows, split `app.js` into:

```text
src/
  main.js
  palette.js
  convert.js
  render.js
  export.js
```

## Open Decisions

These items should be resolved before implementation goes too far:

- which default bead palette and standard code set to ship first
- whether target size should support unlocked width and height or only square presets
- whether empty background should map to a real bead color or a no-bead cell in future versions
- whether the first export format should be PNG only or PNG plus CSV

## Recommended Next Step

Build the MVP as a static browser tool with:

- one palette pack
- one image upload flow
- one `48 x 48` default target
- one preview
- one assembly grid
- one materials summary

That is enough to validate the workflow before adding beautification or Python processing.
