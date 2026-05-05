import sharp from "/Users/liwenzhong/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp/lib/index.js";

import { loadPaletteById } from "../src/palette.js";
import { buildPatternFromPixels, normalizeTargetSize } from "../src/pattern-core.js";
import {
  detectContentBoundsFromPixels,
  getCornerAverage,
  sampleGridFromPixels
} from "../src/sampling-core.js";

const imagePath = process.argv[2];
const widthArg = process.argv[3] ?? "48";
const heightArg = process.argv[4] ?? widthArg;
const paletteId = process.argv[5] ?? "default-18";
const maxColorsArg = process.argv[6] ?? "0";
const cleanupPassesArg = process.argv[7] ?? "1";
const presetArg = process.argv[8] ?? "custom";
const removeBackgroundArg = process.argv[9] ?? "false";

if (!imagePath) {
  console.error(
    "Usage: node scripts/smoke-test.mjs <image-path> [width] [height] [palette-id] [max-colors] [cleanup-passes]"
    + " [preset-id]"
  );
  process.exit(1);
}

const palette = await loadPaletteById(paletteId);
const target = normalizeTargetSize({
  targetWidth: widthArg,
  targetHeight: heightArg
});

const baseImage = sharp(imagePath).flatten({ background: "#ffffff" });
const metadata = await baseImage.metadata();
const { data: fullData, info: fullInfo } = await baseImage
  .removeAlpha()
  .raw()
  .toBuffer({ resolveWithObject: true });

const cornerSize = Math.max(
  2,
  Math.min(12, Math.floor(Math.min(fullInfo.width, fullInfo.height) * 0.06))
);
const background = getCornerAverage(fullData, fullInfo.width, fullInfo.height, cornerSize, 3);
const cropBounds = detectContentBoundsFromPixels({
  imageData: fullData,
  width: fullInfo.width,
  height: fullInfo.height,
  background,
  channelsPerPixel: 3
});
const { data: croppedData } = await baseImage
  .extract(cropBounds)
  .removeAlpha()
  .raw()
  .toBuffer({ resolveWithObject: true });

const pixelData = sampleGridFromPixels({
  imageData: croppedData,
  width: cropBounds.width,
  height: cropBounds.height,
  targetWidth: target.width,
  targetHeight: target.height,
  background,
  channelsPerPixel: 3
});

const conversion = buildPatternFromPixels({
  pixelData,
  targetWidth: target.width,
  targetHeight: target.height,
  palette,
  sourceWidth: metadata.width ?? target.width,
  sourceHeight: metadata.height ?? target.height,
  sourceBackgroundRgb: background,
  fitMode: "content-trim-direct-sample",
  optimization: {
    preset: presetArg,
    presetLabel: presetArg,
    maxColors: maxColorsArg,
    cleanupPasses: cleanupPassesArg,
    removeBackground: removeBackgroundArg === "true"
  }
});

const topColors = conversion.counts.slice(0, 8);
const payload = {
  source: conversion.source,
  target: conversion.target,
  totalBeads: conversion.totalBeads,
  colorsUsed: conversion.counts.length,
  optimization: conversion.optimization,
  comparison: conversion.comparison,
  topColors
};

console.log(JSON.stringify(payload, null, 2));
