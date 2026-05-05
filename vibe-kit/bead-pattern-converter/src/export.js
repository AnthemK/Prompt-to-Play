import {
  drawCard,
  drawCenteredWrappedTitle,
  drawRoundedRect,
  drawWrappedText,
  drawWrappedTextBlock,
  measureWrappedTextHeight
} from "./canvas-utils.js?v=20260505-7";

// Export rendering reuses shared canvas primitives so the printable sheet and
// on-screen cards can evolve with the same typography and framing rules.

function downloadBlob(blob, filename) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  link.click();

  setTimeout(() => {
    URL.revokeObjectURL(objectUrl);
  }, 0);
}

function sanitizeFileStem(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "bead-pattern";
}

function buildFileStem(conversion) {
  return sanitizeFileStem(
    `${conversion.palette.name}-${conversion.optimization.preset}-${conversion.target.width}x${conversion.target.height}`
  );
}

const EXPORT_PRESETS = {
  "build-sheet": {
    id: "build-sheet",
    label: "Build sheet",
    filenameSuffix: "build-sheet"
  },
  "share-sheet": {
    id: "share-sheet",
    label: "Share sheet",
    filenameSuffix: "share-sheet"
  },
  "materials-sheet": {
    id: "materials-sheet",
    label: "Materials sheet",
    filenameSuffix: "materials-sheet"
  }
};

function getExportPreset(presetId) {
  return EXPORT_PRESETS[presetId] ?? EXPORT_PRESETS["build-sheet"];
}

function normalizeDisplayTitle(value) {
  return String(value).replace(/\s+/g, " ").trim() || "Bead Pattern";
}

function escapeCsvCell(value) {
  const text = String(value);
  if (text.includes(",") || text.includes('"') || text.includes("\n")) {
    return `"${text.replaceAll('"', '""')}"`;
  }

  return text;
}

export function exportCanvasAsPng(canvas, filename) {
  canvas.toBlob((blob) => {
    if (!blob) {
      return;
    }

    downloadBlob(blob, filename);
  }, "image/png");
}

