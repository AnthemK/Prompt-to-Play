# Memory - Snake Project Handoff

本文档是该项目的长期记忆文件。目标：
- 即使对话上下文清空，阅读本文档后可完整恢复开发进度。
- 交接给另一个模型/开发者时，可快速上手并继续迭代。

## 1. 项目定位

- 项目名称：`Snake Game`
- 路径：`/Users/liwenzhong/Desktop/Working/VSCode/Snake`
- 技术栈：原生 `HTML + CSS + JavaScript`
- 约束：
  - 不使用第三方前端框架/构建工具/游戏引擎
  - 保持最小工程结构，便于本地直接运行

## 2. 当前文件清单（2026-04-08）

- `assets/snake-head.svg`
- `assets/snake-body.svg`
- `assets/food.svg`
- `assets/bg-meadow.svg`
- `assets/bg-midnight.svg`
- `assets/bg-sunset.svg`
- `index.html`
- `style.css`
- `game.js`
- `README.md`
- `Memory.md`

## 3. 当前功能状态（已完成）

### 3.1 基础玩法
- 固定网格移动（20x20）
- 随机食物生成（不与蛇重叠）
- 吃到食物后增长与计分
- 撞墙/撞自己结束
- Restart 重开

### 3.2 控制与状态
- 方向键 + `W/A/S/D` 控制
- `P` 键与按钮暂停/继续
- `P` 长按重复触发抑制（`event.repeat`）
- 难度切换（`easy/medium/hard`）即时生效
- 运行状态显示：`Running / Paused / Stopped`

### 3.3 贴图与主题
- 蛇头、蛇身、食物使用 SVG 贴图
- 背景主题切换：`meadow / midnight / sunset`
- 每个主题使用不同背景贴图与配色变量
- 贴图加载失败时自动回退纯色绘制

### 3.4 音效
- Web Audio 动态合成音效（无外部音频文件）
- 事件：吃食物、暂停/继续、Game Over
- 音效开关按钮：`Sound: On/Off`
- 音频能力缺失或未解锁时静默降级

### 3.5 持久化
使用 `localStorage` 保存并恢复：
- `snake.highScore`（最高分）
- `snake.soundEnabled`（音效开关）
- `snake.theme`（主题）

刷新页面后自动恢复以上状态。

## 4. 关键实现细节

### 4.1 当前关键变量（`game.js`）
- 游戏：`snake, direction, nextDirection, food, score, isGameOver, isPaused`
- 速度：`tickMs, timerId`
- 视觉：`sprites`
- 音频：`audioContext, soundEnabled`
- 持久化：`highScore`

### 4.2 核心函数
- `update()`：主循环推进逻辑
- `draw()`：画布渲染入口
- `drawSpriteCell()`：贴图优先 + 纯色回退
- `updateHighScoreIfNeeded()`：最高分更新并持久化
- `toggleSound()`：音效开关与持久化
- `applyTheme()`：主题应用与持久化
- `initPersistentSettings()`：启动时恢复用户偏好

### 4.3 已知关键修复（必须保留）
- 自撞误判修复：
  - 若本帧吃到食物，检测整条蛇身
  - 若本帧不吃食物，检测 `snake.slice(0, -1)`
- 目的：避免“头进入本帧将离开的尾巴格子”被误判为自撞。

### 4.4 输入与音频协作
- 用户按键/按钮交互时调用 `unlockAudio()`
- 音效关闭时不触发 `AudioContext` 播放
- 音效开启后首次交互会尝试恢复音频上下文

## 5. 样式与主题结构

### 5.1 `style.css`
- 使用 CSS 变量定义颜色与背景纹理
- `body[data-theme="..."]` 覆盖主题变量
- 背景由 `--halo` + `--texture` 叠加形成
- `#sound-btn.muted` 用于音效关闭视觉态

### 5.2 `index.html`
- 状态区：`Score`、`Best`、运行状态、`Game Over`
- 控件区：`Difficulty`、`Theme`、`Sound`、`Pause`
- 画布 + 提示 + `Restart`

## 6. 运行方式

```bash
cd /Users/liwenzhong/Desktop/Working/VSCode/Snake
python3 -m http.server 8765
```

打开：`http://127.0.0.1:8765/index.html`

## 7. 自检方法

### 7.1 当前可用方案
由于环境无 `node/deno/bun`，采用：
1. `osascript -l JavaScript` + 模拟 DOM/Canvas/Audio/Storage 进行逻辑回归
2. `python3 -m http.server` + `curl -I` 校验页面与资源可访问

### 7.2 本轮重点回归点
- 最高分是否会更新并持久化
- 音效开关是否生效并持久化
- 主题切换是否生效并持久化
- 贴图/背景资源是否可访问
- 原有玩法（暂停、难度、碰撞、重开）是否无回归

## 8. 协作约束（必须遵守）

用户明确要求：
- 每次代码修改后，必须同步更新 `README.md`
- 每次代码修改后，必须同步更新 `Memory.md`

推荐固定流程：
1. 改代码/资源
2. 更新 README
3. 更新 Memory
4. 回归测试
5. 汇报结果

## 9. 迭代时间线（摘要）

1. 初始化项目并实现基础贪吃蛇
2. 修复尾巴移动场景自撞误判
3. 增加暂停/继续、难度调节
4. 增加 `WASD` 与 `P` 快捷键
5. 增加角色/食物贴图与音效
6. 增加最高分持久化、音效开关、背景贴图主题切换（当前）

## 10. 下一步候选

- 加“重置最高分”按钮
- 音量滑块
- 更多主题包（含蛇/食物贴图联动）
- 可选网格开关

## 11. 快速接手清单

1. 打开 `README.md` 查看玩法与用户可见功能
2. 打开 `game.js` 重点看：
   `initPersistentSettings()`、`applyTheme()`、`toggleSound()`、`updateHighScoreIfNeeded()`
3. 启动本地服务手动试玩并刷新验证持久化
4. 改动后务必同步更新 README + Memory

