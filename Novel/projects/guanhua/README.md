# 观化

暂定类型：仙侠长篇

当前主宗门：

- 太一门

## 语言约定

《观化》是一部中文小说。

默认规则：

- 所有创作性文档以中文为准
- 设定、人物、大纲、正文都直接用中文撰写
- 若引用外部理论或方法，可保留少量英文关键词，但不应让英文成为主表达

## 这个项目是什么

《观化》是 `Novel` 工作区下的第一本正式小说项目。

当前阶段已经完成卷一骨架搭建，并已进入正文前段试写与复核。

当前最重要的三件事是：

1. 继续收束卷一高频写作接口
2. 继续校准人物回填、群像分布与正文文气
3. 在不破坏边界的前提下推进卷一细纲和正文

## 当前推荐流程

相比“基础设定 -> 大纲 -> 正文”的粗线流程，这个项目采用更细的七阶段路径：

1. `00-reference/`
   - 先整理外部参考、研究问题与可借鉴材料
2. `01-foundations/`
   - 先定义题材承诺、核心卖点、主题问题、研究边界
3. `02-setting/`
   - 再建立世界规则、修行体系、势力结构、历史时间线
4. `03-characters/`
   - 明确主角与核心角色的功能、关系、弧光和阶段变化
5. `04-plot/`
   - 先搭长线故事引擎，再拆卷纲和章纲
6. `05-drafts/`
   - 在规则和提纲已经过压力测试后进入正文
7. `06-revision/`
   - 先做结构修订，再做连续性审计，再做语言层修整
8. `07-release/`
   - 整理对外版本、简介、投稿或发布材料

这个流程的核心判断是：

- 世界观不能脱离冲突和人物空转
- 角色弧光不能等正文时再临时补
- 大纲必须建立在“规则可运行、人物可推动”的前提上

## 当前文档边界补充

### 正式层与运行层

这个项目顶层明确分为两类：

- 正式层
  - `docs/`
  - `01-foundation/` 到 `07-release/`
- 运行层
  - `08-experimental-writing/`
  - `09-cache/`

正式层负责长期维护和唯一出处。

运行层只服务当前任务与实验流程，不应沉淀成第二知识库。

### 索引类型

项目中的索引职责固定区分为四类：

1. `README`
   - 目录入口
2. `index`
   - 人工阅读索引
3. `meta`
   - 结构化导航索引
4. `cache`
   - 当前任务的临时上下文包

### 人物文档

人物文档需要区分两层：

1. 基础设定
   - 出身、位置、性格、能力、欲望、缺陷、初始关系
2. 剧情后变化
   - 某个阶段后发生的位移、关系变化、判断变化与代价

不能把这两层混成一团。

### `04-plot/` 与 `05-drafts/`

- `04-plot/`
  - 只放结构性文档
  - 包括卷纲、章纲、逐章功能表、正文细纲、伏笔账本、骨架复核
- `05-drafts/`
  - 只放正文草稿
  - 包括章节初稿、场景草稿、试写片段与连贯小说文本

判断标准：

- 如果文档主要服务作者排结构，放 `04-plot/`
- 如果文档主要服务读者阅读文本，放 `05-drafts/`

## 先看哪里

- 项目状态与交接：
  - `MEMORY.md`
- 当前阶段任务：
  - `TODO.md`
- 写作流程：
  - `docs/WORKFLOW.md`
- 文档边界：
  - `docs/DOC_GOVERNANCE.md`
- 命名规则：
  - `docs/NAMING_RULES.md`
- 质量标准：
  - `docs/QUALITY_BARS.md`
- 小说本体文风原则：
  - `01-foundation/novel-style-principles.md`
- 写作执行规则：
  - `docs/WRITING_EXECUTION_RULES.md`
- 外部参考与研究：
  - `00-reference/README.md`
- 立项与题材承诺：
  - `01-foundation/README.md`
- 世界设定：
  - `02-setting/README.md`
- 角色系统：
  - `03-characters/README.md`
- 大纲与细纲：
  - `04-plot/README.md`
- 正式正文草稿：
  - `05-drafts/README.md`
- 修订问题：
  - `06-revision/README.md`
- 对外材料：
  - `07-release/README.md`
- 实验性写作：
  - `08-experimental-writing/README.md`

## 树型阅读原则

这个项目采用：

- 树型分层
- 逐层展开
- 唯一出处

更具体地说：

- 当前层 README 先概括本层整体内容
- 若要继续深入，先进入下一层目录
- 进入下一层后，优先读下一层 README
- 具体内容只在唯一权威文件中出现，其他地方只做引用与指路

## 目录结构

```text
guanhua/
  README.md
  MEMORY.md
  TODO.md
  docs/
  00-reference/
  01-foundation/
  02-setting/
    README.md
    assets/
    01-foundations/
    02-world-order/
    03-taiyi/
      01-overview/
      02-organization/
      03-curriculum-and-operations/
      04-lineages/
      assets/
  03-characters/
  04-plot/
    volume-01/
  05-drafts/
  06-revision/
  07-release/
```
