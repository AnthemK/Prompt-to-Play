import { createBrowserProcessingAdapter } from "./browser-processing-adapter.js?v=20260505-9";
import {
  renderDiagnostics,
  resetDiagnostics
} from "./diagnostics.js?v=20260505-9";
import {
  exportCanvasAsPng,
  exportOverviewPng,
  exportMaterialsCsv,
  getGridFilename,
  getOverviewFilename,
  getPreviewFilename
} from "./export.js?v=20260505-9";
import {
  applyOptimizationPreset,
  populateOptimizationPresets,
  populatePalettes,
  readOptimizationOptions,
  renderOptimizationSummary,
  renderPaletteDetails,
  syncPresetFromInputs
} from "./controls-view.js?v=20260505-8";
import { loadPaletteById } from "./palette.js?v=20260505-8";
import { createProcessingRequest } from "./processing-contract.js?v=20260505-9";
import {
  renderBeadPreview,
  renderBuildGrid,
  renderComparisonSummary,
  renderMaterialsTable,
  renderSourcePreview
} from "./render.js?v=20260505-8";

const processingAdapter = createBrowserProcessingAdapter();

const elements = {
  form: document.querySelector("#controls-form"),
  imageInput: document.querySelector("#image-input"),
  widthInput: document.querySelector("#width-input"),
  heightInput: document.querySelector("#height-input"),
  paletteSelect: document.querySelector("#palette-select"),
  paletteName: document.querySelector("#palette-name"),
  paletteMeta: document.querySelector("#palette-meta"),
  paletteBadge: document.querySelector("#palette-badge"),
  paletteBestFor: document.querySelector("#palette-best-for"),
  paletteDescription: document.querySelector("#palette-description"),
  paletteTradeoff: document.querySelector("#palette-tradeoff"),
  paletteNotes: document.querySelector("#palette-notes"),
  optimizationPresetSelect: document.querySelector("#optimization-preset-select"),
  maxColorsInput: document.querySelector("#max-colors-input"),
  maxColorsNote: document.querySelector("#max-colors-note"),
  cleanupPassesInput: document.querySelector("#cleanup-passes-input"),
  optimizationSummary: document.querySelector("#optimization-summary"),
  showCodesInput: document.querySelector("#show-codes-input"),
  removeBackgroundInput: document.querySelector("#remove-background-input"),
  showCutReferenceInput: document.querySelector("#show-cut-reference-input"),
  generateButton: document.querySelector("#generate-button"),
  exportPreviewButton: document.querySelector("#export-preview-button"),
  exportGridButton: document.querySelector("#export-grid-button"),
  exportSheetButton: document.querySelector("#export-sheet-button"),
  exportCsvButton: document.querySelector("#export-csv-button"),
  exportPresetSelect: document.querySelector("#export-preset-select"),
  statusMessage: document.querySelector("#status-message"),
  metaSummary: document.querySelector("#meta-summary"),
  materialsSummary: document.querySelector("#materials-summary"),
  sourceCanvas: document.querySelector("#source-canvas"),
  rawPreviewCanvas: document.querySelector("#raw-preview-canvas"),
  previewCanvas: document.querySelector("#preview-canvas"),
  gridCanvas: document.querySelector("#grid-canvas"),
  materialsBody: document.querySelector("#materials-body"),
  comparisonSummary: document.querySelector("#comparison-summary"),
  diagnosticsPanel: document.querySelector("#diagnostics-panel")
};

const state = {
  image: null,
  conversion: null,
  sourceName: "Bead Pattern",
  cropBounds: null,
  busy: false
};

function setStatus(message) {
  elements.statusMessage.textContent = message;
}

function clearCanvas(canvas) {
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, canvas.width, canvas.height);
}

function setExportEnabled(enabled) {
  elements.exportPreviewButton.disabled = !enabled;
  elements.exportGridButton.disabled = !enabled;
  elements.exportSheetButton.disabled = !enabled;
  elements.exportCsvButton.disabled = !enabled;
}