function renderBuildSheetCanvas({ conversion, gridCanvas, previewCanvas, title }) {
  const canvas = document.createElement("canvas");
  canvas.width = 1800;
  canvas.height = 2400;
  const context = canvas.getContext("2d");

  context.fillStyle = "#f8f4ee";
  context.fillRect(0, 0, canvas.width, canvas.height);

  context.fillStyle = "#4d4037";
  context.textAlign = "center";
  context.font = "700 56px 'Avenir Next', 'PingFang SC', sans-serif";
  const titleBottom = drawCenteredWrappedTitle(
    context,
    `${normalizeDisplayTitle(title)} Bead Pattern Sheet`,
    canvas.width / 2,
    84,
    1320,
    62,
    2
  );

  context.font = "400 26px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillStyle = "#77675b";
  context.fillText(
    `${conversion.target.width} x ${conversion.target.height} grid · ${conversion.totalBeads} beads · ${conversion.optimization.presetLabel}`,
    canvas.width / 2,
    titleBottom + 8
  );

  const gridX = 70;
  const gridY = 210;
  const gridWidth = 1240;
  const gridHeight = 1240;
  drawCard(context, gridX, gridY, gridWidth, gridHeight);
  context.drawImage(gridCanvas, gridX + 20, gridY + 20, gridWidth - 40, gridHeight - 40);

  const sidebarX = 1350;
  const sidebarWidth = 380;
  const summaryLines = [
    `Palette: ${conversion.palette.name}`,
    `Preset: ${conversion.optimization.presetLabel}`,
    `Max colors: ${conversion.optimization.maxColors || "Full palette"}`,
    `Cleanup passes: ${conversion.optimization.cleanupPasses}`,
    `Background: ${conversion.optimization.removeBackground ? "Outer background removed" : "Background kept"}`,
    `Empty cells: ${conversion.background.removedCells}`,
    `Changed cells: ${conversion.comparison.changedCells}`,
    `Optimized colors: ${conversion.comparison.optimizedColorsUsed}`
  ];
  context.font = "400 24px 'Avenir Next', 'PingFang SC', sans-serif";
  const summaryLineHeight = 32;
  const summaryTextHeight = summaryLines.reduce(
    (total, line) => total + measureWrappedTextHeight(context, line, sidebarWidth - 56, summaryLineHeight),
    0
  );
  const summaryCardHeight = Math.max(290, 120 + summaryTextHeight);
  const noteText = conversion.optimization.removeBackground
    ? "Cells marked with a faint X are intentionally empty background holes removed from the outer edge. Matching colors inside the subject stay untouched."
    : "Pure grid export stays available separately. This overview sheet is designed for sharing, printing, and quick manual assembly reference.";
  context.font = "400 23px 'Avenir Next', 'PingFang SC', sans-serif";
  const noteLineHeight = 32;
  const noteCardHeight = Math.max(
    240,
    110 + measureWrappedTextHeight(context, noteText, sidebarWidth - 56, noteLineHeight)
  );

  drawCard(context, sidebarX, gridY, sidebarWidth, 360);
  context.textAlign = "center";
  context.fillStyle = "#4d4037";
  context.font = "700 34px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillText("Preview", sidebarX + sidebarWidth / 2, gridY + 56);
  context.drawImage(previewCanvas, sidebarX + 45, gridY + 95, 290, 220);

  drawCard(context, sidebarX, gridY + 390, sidebarWidth, summaryCardHeight);
  context.textAlign = "left";
  context.fillStyle = "#4d4037";
  context.font = "700 30px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillText("Build Summary", sidebarX + 28, gridY + 438);
  context.font = "400 24px 'Avenir Next', 'PingFang SC', sans-serif";
  drawWrappedTextBlock(
    context,
    summaryLines,
    sidebarX + 28,
    gridY + 488,
    sidebarWidth - 56,
    summaryLineHeight
  );

  const notesY = gridY + 390 + summaryCardHeight + 30;
  drawCard(context, sidebarX, notesY, sidebarWidth, noteCardHeight);
  context.font = "700 30px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillText("Pattern Notes", sidebarX + 28, notesY + 48);
  context.font = "400 23px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillStyle = "#6e5f54";
  drawWrappedText(
    context,
    noteText,
    sidebarX + 28,
    notesY + 95,
    sidebarWidth - 56,
    noteLineHeight
  );

  const tableX = 70;
  const tableY = 1480;
  const tableWidth = 1660;
  const tableHeight = 760;
  drawCard(context, tableX, tableY, tableWidth, tableHeight);

  context.textAlign = "center";
  context.fillStyle = "#e89a84";
  drawRoundedRect(context, tableX + 20, tableY + 20, tableWidth - 40, 54, 20);
  context.fill();
  context.fillStyle = "#fffaf7";
  context.font = "700 32px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillText("Palette & Usage", canvas.width / 2, tableY + 57);

  const columns = [
    { label: "Swatch", width: 150 },
    { label: "Code", width: 170 },
    { label: "Color", width: 430 },
    { label: "HEX", width: 260 },
    { label: "Count", width: 180 },
    { label: "Share", width: 210 }
  ];
  const headerY = tableY + 108;
  let cursorX = tableX + 32;
  context.textAlign = "left";
  context.fillStyle = "#4d4037";
  context.font = "700 24px 'Avenir Next', 'PingFang SC', sans-serif";
  for (const column of columns) {
    context.fillText(column.label, cursorX + 8, headerY);
    cursorX += column.width;
  }

  const rowStartY = tableY + 146;
  const rowHeight = 58;
  const maxRows = Math.min(conversion.counts.length, 10);
  context.font = "400 22px 'Avenir Next', 'PingFang SC', sans-serif";

  for (let index = 0; index < maxRows; index += 1) {
    const item = conversion.counts[index];
    const rowY = rowStartY + index * rowHeight;
    context.strokeStyle = "rgba(177, 144, 127, 0.35)";
    context.beginPath();
    context.moveTo(tableX + 28, rowY + 34);
    context.lineTo(tableX + tableWidth - 28, rowY + 34);
    context.stroke();

    let cellX = tableX + 32;
    context.fillStyle = item.hex;
    context.fillRect(cellX + 10, rowY - 8, 34, 34);
    context.strokeStyle = "rgba(0, 0, 0, 0.12)";
    context.strokeRect(cellX + 10, rowY - 8, 34, 34);
    cellX += columns[0].width;

    context.fillStyle = "#4d4037";
    context.fillText(item.paletteId, cellX + 8, rowY + 16);
    cellX += columns[1].width;

    context.fillText(item.name, cellX + 8, rowY + 16);
    cellX += columns[2].width;

    context.fillText(item.hex, cellX + 8, rowY + 16);
    cellX += columns[3].width;

    context.fillText(String(item.count), cellX + 8, rowY + 16);
    cellX += columns[4].width;

    const shareBase = conversion.totalBeads > 0 ? conversion.totalBeads : 1;
    const share = `${Math.round((item.count / shareBase) * 1000) / 10}%`;
    context.fillText(share, cellX + 8, rowY + 16);
  }

  drawCard(context, 70, 2270, 420, 82);
  context.textAlign = "center";
  context.fillStyle = "#4d4037";
  context.font = "700 34px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillText(`Placed beads: ${conversion.totalBeads}`, 280, 2322);

  drawCard(context, 540, 2270, 360, 82);
  context.font = "700 30px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillStyle = "#6e5f54";
  context.fillText(`Empty cells: ${conversion.background.removedCells}`, 720, 2321);

  drawCard(context, 950, 2270, 780, 82);
  context.font = "400 24px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillStyle = "#6e5f54";
  context.fillText(
    `Raw colors ${conversion.comparison.rawColorsUsed} → Optimized ${conversion.comparison.optimizedColorsUsed} · Changed ${conversion.comparison.changedCells} cells`,
    1340,
    2321
  );

  return canvas;
}

