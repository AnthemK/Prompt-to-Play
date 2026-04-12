# Novel Workspace

这个目录用于管理多个网络小说项目，以及它们之间可复用的创作经验。

## 设计目标

- 一个小说任务一个目录，避免设定、提纲、正文互相污染
- 跨项目经验单独沉淀，避免埋进某个具体项目里
- 文档按“读者和用途”分层，不把说明、交接、路线图写混
- 让人和 agent 都能快速接手当前项目

## 目录结构

```text
Novel/
  README.md
  MEMORY.md
  TODO.md
  shared/
    README.md
    NOVEL_PLAYBOOK.md
    STAGE_UPDATES.md
    templates/
      project-template/
  projects/
    README.md
  archive/
    README.md
```

## 目录职责

- `README.md`
  - 根导航
  - 说明整体结构与使用规则
- `MEMORY.md`
  - 当前工作区状态
  - 给后续接手者的快速交接页
- `TODO.md`
  - 工作区级别的改进事项
  - 不写具体某本书的剧情计划
- `shared/`
  - 跨项目可复用经验、模板、流程约定
- `projects/`
  - 每个具体小说项目各自独立管理
- `archive/`
  - 已暂停、已完结或只留档不继续推进的项目

## 项目内推荐结构

每个具体小说项目都建议从 `shared/templates/project-template/` 复制一份开始，再按需要增删。

核心原则：

- `README.md`
  - 只回答“这本书现在是什么、要写什么、先看哪里”
- `MEMORY.md`
  - 只记录当前进度、关键决定、已知风险、接手提示
- `TODO.md`
  - 只记录下一阶段计划和优先级
- `docs/`
  - 放长期参考资料，例如世界观、角色圣经、主线蓝图、文风规则
- `01-planning/`
  - 立项、定位、卖点、题材判断
- `02-outlines/`
  - 卷纲、章纲、关系图、节奏表
- `03-drafts/`
  - 正文草稿
- `04-revision/`
  - 审校、重写、问题单
- `05-release/`
  - 对外版本、投稿稿、发布说明

## 使用约定

- 新开一本书时，在 `projects/` 下新建一个英文或拼音 slug 目录
- 项目名尽量稳定；对外中文名可以写在项目内文档，不必硬写进路径
- 跨项目经验先记到 `shared/STAGE_UPDATES.md`
- 稳定后再整理进 `shared/NOVEL_PLAYBOOK.md`
- 不要把某本书的专属设定写进 `shared/`

## 为什么这样分

这个结构借鉴了同仓库里已有的两类经验：

- 共享经验区应独立存在，而不是散落在项目内部
- `README / MEMORY / TODO / docs` 需要明确边界，否则长期协作会迅速失焦

这两点对写小说比对做游戏更重要，因为设定、提纲、正文、复盘天然更容易互相混写。
