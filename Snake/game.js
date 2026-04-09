const canvas = document.getElementById("game-canvas");
const ctx = canvas.getContext("2d");
const scoreEl = document.getElementById("score");
const bestScoreEl = document.getElementById("best-score");
const gameStateEl = document.getElementById("game-state");
const gameOverEl = document.getElementById("game-over");
const difficultyEl = document.getElementById("difficulty");
const themeSelectEl = document.getElementById("theme-select");
const soundBtn = document.getElementById("sound-btn");
const pauseBtn = document.getElementById("pause-btn");
const restartBtn = document.getElementById("restart-btn");

const GRID_SIZE = 20;
const CELL_SIZE = canvas.width / GRID_SIZE;
const DIFFICULTY_TICK = {
  easy: 160,
  medium: 120,
  hard: 80,
};
const DIRECTION_KEY_MAP = {
  ArrowUp: { x: 0, y: -1 },
  ArrowDown: { x: 0, y: 1 },
  ArrowLeft: { x: -1, y: 0 },
  ArrowRight: { x: 1, y: 0 },
  w: { x: 0, y: -1 },
  s: { x: 0, y: 1 },
  a: { x: -1, y: 0 },
  d: { x: 1, y: 0 },
};
const SPRITE_PATHS = {
  head: "assets/snake-head.svg",
  body: "assets/snake-body.svg",
  food: "assets/food.svg",
};
const THEMES = ["meadow", "midnight", "sunset"];
const STORAGE_KEYS = {
  highScore: "snake.highScore",
  soundEnabled: "snake.soundEnabled",
  theme: "snake.theme",
};

let snake;
let direction;
let nextDirection;
let food;
let score;
let highScore;
let isGameOver;
let isPaused;
let tickMs;
let timerId;
let sprites;
let audioContext;
let soundEnabled;

function readStorage(key) {
  if (typeof localStorage === "undefined") {
    return null;
  }

  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key, value) {
  if (typeof localStorage === "undefined") {
    return;
  }

  try {
    localStorage.setItem(key, value);
  } catch {
    // Ignore write failures to keep game playable.
  }
}

function loadSprite(src) {
  const sprite = {
    image: new Image(),
    loaded: false,
  };

  sprite.image.addEventListener("load", () => {
    sprite.loaded = true;
    draw();
  });

  sprite.image.addEventListener("error", () => {
    sprite.loaded = false;
  });

  sprite.image.src = src;
  return sprite;
}

function initSprites() {
  sprites = {
    head: loadSprite(SPRITE_PATHS.head),
    body: loadSprite(SPRITE_PATHS.body),
    food: loadSprite(SPRITE_PATHS.food),
  };
}

function getAudioContext() {
  const AudioCtor = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtor) {
    return null;
  }

  if (!audioContext) {
    audioContext = new AudioCtor();
  }

  return audioContext;
}

function unlockAudio() {
  if (!soundEnabled) {
    return;
  }

  const audio = getAudioContext();
  if (!audio) {
    return;
  }

  if (audio.state === "suspended") {
    audio.resume().catch(() => {
      // Ignore resume failures, game can continue silently.
    });
  }
}

function playTone(frequency, durationMs, options = {}) {
  if (!soundEnabled) {
    return;
  }

  const audio = getAudioContext();
  if (!audio || audio.state !== "running") {
    return;
  }

  const type = options.type || "square";
  const volume = options.volume ?? 0.06;
  const delaySeconds = options.delaySeconds ?? 0;
  const startAt = audio.currentTime + delaySeconds;
  const stopAt = startAt + durationMs / 1000;

  const oscillator = audio.createOscillator();
  const gainNode = audio.createGain();

  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, startAt);

  gainNode.gain.setValueAtTime(0, startAt);
  gainNode.gain.linearRampToValueAtTime(volume, startAt + 0.01);
  gainNode.gain.linearRampToValueAtTime(0, stopAt);

  oscillator.connect(gainNode);
  gainNode.connect(audio.destination);

  oscillator.onended = () => {
    oscillator.disconnect();
    gainNode.disconnect();
  };

  oscillator.start(startAt);
  oscillator.stop(stopAt);
}