function renderShareSheetCanvas({ conversion, previewCanvas, title }) {
  const canvas = document.createElement("canvas");
  canvas.width = 1600;
  canvas.height = 2000;
  const context = canvas.getContext("2d");

  context.fillStyle = "#f8f4ee";
  context.fillRect(0, 0, canvas.width, canvas.height);

  context.fillStyle = "#4d4037";
  context.textAlign = "center";
  context.font = "700 60px 'Avenir Next', 'PingFang SC', sans-serif";
  const titleBottom = drawCenteredWrappedTitle(
    context,
    `${normalizeDisplayTitle(title)} Bead Pattern`,
    canvas.width / 2,
    88,
    1200,
    66,
    2
  );

  context.font = "400 28px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillStyle = "#77675b";
  context.fillText(
    `${conversion.target.width} x ${conversion.target.height} · ${conversion.totalBeads} beads · ${conversion.counts.length} colors`,
    canvas.width / 2,
    titleBottom + 12
  );

  drawCard(context, 120, 220, 1360, 920);
  context.drawImage(previewCanvas, 220, 300, 1160, 760);

  drawCard(context, 120, 1180, 1360, 230);
  context.textAlign = "left";
  context.fillStyle = "#4d4037";
  context.font = "700 34px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillText("Summary", 160, 1245);
  context.font = "400 26px 'Avenir Next', 'PingFang SC', sans-serif";
  const summaryLines = [
    `Palette: ${conversion.palette.name}`,
    `Preset: ${conversion.optimization.presetLabel}`,
    `Background: ${conversion.optimization.removeBackground ? "Outer background removed" : "Background kept"}`,
    `Changed cells: ${conversion.comparison.changedCells} (${Math.round(conversion.comparison.changedRatio * 1000) / 10}%)`
  ];
  drawWrappedTextBlock(context, summaryLines, 160, 1302, 1280, 34);

  drawCard(context, 120, 1450, 1360, 420);
  context.font = "700 34px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillText("Top colors", 160, 1515);
  context.font = "400 24px 'Avenir Next', 'PingFang SC', sans-serif";
  let rowY = 1575;
  for (const item of conversion.counts.slice(0, 8)) {
    context.fillStyle = item.hex;
    context.fillRect(160, rowY - 20, 28, 28);
    context.strokeStyle = "rgba(0, 0, 0, 0.12)";
    context.strokeRect(160, rowY - 20, 28, 28);
    context.fillStyle = "#4d4037";
    context.fillText(`${item.paletteId} · ${item.name} · ${item.count}`, 208, rowY + 2);
    rowY += 38;
  }

  return canvas;
}

