export const PALETTE_MANIFEST = [
  {
    id: "default-18",
    name: "Default Bead Palette (18 Colors)",
    brand: "Vibe Kit",
    description:
      "A balanced general-purpose palette with neutrals, warm tones, yellow range, and a few basic accent colors.",
    notes: [
      "Designed as the default palette for mixed everyday images instead of portrait-only subjects.",
      "Adds dedicated yellow and cool accent coverage so bright objects do not collapse into pink or red."
    ],
    recommendation: {
      badge: "Recommended default",
      bestFor: "Everyday icons, simple objects, fast first passes",
      tradeoff: "Fast and easy to read, but not the best choice for subtle skin tones or high-fidelity color matching."
    },
    colorCount: 18,
    loader: "default-18"
  },
  {
    id: "portrait-24",
    name: "Portrait Plus (24 Colors)",
    brand: "Vibe Kit",
    description:
      "A wider portrait-oriented palette with extra skin, blush, and dark-tone separation.",
    notes: [
      "Better tonal range than the starter palette.",
      "Intended for portraits, characters, and stylized mascot art."
    ],
    recommendation: {
      badge: "Portrait-friendly",
      bestFor: "Faces, mascots, soft shading, stylized characters",
      tradeoff: "Gives better warm-tone separation, but may bias non-portrait images toward softer reds and skin-like tones."
    },
    colorCount: 24,
    loader: "portrait-24"
  },
  {
    id: "mard-221",
    name: "Mard 221 Standard Palette",
    brand: "Mard",
    description:
      "Imported from the public Mard 221-color standard chart used by pindou.online. This is the broad production palette for precise matching.",
    notes: [
      "Covers the A~M nine-series 221-color standard set shown on pindou.online.",
      "Best for higher-fidelity conversions when the smaller starter palettes cannot represent a source image accurately."
    ],
    recommendation: {
      badge: "High-fidelity",
      bestFor: "Production output, detailed artwork, difficult color subjects",
      tradeoff: "Highest fidelity and widest coverage, but can introduce more colors and a busier materials list."
    },
    colorCount: 221,
    loader: "mard-221"
  }
];
