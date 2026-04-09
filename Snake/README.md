# Snake Game

一个使用原生 `HTML + CSS + JavaScript` 实现的经典贪吃蛇小游戏，无第三方依赖、无构建工具，适合在本地直接打开运行。

## 1. 如何启动

### 方式 A：本地静态服务（推荐）
在 macOS + VS Code 终端中执行：

```bash
cd /Users/liwenzhong/Desktop/Working/VSCode/Snake
python3 -m http.server 8765
```

然后在浏览器访问：

```text
http://127.0.0.1:8765/index.html
```

### 方式 B：直接双击打开
也可以直接打开 `index.html`，但推荐方式 A，行为更接近真实 Web 环境。

## 2. 项目结构

```text
Snake/
├── assets/
│   ├── snake-head.svg   # 蛇头贴图
│   ├── snake-body.svg   # 蛇身贴图
│   ├── food.svg         # 食物贴图
│   ├── bg-meadow.svg    # 草地主题背景贴图
│   ├── bg-midnight.svg  # 夜色主题背景贴图
│   └── bg-sunset.svg    # 日落主题背景贴图
├── index.html           # 页面结构：标题、分数/最高分、状态、控件、画布
├── style.css            # 页面布局与主题样式（含背景贴图主题）
├── game.js              # 游戏逻辑（移动、碰撞、计分、高分持久化、暂停、难度、贴图、音效开关）
├── README.md
└── Memory.md
```

## 3. 交互说明

- 方向键或 `WASD`：控制蛇移动
- `P` 键 或 `Pause/Continue` 按钮：暂停或继续当前局（游戏结束后不可继续）
- `Difficulty` 下拉框：切换 `Easy / Medium / Hard`，实时改变移动速度
- `Theme` 下拉框：切换 `Meadow / Midnight / Sunset` 背景贴图主题
- `Sound: On/Off` 按钮：开启/关闭音效
- 音效触发（开启音效时）：
  - 吃到食物
  - 暂停/继续
  - Game Over
- 最高分：
  - 页面显示 `Best`
  - 使用 `localStorage` 自动持久化，刷新页面后保留
- 游戏规则：
  - 吃到食物后，蛇身增长，分数 +1
  - 撞墙或撞到自己，游戏结束并显示 `Game Over`
- `Restart` 按钮：重置当前对局并重新开始（不清空最高分）

## 4. 设计思路（可 Review）

### 4.1 技术选型
- 使用 `canvas` 进行网格渲染，避免大量 DOM 节点更新。
- 使用固定时间步长（`setInterval`）驱动更新，保证移动节奏稳定。
- 使用本地 SVG 贴图渲染蛇和食物，提供比纯色块更清晰的视觉反馈。
- 使用本地 SVG 背景贴图 + CSS 变量切换主题。
- 使用 Web Audio API 生成轻量音效（无需额外音频文件）。

### 4.2 状态建模
`game.js` 维护以下核心状态：
- `snake`：蛇身数组，`snake[0]` 为蛇头
- `direction` / `nextDirection`：当前方向与下一帧方向
- `food`：食物坐标
- `score`：当前分数
- `highScore`：最高分（持久化）
- `isGameOver` / `isPaused`：结束与暂停状态
- `tickMs` / `timerId`：难度对应的更新速度与定时器
- `sprites`：贴图资源加载状态
- `audioContext` / `soundEnabled`：音频上下文与音效开关状态

### 4.3 持久化策略
使用 `localStorage` 保存：
- `snake.highScore`
- `snake.soundEnabled`
- `snake.theme`

并通过 `readStorage` / `writeStorage` 封装读写（异常时降级，不影响游戏可玩性）。

### 4.4 主循环
每一帧执行 `update()`：
1. 若 `isGameOver` 或 `isPaused`，直接返回
2. 应用 `nextDirection`
3. 计算蛇头下一格位置
4. 判定撞墙
5. 判定撞自己（按是否吃到食物区分检查范围，避免尾巴移动误判）
6. 蛇头入队
7. 吃到食物则加分、更新最高分、重生食物并播放音效，否则弹出尾巴
8. `draw()` 重绘

### 4.5 渲染策略（贴图）
- `loadSprite()` 异步加载本地 SVG 贴图。
- `drawSpriteCell()` 优先使用贴图，加载失败时回退纯色块。
- 蛇头/蛇身/食物分别使用不同贴图。

### 4.6 主题切换（背景贴图）
- 通过 `body[data-theme="..."]` 切换主题变量。
- 每个主题绑定自己的背景贴图：
  - `meadow` -> `assets/bg-meadow.svg`
  - `midnight` -> `assets/bg-midnight.svg`
  - `sunset` -> `assets/bg-sunset.svg`
- 主题选择会持久化，刷新后自动恢复。

### 4.7 音效机制与开关
- 音效由 `AudioContext` + `OscillatorNode` + `GainNode` 合成。
- `soundEnabled` 为统一开关，关闭后所有音效函数直接返回。
- `unlockAudio()` 在用户交互后尝试 `resume()`，兼容浏览器自动播放限制。

### 4.8 输入控制
- 支持方向键与 `W/A/S/D`
- 支持 `P` 快速暂停/继续
- 阻止默认滚动（`preventDefault`）
- 禁止 180° 反向掉头
- 对 `P` 长按重复触发做抑制（忽略 `event.repeat`）

### 4.9 重开机制
`resetGame()` 统一重置：
- 蛇位置与初始方向
- 分数显示
- Game Over 状态
- 暂停状态与按钮文案
- 食物重生与首帧绘制

## 5. Review 建议关注点

1. 最高分在刷新后是否正确恢复。
2. 音效开关在刷新后是否保持用户设置。
3. 主题切换是否即时生效、刷新后是否恢复。
4. 主题变化后对文字/控件可读性是否保持。
5. 贴图加载失败时纯色回退是否可用。
6. 音频不支持或未解锁时是否静默降级。
7. 碰撞判定（尤其尾巴移动场景）是否无回归。
8. 暂停/难度切换与重开逻辑是否互不干扰。

## 6. 可选扩展（后续）

- 增加“重置最高分”按钮
- 增加音量滑块（而非仅开关）
- 增加更多主题包（贴图+配色）

