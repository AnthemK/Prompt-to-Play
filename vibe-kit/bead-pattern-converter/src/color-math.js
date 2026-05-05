// Color-math stays isolated so matching strategy changes do not leak into
// rendering, sampling, or UI modules.
export function clampGridDimension(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }

  return Math.max(8, Math.min(128, parsed));
}

function srgbToLinear(channel) {
  const normalized = channel / 255;
  if (normalized <= 0.04045) {
    return normalized / 12.92;
  }

  return ((normalized + 0.055) / 1.055) ** 2.4;
}

export function rgbToLab(rgb) {
  const red = srgbToLinear(rgb[0]);
  const green = srgbToLinear(rgb[1]);
  const blue = srgbToLinear(rgb[2]);

  const x = (red * 0.4124564 + green * 0.3575761 + blue * 0.1804375) / 0.95047;
  const y = (red * 0.2126729 + green * 0.7151522 + blue * 0.072175) / 1;
  const z = (red * 0.0193339 + green * 0.119192 + blue * 0.9503041) / 1.08883;

  const transform = (value) => {
    if (value > 0.008856) {
      return value ** (1 / 3);
    }

    return (7.787 * value) + (16 / 116);
  };

  const fx = transform(x);
  const fy = transform(y);
  const fz = transform(z);

  return [
    (116 * fy) - 16,
    500 * (fx - fy),
    200 * (fy - fz)
  ];
}

export function computeColorDistance(source, target) {
  const [l1, a1, b1] = source;
  const [l2, a2, b2] = target;
  const averageLightness = (l1 + l2) / 2;
  const chroma1 = Math.sqrt((a1 * a1) + (b1 * b1));
  const chroma2 = Math.sqrt((a2 * a2) + (b2 * b2));
  const averageChroma = (chroma1 + chroma2) / 2;
  const compensation = 0.5 * (1 - Math.sqrt((averageChroma ** 7) / ((averageChroma ** 7) + (25 ** 7))));
  const adjustedA1 = (1 + compensation) * a1;
  const adjustedA2 = (1 + compensation) * a2;
  const adjustedChroma1 = Math.sqrt((adjustedA1 * adjustedA1) + (b1 * b1));
  const adjustedChroma2 = Math.sqrt((adjustedA2 * adjustedA2) + (b2 * b2));
  const averageAdjustedChroma = (adjustedChroma1 + adjustedChroma2) / 2;
  const hue1 = Math.atan2(b1, adjustedA1);
  const hue2 = Math.atan2(b2, adjustedA2);
  const normalizedHue1 = hue1 >= 0 ? hue1 : hue1 + (2 * Math.PI);
  const normalizedHue2 = hue2 >= 0 ? hue2 : hue2 + (2 * Math.PI);
  const lightnessDelta = l2 - l1;
  const chromaDelta = adjustedChroma2 - adjustedChroma1;

  let hueDeltaAngle = normalizedHue2 - normalizedHue1;
  if (adjustedChroma1 * adjustedChroma2 === 0) {
    hueDeltaAngle = 0;
  } else if (hueDeltaAngle > Math.PI) {
    hueDeltaAngle -= 2 * Math.PI;
  } else if (hueDeltaAngle < -Math.PI) {
    hueDeltaAngle += 2 * Math.PI;
  }

  const hueDelta = 2 * Math.sqrt(adjustedChroma1 * adjustedChroma2) * Math.sin(hueDeltaAngle / 2);

  let averageHue = normalizedHue1 + normalizedHue2;
  if (adjustedChroma1 * adjustedChroma2 === 0) {
    averageHue = normalizedHue1 + normalizedHue2;
  } else if (Math.abs(normalizedHue1 - normalizedHue2) > Math.PI) {
    averageHue += 2 * Math.PI;
  }
  averageHue /= 2;

  const angleInDegrees = averageHue * (180 / Math.PI);
  const t =
    1 -
    (0.17 * Math.cos((averageHue - (30 * Math.PI / 180)))) +
    (0.24 * Math.cos(2 * averageHue)) +
    (0.32 * Math.cos((3 * averageHue) + (6 * Math.PI / 180))) -
    (0.2 * Math.cos((4 * averageHue) - (63 * Math.PI / 180)));
  const deltaTheta = 30 * Math.exp(-(((angleInDegrees - 275) / 25) ** 2));
  const rotationFactor = 2 * Math.sqrt((averageAdjustedChroma ** 7) / ((averageAdjustedChroma ** 7) + (25 ** 7)));
  const lightnessScale =
    1 + ((0.015 * ((averageLightness - 50) ** 2)) / Math.sqrt(20 + ((averageLightness - 50) ** 2)));
  const chromaScale = 1 + (0.045 * averageAdjustedChroma);
  const hueScale = 1 + (0.015 * averageAdjustedChroma * t);
  const rotationTerm = -Math.sin(2 * deltaTheta * (Math.PI / 180)) * rotationFactor;

  const lightnessComponent = lightnessDelta / lightnessScale;
  const chromaComponent = chromaDelta / chromaScale;
  const hueComponent = hueDelta / hueScale;

  return Math.sqrt(
    (lightnessComponent * lightnessComponent) +
    (chromaComponent * chromaComponent) +
    (hueComponent * hueComponent) +
    (rotationTerm * chromaComponent * hueComponent)
  );
}

export function findNearestColor(rgb, paletteColors) {
  const sampledLab = rgbToLab(rgb);
  return findNearestColorFromLab(sampledLab, paletteColors);
}

export function findNearestColorFromLab(sampledLab, paletteColors) {
  let bestMatch = paletteColors[0];
  let bestDistance = Number.POSITIVE_INFINITY;

  for (const color of paletteColors) {
    if (!color.lab) {
      color.lab = rgbToLab(color.rgb);
    }

    const distance = computeColorDistance(sampledLab, color.lab);
    if (distance < bestDistance) {
      bestDistance = distance;
      bestMatch = color;
    }
  }

  return bestMatch;
}
