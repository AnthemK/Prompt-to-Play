import { PALETTE_MANIFEST } from "../data/palette-manifest.js?v=20260505-8";

// Palette access is centralized here so the rest of the app never depends on
// raw catalog structure or duplicate hex-to-rgb conversion logic.

function hexToRgb(hex) {
  const normalized = hex.replace("#", "");
  const value = Number.parseInt(normalized, 16);

  return [
    (value >> 16) & 255,
    (value >> 8) & 255,
    value & 255
  ];
}

const loaderCache = new Map();

function clonePaletteSummary(summary) {
  return {
    id: summary.id,
    name: summary.name,
    brand: summary.brand,
    description: summary.description,
    colorCount: summary.colorCount,
    notes: summary.notes,
    recommendation: summary.recommendation
  };
}

function getManifestEntry(paletteId) {
  const manifestEntry = PALETTE_MANIFEST.find((entry) => entry.id === paletteId);
  if (!manifestEntry) {
    throw new Error(`Unknown palette: ${paletteId}`);
  }

  return manifestEntry;
}

function normalizePalette(manifestEntry, colors) {
  return {
    ...clonePaletteSummary(manifestEntry),
    colors: colors.map((color) => ({
      ...color,
      rgb: hexToRgb(color.hex)
    }))
  };
}

async function loadPaletteColors(loaderId) {
  if (loaderCache.has(loaderId)) {
    return loaderCache.get(loaderId);
  }

  let colors;
  if (loaderId === "default-18") {
    const module = await import("../data/palette-payloads.js?v=20260505-8");
    colors = module.DEFAULT_18_COLORS;
  } else if (loaderId === "portrait-24") {
    const module = await import("../data/palette-payloads.js?v=20260505-8");
    colors = module.PORTRAIT_24_COLORS;
  } else if (loaderId === "mard-221") {
    const module = await import("../data/mard-221.js?v=20260505-8");
    colors = module.MARD_221_PALETTE.colors;
  } else {
    throw new Error(`Unknown palette loader: ${loaderId}`);
  }

  loaderCache.set(loaderId, colors);
  return colors;
}

export function listPaletteSummaries() {
  return PALETTE_MANIFEST.map((entry) => clonePaletteSummary(entry));
}

export function getPaletteSummaryById(paletteId) {
  return clonePaletteSummary(getManifestEntry(paletteId));
}

export async function loadPaletteById(paletteId) {
  const manifestEntry = getManifestEntry(paletteId);
  const colors = await loadPaletteColors(manifestEntry.loader);
  return normalizePalette(manifestEntry, colors);
}

// Synchronous access remains available for CLI tests and scripts that already
// run under Node ESM and can tolerate eager imports. The browser UI should
// prefer `loadPaletteById` so large palettes can stay lazy.
export async function getPaletteById(paletteId) {
  return loadPaletteById(paletteId);
}
