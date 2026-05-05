// Diagnostics are intentionally read-only: they expose how the pipeline made
// its choices without affecting the primary authoring workflow.
function formatShare(count, total) {
  if (!total) {
    return "0%";
  }

  return `${((count / total) * 100).toFixed(1)}%`;
}

function createMetric(label, value) {
  const metric = document.createElement("div");
  metric.className = "diagnostic-metric";

  const labelNode = document.createElement("span");
  labelNode.className = "diagnostic-label";
  labelNode.textContent = label;

  const valueNode = document.createElement("strong");
  valueNode.className = "diagnostic-value";
  valueNode.textContent = value;

  metric.append(labelNode, valueNode);
  return metric;
}

function createTopColorItem(item, totalBeads) {
  const row = document.createElement("div");
  row.className = "diagnostic-color-row";

  const swatch = document.createElement("span");
  swatch.className = "diagnostic-swatch";
  swatch.style.backgroundColor = item.hex;

  const code = document.createElement("span");
  code.className = "diagnostic-code";
  code.textContent = item.paletteId;

  const name = document.createElement("span");
  name.className = "diagnostic-name";
  name.textContent = item.name;

  const count = document.createElement("span");
  count.className = "diagnostic-count";
  count.textContent = `${item.count} · ${formatShare(item.count, totalBeads)}`;

  row.append(swatch, code, name, count);
  return row;
}

function createRemapItem(item, changedCells) {
  const row = document.createElement("div");
  row.className = "diagnostic-remap-row";

  const from = document.createElement("span");
  from.className = "diagnostic-remap-from";
  from.textContent = `${item.fromId} ${item.fromName}`;

  const arrow = document.createElement("span");
  arrow.className = "diagnostic-remap-arrow";
  arrow.textContent = "→";

  const to = document.createElement("span");
  to.className = "diagnostic-remap-to";
  to.textContent = `${item.toId} ${item.toName}`;

  const count = document.createElement("span");
  count.className = "diagnostic-count";
  count.textContent = `${item.count} · ${formatShare(item.count, changedCells)}`;

  row.append(from, arrow, to, count);
  return row;
}

export function resetDiagnostics(container) {
  container.innerHTML = "";

  const placeholder = document.createElement("p");
  placeholder.className = "diagnostic-placeholder";
  placeholder.textContent = "Generate a pattern to inspect palette usage, background removal, and optimization impact.";
  container.appendChild(placeholder);
}

export function renderDiagnostics(container, conversion) {
  container.innerHTML = "";
  const removedShare = formatShare(conversion.background.removedCells, conversion.totalCells);
  const changedShare = formatShare(conversion.comparison.changedCells, conversion.totalCells);

  const metrics = document.createElement("div");
  metrics.className = "diagnostic-metrics";
  metrics.append(
    createMetric("Placed beads", `${conversion.totalBeads} / ${conversion.totalCells}`),
    createMetric("Raw → optimized colors", `${conversion.comparison.rawColorsUsed} → ${conversion.comparison.optimizedColorsUsed}`),
    createMetric("Changed cells", `${conversion.comparison.changedCells} (${changedShare})`),
    createMetric("Removed background cells", `${conversion.background.removedCells} (${removedShare})`)
  );

  const topColors = document.createElement("div");
  topColors.className = "diagnostic-section";

  const colorsTitle = document.createElement("h3");
  colorsTitle.textContent = "Ranked mapped colors";
  topColors.appendChild(colorsTitle);

  const colorsNote = document.createElement("p");
  colorsNote.className = "diagnostic-note";
  colorsNote.textContent = "These are the optimized palette colors that remain in the final pattern.";
  topColors.appendChild(colorsNote);

  for (const item of conversion.counts.slice(0, 12)) {
    topColors.appendChild(createTopColorItem(item, conversion.totalBeads));
  }

  const background = document.createElement("div");
  background.className = "diagnostic-section";

  const backgroundTitle = document.createElement("h3");
  backgroundTitle.textContent = "Background handling";
  background.appendChild(backgroundTitle);

  const backgroundList = document.createElement("ul");
  backgroundList.className = "diagnostic-list";
  backgroundList.innerHTML = `
    <li>Mode: ${conversion.optimization.removeBackground ? "Outer edge background removed" : "Background kept"}</li>
    <li>Detected source edge RGB: ${conversion.background.sourceRgb.map((value) => Math.round(value)).join(", ")}</li>
    <li>Removed edge-connected cells: ${conversion.background.removedCells}</li>
    <li>Background palette id: ${conversion.background.backgroundPaletteId ?? "None"}</li>
  `;
  background.appendChild(backgroundList);

  const remaps = document.createElement("div");
  remaps.className = "diagnostic-section";

  const remapsTitle = document.createElement("h3");
  remapsTitle.textContent = "Top cleanup / reduction remaps";
  remaps.appendChild(remapsTitle);

  const remapsNote = document.createElement("p");
  remapsNote.className = "diagnostic-note";
  remapsNote.textContent = "These show which raw palette matches were most often rewritten by color reduction or cleanup.";
  remaps.appendChild(remapsNote);

  if (conversion.comparison.remappedPairs.length === 0) {
    const empty = document.createElement("p");
    empty.className = "diagnostic-placeholder";
    empty.textContent = "No cells were remapped after the initial palette match.";
    remaps.appendChild(empty);
  } else {
    for (const item of conversion.comparison.remappedPairs.slice(0, 8)) {
      remaps.appendChild(createRemapItem(item, conversion.comparison.changedCells || 1));
    }
  }

  container.append(metrics, topColors, remaps, background);
}
