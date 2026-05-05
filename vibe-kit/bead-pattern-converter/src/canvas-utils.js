// Shared canvas helpers keep preview rendering and export rendering visually
// consistent, especially for wrapped text and card framing.
export function getContrastColor(hex) {
  const normalized = hex.replace("#", "");
  const value = Number.parseInt(normalized, 16);
  const red = (value >> 16) & 255;
  const green = (value >> 8) & 255;
  const blue = value & 255;
  const luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255;
  return luminance > 0.65 ? "#2a241f" : "#fffdf6";
}

export function drawRemovedCellMarker(context, x, y, size) {
  context.save();
  context.strokeStyle = "rgba(140, 123, 109, 0.28)";
  context.lineWidth = Math.max(1, size * 0.05);
  context.beginPath();
  context.moveTo(x + (size * 0.22), y + (size * 0.22));
  context.lineTo(x + (size * 0.78), y + (size * 0.78));
  context.moveTo(x + (size * 0.78), y + (size * 0.22));
  context.lineTo(x + (size * 0.22), y + (size * 0.78));
  context.stroke();
  context.restore();
}

export function drawRoundedRect(context, x, y, width, height, radius) {
  context.beginPath();
  context.moveTo(x + radius, y);
  context.lineTo(x + width - radius, y);
  context.quadraticCurveTo(x + width, y, x + width, y + radius);
  context.lineTo(x + width, y + height - radius);
  context.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  context.lineTo(x + radius, y + height);
  context.quadraticCurveTo(x, y + height, x, y + height - radius);
  context.lineTo(x, y + radius);
  context.quadraticCurveTo(x, y, x + radius, y);
  context.closePath();
}

export function drawCard(context, x, y, width, height) {
  drawRoundedRect(context, x, y, width, height, 18);
  context.fillStyle = "#fffdf9";
  context.strokeStyle = "#e7b9a8";
  context.lineWidth = 2;
  context.fill();
  context.stroke();
}

function breakLongWord(context, word, maxWidth) {
  const segments = [];
  let segment = "";

  for (const char of String(word)) {
    const testSegment = `${segment}${char}`;
    if (context.measureText(testSegment).width > maxWidth && segment) {
      segments.push(segment);
      segment = char;
    } else {
      segment = testSegment;
    }
  }

  if (segment) {
    segments.push(segment);
  }

  return segments;
}

export function drawWrappedText(context, text, x, y, maxWidth, lineHeight) {
  const words = String(text).split(/\s+/);
  let line = "";
  let cursorY = y;

  for (const word of words) {
    if (context.measureText(word).width > maxWidth) {
      const segments = breakLongWord(context, word, maxWidth);
      if (line) {
        context.fillText(line, x, cursorY);
        cursorY += lineHeight;
        line = "";
      }

      for (let index = 0; index < segments.length; index += 1) {
        const segment = segments[index];
        const isLast = index === segments.length - 1;
        if (isLast) {
          line = segment;
        } else {
          context.fillText(segment, x, cursorY);
          cursorY += lineHeight;
        }
      }
      continue;
    }

    const testLine = line ? `${line} ${word}` : word;
    if (context.measureText(testLine).width > maxWidth && line) {
      context.fillText(line, x, cursorY);
      line = word;
      cursorY += lineHeight;
    } else {
      line = testLine;
    }
  }

  if (line) {
    context.fillText(line, x, cursorY);
    cursorY += lineHeight;
  }

  return cursorY;
}

export function measureWrappedTextHeight(context, text, maxWidth, lineHeight) {
  const words = String(text).split(/\s+/);
  let line = "";
  let lines = 0;

  for (const word of words) {
    if (context.measureText(word).width > maxWidth) {
      if (line) {
        lines += 1;
        line = "";
      }
      lines += breakLongWord(context, word, maxWidth).length;
      continue;
    }

    const testLine = line ? `${line} ${word}` : word;
    if (context.measureText(testLine).width > maxWidth && line) {
      lines += 1;
      line = word;
    } else {
      line = testLine;
    }
  }

  if (line) {
    lines += 1;
  }

  return lines * lineHeight;
}

export function drawWrappedTextBlock(context, lines, x, y, maxWidth, lineHeight) {
  let cursorY = y;
  for (const line of lines) {
    cursorY = drawWrappedText(context, line, x, cursorY, maxWidth, lineHeight);
  }
  return cursorY;
}

export function drawCenteredWrappedTitle(context, text, centerX, y, maxWidth, lineHeight, maxLines) {
  const words = String(text).split(/\s+/).filter(Boolean);
  const lines = [];
  let line = "";

  for (const word of words) {
    const testLine = line ? `${line} ${word}` : word;
    if (context.measureText(testLine).width > maxWidth && line) {
      lines.push(line);
      line = word;
    } else {
      line = testLine;
    }
  }

  if (line) {
    lines.push(line);
  }

  const trimmedLines = lines.slice(0, maxLines);
  if (lines.length > maxLines) {
    const lastIndex = trimmedLines.length - 1;
    trimmedLines[lastIndex] = `${trimmedLines[lastIndex]}...`;
  }

  for (let index = 0; index < trimmedLines.length; index += 1) {
    context.fillText(trimmedLines[index], centerX, y + index * lineHeight);
  }

  return y + trimmedLines.length * lineHeight;
}
