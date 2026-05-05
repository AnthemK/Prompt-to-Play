import { performance } from "node:perf_hooks";

import { loadPaletteById } from "../src/palette.js";
import {
  buildInitialCells,
  countCellDifferences,
  indexGrid,
  removeOuterBackground,
  smoothIsolatedCells,
  summarizeCounts
} from "../src/pattern-ops.js";

function buildSyntheticPixels(width, height) {
  const pixelData = new Uint8ClampedArray(width * height * 4);

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const index = (y * width + x) * 4;
      const band = (x + y) % 6;
      const palette = [
        [255, 208, 72],
        [214, 90, 87],
        [244, 242, 235],
        [75, 64, 59],
        [139, 184, 221],
        [125, 163, 109]
      ][band];

      pixelData[index] = palette[0];
      pixelData[index + 1] = palette[1];
      pixelData[index + 2] = palette[2];
      pixelData[index + 3] = 255;
    }
  }

  return pixelData;
}

function buildScenarioList() {
  return [
    { paletteId: "default-18", size: 48, cleanupPasses: 1 },
    { paletteId: "default-18", size: 96, cleanupPasses: 1 },
    { paletteId: "default-18", size: 128, cleanupPasses: 1 },
    { paletteId: "mard-221", size: 48, cleanupPasses: 1 },
    { paletteId: "mard-221", size: 96, cleanupPasses: 1 },
    { paletteId: "mard-221", size: 128, cleanupPasses: 1 },
    { paletteId: "mard-221", size: 256, cleanupPasses: 1 }
  ];
}

// This benchmark intentionally bypasses the user-facing 128x128 clamp so we
// can measure raw pipeline scaling and document what a future 256x256 mode
// would cost before changing product limits.
function buildPatternWithoutClamp({
  pixelData,
  targetWidth,
  targetHeight,
  palette,
  sourceBackgroundRgb,
  cleanupPasses
}) {
  const width = targetWidth;
  const height = targetHeight;
  const paletteById = new Map(palette.colors.map((color) => [color.id, color]));
  let rawFlatCells = buildInitialCells(pixelData, width, height, palette);
  let removedBackgroundCells = 0;
  let backgroundPaletteId = null;

  const backgroundRemoval = removeOuterBackground(
    rawFlatCells,
    width,
    height,
    sourceBackgroundRgb
  );
  rawFlatCells = backgroundRemoval.cells;
  removedBackgroundCells = backgroundRemoval.removedCells;
  backgroundPaletteId = backgroundRemoval.backgroundPaletteId;

  let optimizedFlatCells = rawFlatCells;
  if (cleanupPasses > 0) {
    optimizedFlatCells = smoothIsolatedCells(
      optimizedFlatCells,
      width,
      height,
      cleanupPasses,
      paletteById
    );
  }

  const rawCounts = summarizeCounts(rawFlatCells, palette);
  const optimizedCounts = summarizeCounts(optimizedFlatCells, palette);

  return {
    target: { width, height },
    raw: {
      grid: indexGrid(rawFlatCells, width),
      counts: rawCounts,
      colorsUsed: rawCounts.length
    },
    optimized: {
      grid: indexGrid(optimizedFlatCells, width),
      counts: optimizedCounts,
      colorsUsed: optimizedCounts.length
    },
    counts: optimizedCounts,
    totalBeads: optimizedFlatCells.filter((cell) => cell.paletteId).length,
    totalCells: width * height,
    comparison: {
      changedCells: countCellDifferences(rawFlatCells, optimizedFlatCells),
      rawColorsUsed: rawCounts.length,
      optimizedColorsUsed: optimizedCounts.length
    },
    background: {
      removedCells: removedBackgroundCells,
      backgroundPaletteId
    }
  };
}

async function runScenario({ paletteId, size, cleanupPasses }) {
  const palette = await loadPaletteById(paletteId);
  const pixelData = buildSyntheticPixels(size, size);
  const timings = [];
  let lastConversion = null;

  for (let iteration = 0; iteration < 3; iteration += 1) {
    const startedAt = performance.now();
    lastConversion = buildPatternWithoutClamp({
      pixelData,
      targetWidth: size,
      targetHeight: size,
      palette,
      sourceBackgroundRgb: [244, 242, 235],
      cleanupPasses
    });
    timings.push(performance.now() - startedAt);
  }

  const averageMs = timings.reduce((sum, value) => sum + value, 0) / timings.length;
  const previewCellPixels = Number(((480 - 36) / size).toFixed(2));
  const gridCellPixels = Number(Math.floor((960 - 40) / size).toFixed(2));

  return {
    paletteId,
    size,
    averageMs: Number(averageMs.toFixed(2)),
    minMs: Number(Math.min(...timings).toFixed(2)),
    maxMs: Number(Math.max(...timings).toFixed(2)),
    totalBeads: lastConversion.totalBeads,
    colorsUsed: lastConversion.counts.length,
    changedCells: lastConversion.comparison.changedCells,
    previewCellPixels,
    gridCellPixels,
    codeLabelsReadable: gridCellPixels >= 13
  };
}

const results = [];
for (const scenario of buildScenarioList()) {
  results.push(await runScenario(scenario));
}

console.log(JSON.stringify({ results }, null, 2));
