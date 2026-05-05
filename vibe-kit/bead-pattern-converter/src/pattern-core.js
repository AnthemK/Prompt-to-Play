import { clampGridDimension } from "./color-math.js?v=20260505-7";
import {
  buildInitialCells,
  countCellDifferences,
  indexGrid,
  reduceColors,
  removeOuterBackground,
  smoothIsolatedCells,
  summarizeCounts
} from "./pattern-ops.js?v=20260505-7";

// Pattern core orchestrates the conversion result shape. The heavy lifting
// lives in dedicated modules so this file stays focused on pipeline assembly.

function clampCleanupPasses(value) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) {
    return 0;
  }

  return Math.max(0, Math.min(4, parsed));
}

function clampMaxColors(value, paletteSize) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return 0;
  }

  return Math.max(1, Math.min(paletteSize, parsed));
}

function clampBackgroundRemoval(value) {
  return Boolean(value);
}

function summarizeRemappedPairs(rawFlatCells, optimizedFlatCells, paletteById) {
  const pairCounts = new Map();

  for (let index = 0; index < rawFlatCells.length; index += 1) {
    const rawCell = rawFlatCells[index];
    const optimizedCell = optimizedFlatCells[index];
    const rawId = rawCell.paletteId;
    const optimizedId = optimizedCell.paletteId;

    if (!rawId || !optimizedId || rawId === optimizedId) {
      continue;
    }

    const key = `${rawId}->${optimizedId}`;
    pairCounts.set(key, (pairCounts.get(key) ?? 0) + 1);
  }

  return [...pairCounts.entries()]
    .map(([key, count]) => {
      const [fromId, toId] = key.split("->");
      return {
        fromId,
        toId,
        fromName: paletteById.get(fromId)?.name ?? fromId,
        toName: paletteById.get(toId)?.name ?? toId,
        count
      };
    })
    .sort((left, right) => right.count - left.count);
}

export function buildPatternFromPixels({
  pixelData,
  targetWidth,
  targetHeight,
  palette,
  sourceWidth = targetWidth,
  sourceHeight = targetHeight,
  sourceBackgroundRgb = null,
  fitMode = "contain",
  optimization = {}
}) {
  const width = clampGridDimension(targetWidth, 48);
  const height = clampGridDimension(targetHeight, 48);
  const maxColors = clampMaxColors(optimization.maxColors, palette.colors.length);
  const cleanupPasses = clampCleanupPasses(optimization.cleanupPasses);
  const removeBackground = clampBackgroundRemoval(optimization.removeBackground);
  const paletteById = new Map(palette.colors.map((color) => [color.id, color]));

  // Keep the initial palette match faithful to the sampled image before any
  // optional cleanup runs change the bead layout for readability.
  let rawFlatCells = buildInitialCells(pixelData, width, height, palette);
  let removedBackgroundCells = 0;
  let backgroundPaletteId = null;

  if (removeBackground) {
    const backgroundRemoval = removeOuterBackground(
      rawFlatCells,
      width,
      height,
      sourceBackgroundRgb
    );
    rawFlatCells = backgroundRemoval.cells;
    removedBackgroundCells = backgroundRemoval.removedCells;
    backgroundPaletteId = backgroundRemoval.backgroundPaletteId;
  }

  let optimizedFlatCells = rawFlatCells;

  if (maxColors > 0) {
    optimizedFlatCells = reduceColors(optimizedFlatCells, palette, maxColors);
  }

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
  const changedCells = countCellDifferences(rawFlatCells, optimizedFlatCells);
  const remappedPairs = summarizeRemappedPairs(rawFlatCells, optimizedFlatCells, paletteById);
  const rawResult = {
    grid: indexGrid(rawFlatCells, width),
    counts: rawCounts,
    colorsUsed: rawCounts.length
  };
  const optimizedResult = {
    grid: indexGrid(optimizedFlatCells, width),
    counts: optimizedCounts,
    colorsUsed: optimizedCounts.length
  };

  return {
    source: {
      width: sourceWidth,
      height: sourceHeight
    },
    target: {
      width,
      height
    },
    palette: {
      id: palette.id,
      name: palette.name
    },
    raw: rawResult,
    optimized: optimizedResult,
    grid: optimizedResult.grid,
    counts: optimizedResult.counts,
    totalBeads: optimizedFlatCells.filter((cell) => cell.paletteId).length,
    totalCells: width * height,
    fitMode,
    optimization: {
      preset: optimization.preset ?? "custom",
      presetLabel: optimization.presetLabel ?? "Custom",
      maxColors,
      cleanupPasses,
      removeBackground
    },
    comparison: {
      changedCells,
      changedRatio: changedCells / (width * height),
      rawColorsUsed: rawResult.colorsUsed,
      optimizedColorsUsed: optimizedResult.colorsUsed,
      remappedPairs
    },
    background: {
      removed: removeBackground,
      removedCells: removedBackgroundCells,
      backgroundPaletteId,
      sourceRgb: sourceBackgroundRgb
    }
  };
}

export function normalizeTargetSize({ targetWidth, targetHeight }) {
  return {
    width: clampGridDimension(targetWidth, 48),
    height: clampGridDimension(targetHeight, 48)
  };
}
