export const OPTIMIZATION_PRESETS = [
  {
    id: "faithful",
    label: "Faithful",
    maxColors: 0,
    cleanupPasses: 0,
    description: "Keep the full palette match with no cleanup."
  },
  {
    id: "balanced",
    label: "Balanced",
    maxColors: 0,
    cleanupPasses: 1,
    description: "Keep color freedom but smooth obvious single-pixel noise."
  },
  {
    id: "bold-cleanup",
    label: "Bold Cleanup",
    maxColors: 12,
    cleanupPasses: 2,
    description: "Reduce palette spread and clean noisy fragments more aggressively."
  },
  {
    id: "custom",
    label: "Custom",
    maxColors: null,
    cleanupPasses: null,
    description: "Use manual values for max colors and cleanup passes."
  }
];

export function getPresetById(presetId) {
  return OPTIMIZATION_PRESETS.find((preset) => preset.id === presetId) ?? OPTIMIZATION_PRESETS[0];
}

export function findMatchingPreset(maxColors, cleanupPasses) {
  return OPTIMIZATION_PRESETS.find((preset) =>
    preset.id !== "custom" &&
    preset.maxColors === maxColors &&
    preset.cleanupPasses === cleanupPasses
  ) ?? null;
}
