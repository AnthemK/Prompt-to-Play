import {
  buildPatternFromPixels,
  normalizeTargetSize
} from "./pattern-core.js?v=20260505-7";
import {
  detectContentBoundsFromPixels,
  getCornerAverage,
  sampleGridFromPixels
} from "./sampling-core.js?v=20260505-7";

function analyzeImageContent(image) {
  const maxSampleEdge = 512;
  const sampleScale = Math.min(1, maxSampleEdge / Math.max(image.width, image.height));
  const sampleWidth = Math.max(1, Math.round(image.width * sampleScale));
  const sampleHeight = Math.max(1, Math.round(image.height * sampleScale));
  const sampleCanvas = document.createElement("canvas");
  sampleCanvas.width = sampleWidth;
  sampleCanvas.height = sampleHeight;
  const sampleContext = sampleCanvas.getContext("2d", { willReadFrequently: true });

  sampleContext.fillStyle = "#ffffff";
  sampleContext.fillRect(0, 0, sampleWidth, sampleHeight);
  sampleContext.drawImage(image, 0, 0, sampleWidth, sampleHeight);

  const imageData = sampleContext.getImageData(0, 0, sampleWidth, sampleHeight).data;
  const cornerSize = Math.max(
    2,
    Math.min(12, Math.floor(Math.min(sampleWidth, sampleHeight) * 0.06))
  );
  const background = getCornerAverage(imageData, sampleWidth, sampleHeight, cornerSize);

  const sampleBounds = detectContentBoundsFromPixels({
    imageData,
    width: sampleWidth,
    height: sampleHeight,
    background
  });

  if (sampleBounds.left === 0 && sampleBounds.top === 0 &&
    sampleBounds.width === sampleWidth && sampleBounds.height === sampleHeight) {
    return {
      background,
      bounds: {
        x: 0,
        y: 0,
        width: image.width,
        height: image.height
      }
    };
  }

  const scaleX = image.width / sampleWidth;
  const scaleY = image.height / sampleHeight;

  const sourceX = Math.max(0, Math.floor(sampleBounds.left * scaleX));
  const sourceY = Math.max(0, Math.floor(sampleBounds.top * scaleY));
  const sourceMaxX = Math.min(image.width, Math.ceil((sampleBounds.left + sampleBounds.width) * scaleX));
  const sourceMaxY = Math.min(image.height, Math.ceil((sampleBounds.top + sampleBounds.height) * scaleY));

  return {
    background,
    bounds: {
      x: sourceX,
      y: sourceY,
      width: Math.max(1, sourceMaxX - sourceX),
      height: Math.max(1, sourceMaxY - sourceY)
    }
  };
}

export function getContentBoundsForImage(image) {
  return analyzeImageContent(image).bounds;
}

function drawFittedImage(context, image, width, height, cropBounds) {
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
}

function sampleImageToGrid(image, cropBounds, background, targetWidth, targetHeight) {
  const cropCanvas = document.createElement("canvas");
  cropCanvas.width = cropBounds.width;
  cropCanvas.height = cropBounds.height;
  const cropContext = cropCanvas.getContext("2d", { willReadFrequently: true });

  cropContext.fillStyle = "#ffffff";
  cropContext.fillRect(0, 0, cropBounds.width, cropBounds.height);
  cropContext.drawImage(
    image,
    cropBounds.x,
    cropBounds.y,
    cropBounds.width,
    cropBounds.height,
    0,
    0,
    cropBounds.width,
    cropBounds.height
  );

  const sourceData = cropContext.getImageData(0, 0, cropBounds.width, cropBounds.height).data;
  return sampleGridFromPixels({
    imageData: sourceData,
    width: cropBounds.width,
    height: cropBounds.height,
    targetWidth,
    targetHeight,
    background
  });
}

export function convertImageToPattern({
  image,
  palette,
  targetWidth,
  targetHeight,
  optimization
}) {
  const { width, height } = normalizeTargetSize({ targetWidth, targetHeight });
  const analysis = analyzeImageContent(image);
  const pixelData = sampleImageToGrid(
    image,
    analysis.bounds,
    analysis.background,
    width,
    height
  );

  return buildPatternFromPixels({
    pixelData,
    targetWidth: width,
    targetHeight: height,
    palette,
    sourceWidth: image.width,
    sourceHeight: image.height,
    sourceBackgroundRgb: analysis.background,
    fitMode: "content-trim-direct-sample",
    optimization
  });
}

export { drawFittedImage };
