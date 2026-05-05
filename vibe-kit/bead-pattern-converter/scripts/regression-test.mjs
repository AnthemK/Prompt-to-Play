import assert from "node:assert/strict";

import { loadPaletteById } from "../src/palette.js";
import { buildPatternFromPixels } from "../src/pattern-core.js";
import { REGRESSION_FIXTURES } from "../fixtures/regression-fixtures.js";

function flattenRgbPixels(pixels) {
  const pixelData = new Uint8ClampedArray(pixels.length * 4);

  for (let index = 0; index < pixels.length; index += 1) {
    const [red, green, blue] = pixels[index];
    const outputIndex = index * 4;
    pixelData[outputIndex] = red;
    pixelData[outputIndex + 1] = green;
    pixelData[outputIndex + 2] = blue;
    pixelData[outputIndex + 3] = 255;
  }

  return pixelData;
}

function countsToMap(conversion) {
  return new Map(conversion.counts.map((item) => [item.paletteId, item.count]));
}

function getCell(conversion, x, y) {
  return conversion.grid[y][x];
}

let passed = 0;

for (const fixture of REGRESSION_FIXTURES) {
  const palette = await loadPaletteById(fixture.paletteId);
  const conversion = buildPatternFromPixels({
    pixelData: flattenRgbPixels(fixture.pixels),
    targetWidth: fixture.width,
    targetHeight: fixture.height,
    palette,
    sourceWidth: fixture.width,
    sourceHeight: fixture.height,
    sourceBackgroundRgb: fixture.sourceBackgroundRgb ?? null,
    fitMode: "regression-fixture",
    optimization: fixture.optimization
  });

  const counts = countsToMap(conversion);
  assert.equal(
    conversion.totalBeads,
    fixture.expected.totalBeads,
    `${fixture.name}: totalBeads`
  );
  assert.equal(
    conversion.counts.length,
    fixture.expected.colorsUsed,
    `${fixture.name}: colorsUsed`
  );
  assert.equal(
    conversion.comparison.changedCells,
    fixture.expected.changedCells,
    `${fixture.name}: changedCells`
  );
  assert.equal(
    conversion.background.removedCells,
    fixture.expected.removedCells,
    `${fixture.name}: removedCells`
  );

  for (const [paletteId, expectedCount] of Object.entries(fixture.expected.counts ?? {})) {
    assert.equal(
      counts.get(paletteId) ?? 0,
      expectedCount,
      `${fixture.name}: count for ${paletteId}`
    );
  }

  if ("centerPaletteId" in fixture.expected) {
    const centerX = Math.floor(fixture.width / 2);
    const centerY = Math.floor(fixture.height / 2);
    assert.equal(
      getCell(conversion, centerX, centerY).paletteId,
      fixture.expected.centerPaletteId,
      `${fixture.name}: centerPaletteId`
    );
  }

  if ("topLeftPaletteId" in fixture.expected) {
    assert.equal(
      getCell(conversion, 0, 0).paletteId,
      fixture.expected.topLeftPaletteId,
      `${fixture.name}: topLeftPaletteId`
    );
  }

  passed += 1;
}

console.log(JSON.stringify({
  passed,
  fixtures: REGRESSION_FIXTURES.map((fixture) => fixture.name)
}, null, 2));
