import {
  drawRemovedCellMarker,
  getContrastColor
} from "./canvas-utils.js?v=20260505-7";

export function renderSourcePreview(canvas, image, cropBounds = null, options = {}) {
  const context = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;

  context.clearRect(0, 0, width, height);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);

  const sourceWidth = cropBounds?.width ?? image.width;
  const sourceHeight = cropBounds?.height ?? image.height;
  const sourceX = cropBounds?.x ?? 0;
  const sourceY = cropBounds?.y ?? 0;
  const scale = Math.min(width / sourceWidth, height / sourceHeight);
  const drawWidth = sourceWidth * scale;
  const drawHeight = sourceHeight * scale;
  const offsetX = (width - drawWidth) / 2;
  const offsetY = (height - drawHeight) / 2;

  // Source preview should stay visually aligned with the cropped conversion
  // bounds so manual inspection and generated previews use the same framing.
  context.imageSmoothingEnabled = true;
  context.imageSmoothingQuality = "high";
  context.drawImage(
    image,
    sourceX,
    sourceY,
    sourceWidth,
    sourceHeight,
    offsetX,
    offsetY,
    drawWidth,
    drawHeight
  );

  if (!options.showCutReference || !options.conversion || !cropBounds) {
    return;
  }

  const conversion = options.conversion;
  const cellWidth = drawWidth / conversion.target.width;
  const cellHeight = drawHeight / conversion.target.height;
  context.save();

  for (const row of conversion.grid) {
    for (const cell of row) {
      if (!cell.removedBackground) {
        continue;
      }

      const cellX = offsetX + (cell.x * cellWidth);
      const cellY = offsetY + (cell.y * cellHeight);
      context.fillStyle = "rgba(151, 126, 110, 0.16)";
      context.fillRect(cellX, cellY, Math.ceil(cellWidth), Math.ceil(cellHeight));
      drawRemovedCellMarker(context, cellX, cellY, Math.min(cellWidth, cellHeight));
    }
  }

  context.restore();
}

export function renderBeadPreview(canvas, conversion) {
  const context = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const previewPadding = Math.max(18, Math.round(Math.min(width, height) * 0.05));
  const drawWidth = width - (previewPadding * 2);
  const drawHeight = height - (previewPadding * 2);
  const cellWidth = drawWidth / conversion.target.width;
  const cellHeight = drawHeight / conversion.target.height;

  // A soft outer frame keeps white or near-white bead colors from visually
  // disappearing into the page background.
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#f8f5ee";
  context.fillRect(0, 0, width, height);
  context.fillStyle = "#fffdf8";
  context.fillRect(previewPadding, previewPadding, drawWidth, drawHeight);
  context.strokeStyle = "rgba(111, 96, 86, 0.12)";
  context.lineWidth = 1;
  context.strokeRect(
    previewPadding + 0.5,
    previewPadding + 0.5,
    drawWidth - 1,
    drawHeight - 1
  );

  for (const row of conversion.grid) {
    for (const cell of row) {
      if (!cell.color) {
        continue;
      }

      context.fillStyle = cell.color.hex;
      context.fillRect(
        previewPadding + (cell.x * cellWidth),
        previewPadding + (cell.y * cellHeight),
        Math.ceil(cellWidth),
        Math.ceil(cellHeight)
      );
    }
  }
}

export function renderComparisonSummary(target, conversion) {
  const { changedCells, changedRatio, rawColorsUsed, optimizedColorsUsed } = conversion.comparison;
  const percent = Math.round(changedRatio * 1000) / 10;
  target.textContent =
    `${changedCells} cells changed (${percent}%). ` +
    `Raw colors: ${rawColorsUsed}. Optimized colors: ${optimizedColorsUsed}.`;
}

export function renderBuildGrid(canvas, conversion, { showCodes }) {
  const context = canvas.getContext("2d");
  const gridWidth = conversion.target.width;
  const gridHeight = conversion.target.height;
  const labelBand = 40;
  const cellSize = Math.floor(
    Math.min((canvas.width - labelBand) / gridWidth, (canvas.height - labelBand) / gridHeight)
  );
  const drawWidth = labelBand + cellSize * gridWidth;
  const drawHeight = labelBand + cellSize * gridHeight;

  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "#fffef9";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.strokeStyle = "#ddcfbe";
  context.strokeRect(0.5, 0.5, drawWidth - 1, drawHeight - 1);
  context.font = `${Math.max(11, Math.floor(cellSize * 0.28))}px "Avenir Next", sans-serif`;
  context.textAlign = "center";
  context.textBaseline = "middle";

  for (let x = 0; x < gridWidth; x += 1) {
    const labelX = labelBand + x * cellSize + cellSize / 2;
    context.fillStyle = "#66584e";
    context.fillText(String(x + 1), labelX, labelBand / 2);
  }

  for (let y = 0; y < gridHeight; y += 1) {
    const labelY = labelBand + y * cellSize + cellSize / 2;
    context.fillStyle = "#66584e";
    context.fillText(String(y + 1), labelBand / 2, labelY);
  }

  for (const row of conversion.grid) {
    for (const cell of row) {
      const drawX = labelBand + cell.x * cellSize;
      const drawY = labelBand + cell.y * cellSize;

      if (cell.color) {
        context.fillStyle = cell.color.hex;
        context.fillRect(drawX, drawY, cellSize, cellSize);
      } else {
        context.clearRect(drawX, drawY, cellSize, cellSize);
        context.fillStyle = "#fffdf8";
        context.fillRect(drawX, drawY, cellSize, cellSize);
        if (cell.removedBackground) {
          drawRemovedCellMarker(context, drawX, drawY, cellSize);
        }
      }

      context.strokeStyle = "rgba(86, 65, 53, 0.18)";
      context.strokeRect(drawX + 0.5, drawY + 0.5, cellSize, cellSize);

      if (showCodes && cellSize >= 13 && cell.color) {
        context.fillStyle = getContrastColor(cell.color.hex);
        context.fillText(cell.paletteId, drawX + cellSize / 2, drawY + cellSize / 2);
      }
    }
  }
}

export function renderMaterialsTable(tableBody, conversion) {
  tableBody.textContent = "";

  for (const item of conversion.counts) {
    const row = document.createElement("tr");

    const swatchCell = document.createElement("td");
    const swatch = document.createElement("div");
    swatch.className = "swatch";
    swatch.style.backgroundColor = item.hex;
    swatchCell.appendChild(swatch);

    const codeCell = document.createElement("td");
    codeCell.textContent = item.paletteId;

    const nameCell = document.createElement("td");
    nameCell.textContent = item.name;

    const countCell = document.createElement("td");
    countCell.textContent = String(item.count);

    row.append(swatchCell, codeCell, nameCell, countCell);
    tableBody.appendChild(row);
  }
}