function playEatSound() {
  playTone(680, 70, { type: "triangle", volume: 0.07 });
  playTone(860, 90, { type: "triangle", volume: 0.06, delaySeconds: 0.05 });
}

function playPauseSound(paused) {
  if (paused) {
    playTone(360, 80, { type: "sine", volume: 0.06 });
    playTone(280, 100, { type: "sine", volume: 0.05, delaySeconds: 0.06 });
    return;
  }

  playTone(320, 70, { type: "sine", volume: 0.06 });
  playTone(460, 90, { type: "sine", volume: 0.05, delaySeconds: 0.05 });
}

function playGameOverSound() {
  playTone(280, 120, { type: "sawtooth", volume: 0.07 });
  playTone(220, 180, { type: "sawtooth", volume: 0.06, delaySeconds: 0.09 });
}

function updateSoundButton() {
  soundBtn.textContent = soundEnabled ? "Sound: On" : "Sound: Off";
  soundBtn.classList.toggle("muted", !soundEnabled);
}

function updateBestScoreLabel() {
  bestScoreEl.textContent = String(highScore);
}

function updateGameStateLabel() {
  if (isGameOver) {
    gameStateEl.textContent = "Stopped";
    gameStateEl.classList.remove("paused");
    return;
  }

  if (isPaused) {
    gameStateEl.textContent = "Paused";
    gameStateEl.classList.add("paused");
    return;
  }

  gameStateEl.textContent = "Running";
  gameStateEl.classList.remove("paused");
}

function applyTheme(themeName) {
  const selectedTheme = THEMES.includes(themeName) ? themeName : "meadow";
  document.body.dataset.theme = selectedTheme;
  themeSelectEl.value = selectedTheme;
  writeStorage(STORAGE_KEYS.theme, selectedTheme);
}

function initPersistentSettings() {
  const storedBest = Number.parseInt(readStorage(STORAGE_KEYS.highScore) || "0", 10);
  highScore = Number.isFinite(storedBest) && storedBest >= 0 ? storedBest : 0;
  updateBestScoreLabel();

  const storedSound = readStorage(STORAGE_KEYS.soundEnabled);
  soundEnabled = storedSound !== "false";
  updateSoundButton();

  const storedTheme = readStorage(STORAGE_KEYS.theme);
  applyTheme(storedTheme || themeSelectEl.value);
}

function restartLoop() {
  if (timerId !== undefined) {
    clearInterval(timerId);
  }

  timerId = setInterval(update, tickMs);
}

function resetGame() {
  snake = [{ x: 10, y: 10 }];
  direction = { x: 1, y: 0 };
  nextDirection = { x: 1, y: 0 };
  score = 0;
  isGameOver = false;
  isPaused = false;
  food = spawnFood();

  scoreEl.textContent = String(score);
  pauseBtn.textContent = "Pause";
  gameOverEl.classList.remove("show");
  updateGameStateLabel();
  draw();
}

function spawnFood() {
  let candidate;

  do {
    candidate = {
      x: Math.floor(Math.random() * GRID_SIZE),
      y: Math.floor(Math.random() * GRID_SIZE),
    };
  } while (snake.some((segment) => segment.x === candidate.x && segment.y === candidate.y));

  return candidate;
}

function isOutOfBounds(point) {
  return point.x < 0 || point.x >= GRID_SIZE || point.y < 0 || point.y >= GRID_SIZE;
}

function updateHighScoreIfNeeded() {
  if (score <= highScore) {
    return;
  }

  highScore = score;
  updateBestScoreLabel();
  writeStorage(STORAGE_KEYS.highScore, String(highScore));
}

function endGame() {
  isGameOver = true;
  isPaused = false;
  pauseBtn.textContent = "Pause";
  updateGameStateLabel();
  gameOverEl.classList.add("show");
  playGameOverSound();
}

