# Bead Pattern Converter User Guide

This guide is for end users who want to launch the tool, generate a bead
pattern, and export usable results without reading the source code.

## Quick Start

The fastest startup method on macOS:

1. Open the `bead-pattern-converter` folder.
2. Double-click `start.command`.
3. Wait for the browser tab to open automatically.

If the browser does not open by itself, visit:

- `http://localhost:8765`

Terminal fallback:

```bash
cd vibe-kit/bead-pattern-converter
python3 launcher.py
```

## Basic Workflow

1. Choose a source image.
2. Set the target grid size.
3. Choose a palette.
4. Choose an optimization preset.
5. Decide whether to remove the outer background.
6. Click `Generate pattern`.
7. Review the source preview, raw palette match, optimized preview, build grid, and materials.
8. Export the format you need.

## Which Palette Should I Pick?

### Default Bead Palette (18 Colors)

Use this when:

- you want fast iteration
- you are testing rough composition
- you do not need high color fidelity

Tradeoff:

- fastest option
- lowest color detail

### Portrait Plus (24 Colors)

Use this when:

- the image contains faces, skin, or warm soft tones
- you want a slightly richer result without using the full production palette

Tradeoff:

- still lightweight
- less universal than the full palette

### Mard 221 Standard Palette

Use this when:

- you want the closest possible color match
- the image uses many subtle color steps
- you are preparing a more serious final pattern

Tradeoff:

- slowest option
- creates denser material lists

## Which Cleanup Preset Should I Pick?

### Faithful

Use this when:

- you want the output to stay close to the original image
- you do not want aggressive cleanup

### Balanced

Use this when:

- you want a practical default
- you want some cleanup without heavily changing the design

This is the best starting point for most images.

### Bold Cleanup

Use this when:

- the result looks noisy
- the source image is small, messy, or highly compressed

Tradeoff:

- easier to assemble
- may simplify details more aggressively

## Background Removal

If `Remove outer background color` is enabled:

- the tool removes only the background that is connected to the outer edge
- it does not remove same-color regions inside the subject
- removed cells become empty holes instead of placed beads

If `Show cut reference on source preview` is enabled:

- the source preview shows which outer cells will be removed

## Understanding the Results

### Source Image

Shows the working crop used for conversion.

### Raw Palette Match

Shows the direct palette mapping before optional cleanup.

### Optimized Bead Preview

Shows the final result after color limiting, cleanup, and optional background removal.

### Build Grid

Shows the final cell layout for assembly.

If color codes are enabled, each placed bead cell shows its palette code when
the grid is large enough to keep the labels readable.

### Materials Summary

Shows:

- all used bead colors
- their codes
- their names
- how many beads of each are needed

### Matching Diagnostics

Use this panel when you want to understand:

- which colors dominate the final output
- how many cells changed during cleanup
- how much background was removed
- which raw colors were merged into other colors

## Export Options

### Export Preview PNG

Use this for:

- a quick final image
- simple sharing

### Export Pure Grid PNG

Use this for:

- a clean grid-only reference
- manual assembly

### Export Sheet PNG

Choose a `Sheet preset` first:

- `Build sheet`: assembly-focused
- `Share sheet`: presentation-focused
- `Materials sheet`: purchasing-focused

### Export Materials CSV

Use this when:

- you want a shopping or inventory list
- you want to keep a machine-readable record of the result

## Recommended Sizes

### 48 x 48

Best for:

- quick tests
- simple icons
- small gift designs

### 96 x 96

Best for:

- more detailed images
- better shape retention

### 128 x 128

Best for:

- high-detail local work
- richer full-palette results

Tradeoff:

- slower than small grids
- denser build grid

## Current Limits

The V1 tool currently supports up to `128 x 128`.

Why:

- larger grids become much slower with large palettes
- preview cells become too small to inspect comfortably
- single-page build sheets stop being readable for manual placement

## Troubleshooting

### The page does not open

Try:

1. Close the existing browser tab.
2. Stop the old launcher window.
3. Double-click `start.command` again.
4. If needed, open `http://localhost:8765` manually.

### The output looks too noisy

Try:

- switching from `Faithful` to `Balanced`
- increasing cleanup
- using a smaller target grid

### The colors look too simplified

Try:

- switching to `Mard 221 Standard Palette`
- using `Faithful`
- keeping `Max colors` at `0`

### Too much background was removed

Try:

- turning off `Remove outer background color`
- checking the source preview cut reference

### Export buttons are disabled

Generate a pattern first. Export becomes available only after a successful run.
