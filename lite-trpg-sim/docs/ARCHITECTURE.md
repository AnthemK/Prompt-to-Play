# Architecture Guide

本文档描述当前代码库的高层结构，重点回答三个问题：

1. 哪些代码属于系统层，哪些属于故事层
2. 前后端如何协作
3. 新功能应该落在哪一层

## 1. 设计目标

- 让“故事内容”和“游戏系统”解耦
- 让前端尽量不关心题材、分支条件、规则细节
- 让后端可以通过统一接口挂接不同故事包
- 让新机制先成为通用系统能力，再被故事包消费

## 2. 目录分层

```text
lite-trpg-sim/
  launcher.py               # 本地启动器
  frontend/                 # 通用浏览器 UI
  backend/
    server.py              # HTTP API 边界
    game/                  # 系统层：引擎 / 规则 / 解释器 / 运行时接口
    stories/               # 内容层：story pack 数据与作者文档
  docs/                     # 分级技术文档
```

## 3. 系统层职责

### `backend/game/engine.py`

- 管理会话
- 管理存档与读档
- 聚合前端视图
- 只依赖 `StoryRuntime`，不依赖具体题材

### `backend/game/story_interface.py`

- 定义统一故事运行时接口
- `GameEngine` 与具体故事实现之间的唯一契约

### `backend/game/story_runtime.py`

- 当前的默认故事实现
- 输入是已归一化的 story pack 数据
- 输出是引擎可消费的运行时行为

### `backend/game/content.py`

- 扫描 `backend/stories/*`
- 加载 `story.json` / `story.yaml`
- 做最小字段校验与默认值填充

### `backend/game/adventure.py`

- 通用节点解释器
- 负责执行 node/action/effect DSL
- 负责遭遇态启动、推进、结束
- 负责遭遇阶段切换、阶段动作合并、回合规则执行

### `backend/game/rules.py`

- 轻量规则层
- 负责资源、状态、检定、被动效果生命周期
- 当前统一结算已覆盖 `check/save/contest/damage`
- `damage` 当前支持伤害类型、平减伤、百分比减伤、穿透、目标切换（player/enemy）

### `backend/game/resolution.py`

- 统一结算输出结构
- 用来把“发生了什么、为什么发生、影响了什么”记录成一套标准 payload

## 4. 内容层职责

### `backend/stories/<story_id>/story.json|yaml`

故事包负责：

- 世界观
- 剧情文本
- 职业模板
- 物品、状态、结局
- 节点、行动、效果、遭遇模板
- 故事级规则参数

故事包不应该负责：

- HTTP 协议
- 前端渲染逻辑
- 存档实现细节
- 题材专属 Python/JS 代码

## 5. 前后端数据流

### 开局

1. 前端请求 `GET /api/meta`
2. 用户选择故事包、名字、职业
3. 前端请求 `POST /api/game/new`
4. 后端返回标准 `view`
5. 前端只渲染 `view`

### 行动推进

1. 前端点击某个 `action_id`
2. 前端请求 `POST /api/game/{session_id}/action`
3. 后端执行故事解释器与规则层
4. 后端返回新的 `view`
5. 前端刷新主界面并触发本地自动存档

### 存档

1. 前端请求 `POST /api/game/{session_id}/save`
2. 后端返回 canonical save payload
3. 前端把该 payload 存进本地槽位或导出文件

## 6. 新功能落点规则

### 应放到系统层的内容

- 新的 effect/op
- 新的遭遇类型
- 新的检定或结算机制
- 新的状态生命周期
- 新的通用视图字段
- 新的存档结构

### 应放到故事层的内容

- 新世界观文本
- 新职业数值
- 新节点与分支
- 新结局
- 某个故事专属的敌人、地点、事件

## 7. 当前架构边界

当前架构已经做到：

- 前端不写具体剧情
- 引擎不写具体题材常量
- 故事包可切换
- 统一结算开始成形
- 遭遇态进入正式 state/save/view

当前仍需继续演进：

- 技能层与熟练
- 更完整的 encounter 模型
- 更强的 effect 生命周期
- 更强的 schema 校验和工具链