function update() {
  if (isGameOver || isPaused) {
    return;
  }

  direction = nextDirection;

  const head = {
    x: snake[0].x + direction.x,
    y: snake[0].y + direction.y,
  };

  if (isOutOfBounds(head)) {
    endGame();
    draw();
    return;
  }

  const ateFood = head.x === food.x && head.y === food.y;
  const bodyToCheck = ateFood ? snake : snake.slice(0, -1);
  const collidedWithBody = bodyToCheck.some(
    (segment) => segment.x === head.x && segment.y === head.y
  );

  if (collidedWithBody) {
    endGame();
    draw();
    return;
  }

  snake.unshift(head);

  if (ateFood) {
    score += 1;
    scoreEl.textContent = String(score);
    updateHighScoreIfNeeded();
    food = spawnFood();
    playEatSound();
  } else {
    snake.pop();
  }

  draw();
}

function drawCell(x, y, color) {
  ctx.fillStyle = color;
  ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
}

function drawSpriteCell(sprite, x, y, fallbackColor) {
  if (sprite && sprite.loaded) {
    ctx.drawImage(sprite.image, x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
    return;
  }

  drawCell(x, y, fallbackColor);
}

function drawGrid() {
  ctx.strokeStyle = "rgba(47, 72, 88, 0.12)";
  ctx.lineWidth = 1;

  for (let i = 0; i <= GRID_SIZE; i += 1) {
    const p = i * CELL_SIZE;

    ctx.beginPath();
    ctx.moveTo(p, 0);
    ctx.lineTo(p, canvas.height);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(0, p);
    ctx.lineTo(canvas.width, p);
    ctx.stroke();
  }
}

function draw() {
  if (!snake || !food) {
    return;
  }

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  drawGrid();
  drawSpriteCell(sprites.food, food.x, food.y, "#e74c3c");

  snake.forEach((segment, index) => {
    const sprite = index === 0 ? sprites.head : sprites.body;
    const fallback = index === 0 ? "#1f6a3d" : "#2d8a4f";
    drawSpriteCell(sprite, segment.x, segment.y, fallback);
  });
}

function canTurn(newDirection) {
  return !(newDirection.x === -direction.x && newDirection.y === -direction.y);
}

function handleKeydown(event) {
  const keyLower = event.key.toLowerCase();

  if (keyLower === "p") {
    if (isGameOver || event.repeat) {
      return;
    }

    unlockAudio();
    event.preventDefault();
    togglePause();
    return;
  }

  const requested = DIRECTION_KEY_MAP[event.key] || DIRECTION_KEY_MAP[keyLower];
  if (!requested || isGameOver || isPaused) {
    return;
  }

  unlockAudio();
  event.preventDefault();

  if (canTurn(requested)) {
    nextDirection = requested;
  }
}

function setDifficulty(level) {
  tickMs = DIFFICULTY_TICK[level] || DIFFICULTY_TICK.medium;
  restartLoop();
}

function togglePause() {
  if (isGameOver) {
    return;
  }

  isPaused = !isPaused;
  pauseBtn.textContent = isPaused ? "Continue" : "Pause";
  updateGameStateLabel();
  playPauseSound(isPaused);
}

function toggleSound() {
  soundEnabled = !soundEnabled;
  updateSoundButton();
  writeStorage(STORAGE_KEYS.soundEnabled, String(soundEnabled));

  if (soundEnabled) {
    unlockAudio();
    playTone(500, 90, { type: "triangle", volume: 0.05 });
  }
}

window.addEventListener("keydown", handleKeydown, { passive: false });
pauseBtn.addEventListener("click", () => {
  unlockAudio();
  togglePause();
});
soundBtn.addEventListener("click", () => {
  toggleSound();
});
restartBtn.addEventListener("click", () => {
  unlockAudio();
  resetGame();
});
difficultyEl.addEventListener("change", (event) => {
  setDifficulty(event.target.value);
});
themeSelectEl.addEventListener("change", (event) => {
  applyTheme(event.target.value);
});

initSprites();
initPersistentSettings();
tickMs = DIFFICULTY_TICK[difficultyEl.value] || DIFFICULTY_TICK.medium;
resetGame();
restartLoop();