function setBusy(isBusy, message = null) {
  // V1 keeps a simple global busy gate so users cannot accidentally stack
  // multiple generate/export actions on top of the same in-memory state.
  state.busy = isBusy;
  elements.generateButton.disabled = isBusy;
  elements.generateButton.textContent = isBusy ? "Generating..." : "Generate pattern";
  elements.imageInput.disabled = isBusy;
  elements.paletteSelect.disabled = isBusy;
  elements.widthInput.disabled = isBusy;
  elements.heightInput.disabled = isBusy;
  elements.optimizationPresetSelect.disabled = isBusy;
  elements.maxColorsInput.disabled = isBusy;
  elements.cleanupPassesInput.disabled = isBusy;
  elements.showCodesInput.disabled = isBusy;
  elements.removeBackgroundInput.disabled = isBusy;
  elements.showCutReferenceInput.disabled = isBusy;
  elements.exportPresetSelect.disabled = isBusy;
  if (message) {
    setStatus(message);
  }
}

function deriveProjectTitle(filename) {
  const base = filename.replace(/\.[^.]+$/, "");
  const normalized = base.replace(/[_-]+/g, " ").trim();
  return normalized || "Bead Pattern";
}

function loadImageFromFile(file) {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const image = new Image();

    image.onload = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(image);
    };

    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Failed to load the selected image."));
    };

    image.src = objectUrl;
  });
}

function rerenderSourcePreviewIfNeeded() {
  if (!state.image) {
    return;
  }

  renderSourcePreview(
    elements.sourceCanvas,
    state.image,
    state.cropBounds,
    {
      showCutReference: elements.showCutReferenceInput.checked,
      conversion: state.conversion
    }
  );
}

async function handleImageSelection() {
  const [file] = elements.imageInput.files;
  if (!file) {
    state.image = null;
    state.conversion = null;
    state.cropBounds = null;
    setStatus("Choose an image to begin.");
    return;
  }

  if (file.type && !file.type.startsWith("image/")) {
    state.image = null;
    state.conversion = null;
    state.cropBounds = null;
    setStatus("The selected file is not an image. Choose a PNG, JPG, or other browser-supported image.");
    return;
  }

  setStatus(`Loading ${file.name}...`);

  try {
    state.image = await loadImageFromFile(file);
    state.sourceName = deriveProjectTitle(file.name);
    state.conversion = null;
    state.cropBounds = null;
    rerenderSourcePreviewIfNeeded();
    setStatus(`Loaded ${file.name}. Ready to generate the bead pattern.`);
  } catch (error) {
    state.image = null;
    state.conversion = null;
    state.cropBounds = null;
    setStatus(error.message);
  }
}

function updateSummaries(conversion) {
  elements.metaSummary.textContent =
    `${conversion.target.width} x ${conversion.target.height} grid, ` +
    `${conversion.totalBeads} beads, ${conversion.counts.length} colors used.`;
  elements.materialsSummary.textContent =
    `${conversion.counts.length} colors, ${conversion.totalBeads} placed beads, ` +
    `${conversion.optimization.cleanupPasses} cleanup passes, ` +
    `${conversion.optimization.presetLabel}.`;
  if (conversion.background.removed) {
    elements.materialsSummary.textContent +=
      ` Removed ${conversion.background.removedCells} outer background cells.`;
  }
  renderComparisonSummary(elements.comparisonSummary, conversion);
}

function resetOutputs() {
  // Clear all derived views when the source image changes or a run is reset so
  // stale previews and exports never appear to belong to the next image.
  state.conversion = null;
  state.cropBounds = null;
  elements.metaSummary.textContent = "No pattern generated yet.";
  elements.materialsSummary.textContent = "No materials counted yet.";
  elements.comparisonSummary.textContent = "No optimization changes to compare yet.";
  elements.materialsBody.innerHTML =
    '<tr><td colspan="4" class="placeholder-cell">Generate a pattern to see the material list.</td></tr>';
  resetDiagnostics(elements.diagnosticsPanel);
  clearCanvas(elements.rawPreviewCanvas);
  clearCanvas(elements.previewCanvas);
  clearCanvas(elements.gridCanvas);
  setExportEnabled(false);
}