function renderMaterialsSheetCanvas({ conversion, title }) {
  const canvas = document.createElement("canvas");
  canvas.width = 1700;
  canvas.height = 2200;
  const context = canvas.getContext("2d");

  context.fillStyle = "#f8f4ee";
  context.fillRect(0, 0, canvas.width, canvas.height);

  context.fillStyle = "#4d4037";
  context.textAlign = "center";
  context.font = "700 56px 'Avenir Next', 'PingFang SC', sans-serif";
  const titleBottom = drawCenteredWrappedTitle(
    context,
    `${normalizeDisplayTitle(title)} Materials Sheet`,
    canvas.width / 2,
    84,
    1260,
    62,
    2
  );

  context.font = "400 26px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillStyle = "#77675b";
  context.fillText(
    `${conversion.palette.name} · ${conversion.totalBeads} placed beads · ${conversion.counts.length} colors`,
    canvas.width / 2,
    titleBottom + 8
  );

  drawCard(context, 70, 210, 1560, 180);
  context.textAlign = "left";
  context.fillStyle = "#4d4037";
  context.font = "700 32px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillText("Procurement summary", 110, 272);
  context.font = "400 24px 'Avenir Next', 'PingFang SC', sans-serif";
  drawWrappedTextBlock(context, [
    `Grid: ${conversion.target.width} x ${conversion.target.height}`,
    `Preset: ${conversion.optimization.presetLabel}`,
    `Removed outer background cells: ${conversion.background.removedCells}`,
    `Top material share: ${conversion.counts[0] ? `${conversion.counts[0].paletteId} ${Math.round((conversion.counts[0].count / Math.max(conversion.totalBeads, 1)) * 1000) / 10}%` : "None"}`
  ], 110, 322, 1480, 32);

  const tableX = 70;
  const tableY = 430;
  const tableWidth = 1560;
  const tableHeight = 1680;
  drawCard(context, tableX, tableY, tableWidth, tableHeight);

  context.textAlign = "center";
  context.fillStyle = "#e89a84";
  drawRoundedRect(context, tableX + 20, tableY + 20, tableWidth - 40, 54, 20);
  context.fill();
  context.fillStyle = "#fffaf7";
  context.font = "700 32px 'Avenir Next', 'PingFang SC', sans-serif";
  context.fillText("Palette & Usage", canvas.width / 2, tableY + 57);

  const columns = [
    { label: "Swatch", width: 150 },
    { label: "Code", width: 170 },
    { label: "Color", width: 480 },
    { label: "HEX", width: 260 },
    { label: "Count", width: 180 },
    { label: "Share", width: 220 }
  ];
  const headerY = tableY + 108;
  let cursorX = tableX + 32;
  context.textAlign = "left";
  context.fillStyle = "#4d4037";
  context.font = "700 24px 'Avenir Next', 'PingFang SC', sans-serif";
  for (const column of columns) {
    context.fillText(column.label, cursorX + 8, headerY);
    cursorX += column.width;
  }

  const rowStartY = tableY + 146;
  const rowHeight = 56;
  const maxRows = Math.min(conversion.counts.length, 24);
  context.font = "400 22px 'Avenir Next', 'PingFang SC', sans-serif";

  for (let index = 0; index < maxRows; index += 1) {
    const item = conversion.counts[index];
    const rowY = rowStartY + index * rowHeight;
    context.strokeStyle = "rgba(177, 144, 127, 0.35)";
    context.beginPath();
    context.moveTo(tableX + 28, rowY + 34);
    context.lineTo(tableX + tableWidth - 28, rowY + 34);
    context.stroke();

    let cellX = tableX + 32;
    context.fillStyle = item.hex;
    context.fillRect(cellX + 10, rowY - 8, 34, 34);
    context.strokeStyle = "rgba(0, 0, 0, 0.12)";
    context.strokeRect(cellX + 10, rowY - 8, 34, 34);
    cellX += columns[0].width;

    context.fillStyle = "#4d4037";
    context.fillText(item.paletteId, cellX + 8, rowY + 16);
    cellX += columns[1].width;
    context.fillText(item.name, cellX + 8, rowY + 16);
    cellX += columns[2].width;
    context.fillText(item.hex, cellX + 8, rowY + 16);
    cellX += columns[3].width;
    context.fillText(String(item.count), cellX + 8, rowY + 16);
    cellX += columns[4].width;
    context.fillText(`${Math.round((item.count / Math.max(conversion.totalBeads, 1)) * 1000) / 10}%`, cellX + 8, rowY + 16);
  }

  return canvas;
}

