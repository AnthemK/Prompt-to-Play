import {
  convertImageToPattern,
  getContentBoundsForImage
} from "./convert.js?v=20260505-8";
import {
  createProcessingResult,
  validateProcessingRequest
} from "./processing-contract.js?v=20260505-9";

// Browser adapter: uses canvas-based local image processing while presenting a
// stable shape that a future Python-backed adapter can also implement.
export function createBrowserProcessingAdapter() {
  return {
    id: "browser-canvas",
    analyzeSource(image) {
      return {
        cropBounds: getContentBoundsForImage(image)
      };
    },
    buildPattern(request) {
      validateProcessingRequest(request);
      const cropBounds = getContentBoundsForImage(request.source.image);
      const conversion = convertImageToPattern({
        image: request.source.image,
        palette: request.palette,
        targetWidth: request.target.width,
        targetHeight: request.target.height,
        optimization: request.optimization
      });

      return createProcessingResult({
        conversion,
        cropBounds
      });
    }
  };
}
