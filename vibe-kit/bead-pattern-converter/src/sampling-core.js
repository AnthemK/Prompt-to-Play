export const BACKGROUND_THRESHOLD = 18;
export const DOMINANT_BUCKET_STEP = 32;

function getChannelOffset(index, x, y, width, channelsPerPixel) {
  return (y * width + x) * channelsPerPixel + index;
}

export function getCornerAverage(imageData, width, height, sampleSize, channelsPerPixel = 4) {
  let red = 0;
  let green = 0;
  let blue = 0;
  let count = 0;

  const readPixel = (x, y) => {
    red += imageData[getChannelOffset(0, x, y, width, channelsPerPixel)];
    green += imageData[getChannelOffset(1, x, y, width, channelsPerPixel)];
    blue += imageData[getChannelOffset(2, x, y, width, channelsPerPixel)];
    count += 1;
  };

  for (let y = 0; y < sampleSize; y += 1) {
    for (let x = 0; x < sampleSize; x += 1) {
      readPixel(x, y);
      readPixel(width - 1 - x, y);
      readPixel(x, height - 1 - y);
      readPixel(width - 1 - x, height - 1 - y);
    }
  }

  return [red / count, green / count, blue / count];
}

export function colorDeltaFromBackground(red, green, blue, background) {
  const redDiff = red - background[0];
  const greenDiff = green - background[1];
  const blueDiff = blue - background[2];

  return Math.sqrt(
    (redDiff * redDiff) +
    (greenDiff * greenDiff) +
    (blueDiff * blueDiff)
  );
}

export function detectContentBoundsFromPixels({
  imageData,
  width,
  height,
  background,
  channelsPerPixel = 4,
  threshold = BACKGROUND_THRESHOLD,
  paddingRatio = 0.04,
  minPadding = 2
}) {
  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const red = imageData[getChannelOffset(0, x, y, width, channelsPerPixel)];
      const green = imageData[getChannelOffset(1, x, y, width, channelsPerPixel)];
      const blue = imageData[getChannelOffset(2, x, y, width, channelsPerPixel)];
      const colorDelta = colorDeltaFromBackground(red, green, blue, background);

      if (colorDelta < threshold) {
        continue;
      }

      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
    }
  }

  if (maxX < minX || maxY < minY) {
    return { left: 0, top: 0, width, height };
  }

  const paddingX = Math.max(minPadding, Math.round((maxX - minX + 1) * paddingRatio));
  const paddingY = Math.max(minPadding, Math.round((maxY - minY + 1) * paddingRatio));

  return {
    left: Math.max(0, minX - paddingX),
    top: Math.max(0, minY - paddingY),
    width: Math.min(width, maxX + paddingX + 1) - Math.max(0, minX - paddingX),
    height: Math.min(height, maxY + paddingY + 1) - Math.max(0, minY - paddingY)
  };
}

export function sampleGridFromPixels({
  imageData,
  width,
  height,
  targetWidth,
  targetHeight,
  background,
  channelsPerPixel = 4,
  threshold = BACKGROUND_THRESHOLD,
  bucketStep = DOMINANT_BUCKET_STEP,
  foregroundMinShare = 0.18,
  dominantBucketForegroundShare = 0.55,
  dominantBucketTotalShare = 0.28
}) {
  const pixelData = new Uint8ClampedArray(targetWidth * targetHeight * 4);

  for (let targetY = 0; targetY < targetHeight; targetY += 1) {
    const startY = Math.floor((targetY * height) / targetHeight);
    const endY = Math.max(startY + 1, Math.floor(((targetY + 1) * height) / targetHeight));

    for (let targetX = 0; targetX < targetWidth; targetX += 1) {
      const startX = Math.floor((targetX * width) / targetWidth);
      const endX = Math.max(startX + 1, Math.floor(((targetX + 1) * width) / targetWidth));
      let totalRed = 0;
      let totalGreen = 0;
      let totalBlue = 0;
      let totalCount = 0;
      let foregroundRed = 0;
      let foregroundGreen = 0;
      let foregroundBlue = 0;
      let foregroundCount = 0;
      const foregroundBuckets = new Map();

      for (let sourceY = startY; sourceY < endY; sourceY += 1) {
        for (let sourceX = startX; sourceX < endX; sourceX += 1) {
          const red = imageData[getChannelOffset(0, sourceX, sourceY, width, channelsPerPixel)];
          const green = imageData[getChannelOffset(1, sourceX, sourceY, width, channelsPerPixel)];
          const blue = imageData[getChannelOffset(2, sourceX, sourceY, width, channelsPerPixel)];
          totalRed += red;
          totalGreen += green;
          totalBlue += blue;
          totalCount += 1;

          const colorDelta = colorDeltaFromBackground(red, green, blue, background);
          if (colorDelta >= threshold) {
            foregroundRed += red;
            foregroundGreen += green;
            foregroundBlue += blue;
            foregroundCount += 1;

            const bucketKey = [
              Math.round(red / bucketStep),
              Math.round(green / bucketStep),
              Math.round(blue / bucketStep)
            ].join(":");
            const bucket = foregroundBuckets.get(bucketKey) ?? {
              red: 0,
              green: 0,
              blue: 0,
              count: 0
            };
            bucket.red += red;
            bucket.green += green;
            bucket.blue += blue;
            bucket.count += 1;
            foregroundBuckets.set(bucketKey, bucket);
          }
        }
      }

      const useForeground = foregroundCount > 0 && foregroundCount >= Math.ceil(totalCount * foregroundMinShare);
      let averageRed = totalRed / totalCount;
      let averageGreen = totalGreen / totalCount;
      let averageBlue = totalBlue / totalCount;

      if (useForeground) {
        const dominantBucket = [...foregroundBuckets.values()].sort(
          (left, right) => right.count - left.count
        )[0];
        const useDominantBucket =
          dominantBucket &&
          dominantBucket.count >= Math.max(2, Math.ceil(foregroundCount * dominantBucketForegroundShare)) &&
          dominantBucket.count >= Math.ceil(totalCount * dominantBucketTotalShare);

        if (useDominantBucket) {
          averageRed = dominantBucket.red / dominantBucket.count;
          averageGreen = dominantBucket.green / dominantBucket.count;
          averageBlue = dominantBucket.blue / dominantBucket.count;
        } else {
          averageRed = foregroundRed / foregroundCount;
          averageGreen = foregroundGreen / foregroundCount;
          averageBlue = foregroundBlue / foregroundCount;
        }
      }

      const outputIndex = (targetY * targetWidth + targetX) * 4;
      pixelData[outputIndex] = Math.round(averageRed);
      pixelData[outputIndex + 1] = Math.round(averageGreen);
      pixelData[outputIndex + 2] = Math.round(averageBlue);
      pixelData[outputIndex + 3] = 255;
    }
  }

  return pixelData;
}
