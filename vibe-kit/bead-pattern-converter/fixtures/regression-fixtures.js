function buildPixels(width, height, pixelForCell) {
  const pixels = [];

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      pixels.push(pixelForCell(x, y));
    }
  }

  return pixels;
}

export const REGRESSION_FIXTURES = [
  {
    name: "yellow_mapping_stays_in_yellow_family",
    paletteId: "default-18",
    width: 8,
    height: 8,
    pixels: buildPixels(8, 8, (x) => (x < 4
      ? [242, 216, 88]
      : [219, 164, 55])),
    optimization: {
      preset: "faithful",
      presetLabel: "Faithful",
      maxColors: 0,
      cleanupPasses: 0,
      removeBackground: false
    },
    expected: {
      totalBeads: 64,
      colorsUsed: 2,
      changedCells: 0,
      removedCells: 0,
      counts: {
        Y4: 32,
        Y8: 32
      }
    }
  },
  {
    name: "outer_background_removal_preserves_inner_hole",
    paletteId: "default-18",
    width: 8,
    height: 8,
    pixels: buildPixels(8, 8, (x, y) => {
      const isOuterBorder = x === 0 || x === 7 || y === 0 || y === 7;
      const isRedRing = x === 1 || x === 6 || y === 1 || y === 6;
      if (isOuterBorder) {
        return [244, 242, 235];
      }
      if (isRedRing) {
        return [212, 90, 87];
      }
      return [244, 242, 235];
    }),
    sourceBackgroundRgb: [244, 242, 235],
    optimization: {
      preset: "faithful",
      presetLabel: "Faithful",
      maxColors: 0,
      cleanupPasses: 0,
      removeBackground: true
    },
    expected: {
      totalBeads: 36,
      colorsUsed: 2,
      changedCells: 0,
      removedCells: 28,
      counts: {
        R2: 20,
        H2: 16
      },
      centerPaletteId: "H2",
      topLeftPaletteId: null
    }
  },
  {
    name: "isolated_noise_cleanup_rewrites_lonely_cell",
    paletteId: "default-18",
    width: 8,
    height: 8,
    pixels: buildPixels(8, 8, (x, y) => (
      x === 4 && y === 4
        ? [43, 39, 37]
        : [212, 90, 87]
    )),
    optimization: {
      preset: "balanced",
      presetLabel: "Balanced",
      maxColors: 0,
      cleanupPasses: 1,
      removeBackground: false
    },
    expected: {
      totalBeads: 64,
      colorsUsed: 1,
      changedCells: 1,
      removedCells: 0,
      counts: {
        R2: 64
      },
      centerPaletteId: "R2"
    }
  },
  {
    name: "colored_background_removal_works_on_non_white_edges",
    paletteId: "default-18",
    width: 8,
    height: 8,
    pixels: buildPixels(8, 8, (x, y) => {
      const isOuterBorder = x === 0 || x === 7 || y === 0 || y === 7;
      const isRedRing = x === 1 || x === 6 || y === 1 || y === 6;
      if (isOuterBorder) {
        return [139, 184, 221];
      }
      if (isRedRing) {
        return [212, 90, 87];
      }
      return [139, 184, 221];
    }),
    sourceBackgroundRgb: [139, 184, 221],
    optimization: {
      preset: "faithful",
      presetLabel: "Faithful",
      maxColors: 0,
      cleanupPasses: 0,
      removeBackground: true
    },
    expected: {
      totalBeads: 36,
      colorsUsed: 2,
      changedCells: 0,
      removedCells: 28,
      counts: {
        R2: 20,
        B4: 16
      },
      centerPaletteId: "B4",
      topLeftPaletteId: null
    }
  },
  {
    name: "portrait_palette_keeps_soft_skin_tones_separate",
    paletteId: "portrait-24",
    width: 8,
    height: 8,
    pixels: buildPixels(8, 8, (x) => {
      if (x < 3) {
        return [239, 216, 214];
      }
      if (x < 6) {
        return [239, 175, 153];
      }
      return [131, 79, 75];
    }),
    optimization: {
      preset: "faithful",
      presetLabel: "Faithful",
      maxColors: 0,
      cleanupPasses: 0,
      removeBackground: false
    },
    expected: {
      totalBeads: 64,
      colorsUsed: 3,
      changedCells: 0,
      removedCells: 0,
      counts: {
        E18: 24,
        F16: 24,
        F6: 16
      }
    }
  },
  {
    name: "mard_221_keeps_major_color_families_separate",
    paletteId: "mard-221",
    width: 8,
    height: 8,
    pixels: buildPixels(8, 8, (x, y) => {
      if (x < 4 && y < 4) {
        return [255, 200, 48];
      }
      if (x >= 4 && y < 4) {
        return [247, 73, 65];
      }
      if (x < 4 && y >= 4) {
        return [15, 84, 192];
      }
      return [72, 70, 78];
    }),
    optimization: {
      preset: "faithful",
      presetLabel: "Faithful",
      maxColors: 0,
      cleanupPasses: 0,
      removeBackground: false
    },
    expected: {
      totalBeads: 64,
      colorsUsed: 4,
      changedCells: 0,
      removedCells: 0,
      counts: {
        A26: 16,
        F3: 16,
        C8: 16,
        H5: 16
      }
    }
  }
];
