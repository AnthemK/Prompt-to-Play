# Codex 桌面宠物

这个目录用于保存 Codex 桌面宠物的设计资料、生成记录和最终资源。本文描述的是通用的 Codex v2 宠物生成与安装流程，不绑定某一只宠物或某台电脑。

## 最终交付物

一个可安装的 v2 宠物由以下文件组成：

```text
<pet-id>/
├── pet.json
└── spritesheet.webp
```

其中 `pet.json` 必须声明 `spriteVersionNumber: 2`。`spritesheet.webp` 是一个 8 列 × 11 行的透明精灵图：每格 `192 × 208` 像素，完整尺寸为 `1536 × 2288` 像素。

前 9 行是常规动画（idle、左右拖拽跑动、waving、jumping、failed、waiting、running、review）；最后 2 行提供 16 个顺时针视线方向。8 × 9 的常规动画图仅用于中间检查，不能作为新宠物安装。

## 默认目录

以下是 Codex 与 `hatch-pet` 流程默认使用的目录。`${CODEX_HOME:-$HOME/.codex}` 表示优先使用已设置的 `CODEX_HOME`，否则使用 `$HOME/.codex`。

| 用途 | 默认位置 | 说明 |
| --- | --- | --- |
| Codex 数据根目录 | `${CODEX_HOME:-$HOME/.codex}` | 所有下列 Codex 专用目录的根目录。 |
| 宠物生成规范与脚本 | `${CODEX_HOME:-$HOME/.codex}/skills/hatch-pet/` | 含 `scripts/`、`references/` 等确定性组装、验证与 QA 工具。 |
| 图像生成工具规范 | `${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/` | 生成宠物原图时遵循的图像生成工作流。 |
| 图像生成临时输出 | `${CODEX_HOME:-$HOME/.codex}/generated_images/` | 图像工具的临时文件；选中的图复制进运行目录后可清理。 |
| 已安装自定义宠物 | `${CODEX_HOME:-$HOME/.codex}/pets/<pet-id>/` | Codex 实际读取的安装目录，内含 `pet.json` 与 `spritesheet.webp`。 |

运行过程目录并没有由系统强制规定的默认位置：生成时通过 `--output-dir` 指定。为便于把素材和记录放在项目中，本仓库建议采用：

```text
$PROJECT_ROOT/codex-pet/runs/<YYYYMMDD-HHMMSS>-<pet-id>/
```

其中 `$PROJECT_ROOT` 是本仓库根目录。不要把工作目录误当作安装目录；只有复制到 `${CODEX_HOME:-$HOME/.codex}/pets/<pet-id>/` 后，宠物才会被 Codex 使用。

## 通用生成流程

1. 定义宠物
   确定 `pet-id`、显示名称、简介、视觉风格和参考图。没有参考图时，先生成一张主形象，作为后续所有动画的统一视觉依据。

2. 建立运行目录
   在 `codex-pet/runs/` 下创建本次运行目录，保存请求信息、提示词、参考图、生成结果和 QA 记录。不要直接在安装目录中制作或修改中间文件。

3. 生成并检查 9 行常规动画
   每一行都保持相同的轮廓、脸部、材质、配色与道具；其中 `running-left` 只有在镜像不会改变身份特征或道具语义时，才可由已验证的 `running-right` 确定性镜像得到。逐行检查帧数、裁切、背景、连通性与动画连续性。

4. 生成并检查 16 个视线方向
   先确认上、屏幕右、下、屏幕左四个基准方向，再按顺时针顺序生成两行各 8 格的连续视线动作。方向表现应来自宠物自然的头部、眼睛、身体或附属物运动，而非简单旋转整张精灵图。

5. 组装、清理与 QA
   用 `hatch-pet` 提供的脚本将帧组装成 8 × 11 图集，并只在最终图集上执行一次透明背景/chroma 清理。验证尺寸、v2 结构、常规动画预览、16 方向连续性，以及独立的方向语义检查；所有硬性问题修复后才能打包。

6. 安装
   将通过验证的 `spritesheet.webp` 与对应的 `pet.json` 一起放入安装目录。若更新外观或动作，应重新组装并验证完整图集后再覆盖安装文件。

## 推荐的运行目录结构

```text
codex-pet/runs/<timestamp>-<pet-id>/
├── pet_request.json          # 名称、描述、风格、chroma key 等请求信息
├── imagegen-jobs.json        # 图像任务与依赖关系
├── references/               # 用户参考图、canonical base、布局参考
├── prompts/                  # 每个图像任务的提示词
├── decoded/                  # 已选定并复制进来的原始生成图/行条
├── frames/                   # 从常规动画行提取的帧
├── qa/                       # contact sheet、预览、方向与验证报告
└── final/                    # 最终 spritesheet 与 validation JSON
```

完成并安装后，至少保留 `final/spritesheet-extended.webp`、`final/validation-extended.json` 及 `qa/` 中的关键检查报告。提示词、布局参考、行条、单帧和中间 8 × 9 图集可在不再需要排错时清理。

## 安装格式与命令

`pet.json` 的最小格式如下：

```json
{
  "id": "<pet-id>",
  "displayName": "<显示名称>",
  "description": "<一句话描述>",
  "spriteVersionNumber": 2,
  "spritesheetPath": "spritesheet.webp"
}
```

当最终图集已通过验证时，可按以下方式安装：

```bash
PET_ID="<pet-id>"
RUN_DIR="$PROJECT_ROOT/codex-pet/runs/<run-directory>"
PET_DIR="${CODEX_HOME:-$HOME/.codex}/pets/$PET_ID"

mkdir -p "$PET_DIR"
cp "$RUN_DIR/final/spritesheet-extended.webp" "$PET_DIR/spritesheet.webp"
```

随后将该宠物对应的 `pet.json` 写入 `$PET_DIR/pet.json`。两个文件必须成对更新。

## 更新与卸载

- 更新：保留旧运行目录用于追溯；在新的运行目录中完成生成和 QA，再覆盖 `${CODEX_HOME:-$HOME/.codex}/pets/<pet-id>/` 内的两个安装文件。
- 卸载：删除该宠物自己的安装目录即可，不会影响运行记录或其他宠物。

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/pets/<pet-id>"
```

如果安装后界面未立即刷新，可重新加载 Codex 窗口或重启相关任务。