async function generatePattern() {
  if (state.busy) {
    return;
  }

  if (!state.image) {
    setStatus("Select a source image before generating a pattern.");
    return;
  }

  setBusy(true, "Generating bead pattern...");

  try {
    const palette = await loadPaletteById(elements.paletteSelect.value);
    const request = createProcessingRequest({
      image: state.image,
      palette,
      targetWidth: elements.widthInput.value,
      targetHeight: elements.heightInput.value,
      optimization: readOptimizationOptions(elements)
    });
    const result = processingAdapter.buildPattern(request);

    state.conversion = result.conversion;
    state.cropBounds = result.cropBounds;

    rerenderSourcePreviewIfNeeded();
    renderBeadPreview(elements.rawPreviewCanvas, {
      ...result.conversion,
      grid: result.conversion.raw.grid
    });
    renderBeadPreview(elements.previewCanvas, result.conversion);
    renderBuildGrid(elements.gridCanvas, result.conversion, {
      showCodes: elements.showCodesInput.checked
    });
    renderMaterialsTable(elements.materialsBody, result.conversion);
    renderDiagnostics(elements.diagnosticsPanel, result.conversion);
    updateSummaries(result.conversion);
    setExportEnabled(true);

    setStatus(
      `Pattern generated with ${result.conversion.counts.length} colors and ${result.conversion.totalBeads} total beads.`
    );
  } catch (error) {
    setExportEnabled(false);
    resetDiagnostics(elements.diagnosticsPanel);
    setStatus(
      error instanceof Error
        ? error.message
        : "Failed to generate the bead pattern. Check the selected image and settings, then try again."
    );
  } finally {
    setBusy(false);
  }
}

function rerenderGridIfNeeded() {
  if (!state.conversion) {
    return;
  }

  renderBuildGrid(elements.gridCanvas, state.conversion, {
    showCodes: elements.showCodesInput.checked
  });
}

function installEventHandlers() {
  elements.imageInput.addEventListener("change", async () => {
    resetOutputs();
    await handleImageSelection();
  });

  elements.form.addEventListener("submit", (event) => {
    event.preventDefault();
    void generatePattern();
  });

  elements.showCodesInput.addEventListener("change", () => {
    rerenderGridIfNeeded();
  });

  elements.paletteSelect.addEventListener("change", () => {
    renderPaletteDetails(elements);
  });

  elements.optimizationPresetSelect.addEventListener("change", () => {
    applyOptimizationPreset(elements, elements.optimizationPresetSelect.value);
  });

  elements.maxColorsInput.addEventListener("input", () => {
    syncPresetFromInputs(elements);
    renderOptimizationSummary(elements);
  });

  elements.cleanupPassesInput.addEventListener("input", () => {
    syncPresetFromInputs(elements);
    renderOptimizationSummary(elements);
  });

  elements.removeBackgroundInput.addEventListener("change", () => {
    renderOptimizationSummary(elements);
  });

  elements.showCutReferenceInput.addEventListener("change", () => {
    rerenderSourcePreviewIfNeeded();
  });

  elements.exportPreviewButton.addEventListener("click", () => {
    if (!state.conversion || state.busy) {
      return;
    }

    exportCanvasAsPng(
      elements.previewCanvas,
      getPreviewFilename(state.conversion)
    );
    setStatus("Preview PNG exported.");
  });

  elements.exportGridButton.addEventListener("click", () => {
    if (!state.conversion || state.busy) {
      return;
    }

    exportCanvasAsPng(
      elements.gridCanvas,
      getGridFilename(state.conversion)
    );
    setStatus("Pure grid PNG exported.");
  });

  elements.exportSheetButton.addEventListener("click", () => {
    if (!state.conversion || state.busy) {
      return;
    }

    exportOverviewPng({
      conversion: state.conversion,
      gridCanvas: elements.gridCanvas,
      previewCanvas: elements.previewCanvas,
      title: state.sourceName,
      preset: elements.exportPresetSelect.value
    });
    setStatus("Sheet PNG exported.");
  });

  elements.exportCsvButton.addEventListener("click", () => {
    if (!state.conversion || state.busy) {
      return;
    }

    exportMaterialsCsv(state.conversion);
    setStatus("Materials CSV exported.");
  });
}

function bootstrap() {
  populatePalettes(elements.paletteSelect);
  populateOptimizationPresets(elements.optimizationPresetSelect);
  renderPaletteDetails(elements);
  applyOptimizationPreset(elements, "balanced");
  installEventHandlers();
  resetOutputs();
  setExportEnabled(false);
  clearCanvas(elements.sourceCanvas);
}

bootstrap();
