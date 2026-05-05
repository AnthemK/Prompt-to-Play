import {
  getPaletteSummaryById,
  listPaletteSummaries
} from "./palette.js?v=20260505-8";
import {
  findMatchingPreset,
  getPresetById,
  OPTIMIZATION_PRESETS
} from "./optimization-presets.js?v=20260505-8";

// This module keeps control-panel population and form-reading logic out of the
// main application coordinator so UI wiring does not keep growing in one file.

export function populatePalettes(selectElement) {
  const palettes = listPaletteSummaries();
  for (const palette of palettes) {
    const option = document.createElement("option");
    option.value = palette.id;
    option.textContent = palette.name;
    selectElement.appendChild(option);
  }
}

export function populateOptimizationPresets(selectElement) {
  for (const preset of OPTIMIZATION_PRESETS) {
    const option = document.createElement("option");
    option.value = preset.id;
    option.textContent = preset.label;
    selectElement.appendChild(option);
  }
}

export function applyOptimizationPreset(elements, presetId) {
  const preset = getPresetById(presetId);
  if (preset.maxColors !== null) {
    elements.maxColorsInput.value = String(preset.maxColors);
  }
  if (preset.cleanupPasses !== null) {
    elements.cleanupPassesInput.value = String(preset.cleanupPasses);
  }
  elements.optimizationPresetSelect.value = preset.id;
  renderOptimizationSummary(elements);
}

export function syncPresetFromInputs(elements) {
  const maxColors = Number.parseInt(elements.maxColorsInput.value, 10);
  const cleanupPasses = Number.parseInt(elements.cleanupPassesInput.value, 10);
  const matchedPreset = findMatchingPreset(maxColors, cleanupPasses);
  elements.optimizationPresetSelect.value = matchedPreset?.id ?? "custom";
}

export function renderPaletteDetails(elements) {
  const palette = getPaletteSummaryById(elements.paletteSelect.value);
  elements.paletteName.textContent = palette.name;
  elements.paletteMeta.textContent = `${palette.brand} · ${palette.colorCount} colors`;
  elements.paletteBadge.textContent = palette.recommendation?.badge ?? "";
  elements.paletteBestFor.textContent = palette.recommendation?.bestFor
    ? `Best for: ${palette.recommendation.bestFor}`
    : "";
  elements.paletteDescription.textContent = palette.description;
  elements.paletteTradeoff.textContent = palette.recommendation?.tradeoff ?? "";
  elements.paletteNotes.textContent = "";
  elements.maxColorsInput.max = String(palette.colorCount);
  elements.maxColorsNote.textContent =
    `Use 0 to keep the full selected palette. Current palette supports up to ${palette.colorCount} colors.`;

  const currentMaxColors = Number.parseInt(elements.maxColorsInput.value, 10);
  if (Number.isFinite(currentMaxColors) && currentMaxColors > palette.colorCount) {
    elements.maxColorsInput.value = String(palette.colorCount);
  }

  for (const note of palette.notes ?? []) {
    const item = document.createElement("li");
    item.textContent = note;
    elements.paletteNotes.appendChild(item);
  }
}

export function readOptimizationOptions(elements) {
  const preset = getPresetById(elements.optimizationPresetSelect.value);
  return {
    preset: preset.id,
    presetLabel: preset.label,
    maxColors: elements.maxColorsInput.value,
    cleanupPasses: elements.cleanupPassesInput.value,
    removeBackground: elements.removeBackgroundInput.checked
  };
}

export function renderOptimizationSummary(elements) {
  const maxColors = Number.parseInt(elements.maxColorsInput.value, 10);
  const cleanupPasses = Number.parseInt(elements.cleanupPassesInput.value, 10);
  const preset = getPresetById(elements.optimizationPresetSelect.value);
  const colorSummary = Number.isFinite(maxColors) && maxColors > 0
    ? `max ${maxColors} colors`
    : "full palette";
  const cleanupSummary = Number.isFinite(cleanupPasses) && cleanupPasses > 0
    ? `${cleanupPasses} cleanup pass${cleanupPasses === 1 ? "" : "es"}`
    : "no cleanup";
  const backgroundSummary = elements.removeBackgroundInput.checked
    ? "outer background removed"
    : "background kept";
  elements.optimizationSummary.textContent =
    `${preset.label} · ${colorSummary} · ${cleanupSummary} · ${backgroundSummary}`;
}
