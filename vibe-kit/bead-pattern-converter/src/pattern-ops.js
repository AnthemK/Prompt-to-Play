import {
  computeColorDistance,
  findNearestColor,
  findNearestColorFromLab,
  rgbToLab
} from "./color-math.js?v=20260505-7";

// Cell operations live separately from result assembly so cleanup, reduction,
// and background-removal strategies can evolve independently.

export function summarizeCounts(flatCells, palette) {
  const counts = new Map();

  for (const cell of flatCells) {
    if (!cell.paletteId) {
      continue;
    }

    counts.set(cell.paletteId, (counts.get(cell.paletteId) ?? 0) + 1);
  }

  return palette.colors
    .filter((color) => counts.has(color.id))
    .map((color) => ({
      paletteId: color.id,
      name: color.name,
      hex: color.hex,
      count: counts.get(color.id)
    }))
    .sort((left, right) => right.count - left.count);
}

export function countCellDifferences(leftCells, rightCells) {
  let changedCells = 0;

  for (let index = 0; index < leftCells.length; index += 1) {
    if (leftCells[index].paletteId !== rightCells[index].paletteId) {
      changedCells += 1;
    }
  }

  return changedCells;
}

export function indexGrid(flatCells, width) {
  const grid = [];

  for (let index = 0; index < flatCells.length; index += width) {
    grid.push(flatCells.slice(index, index + width));
  }

  return grid;
}

export function reduceColors(flatCells, palette, maxColors) {
  if (maxColors <= 0) {
    return flatCells;
  }

  const counts = summarizeCounts(flatCells, palette);
  if (counts.length <= maxColors) {
    return flatCells;
  }

  const allowedIds = new Set(counts.slice(0, maxColors).map((item) => item.paletteId));
  const allowedColors = palette.colors.filter((color) => allowedIds.has(color.id));

  return flatCells.map((cell) => {
    if (!cell.paletteId) {
      return cell;
    }

    if (allowedIds.has(cell.paletteId)) {
      return cell;
    }

    const remappedColor = cell.sampledLab
      ? findNearestColorFromLab(cell.sampledLab, allowedColors)
      : findNearestColor(cell.sampledRgb, allowedColors);
    return {
      ...cell,
      paletteId: remappedColor.id,
      color: remappedColor
    };
  });
}

export function smoothIsolatedCells(flatCells, width, height, cleanupPasses, paletteById) {
  let currentCells = flatCells;

  for (let pass = 0; pass < cleanupPasses; pass += 1) {
    const nextCells = currentCells.map((cell) => ({ ...cell }));

    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const index = y * width + x;
        const cell = currentCells[index];
        if (!cell.paletteId) {
          continue;
        }
        const neighborCounts = new Map();
        let sameColorNeighbors = 0;

        for (let offsetY = -1; offsetY <= 1; offsetY += 1) {
          for (let offsetX = -1; offsetX <= 1; offsetX += 1) {
            if (offsetX === 0 && offsetY === 0) {
              continue;
            }

            const neighborX = x + offsetX;
            const neighborY = y + offsetY;
            if (neighborX < 0 || neighborX >= width || neighborY < 0 || neighborY >= height) {
              continue;
            }

            const neighbor = currentCells[neighborY * width + neighborX];
            if (!neighbor.paletteId) {
              continue;
            }

            neighborCounts.set(
              neighbor.paletteId,
              (neighborCounts.get(neighbor.paletteId) ?? 0) + 1
            );

            if (neighbor.paletteId === cell.paletteId) {
              sameColorNeighbors += 1;
            }
          }
        }

        if (sameColorNeighbors >= 2 || neighborCounts.size === 0) {
          continue;
        }

        const dominantEntry = [...neighborCounts.entries()].sort(
          (left, right) => right[1] - left[1]
        )[0];
        if (!dominantEntry) {
          continue;
        }

        const [dominantId, dominantCount] = dominantEntry;
        if (dominantId === cell.paletteId || dominantCount < 4) {
          continue;
        }

        const replacementColor = paletteById.get(dominantId);
        if (!replacementColor) {
          continue;
        }

        nextCells[index] = {
          ...nextCells[index],
          paletteId: dominantId,
          color: replacementColor
        };
      }
    }

    currentCells = nextCells;
  }

  return currentCells;
}

export function removeOuterBackground(flatCells, width, height, sourceBackgroundRgb) {
  if (!sourceBackgroundRgb) {
    return {
      cells: flatCells,
      removedCells: 0,
      backgroundPaletteId: null
    };
  }

  const backgroundLab = rgbToLab(sourceBackgroundRgb);
  const backgroundThreshold = 9;
  const nextCells = flatCells.map((cell) => ({ ...cell }));
  const visited = new Uint8Array(flatCells.length);
  const stack = [];
  let removedCells = 0;
  const removedPaletteCounts = new Map();

  const tryPush = (index) => {
    if (index < 0 || index >= flatCells.length || visited[index]) {
      return;
    }

    const cell = flatCells[index];
    if (!cell.paletteId) {
      return;
    }

    const cellLab = cell.sampledLab ?? rgbToLab(cell.sampledRgb);
    if (computeColorDistance(cellLab, backgroundLab) > backgroundThreshold) {
      return;
    }

    visited[index] = 1;
    stack.push(index);
  };

  for (let x = 0; x < width; x += 1) {
    tryPush(x);
    tryPush((height - 1) * width + x);
  }

  for (let y = 1; y < height - 1; y += 1) {
    tryPush(y * width);
    tryPush(y * width + (width - 1));
  }

  while (stack.length > 0) {
    const index = stack.pop();
    const x = index % width;
    const y = Math.floor(index / width);
    const currentCell = nextCells[index];
    removedCells += 1;
    removedPaletteCounts.set(
      currentCell.paletteId,
      (removedPaletteCounts.get(currentCell.paletteId) ?? 0) + 1
    );
    nextCells[index] = {
      ...currentCell,
      paletteId: null,
      color: null,
      removedBackground: true,
      backgroundColor: {
        hex: `rgb(${Math.round(sourceBackgroundRgb[0])}, ${Math.round(sourceBackgroundRgb[1])}, ${Math.round(sourceBackgroundRgb[2])})`
      }
    };

    if (x > 0) {
      tryPush(index - 1);
    }
    if (x < width - 1) {
      tryPush(index + 1);
    }
    if (y > 0) {
      tryPush(index - width);
    }
    if (y < height - 1) {
      tryPush(index + width);
    }
  }

  const dominantBackground = [...removedPaletteCounts.entries()].sort(
    (left, right) => right[1] - left[1]
  )[0];
  const backgroundPaletteId = dominantBackground?.[0] ?? null;

  return {
    cells: nextCells,
    removedCells,
    backgroundPaletteId
  };
}

export function buildInitialCells(pixelData, width, height, palette) {
  const cells = [];

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const pixelIndex = (y * width + x) * 4;
      const sampledRgb = [
        pixelData[pixelIndex],
        pixelData[pixelIndex + 1],
        pixelData[pixelIndex + 2]
      ];
      const mappedColor = findNearestColor(sampledRgb, palette.colors);

      cells.push({
        x,
        y,
        sampledRgb,
        sampledLab: rgbToLab(sampledRgb),
        paletteId: mappedColor.id,
        color: mappedColor
      });
    }
  }

  return cells;
}
