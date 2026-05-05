function assert(value, message) {
  if (!value) {
    throw new Error(message);
  }
}

// The UI should only speak to processing adapters through this normalized
// request shape. That keeps browser and future Python implementations aligned.
export function validateProcessingRequest(request) {
  assert(request && typeof request === "object", "Processing request is required.");
  assert(request.source && request.source.image, "Processing request must include a source image.");
  assert(request.palette && request.palette.colors, "Processing request must include a loaded palette.");
  assert(request.target && request.target.width && request.target.height, "Processing request must include target dimensions.");
  assert(request.optimization, "Processing request must include optimization settings.");
}

export function createProcessingRequest({
  image,
  palette,
  targetWidth,
  targetHeight,
  optimization
}) {
  return {
    source: { image },
    palette,
    target: {
      width: targetWidth,
      height: targetHeight
    },
    optimization
  };
}

export function createProcessingResult({
  conversion,
  cropBounds
}) {
  return {
    conversion,
    cropBounds
  };
}