export function exportMaterialsCsv(conversion) {
  const metadataRows = [
    ["# bead_pattern_converter_export", "1"],
    ["# palette", conversion.palette.name],
    ["# palette_id", conversion.palette.id],
    ["# preset", conversion.optimization.presetLabel],
    ["# preset_id", conversion.optimization.preset],
    ["# max_colors", conversion.optimization.maxColors],
    ["# cleanup_passes", conversion.optimization.cleanupPasses],
    ["# remove_background", conversion.optimization.removeBackground],
    ["# total_beads", conversion.totalBeads],
    ["# total_cells", conversion.totalCells],
    ["# removed_background_cells", conversion.background.removedCells],
    ["# background_palette_id", conversion.background.backgroundPaletteId ?? ""],
    ["# raw_colors_used", conversion.comparison.rawColorsUsed],
    ["# optimized_colors_used", conversion.comparison.optimizedColorsUsed],
    ["# changed_cells", conversion.comparison.changedCells],
    ["# changed_ratio", conversion.comparison.changedRatio]
  ];
  const rows = [
    ["palette_code", "color_name", "hex", "count"],
    ...conversion.counts.map((item) => [
      item.paletteId,
      item.name,
      item.hex,
      item.count
    ]),
    ["total", "", "", conversion.totalBeads]
  ];

  const csvText = rows
    .map((row) => row.map((cell) => escapeCsvCell(cell)).join(","))
    .join("\n");
  const metadataText = metadataRows
    .map((row) => row.map((cell) => escapeCsvCell(cell)).join(","))
    .join("\n");

  downloadBlob(
    new Blob([`${metadataText}\n\n${csvText}`], { type: "text/csv;charset=utf-8" }),
    `${buildFileStem(conversion)}-materials.csv`
  );
}

export function getPreviewFilename(conversion) {
  return `${buildFileStem(conversion)}-preview.png`;
}

export function getGridFilename(conversion) {
  return `${buildFileStem(conversion)}-grid.png`;
}

export function getOverviewFilename(conversion) {
  return `${buildFileStem(conversion)}-sheet.png`;
}

export function getOverviewFilenameForPreset(conversion, presetId) {
  const preset = getExportPreset(presetId);
  return `${buildFileStem(conversion)}-${preset.filenameSuffix}.png`;
}

export function exportOverviewPng({ conversion, gridCanvas, previewCanvas, title, preset = "build-sheet" }) {
  const exportPreset = getExportPreset(preset);
  let canvas;

  if (exportPreset.id === "share-sheet") {
    canvas = renderShareSheetCanvas({
      conversion,
      previewCanvas,
      title
    });
  } else if (exportPreset.id === "materials-sheet") {
    canvas = renderMaterialsSheetCanvas({
      conversion,
      title
    });
  } else {
    canvas = renderBuildSheetCanvas({
      conversion,
      gridCanvas,
      previewCanvas,
      title
    });
  }

  exportCanvasAsPng(canvas, getOverviewFilenameForPreset(conversion, exportPreset.id));
}
